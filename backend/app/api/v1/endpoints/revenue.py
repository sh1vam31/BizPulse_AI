from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db
from app.models.auth import User
from app.schemas.revenue import (
    CustomerChurnItem,
    CustomerSegmentDistribution,
    RevenueForecastResponse,
    RevenueOverviewResponse,
    RevenueSimulateRequest,
    RevenueSimulateResponse,
)
from app.services.revenue_service import (
    calculate_customer_churn_risks,
    calculate_customer_segments,
    generate_revenue_forecast,
    get_revenue_overview,
    simulate_revenue_scenario,
)

router = APIRouter()


@router.get("/overview", response_model=RevenueOverviewResponse)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_revenue_overview(db=db, organization_id=current_user.organization_id)


@router.get("/forecast", response_model=RevenueForecastResponse)
def get_forecast(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return generate_revenue_forecast(db=db, organization_id=current_user.organization_id)


@router.post("/forecast/trigger", response_model=RevenueForecastResponse)
def trigger_forecast(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return generate_revenue_forecast(db=db, organization_id=current_user.organization_id)


@router.get("/churn", response_model=List[CustomerChurnItem])
def get_churn_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return calculate_customer_churn_risks(db=db, organization_id=current_user.organization_id)


@router.get("/segments", response_model=List[CustomerSegmentDistribution])
def get_customer_segments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return calculate_customer_segments(db=db, organization_id=current_user.organization_id)


@router.post("/simulate", response_model=RevenueSimulateResponse)
def simulate_revenue(
    req: RevenueSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return simulate_revenue_scenario(db=db, organization_id=current_user.organization_id, req=req)

