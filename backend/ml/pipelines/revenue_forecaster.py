import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from xgboost import XGBRegressor

from ml.baselines.revenue_baseline import MovingAverageRevenueBaseline, calculate_revenue_metrics
from ml.features.revenue_features import (
    REVENUE_FEATURE_COLUMNS,
    create_revenue_forecast_features,
)


class RevenueForecasterPipeline:
    def __init__(self, model_version: str = "v1.0.0"):
        self.model_version = model_version
        self.model: Optional[XGBRegressor] = None
        self.baseline = MovingAverageRevenueBaseline(window=30)
        self.metrics: Dict[str, Dict[str, float]] = {}
        self.residual_std = 0.0

    def train_and_evaluate(self, df_daily_revenue: pd.DataFrame) -> Dict[str, Any]:
        df_featured = create_revenue_forecast_features(df_daily_revenue)

        if len(df_featured) < 10:
            self.baseline.fit(df_featured["revenue"])
            return {
                "status": "trained_baseline_fallback",
                "xgboost_metrics": {"wape": 0.0, "mae": 0.0, "rmse": 0.0},
                "baseline_metrics": {"wape": 0.0, "mae": 0.0, "rmse": 0.0},
            }

        split_idx = int(len(df_featured) * 0.8)
        train_df = df_featured.iloc[:split_idx]
        test_df = df_featured.iloc[split_idx:]

        X_train = train_df[REVENUE_FEATURE_COLUMNS]
        y_train = train_df["revenue"]
        X_test = test_df[REVENUE_FEATURE_COLUMNS]
        y_test = test_df["revenue"]

        # Train XGBoost
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
        xgb_metrics = calculate_revenue_metrics(y_test.values, y_pred_xgb)

        # Baseline
        self.baseline.fit(y_train)
        y_pred_base = self.baseline.predict(len(y_test))
        base_metrics = calculate_revenue_metrics(y_test.values, y_pred_base)

        residuals = y_test.values - y_pred_xgb
        self.residual_std = float(np.std(residuals)) if len(residuals) > 1 else 100.0

        self.metrics = {
            "xgboost": xgb_metrics,
            "moving_average_baseline": base_metrics,
        }

        # Retrain on all data
        self.model.fit(df_featured[REVENUE_FEATURE_COLUMNS], df_featured["revenue"])
        self.baseline.fit(df_featured["revenue"])

        return {
            "status": "success",
            "model_version": self.model_version,
            "xgboost_metrics": xgb_metrics,
            "baseline_metrics": base_metrics,
            "beats_baseline": (xgb_metrics["wape"] <= base_metrics["wape"]),
        }

    def predict_future(self, df_daily_revenue: pd.DataFrame, horizons: List[int] = [7, 30, 90]) -> Dict[str, Any]:
        df_featured = create_revenue_forecast_features(df_daily_revenue)
        max_horizon = max(horizons)

        current_df = df_featured.copy()
        last_date = current_df["date"].max()
        future_predictions = []
        history_revenue = list(current_df["revenue"])

        for step in range(1, max_horizon + 1):
            next_date = last_date + pd.Timedelta(days=step)
            day_of_week = next_date.dayofweek
            day_of_month = next_date.day
            month = next_date.month
            is_weekend = int(day_of_week in [5, 6])

            lag_1 = history_revenue[-1]
            lag_7 = history_revenue[-7] if len(history_revenue) >= 7 else lag_1
            lag_14 = history_revenue[-14] if len(history_revenue) >= 14 else lag_7
            lag_28 = history_revenue[-28] if len(history_revenue) >= 28 else lag_14

            rolling_mean_7 = float(np.mean(history_revenue[-7:]))
            rolling_std_7 = float(np.std(history_revenue[-7:]))
            rolling_mean_30 = float(np.mean(history_revenue[-30:]))

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
            }])[REVENUE_FEATURE_COLUMNS]

            if self.model is not None:
                predicted_rev = float(np.maximum(0.0, self.model.predict(features)[0]))
            else:
                predicted_rev = float(self.baseline.predict(1)[0])

            history_revenue.append(predicted_rev)

            # 95% Confidence Bounds (1.96 * residual std)
            bound_margin = max(50.0, 1.96 * self.residual_std)
            lower_bound = max(0.0, predicted_rev - bound_margin)
            upper_bound = predicted_rev + bound_margin

            future_predictions.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "predicted_revenue": round(predicted_rev, 2),
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
            })

        forecasts_by_horizon = {}
        for h in horizons:
            subset = future_predictions[:h]
            tot = sum(p["predicted_revenue"] for p in subset)
            forecasts_by_horizon[f"{h}_days"] = {
                "horizon_days": h,
                "total_predicted_revenue": round(tot, 2),
                "daily_average": round(tot / h, 2),
                "daily_breakdown": subset,
            }

        return {
            "forecasts": forecasts_by_horizon,
            "metrics": self.metrics,
        }

