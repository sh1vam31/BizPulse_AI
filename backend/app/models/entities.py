from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid, utc_now


class Product(Base):
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    selling_price = Column(Numeric(12, 2), nullable=False)
    reorder_threshold = Column(Integer, default=50, nullable=False)
    safety_stock = Column(Integer, default=20, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    inventory_items = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    sales_items = relationship("Sales", back_populates="product", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="product", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    current_segment = Column(String(100), default="New Customers", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    sales = relationship("Sales", back_populates="customer", cascade="all, delete-orphan")
    features = relationship("CustomerFeatures", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    churn_predictions = relationship("ChurnPrediction", back_populates="customer", cascade="all, delete-orphan")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    reliability_score = Column(Numeric(5, 2), default=100.0, nullable=False)
    average_lead_days = Column(Integer, default=5, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    purchase_orders = relationship("PurchaseOrder", back_populates="supplier", cascade="all, delete-orphan")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    inventory_items = relationship("Inventory", back_populates="warehouse", cascade="all, delete-orphan")

