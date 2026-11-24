from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid, utc_now


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    module = Column(String(50), nullable=False)  # SupplyChain, Revenue
    recommendation_type = Column(String(100), nullable=False)  # REPLENISH_INVENTORY, CHURN_RETENTION, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    affected_entity_type = Column(String(50), nullable=False)  # Product, Customer, Supplier
    affected_entity_id = Column(String(36), nullable=False, index=True)
    evidence = Column(JSON, nullable=True)
    expected_financial_impact = Column(Numeric(14, 2), default=0.0, nullable=False)
    priority = Column(String(20), default="MEDIUM", nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED, EXECUTED
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    approvals = relationship("Approval", back_populates="recommendation", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="recommendation", cascade="all, delete-orphan")


class BusinessPolicy(Base):
    __tablename__ = "business_policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    module = Column(String(50), nullable=False)  # SupplyChain, Revenue
    rule_definition = Column(JSON, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recommendation_id = Column(String(36), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision = Column(String(20), nullable=False)  # APPROVED, REJECTED
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    recommendation = relationship("Recommendation", back_populates="approvals")


class Action(Base):
    __tablename__ = "actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recommendation_id = Column(String(36), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)  # CREATE_PURCHASE_ORDER, CREATE_RETENTION_TASK
    execution_status = Column(String(50), default="PENDING", nullable=False)  # PENDING, SUCCESS, FAILED
    idempotency_key = Column(String(100), unique=True, nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    external_reference = Column(String(255), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    recommendation = relationship("Recommendation", back_populates="actions")

