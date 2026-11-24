import numpy as np
import pandas as pd
from typing import Dict


def calculate_revenue_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    sum_true = np.sum(y_true)
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    wape = float(np.sum(np.abs(y_true - y_pred)) / sum_true) if sum_true > 0 else 0.0

    return {
        "wape": round(wape, 4),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
    }


class MovingAverageRevenueBaseline:
    """
    Predicts future daily revenue using a rolling 30-day moving average.
    """

    def __init__(self, window: int = 30):
        self.window = window
        self.rolling_mean = 0.0

    def fit(self, y: pd.Series):
        self.rolling_mean = float(y.tail(self.window).mean()) if len(y) > 0 else 0.0

    def predict(self, horizon: int) -> np.ndarray:
        return np.full(horizon, max(0.0, self.rolling_mean))

