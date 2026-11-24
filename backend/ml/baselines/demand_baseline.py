import numpy as np
import pandas as pd
from typing import Dict, Tuple


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Computes WAPE, MAE, and RMSE.
    WAPE = sum(|y - y_hat|) / sum(y)
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    # Avoid division by zero
    sum_true = np.sum(y_true)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    wape = float(np.sum(np.abs(y_true - y_pred)) / sum_true) if sum_true > 0 else 0.0

    return {
        "wape": round(wape, 4),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
    }


class SeasonalNaiveDemandBaseline:
    """
    Seasonal Naive baseline: predicts y_t = y_{t-seasonality} (default: 7 days).
    If lag is unavailable, falls back to the rolling historical mean.
    """

    def __init__(self, seasonality: int = 7):
        self.seasonality = seasonality
        self.default_mean = 0.0

    def fit(self, y: pd.Series):
        self.default_mean = float(y.mean()) if len(y) > 0 else 0.0

    def predict(self, y_history: pd.Series, horizon: int) -> np.ndarray:
        history = list(y_history)
        preds = []
        for i in range(horizon):
            if len(history) >= self.seasonality:
                pred = history[-self.seasonality]
            else:
                pred = self.default_mean
            preds.append(max(0.0, float(pred)))
            history.append(pred)
        return np.array(preds)

