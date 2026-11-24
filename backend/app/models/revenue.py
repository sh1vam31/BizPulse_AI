from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid, utc_now


class CustomerFeatures(Base):
    __tablename__ = "customer_features"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    recency_days = Column(Integer, nullable=False)
    frequency = Column(Integer, nullable=False)
    monetary_value = Column(Numeric(12, 2), nullable=False)
    avg_order_value = Column(Numeric(12, 2), nullable=False)
    tenure_days = Column(Integer, nullable=False)
    frequency_trend_slope = Column(Numeric(8, 4), default=0.0, nullable=False)
    computed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    customer = relationship("Customer", back_populates="features")


class ChurnPrediction(Base):
    __tablename__ = "churn_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    churn_probability = Column(Numeric(5, 4), nullable=False)
    risk_category = Column(String(50), nullable=False)  # Low, Medium, High, Critical
    contributing_features = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    customer = relationship("Customer", back_populates="churn_predictions")
    model_version = relationship("ModelVersion", back_populates="churn_predictions")


class RevenueForecast(Base):
    __tablename__ = "revenue_forecasts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id = Column(String(36), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    forecast_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(20), default="DAILY", nullable=False)  # DAILY, WEEKLY, MONTHLY
    predicted_revenue = Column(Numeric(14, 2), nullable=False)
    lower_bound = Column(Numeric(14, 2), nullable=True)
    upper_bound = Column(Numeric(14, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    model_version = relationship("ModelVersion", back_populates="revenue_forecasts")


class CustomerSegment(Base):
    __tablename__ = "customer_segments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_name = Column(String(100), nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

