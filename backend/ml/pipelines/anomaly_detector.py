import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
from sklearn.ensemble import IsolationForest


class AnomalyDetectorPipeline:
    def __init__(self, contamination: float = 0.03):
        self.contamination = contamination

    def detect_sales_anomalies(self, daily_sales: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detects spikes or drops in daily sales using Isolation Forest + rolling Z-score.
        """
        if len(daily_sales) < 7:
            return []

        df = daily_sales.copy().sort_values("date").reset_index(drop=True)
        quantities = df["quantity"].values.reshape(-1, 1)

        iso = IsolationForest(contamination=self.contamination, random_state=42)
        preds = iso.fit_predict(quantities)
        scores = iso.decision_function(quantities)

        mean_qty = float(np.mean(quantities))
        std_qty = float(np.std(quantities)) if np.std(quantities) > 0 else 1.0

        anomalies = []
        for i, (pred, score) in enumerate(zip(preds, scores)):
            val = float(quantities[i][0])
            z_score = (val - mean_qty) / std_qty

            if pred == -1 or abs(z_score) >= 2.5:
                if z_score > 0:
                    anom_type = "SALES_SPIKE"
                    severity = "HIGH" if z_score > 3.5 else "MEDIUM"
                else:
                    anom_type = "SALES_DROP"
                    severity = "CRITICAL" if z_score < -3.0 else "HIGH"

                anomalies.append({
                    "date": str(df.iloc[i]["date"]),
                    "anomaly_type": anom_type,
                    "severity": severity,
                    "actual_value": val,
                    "expected_mean": round(mean_qty, 1),
                    "z_score": round(z_score, 2),
                    "anomaly_score": round(float(score), 4),
                    "evidence": {
                        "date": str(df.iloc[i]["date"]),
                        "sales_quantity": val,
                        "rolling_mean": round(mean_qty, 1),
                        "deviation_sigma": round(z_score, 2),
                    },
                })

        return anomalies

    def detect_supplier_delivery_anomalies(self, purchase_orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects severe delivery delays compared to promised lead times.
        """
        anomalies = []
        for po in purchase_orders:
            expected = po.get("expected_delivery")
            actual = po.get("actual_delivery")
            if expected and actual:
                exp_date = pd.to_datetime(expected)
                act_date = pd.to_datetime(actual)
                delay_days = (act_date - exp_date).days

                if delay_days >= 5:
                    severity = "CRITICAL" if delay_days >= 10 else "HIGH"
                    anomalies.append({
                        "entity_id": po.get("supplier_id"),
                        "anomaly_type": "SUPPLIER_DELIVERY_DELAY",
                        "severity": severity,
                        "delay_days": delay_days,
                        "evidence": {
                            "po_id": po.get("id"),
                            "expected_delivery": str(expected),
                            "actual_delivery": str(actual),
                            "delay_days": delay_days,
                        },
                    })

        return anomalies

