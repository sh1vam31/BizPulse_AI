from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship
from app.models.base import Base, generate_uuid, utc_now


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    warehouse_id = Column(String(36), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True)
    available_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")


class Sales(Base):
    __tablename__ = "sales"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True)

    customer = relationship("Customer", back_populates="sales")
    product = relationship("Product", back_populates="sales_items")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    supplier_id = Column(String(36), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)
    order_date = Column(Date, nullable=False, index=True)
    expected_delivery = Column(Date, nullable=False)
    actual_delivery = Column(Date, nullable=True)
    status = Column(String(50), default="PLACED", nullable=False)  # PLACED, SHIPPED, DELIVERED, CANCELLED

    supplier = relationship("Supplier", back_populates="purchase_orders")
    product = relationship("Product", back_populates="purchase_orders")

