import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple


REVENUE_FEATURE_COLUMNS = [
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_std_7",
    "rolling_mean_30",
    "day_of_week",
    "day_of_month",
    "month",
    "is_weekend",
]


CHURN_FEATURE_COLUMNS = [
    "recency_days",
    "frequency",
    "monetary_value",
    "avg_order_value",
    "tenure_days",
    "frequency_trend_slope",
]


def create_revenue_forecast_features(df_daily: pd.DataFrame) -> pd.DataFrame:
    df = df_daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if len(df) > 1:
        full_idx = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
        df = df.set_index("date").reindex(full_idx, fill_value=0).reset_index()
        df.rename(columns={"index": "date"}, inplace=True)

    df["lag_1"] = df["revenue"].shift(1)
    df["lag_7"] = df["revenue"].shift(7)
    df["lag_14"] = df["revenue"].shift(14)
    df["lag_28"] = df["revenue"].shift(28)

    df["rolling_mean_7"] = df["revenue"].shift(1).rolling(window=7, min_periods=1).mean()
    df["rolling_std_7"] = df["revenue"].shift(1).rolling(window=7, min_periods=1).std().fillna(0)
    df["rolling_mean_30"] = df["revenue"].shift(1).rolling(window=30, min_periods=1).mean()

    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    for col in ["lag_1", "lag_7", "lag_14", "lag_28", "rolling_mean_7", "rolling_mean_30"]:
        df[col] = df[col].bfill().fillna(0)
    df["rolling_std_7"] = df["rolling_std_7"].fillna(0)

    return df


def compute_customer_rfm_features(
    df_transactions: pd.DataFrame, reference_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Computes RFM metrics and purchase velocity for each customer.
    Columns required in df_transactions: ['customer_id', 'transaction_date', 'total_amount']
    """
    if df_transactions.empty:
        return pd.DataFrame(columns=["customer_id"] + CHURN_FEATURE_COLUMNS + ["churn"])

    df = df_transactions.copy()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    ref_date = reference_date or df["transaction_date"].max()

    rows = []
    for cust_id, group in df.groupby("customer_id"):
        tx_dates = group["transaction_date"].sort_values()
        amounts = group["total_amount"].astype(float)

        last_date = tx_dates.max()
        first_date = tx_dates.min()

        recency = max(0, (ref_date - last_date).days)
        frequency = len(tx_dates)
        monetary = float(amounts.sum())
        aov = monetary / frequency if frequency > 0 else 0.0
        tenure = max(1, (ref_date - first_date).days)

        # Velocity: purchases in last 30d vs prior 60d
        cutoff_30 = ref_date - pd.Timedelta(days=30)
        cutoff_90 = ref_date - pd.Timedelta(days=90)

        recent_30_count = len(group[group["transaction_date"] >= cutoff_30])
        prior_60_count = len(group[(group["transaction_date"] >= cutoff_90) & (group["transaction_date"] < cutoff_30)])
        prior_monthly_avg = max(0.5, prior_60_count / 2.0)
        velocity = recent_30_count / prior_monthly_avg

        # Churn definition: If inactive for > 60 days or recency > 2.5 * avg cycle
        avg_cycle = tenure / frequency if frequency > 1 else 45.0
        is_churn = int(recency > 60 and recency > (avg_cycle * 1.5))

        rows.append({
            "customer_id": cust_id,
            "recency_days": recency,
            "frequency": frequency,
            "monetary_value": round(monetary, 2),
            "avg_order_value": round(aov, 2),
            "tenure_days": tenure,
            "frequency_trend_slope": round(velocity, 4),
            "churn": is_churn,
        })

    return pd.DataFrame(rows)
