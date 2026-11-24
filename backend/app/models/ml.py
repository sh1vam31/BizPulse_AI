from sqlalchemy import Column, DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid, utc_now


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_name = Column(String(100), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    algorithm = Column(String(100), nullable=False)
    metrics = Column(JSON, nullable=True)
    artifact_path = Column(String(255), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, DEPRECATED, CANDIDATE
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    predictions = relationship("Prediction", back_populates="model_version", cascade="all, delete-orphan")
    churn_predictions = relationship("ChurnPrediction", back_populates="model_version")
    revenue_forecasts = relationship("RevenueForecast", back_populates="model_version")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # Product, Customer, Revenue
    entity_id = Column(String(36), nullable=False, index=True)
    prediction_type = Column(String(50), nullable=False)  # DEMAND_FORECAST, CHURN, REVENUE
    prediction_value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    model_version = relationship("ModelVersion", back_populates="predictions")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # Product, Supplier, Sales, Revenue
    entity_id = Column(String(36), nullable=False, index=True)
    anomaly_type = Column(String(100), nullable=False)  # INVENTORY_DROP, SALES_SPIKE, REVENUE_DROP, SUPPLIER_DELAY
    severity = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    anomaly_score = Column(Numeric(6, 4), nullable=True)
    evidence = Column(JSON, nullable=True)
    detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

