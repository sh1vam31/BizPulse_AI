import numpy as np
import pandas as pd
from typing import Tuple


FEATURE_COLUMNS = [
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


def create_demand_features(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame with columns ['date', 'quantity'], returns a DataFrame with engineered lag
    and rolling features.
    """
    df = df_daily.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Ensure continuous daily date index
    if len(df) > 1:
        full_idx = pd.date_range(start=df["date"].min(), end=df["date"].max(), freq="D")
        df = df.set_index("date").reindex(full_idx, fill_value=0).reset_index()
        df.rename(columns={"index": "date"}, inplace=True)

    # Lags
    df["lag_1"] = df["quantity"].shift(1)
    df["lag_7"] = df["quantity"].shift(7)
    df["lag_14"] = df["quantity"].shift(14)
    df["lag_28"] = df["quantity"].shift(28)

    # Rolling statistics
    df["rolling_mean_7"] = df["quantity"].shift(1).rolling(window=7, min_periods=1).mean()
    df["rolling_std_7"] = df["quantity"].shift(1).rolling(window=7, min_periods=1).std().fillna(0)
    df["rolling_mean_30"] = df["quantity"].shift(1).rolling(window=30, min_periods=1).mean()

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Fill initial NaNs with backfill/zero
    for col in ["lag_1", "lag_7", "lag_14", "lag_28", "rolling_mean_7", "rolling_mean_30"]:
        df[col] = df[col].bfill().fillna(0)
    df["rolling_std_7"] = df["rolling_std_7"].fillna(0)

    return df


def prepare_train_test_split(df_featured: pd.DataFrame, test_days: int = 14) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Time-aware train/test split.
    """
    if len(df_featured) <= test_days:
        split_idx = int(len(df_featured) * 0.8)
    else:
        split_idx = len(df_featured) - test_days

    train_df = df_featured.iloc[:split_idx].copy()
    test_df = df_featured.iloc[split_idx:].copy()
    return train_df, test_df

