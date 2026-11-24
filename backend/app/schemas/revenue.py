from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RevenueOverviewResponse(BaseModel):
    total_revenue: float
    current_month_revenue: float
    previous_month_revenue: float
    monthly_growth_rate: float
    average_order_value: float
    total_transactions: int
    historical_monthly_trend: List[Dict[str, Any]] = []


class RevenueForecastDailyItem(BaseModel):
    date: str
    predicted_revenue: float
    lower_bound: float
    upper_bound: float


class RevenueForecastHorizonData(BaseModel):
    horizon_days: int
    total_predicted_revenue: float
    daily_average: float
    daily_breakdown: List[RevenueForecastDailyItem]


class RevenueForecastResponse(BaseModel):
    organization_id: str
    forecasts: Dict[str, RevenueForecastHorizonData]
    metrics: Dict[str, Any]
    beats_baseline: bool
    generated_at: datetime


class CustomerChurnItem(BaseModel):
    customer_id: str
    customer_code: str
    name: str
    email: Optional[str] = None
    churn_probability: float
    risk_category: str  # CRITICAL, HIGH, MEDIUM, LOW
    monetary_value: float
    recency_days: int
    velocity_slope: float
    contributing_features: Dict[str, Any]


class CustomerSegmentDistribution(BaseModel):
    segment_name: str
    customer_count: int
    total_revenue: float
    average_spend: float
    revenue_contribution_pct: float


class CustomerLifetimeValueItem(BaseModel):
    customer_id: str
    customer_code: str
    name: str
    historical_spend: float
    estimated_clv: float
    clv_category: str  # Platinum, Gold, Silver, Bronze


class RevenueSimulateRequest(BaseModel):
    high_value_churn_pct: float = Field(0.0, description="e.g. 10 for 10% high-value customer churn")
    aov_change_pct: float = Field(0.0, description="e.g. 15 for 15% increase in Average Order Value")
    retention_improvement_pct: float = Field(0.0, description="e.g. 10 for 10% boost in retention")


class RevenueSimulateResponse(BaseModel):
    scenario_parameters: Dict[str, Any]
    baseline_expected_revenue: float
    simulated_expected_revenue: float
    revenue_difference: float
    percentage_impact: float
    estimated_financial_loss_or_gain: float
    potential_recovery_opportunities: str
    assumptions_summary: str

