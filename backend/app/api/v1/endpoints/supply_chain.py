from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db
from app.models.auth import User
from app.schemas.supply_chain import (
    DemandForecastResponse,
    InventoryOverviewResponse,
    InventoryRiskItem,
    SupplierRiskScorecard,
    SupplyChainSimulateRequest,
    SupplyChainSimulateResponse,
)
from app.services.supply_chain_service import (
    calculate_inventory_risks,
    generate_product_demand_forecast,
    get_inventory_overview,
    get_supplier_scorecards,
    simulate_supply_chain_scenario,
)

router = APIRouter()


@router.get("/inventory", response_model=InventoryOverviewResponse)
def get_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_inventory_overview(db=db, organization_id=current_user.organization_id)


@router.get("/forecast", response_model=DemandForecastResponse)
def get_demand_forecast(
    product_id: str = Query(..., description="Target product ID for forecast"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    forecast = generate_product_demand_forecast(
        db=db, organization_id=current_user.organization_id, product_id=product_id
    )
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return forecast


@router.post("/forecast/trigger", response_model=DemandForecastResponse)
def trigger_demand_forecast(
    product_id: str = Query(..., description="Target product ID to retrain and forecast"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    forecast = generate_product_demand_forecast(
        db=db, organization_id=current_user.organization_id, product_id=product_id
    )
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return forecast


@router.get("/risks", response_model=List[InventoryRiskItem])
def get_inventory_risks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return calculate_inventory_risks(db=db, organization_id=current_user.organization_id)


@router.get("/suppliers", response_model=List[SupplierRiskScorecard])
def get_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_supplier_scorecards(db=db, organization_id=current_user.organization_id)


@router.post("/simulate", response_model=SupplyChainSimulateResponse)
def simulate_supply_chain(
    req: SupplyChainSimulateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return simulate_supply_chain_scenario(
        db=db, organization_id=current_user.organization_id, req=req
    )

