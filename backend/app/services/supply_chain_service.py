from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.entities import Product, Supplier, Warehouse
from app.models.ml import ModelVersion, Prediction
from app.models.supply_chain import Inventory, PurchaseOrder, Sales
from app.schemas.supply_chain import (
    DemandForecastResponse,
    ForecastHorizonData,
    InventoryOverviewItem,
    InventoryOverviewResponse,
    InventoryRiskItem,
    SupplierRiskScorecard,
    SupplyChainSimulateRequest,
    SupplyChainSimulateResponse,
)
from ml.pipelines.demand_forecaster import DemandForecasterPipeline


def get_inventory_overview(db: Session, organization_id: str) -> InventoryOverviewResponse:
    products = db.query(Product).filter(Product.organization_id == organization_id).all()
    items = []
    total_value = 0.0
    low_stock_count = 0
    critical_count = 0

    for p in products:
        stock_agg = (
            db.query(
                func.coalesce(func.sum(Inventory.available_quantity), 0).label("avail"),
                func.coalesce(func.sum(Inventory.reserved_quantity), 0).label("res"),
            )
            .filter(Inventory.product_id == p.id)
            .first()
        )

        avail = int(stock_agg.avail or 0)
        res = int(stock_agg.res or 0)
        val = float(p.unit_cost) * avail
        total_value += val

        if avail <= p.safety_stock:
            status = "CRITICAL"
            critical_count += 1
            low_stock_count += 1
        elif avail <= p.reorder_threshold:
            status = "LOW_STOCK"
            low_stock_count += 1
        elif avail > p.reorder_threshold * 4:
            status = "OVERSTOCKED"
        else:
            status = "HEALTHY"

        items.append(
            InventoryOverviewItem(
                product_id=p.id,
                sku=p.sku,
                product_name=p.name,
                category=p.category,
                available_stock=avail,
                reserved_stock=res,
                reorder_threshold=p.reorder_threshold,
                safety_stock=p.safety_stock,
                stock_status=status,
                unit_cost=float(p.unit_cost),
                total_value=round(val, 2),
            )
        )

    return InventoryOverviewResponse(
        total_products=len(products),
        total_inventory_value=round(total_value, 2),
        low_stock_products_count=low_stock_count,
        critical_shortage_count=critical_count,
        items=items,
    )


def generate_product_demand_forecast(
    db: Session, organization_id: str, product_id: str
) -> Optional[DemandForecastResponse]:
    product = db.query(Product).filter(
        Product.id == product_id, Product.organization_id == organization_id
    ).first()
    if not product:
        return None

    # Fetch daily historical sales
    sales_records = (
        db.query(
            func.date(Sales.transaction_date).label("date"),
            func.sum(Sales.quantity).label("quantity"),
        )
        .filter(Sales.product_id == product.id)
        .group_by(func.date(Sales.transaction_date))
        .order_by(func.date(Sales.transaction_date).asc())
        .all()
    )

    if not sales_records:
        # Default baseline if no sales recorded yet
        base_date = datetime.now(timezone.utc).date()
        daily_sales = pd.DataFrame([
            {"date": (base_date - timedelta(days=i)).strftime("%Y-%m-%d"), "quantity": 5.0}
            for i in range(14, 0, -1)
        ])
    else:
        daily_sales = pd.DataFrame([
            {"date": str(r.date), "quantity": float(r.quantity)} for r in sales_records
        ])

    pipeline = DemandForecasterPipeline(model_version="v1.0.0")
    train_res = pipeline.train_and_evaluate(daily_sales)
    forecast_res = pipeline.predict_future(daily_sales, horizons=[7, 14, 30])

    horizons_dict = {}
    for k, v in forecast_res["forecasts"].items():
        horizons_dict[k] = ForecastHorizonData(
            horizon_days=v["horizon_days"],
            total_demand=v["total_demand"],
            daily_average=v["daily_average"],
            daily_breakdown=v["daily_breakdown"],
        )

    # Persist or update model_version and prediction
    mv = db.query(ModelVersion).filter(
        ModelVersion.model_name == "DemandForecaster",
        ModelVersion.version == "v1.0.0",
    ).first()
    if not mv:
        mv = ModelVersion(
            model_name="DemandForecaster",
            version="v1.0.0",
            algorithm="XGBoostRegressor + SeasonalNaiveBaseline",
            metrics=train_res.get("xgboost_metrics", {}),
            status="ACTIVE",
        )
        db.add(mv)
        db.flush()

    pred_record = Prediction(
        model_version_id=mv.id,
        entity_type="Product",
        entity_id=product.id,
        prediction_type="DEMAND_FORECAST",
        prediction_value={"forecasts": forecast_res["forecasts"]},
    )
    db.add(pred_record)
    db.commit()

    return DemandForecastResponse(
        product_id=product.id,
        sku=product.sku,
        product_name=product.name,
        forecasts=horizons_dict,
        metrics=train_res.get("xgboost_metrics", {}),
        beats_baseline=train_res.get("beats_baseline", True),
        generated_at=datetime.now(timezone.utc),
    )


def calculate_inventory_risks(db: Session, organization_id: str) -> List[InventoryRiskItem]:
    products = db.query(Product).filter(Product.organization_id == organization_id).all()
    risks = []

    for p in products:
        stock_agg = (
            db.query(func.coalesce(func.sum(Inventory.available_quantity), 0))
            .filter(Inventory.product_id == p.id)
            .scalar()
        )
        avail = int(stock_agg or 0)

        # 30-day average daily sales
        sales_sum = (
            db.query(func.coalesce(func.sum(Sales.quantity), 0))
            .filter(
                Sales.product_id == p.id,
                Sales.transaction_date >= datetime.now(timezone.utc) - timedelta(days=30),
            )
            .scalar()
        )
        daily_rate = float(sales_sum or 0) / 30.0
        if daily_rate <= 0:
            daily_rate = 1.0  # conservative baseline

        expected_14d = round(daily_rate * 14.0, 1)
        shortage = max(0.0, expected_14d + p.safety_stock - avail)
        days_left = round(avail / daily_rate, 1) if daily_rate > 0 else 999.0

        if days_left <= 7:
            level = "CRITICAL"
        elif days_left <= 14:
            level = "HIGH"
        elif days_left <= 25:
            level = "MEDIUM"
        else:
            level = "LOW"

        # Outstanding purchase orders
        po_sum = (
            db.query(func.coalesce(func.sum(PurchaseOrder.quantity), 0))
            .filter(
                PurchaseOrder.product_id == p.id,
                PurchaseOrder.status.in_(["PLACED", "SHIPPED"]),
            )
            .scalar()
        )
        outstanding = int(po_sum or 0)
        reorder_qty = max(0, int(expected_14d + p.safety_stock - avail - outstanding))

        stockout_date = None
        if days_left < 60:
            stockout_date = (date.today() + timedelta(days=int(days_left))).isoformat()

        risks.append(
            InventoryRiskItem(
                product_id=p.id,
                sku=p.sku,
                product_name=p.name,
                available_stock=avail,
                safety_stock=p.safety_stock,
                expected_14d_demand=expected_14d,
                expected_shortage=shortage,
                days_of_stock_left=days_left,
                expected_stockout_date=stockout_date,
                risk_level=level,
                recommended_replenishment_quantity=reorder_qty,
            )
        )

    return sorted(risks, key=lambda x: (x.risk_level != "CRITICAL", x.days_of_stock_left))


def get_supplier_scorecards(db: Session, organization_id: str) -> List[SupplierRiskScorecard]:
    suppliers = db.query(Supplier).filter(Supplier.organization_id == organization_id).all()
    scorecards = []

    for s in suppliers:
        po_agg = (
            db.query(
                func.count(PurchaseOrder.id).label("total"),
                func.sum(
                    case(
                        (PurchaseOrder.actual_delivery > PurchaseOrder.expected_delivery, 1),
                        else_=0,
                    )
                ).label("delayed"),
            )
            .filter(PurchaseOrder.supplier_id == s.id)
            .first()
        )

        total = int(po_agg.total or 0)
        delayed = int(po_agg.delayed or 0)
        on_time = (
            round(((total - delayed) / total) * 100.0, 1)
            if total > 0
            else float(s.reliability_score)
        )

        if on_time < 70 or s.average_lead_days > 14:
            risk = "CRITICAL"
        elif on_time < 85 or s.average_lead_days > 8:
            risk = "HIGH"
        elif on_time < 95:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        scorecards.append(
            SupplierRiskScorecard(
                supplier_id=s.id,
                supplier_code=s.supplier_code,
                name=s.name,
                reliability_score=float(s.reliability_score),
                average_lead_days=s.average_lead_days,
                total_orders=total,
                delayed_orders=delayed,
                on_time_delivery_rate=on_time,
                risk_level=risk,
            )
        )

    return scorecards


def simulate_supply_chain_scenario(
    db: Session, organization_id: str, req: SupplyChainSimulateRequest
) -> SupplyChainSimulateResponse:
    # If specific product, query that product, else average across all
    if req.product_id:
        products = db.query(Product).filter(
            Product.id == req.product_id, Product.organization_id == organization_id
        ).all()
    else:
        products = db.query(Product).filter(Product.organization_id == organization_id).limit(10).all()

    if not products:
        baseline_stock = 100
        selling_price = 50.0
    else:
        p = products[0]
        stock_agg = (
            db.query(func.coalesce(func.sum(Inventory.available_quantity), 0))
            .filter(Inventory.product_id == p.id)
            .scalar()
        )
        baseline_stock = int(stock_agg or 100)
        selling_price = float(p.selling_price)

    baseline_demand = 80.0
    # Apply perturbations
    simulated_demand = baseline_demand * (1.0 + (req.demand_change_pct / 100.0))
    simulated_stock = max(0, int(baseline_stock * (1.0 + (req.inventory_reduction_pct / 100.0))))

    # Additional delay impact (delayed delivery means no replenishments arrive during delay window)
    effective_demand_window = simulated_demand + (req.supplier_delay_days * (simulated_demand / 14.0))

    potential_shortage = max(0.0, effective_demand_window - simulated_stock)
    est_loss = round(potential_shortage * selling_price, 2)

    if potential_shortage > 0:
        action = f"Place expedited replenishment order of {int(potential_shortage)} units or engage secondary suppliers."
    else:
        action = "Current inventory remains adequate under simulated conditions."

    return SupplyChainSimulateResponse(
        scenario_parameters={
            "demand_change_pct": req.demand_change_pct,
            "supplier_delay_days": req.supplier_delay_days,
            "inventory_reduction_pct": req.inventory_reduction_pct,
        },
        baseline_available_stock=baseline_stock,
        simulated_available_stock=simulated_stock,
        baseline_expected_demand=round(baseline_demand, 1),
        simulated_expected_demand=round(effective_demand_window, 1),
        potential_shortage_units=round(potential_shortage, 1),
        estimated_financial_loss=est_loss,
        recommended_action=action,
        assumptions_summary=(
            f"Simulated {req.demand_change_pct}% demand shift, {req.supplier_delay_days} days supplier lead delay, "
            f"and {req.inventory_reduction_pct}% inventory change over a 14-day operational window."
        ),
    )
