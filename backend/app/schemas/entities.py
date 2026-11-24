from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class WarehouseResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    location: str
    created_at: datetime
    total_products_stored: Optional[int] = 0
    total_quantity: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


class ProductInventoryItem(BaseModel):
    warehouse_id: str
    warehouse_name: str
    available_quantity: int
    reserved_quantity: int
    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: str
    organization_id: str
    sku: str
    name: str
    category: str
    unit_cost: float
    selling_price: float
    reorder_threshold: int
    safety_stock: int
    created_at: datetime
    total_sales_quantity: Optional[int] = 0
    total_revenue: Optional[float] = 0.0
    available_stock: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductResponse):
    inventory_by_warehouse: List[ProductInventoryItem] = []
    recent_sales_count: int = 0
    outstanding_orders_count: int = 0


class CustomerResponse(BaseModel):
    id: str
    organization_id: str
    customer_code: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    current_segment: str
    created_at: datetime
    total_spend: Optional[float] = 0.0
    total_orders: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(CustomerResponse):
    recent_transactions: List[Dict[str, Any]] = []
    recency_days: Optional[int] = None
    frequency: Optional[int] = None
    monetary_value: Optional[float] = None


class SupplierResponse(BaseModel):
    id: str
    organization_id: str
    supplier_code: str
    name: str
    contact_email: Optional[str] = None
    reliability_score: float
    average_lead_days: int
    created_at: datetime
    total_orders: Optional[int] = 0
    delayed_orders: Optional[int] = 0
    on_time_delivery_rate: Optional[float] = 100.0
    model_config = ConfigDict(from_attributes=True)


class SupplierDetailResponse(SupplierResponse):
    recent_purchase_orders: List[Dict[str, Any]] = []
