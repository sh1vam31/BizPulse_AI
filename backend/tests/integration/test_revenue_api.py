from datetime import datetime, timedelta, timezone
from app.models.entities import Customer, Product
from app.models.supply_chain import Sales


def test_get_revenue_overview_api(client, admin_auth_headers, db, test_organization):
    c = Customer(
        organization_id=test_organization.id,
        customer_code="CUST-REV-1",
        name="Global Retailer",
    )
    p = Product(
        organization_id=test_organization.id,
        sku="SKU-REV-1",
        name="Enterprise Workstation",
        category="Computers",
        unit_cost=1000.0,
        selling_price=1600.0,
    )
    db.add_all([c, p])
    db.commit()

    # Sales in current month and previous month
    now = datetime.now(timezone.utc)
    s1 = Sales(
        customer_id=c.id,
        product_id=p.id,
        quantity=2,
        unit_price=1600.0,
        total_amount=3200.0,
        transaction_date=now - timedelta(days=2),
    )
    s2 = Sales(
        customer_id=c.id,
        product_id=p.id,
        quantity=1,
        unit_price=1600.0,
        total_amount=1600.0,
        transaction_date=now - timedelta(days=40),
    )
    db.add_all([s1, s2])
    db.commit()

    res = client.get("/api/v1/revenue/overview", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] >= 4800.0
    assert data["average_order_value"] >= 1600.0
    assert data["total_transactions"] >= 2


def test_revenue_forecast_pipeline(client, admin_auth_headers, db, test_organization):
    c = Customer(organization_id=test_organization.id, customer_code="CUST-REV-FORECAST", name="Acme Store")
    p = Product(
        organization_id=test_organization.id,
        sku="SKU-REV-FORECAST",
        name="Cloud Router",
        category="Networking",
        unit_cost=100.0,
        selling_price=200.0,
    )
    db.add_all([c, p])
    db.commit()

    # Create 35 days of daily transactions
    base_time = datetime.now(timezone.utc) - timedelta(days=35)
    for day in range(35):
        s_date = base_time + timedelta(days=day)
        amount = 500.0 + (day % 7) * 100.0
        sale = Sales(
            customer_id=c.id,
            product_id=p.id,
            quantity=int(amount / 200.0),
            unit_price=200.0,
            total_amount=amount,
            transaction_date=s_date,
        )
        db.add(sale)
    db.commit()

    res = client.get("/api/v1/revenue/forecast", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "7_days" in data["forecasts"]
    assert "30_days" in data["forecasts"]
    assert "90_days" in data["forecasts"]
    daily_items = data["forecasts"]["30_days"]["daily_breakdown"]
    assert len(daily_items) == 30
    assert daily_items[0]["upper_bound"] >= daily_items[0]["predicted_revenue"]
    assert daily_items[0]["lower_bound"] <= daily_items[0]["predicted_revenue"]


def test_customer_churn_prediction_pipeline(client, admin_auth_headers, db, test_organization):
    # Customer A: highly active (purchased 2 days ago)
    c_active = Customer(organization_id=test_organization.id, customer_code="CUST-ACTIVE-01", name="Active Client")
    # Customer B: lapsed/churned (last purchased 90 days ago)
    c_lapsed = Customer(organization_id=test_organization.id, customer_code="CUST-LAPSED-02", name="Lapsed Client")
    p = Product(organization_id=test_organization.id, sku="SKU-CHURN-ITEM", name="Office Chair", category="Furniture", unit_cost=50.0, selling_price=120.0)
    db.add_all([c_active, c_lapsed, p])
    db.commit()

    now = datetime.now(timezone.utc)
    # Active client: multiple purchases recently
    for d in [2, 10, 20]:
        db.add(Sales(customer_id=c_active.id, product_id=p.id, quantity=1, unit_price=120.0, total_amount=120.0, transaction_date=now - timedelta(days=d)))

    # Lapsed client: only purchased 90 days ago
    db.add(Sales(customer_id=c_lapsed.id, product_id=p.id, quantity=5, unit_price=120.0, total_amount=600.0, transaction_date=now - timedelta(days=90)))
    db.commit()

    res = client.get("/api/v1/revenue/churn", headers=admin_auth_headers)
    assert res.status_code == 200
    churn_list = res.json()
    assert len(churn_list) >= 2

    lapsed_item = next(item for item in churn_list if item["customer_code"] == "CUST-LAPSED-02")
    active_item = next(item for item in churn_list if item["customer_code"] == "CUST-ACTIVE-01")

    # Lapsed customer should have higher churn risk than active customer
    assert lapsed_item["churn_probability"] >= active_item["churn_probability"]
    assert lapsed_item["recency_days"] >= 80


def test_customer_segmentation_api(client, admin_auth_headers, db, test_organization):
    res = client.get("/api/v1/revenue/segments", headers=admin_auth_headers)
    assert res.status_code == 200
    segments = res.json()
    assert isinstance(segments, list)
    if len(segments) > 0:
        s = segments[0]
        assert "segment_name" in s
        assert "customer_count" in s
        assert "total_revenue" in s
        assert "revenue_contribution_pct" in s


def test_what_if_revenue_simulation(client, admin_auth_headers):
    payload = {
        "high_value_churn_pct": 10.0,
        "aov_change_pct": 15.0,
        "retention_improvement_pct": 5.0,
    }
    res = client.post("/api/v1/revenue/simulate", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "baseline_expected_revenue" in data
    assert "simulated_expected_revenue" in data
    assert "revenue_difference" in data
    assert "percentage_impact" in data
    assert "potential_recovery_opportunities" in data

