from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InventoryOverviewItem(BaseModel):
    product_id: str
    sku: str
    product_name: str
    category: str
    available_stock: int
    reserved_stock: int
    reorder_threshold: int
    safety_stock: int
    stock_status: str  # HEALTHY, LOW_STOCK, CRITICAL, OVERSTOCKED
    unit_cost: float
    total_value: float
    model_config = ConfigDict(from_attributes=True)


class InventoryOverviewResponse(BaseModel):
    total_products: int
    total_inventory_value: float
    low_stock_products_count: int
    critical_shortage_count: int
    items: List[InventoryOverviewItem]


class ForecastHorizonData(BaseModel):
    horizon_days: int
    total_demand: float
    daily_average: float
    daily_breakdown: List[Dict[str, Any]]


class DemandForecastResponse(BaseModel):
    product_id: str
    sku: str
    product_name: str
    forecasts: Dict[str, ForecastHorizonData]
    metrics: Dict[str, Any]
    beats_baseline: bool
    generated_at: datetime


class InventoryRiskItem(BaseModel):
    product_id: str
    sku: str
    product_name: str
    available_stock: int
    safety_stock: int
    expected_14d_demand: float
    expected_shortage: float
    days_of_stock_left: float
    expected_stockout_date: Optional[str] = None
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    recommended_replenishment_quantity: int
    model_config = ConfigDict(from_attributes=True)


class SupplierRiskScorecard(BaseModel):
    supplier_id: str
    supplier_code: str
    name: str
    reliability_score: float
    average_lead_days: int
    total_orders: int
    delayed_orders: int
    on_time_delivery_rate: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class SupplyChainSimulateRequest(BaseModel):
    product_id: Optional[str] = None
    demand_change_pct: float = Field(0.0, description="e.g. +20 for +20% demand increase")
    supplier_delay_days: int = Field(0, description="e.g. +5 for 5 days delivery delay")
    inventory_reduction_pct: float = Field(0.0, description="e.g. -30 for 30% inventory reduction")


class SupplyChainSimulateResponse(BaseModel):
    scenario_parameters: Dict[str, Any]
    baseline_available_stock: int
    simulated_available_stock: int
    baseline_expected_demand: float
    simulated_expected_demand: float
    potential_shortage_units: float
    estimated_financial_loss: float
    recommended_action: str
    assumptions_summary: str

