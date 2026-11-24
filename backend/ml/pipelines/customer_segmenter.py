import numpy as np
import pandas as pd
from typing import Any, Dict, List, Tuple
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


class CustomerSegmenterPipeline:
    def __init__(self, n_clusters: int = 5):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans: Optional[KMeans] = None
        self.silhouette: float = 0.0

    def fit_and_segment(self, df_rfm: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Runs RFM standardization, fits KMeans, and assigns business-interpretable segment names.
        """
        if len(df_rfm) < self.n_clusters:
            # Fallback for very small customer bases
            df_out = df_rfm.copy()
            df_out["segment"] = "New Customers"
            return df_out, {"silhouette_score": 0.0, "clusters": 1}

        rfm_features = df_rfm[["recency_days", "frequency", "monetary_value"]].copy()

        # Log transform to handle skewness
        log_rfm = np.log1p(rfm_features)
        scaled_rfm = self.scaler.fit_transform(log_rfm)

        # Optimize k between 3 and 6 if sufficient data
        best_k = min(self.n_clusters, len(df_rfm) - 1)
        best_score = -1.0
        best_km = None

        for k in range(3, min(6, len(df_rfm))):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(scaled_rfm)
            score = silhouette_score(scaled_rfm, labels)
            if score > best_score:
                best_score = score
                best_k = k
                best_km = km

        if best_km is None:
            best_km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            best_km.fit(scaled_rfm)
            best_score = 0.5

        self.kmeans = best_km
        self.silhouette = float(best_score)

        df_out = df_rfm.copy()
        cluster_labels = self.kmeans.labels_
        df_out["cluster"] = cluster_labels

        # Map cluster centers to business segment titles
        cluster_stats = df_out.groupby("cluster").agg({
            "recency_days": "mean",
            "frequency": "mean",
            "monetary_value": "mean",
        })

        segment_mapping = {}
        for c_id, row in cluster_stats.iterrows():
            r = row["recency_days"]
            f = row["frequency"]
            m = row["monetary_value"]

            if m >= cluster_stats["monetary_value"].quantile(0.7) and r <= cluster_stats["recency_days"].median():
                segment = "High-Value Customers"
            elif f >= cluster_stats["frequency"].median() and r <= cluster_stats["recency_days"].median():
                segment = "Loyal Customers"
            elif r > cluster_stats["recency_days"].quantile(0.7) and m >= cluster_stats["monetary_value"].median():
                segment = "At-Risk Customers"
            elif r > cluster_stats["recency_days"].quantile(0.8):
                segment = "Inactive Customers"
            elif f <= 2 and r <= 30:
                segment = "New Customers"
            else:
                segment = "Potential Loyalists"

            segment_mapping[c_id] = segment

        df_out["segment"] = df_out["cluster"].map(segment_mapping)

        return df_out, {
            "silhouette_score": round(self.silhouette, 4),
            "clusters_count": int(best_k),
            "segment_distribution": df_out["segment"].value_counts().to_dict(),
        }

