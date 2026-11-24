from datetime import date, datetime, timedelta, timezone
from app.models.entities import Customer, Product, Supplier
from app.models.supply_chain import Inventory, PurchaseOrder, Sales


def test_generate_and_list_recommendations(client, admin_auth_headers, db, test_organization):
    # Setup Product with stock shortage
    p = Product(
        organization_id=test_organization.id,
        sku="SKU-DECISION-01",
        name="Decision Wireless Headset",
        category="Audio",
        unit_cost=40.0,
        selling_price=90.0,
        reorder_threshold=50,
        safety_stock=20,
    )
    # Setup Supplier with poor performance
    s = Supplier(
        organization_id=test_organization.id,
        supplier_code="SUPP-DECISION-02",
        name="Delayed Logistics Ltd",
        contact_email="help@delayed.com",
        reliability_score=60.0,
        average_lead_days=18,
    )
    # Setup Customer with high spend but lapsed
    c = Customer(
        organization_id=test_organization.id,
        customer_code="CUST-DECISION-03",
        name="High Value Enterprise",
    )
    db.add_all([p, s, c])
    db.commit()

    # Low inventory
    inv = Inventory(product_id=p.id, warehouse_id=p.id, available_quantity=5)
    db.add(inv)

    # Sales for product
    now = datetime.now(timezone.utc)
    db.add(Sales(customer_id=c.id, product_id=p.id, quantity=10, unit_price=90.0, total_amount=900.0, transaction_date=now - timedelta(days=80)))
    db.commit()

    # Trigger recommendation generation
    gen_res = client.post("/api/v1/recommendations/generate", headers=admin_auth_headers)
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["total_generated"] > 0
    assert len(gen_data["recommendations"]) > 0

    # Test listing recommendations
    list_res = client.get("/api/v1/recommendations?status=PENDING", headers=admin_auth_headers)
    assert list_res.status_code == 200
    recs = list_res.json()
    assert len(recs) > 0

    target_rec = recs[0]
    assert "evidence" in target_rec
    assert target_rec["expected_financial_impact"] > 0
    assert target_rec["priority"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    # Test recommendation detail
    detail_res = client.get(f"/api/v1/recommendations/{target_rec['id']}", headers=admin_auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == target_rec["id"]
    assert "suggested_action_type" in detail
    assert "action_payload" in detail

    # Test explanation layer
    explain_res = client.post(f"/api/v1/recommendations/{target_rec['id']}/explain", headers=admin_auth_headers)
    assert explain_res.status_code == 200
    exp = explain_res.json()
    assert exp["recommendation_id"] == target_rec["id"]
    assert len(exp["explanation"]) > 20
    assert "grounded_evidence" in exp
    assert exp["generated_by"] in ["OpenAI-LLM", "Evidence-Grounded-Synthesizer"]

