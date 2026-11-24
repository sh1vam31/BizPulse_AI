from datetime import date, datetime, timedelta, timezone
from app.models.entities import Customer, Product, Supplier, Warehouse
from app.models.supply_chain import Inventory, PurchaseOrder, Sales


def test_get_inventory_overview_api(client, admin_auth_headers, db, test_organization):
    p1 = Product(
        organization_id=test_organization.id,
        sku="SKU-SC-CRITICAL",
        name="Critical Part A",
        category="Parts",
        unit_cost=50.0,
        selling_price=100.0,
        reorder_threshold=30,
        safety_stock=10,
    )
    p2 = Product(
        organization_id=test_organization.id,
        sku="SKU-SC-HEALTHY",
        name="Healthy Part B",
        category="Parts",
        unit_cost=20.0,
        selling_price=40.0,
        reorder_threshold=20,
        safety_stock=5,
    )
    db.add_all([p1, p2])
    db.commit()

    w = Warehouse(organization_id=test_organization.id, name="Main Hub", location="Dallas, TX")
    db.add(w)
    db.commit()

    inv1 = Inventory(product_id=p1.id, warehouse_id=w.id, available_quantity=8)  # <= safety_stock (10) -> CRITICAL
    inv2 = Inventory(product_id=p2.id, warehouse_id=w.id, available_quantity=80)  # Healthy
    db.add_all([inv1, inv2])
    db.commit()

    res = client.get("/api/v1/supply-chain/inventory", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_products"] >= 2
    assert data["critical_shortage_count"] >= 1

    crit_item = next(item for item in data["items"] if item["sku"] == "SKU-SC-CRITICAL")
    assert crit_item["stock_status"] == "CRITICAL"
    assert crit_item["available_stock"] == 8


def test_demand_forecast_with_xgboost_pipeline(client, admin_auth_headers, db, test_organization):
    p = Product(
        organization_id=test_organization.id,
        sku="SKU-DEMAND-ML-1",
        name="High Demand Speaker",
        category="Audio",
        unit_cost=80.0,
        selling_price=150.0,
    )
    db.add(p)
    db.commit()

    c = Customer(organization_id=test_organization.id, customer_code="CUST-SC-1", name="Audio Store")
    db.add(c)
    db.commit()

    # Generate 30 days of sales history with some weekly seasonality
    base_time = datetime.now(timezone.utc) - timedelta(days=30)
    for day in range(30):
        sale_date = base_time + timedelta(days=day)
        qty = 10 + (day % 7) * 2  # Pattern of sales
        sale = Sales(
            customer_id=c.id,
            product_id=p.id,
            quantity=qty,
            unit_price=150.0,
            total_amount=qty * 150.0,
            transaction_date=sale_date,
        )
        db.add(sale)
    db.commit()

    res = client.get(f"/api/v1/supply-chain/forecast?product_id={p.id}", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["sku"] == "SKU-DEMAND-ML-1"
    assert "7_days" in data["forecasts"]
    assert "14_days" in data["forecasts"]
    assert "30_days" in data["forecasts"]
    assert data["forecasts"]["7_days"]["total_demand"] > 0
    assert len(data["forecasts"]["7_days"]["daily_breakdown"]) == 7
    assert "wape" in data["metrics"]


def test_inventory_risks_calculation(client, admin_auth_headers, db, test_organization):
    res = client.get("/api/v1/supply-chain/risks", headers=admin_auth_headers)
    assert res.status_code == 200
    risks = res.json()
    assert isinstance(risks, list)
    if len(risks) > 0:
        item = risks[0]
        assert "risk_level" in item
        assert "expected_14d_demand" in item
        assert "days_of_stock_left" in item
        assert "recommended_replenishment_quantity" in item


def test_supplier_risk_scorecards(client, admin_auth_headers, db, test_organization):
    s = Supplier(
        organization_id=test_organization.id,
        supplier_code="SUPP-RISK-01",
        name="Reliable Freight",
        contact_email="freight@reliable.com",
        reliability_score=92.0,
        average_lead_days=4,
    )
    db.add(s)
    db.commit()

    res = client.get("/api/v1/supply-chain/suppliers", headers=admin_auth_headers)
    assert res.status_code == 200
    cards = res.json()
    target = next((c for c in cards if c["supplier_id"] == s.id), None)
    assert target is not None
    assert target["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def test_what_if_supply_chain_simulation(client, admin_auth_headers):
    payload = {
        "demand_change_pct": 25.0,
        "supplier_delay_days": 5,
        "inventory_reduction_pct": -20.0,
    }
    res = client.post("/api/v1/supply-chain/simulate", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_parameters"]["demand_change_pct"] == 25.0
    assert data["simulated_expected_demand"] > data["baseline_expected_demand"]
    assert data["simulated_available_stock"] < data["baseline_available_stock"]
    assert "recommended_action" in data
    assert "assumptions_summary" in data

