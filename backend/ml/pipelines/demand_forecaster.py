import os
import joblib
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from xgboost import XGBRegressor

from app.core.config import settings
from ml.baselines.demand_baseline import SeasonalNaiveDemandBaseline, calculate_metrics
from ml.features.demand_features import (
    FEATURE_COLUMNS,
    create_demand_features,
    prepare_train_test_split,
)


class DemandForecasterPipeline:
    def __init__(self, model_version: str = "v1.0.0"):
        self.model_version = model_version
        self.model: Optional[XGBRegressor] = None
        self.baseline = SeasonalNaiveDemandBaseline(seasonality=7)
        self.metrics: Dict[str, Dict[str, float]] = {}
        self.is_fitted = False

    def train_and_evaluate(self, df_daily: pd.DataFrame) -> Dict[str, Any]:
        """
        Trains XGBoost Regressor on historical daily sales and evaluates against Seasonal Naive Baseline.
        """
        df_featured = create_demand_features(df_daily)

        if len(df_featured) < 10:
            # Insufficient rows for full time split; train simple baseline
            self.baseline.fit(df_featured["quantity"])
            self.is_fitted = True
            return {
                "status": "trained_baseline_fallback",
                "reason": "Insufficient history (< 10 days)",
                "xgboost_metrics": {"wape": 0.0, "mae": 0.0, "rmse": 0.0},
                "baseline_metrics": {"wape": 0.0, "mae": 0.0, "rmse": 0.0},
            }

        train_df, test_df = prepare_train_test_split(df_featured, test_days=min(14, int(len(df_featured) * 0.2)))

        X_train = train_df[FEATURE_COLUMNS]
        y_train = train_df["quantity"]
        X_test = test_df[FEATURE_COLUMNS]
        y_test = test_df["quantity"]

        # 1. Train XGBoost Regressor
        self.model = XGBRegressor(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

        y_pred_xgb = np.maximum(0.0, self.model.predict(X_test))
        xgb_metrics = calculate_metrics(y_test.values, y_pred_xgb)

        # 2. Fit Seasonal Naive Baseline on training portion
        self.baseline.fit(y_train)
        y_pred_base = self.baseline.predict(y_train, horizon=len(y_test))
        base_metrics = calculate_metrics(y_test.values, y_pred_base)

        self.metrics = {
            "xgboost": xgb_metrics,
            "seasonal_naive_baseline": base_metrics,
        }

        # Retrain model on full dataset for future inference
        self.model.fit(df_featured[FEATURE_COLUMNS], df_featured["quantity"])
        self.baseline.fit(df_featured["quantity"])
        self.is_fitted = True

        return {
            "status": "success",
            "model_version": self.model_version,
            "xgboost_metrics": xgb_metrics,
            "baseline_metrics": base_metrics,
            "beats_baseline": (xgb_metrics["wape"] <= base_metrics["wape"]),
        }

    def predict_future(self, df_daily: pd.DataFrame, horizons: List[int] = [7, 14, 30]) -> Dict[str, Any]:
        """
        Generates recursive forecasts for next 7, 14, and 30 days.
        """
        df_featured = create_demand_features(df_daily)
        max_horizon = max(horizons)

        current_df = df_featured.copy()
        last_date = current_df["date"].max()
        future_predictions: List[Dict[str, Any]] = []

        history_quantities = list(current_df["quantity"])

        for step in range(1, max_horizon + 1):
            next_date = last_date + pd.Timedelta(days=step)
            day_of_week = next_date.dayofweek
            day_of_month = next_date.day
            month = next_date.month
            is_weekend = int(day_of_week in [5, 6])

            lag_1 = history_quantities[-1]
            lag_7 = history_quantities[-7] if len(history_quantities) >= 7 else lag_1
            lag_14 = history_quantities[-14] if len(history_quantities) >= 14 else lag_7
            lag_28 = history_quantities[-28] if len(history_quantities) >= 28 else lag_14

            rolling_mean_7 = float(np.mean(history_quantities[-7:]))
            rolling_std_7 = float(np.std(history_quantities[-7:]))
            rolling_mean_30 = float(np.mean(history_quantities[-30:]))

            features = pd.DataFrame([{
                "lag_1": lag_1,
                "lag_7": lag_7,
                "lag_14": lag_14,
                "lag_28": lag_28,
                "rolling_mean_7": rolling_mean_7,
                "rolling_std_7": rolling_std_7,
                "rolling_mean_30": rolling_mean_30,
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "month": month,
                "is_weekend": is_weekend,
            }])[FEATURE_COLUMNS]

            if self.model is not None:
                predicted_qty = float(np.maximum(0.0, self.model.predict(features)[0]))
            else:
                predicted_qty = float(np.maximum(0.0, self.baseline.predict(pd.Series(history_quantities), 1)[0]))

            history_quantities.append(predicted_qty)

            future_predictions.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "predicted_quantity": round(predicted_qty, 1),
            })

        # Aggregate forecasts by horizon
        forecasts_by_horizon = {}
        for h in horizons:
            subset = future_predictions[:h]
            total_predicted = sum(p["predicted_quantity"] for p in subset)
            daily_avg = total_predicted / h
            forecasts_by_horizon[f"{h}_days"] = {
                "horizon_days": h,
                "total_demand": round(total_predicted, 1),
                "daily_average": round(daily_avg, 1),
                "daily_breakdown": subset,
            }

        return {
            "forecasts": forecasts_by_horizon,
            "metrics": self.metrics,
        }

    def save_artifact(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({"model": self.model, "baseline": self.baseline, "metrics": self.metrics}, filepath)

    def load_artifact(self, filepath: str):
        data = joblib.load(filepath)
        self.model = data.get("model")
        self.baseline = data.get("baseline")
        self.metrics = data.get("metrics", {})
        self.is_fitted = True
