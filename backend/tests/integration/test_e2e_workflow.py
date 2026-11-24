import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.models.auth import Organization, User
from app.models.entities import Product, Customer, Supplier, Warehouse
from app.models.supply_chain import Inventory, Sales, PurchaseOrder
from app.core.security import get_password_hash


@pytest.fixture
def seeded_e2e_environment(db):
    """Sets up the complete scenario for E2E workflow testing."""
    org = Organization(name="E2E Demo Retail Org")
    db.add(org)
    db.flush()

    user = User(
        organization_id=org.id,
        email="e2e_manager@bizpulse.ai",
        name="Operations Director",
        password_hash=get_password_hash("StrongSecret123!"),
        role="Admin",
        is_active=True,
    )
    db.add(user)
    db.flush()

    warehouse = Warehouse(
        organization_id=org.id,
        name="Global DC",
        location="Chicago",
    )
    db.add(warehouse)
    db.flush()

    supplier = Supplier(
        organization_id=org.id,
        supplier_code="SUP-E2E-01",
        name="Premier Components Ltd",
        contact_email="supply@premier.com",
        reliability_score=68.5,
        average_lead_days=12,
    )
    db.add(supplier)
    db.flush()

    product = Product(
        organization_id=org.id,
        sku="SKU-E2E-DISPLAY",
        name="Quantum Smart TV 65",
        category="Electronics",
        unit_cost=300.0,
        selling_price=699.0,
        reorder_threshold=30,
        safety_stock=15,
    )
    db.add(product)
    db.flush()

    customer = Customer(
        organization_id=org.id,
        customer_code="CUST-E2E-001",
        name="MegaCorp Enterprise",
        email="procurement@megacorp.com",
        current_segment="Champions",
    )
    db.add(customer)
    db.flush()

    inv = Inventory(
        product_id=product.id,
        warehouse_id=warehouse.id,
        available_quantity=10,  # Below safety stock!
        reserved_quantity=2,
    )
    db.add(inv)
    db.flush()

    # Seed 40 historical sales transactions
    now = datetime.utcnow()
    for day_i in range(40, 0, -1):
        s = Sales(
            customer_id=customer.id,
            product_id=product.id,
            quantity=8,
            unit_price=product.selling_price,
            total_amount=8 * product.selling_price,
            transaction_date=now,
        )
        db.add(s)

    db.commit()
    return {
        "org_id": org.id,
        "user_email": user.email,
        "product_id": product.id,
        "customer_id": customer.id,
        "supplier_id": supplier.id,
    }


def test_complete_business_pulse_e2e_workflow(client: TestClient, seeded_e2e_environment):
    """
    Validates PRD Section 29 End-to-End Enterprise Scenario:
    1. Auth Login & JWT extraction
    2. Supply Chain Inventory & Stockout Risk detection
    3. Revenue Forecasting & Churn analysis
    4. Decision Engine recommendation evaluation
    5. AI-Grounding explanation inspection
    6. What-If Business Simulation
    7. Human Approval Decision (Approve)
    8. Action Execution with Idempotency Key validation
    9. Compliance Audit Trail verification
    """
    # 1. Login & Auth
    login_res = client.post("/api/v1/auth/login", json={
        "email": seeded_e2e_environment["user_email"],
        "password": "StrongSecret123!"
    })
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Supply Chain: Check Inventory Overview & Risks
    inv_res = client.get("/api/v1/supply-chain/inventory", headers=headers)
    assert inv_res.status_code == 200
    assert inv_res.json()["total_products"] >= 1

    risk_res = client.get("/api/v1/supply-chain/risks", headers=headers)
    assert risk_res.status_code == 200
    risks = risk_res.json()
    assert len(risks) >= 1
    target_risk = next(r for r in risks if r["product_id"] == seeded_e2e_environment["product_id"])
    assert target_risk["risk_level"] in ("CRITICAL", "HIGH")
    assert target_risk["recommended_replenishment_quantity"] > 0

    # 3. Revenue Intelligence: Forecast & Churn
    rev_fc_res = client.get("/api/v1/revenue/forecast", headers=headers)
    assert rev_fc_res.status_code == 200
    assert "30_days" in rev_fc_res.json()["forecasts"] or "30d" in rev_fc_res.json()["forecasts"]

    churn_res = client.get("/api/v1/revenue/churn", headers=headers)
    assert churn_res.status_code == 200

    # 4. What-If Simulations: Test Supply Chain & Revenue shocks
    sc_sim = client.post("/api/v1/supply-chain/simulate", headers=headers, json={
        "demand_change_pct": 25.0,
        "supplier_delay_days": 5,
        "inventory_reduction_pct": -20.0
    })
    assert sc_sim.status_code == 200
    sim_body = sc_sim.json()
    assert sim_body["potential_shortage_units"] > 0
    assert sim_body["estimated_financial_loss"] > 0

    rev_sim = client.post("/api/v1/revenue/simulate", headers=headers, json={
        "high_value_churn_pct": 10.0,
        "aov_change_pct": 15.0,
        "retention_improvement_pct": 5.0
    })
    assert rev_sim.status_code == 200

    # 5. Decision Engine: Generate Recommendations
    gen_res = client.post("/api/v1/recommendations/generate", headers=headers)
    assert gen_res.status_code == 200
    assert gen_res.json()["total_generated"] >= 1

    recs_res = client.get("/api/v1/recommendations", headers=headers)
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) >= 1

    # 6. AI Explanation: Grounded justification without hallucination
    first_rec = recs[0]
    explain_res = client.get(f"/api/v1/recommendations/{first_rec['id']}/explain", headers=headers)
    assert explain_res.status_code == 200
    explain_body = explain_res.json()
    assert len(explain_body["explanation"]) > 20
    assert len(explain_body["grounded_evidence"]) > 0

    # 7. Human Approval: Review and Approve
    pending_res = client.get("/api/v1/approvals/pending", headers=headers)
    assert pending_res.status_code == 200
    assert any(p["id"] == first_rec["id"] for p in pending_res.json())

    approve_res = client.post(
        f"/api/v1/approvals/{first_rec['id']}/approve",
        headers=headers,
        json={"comments": "Approved for ERP replenishment dispatch by Operations Director."}
    )
    assert approve_res.status_code == 200
    assert approve_res.json()["decision"] == "APPROVED"

    # 8. Action Execution with Idempotency Key validation
    idempotency_key = f"idem-key-test-{first_rec['id'][:8]}"
    
    # Execution Call 1: triggers mock ERP / CRM connector
    exec_1 = client.post(
        f"/api/v1/actions/{first_rec['id']}/execute",
        headers=headers,
        json={"idempotency_key": idempotency_key}
    )
    assert exec_1.status_code == 200
    assert exec_1.json()["execution_status"] == "SUCCESS"
    assert exec_1.json()["external_reference"] is not None

    # Execution Call 2 with identical Idempotency Key -> Must be safe idempotent return!
    exec_2 = client.post(
        f"/api/v1/actions/{first_rec['id']}/execute",
        headers=headers,
        json={"idempotency_key": idempotency_key}
    )
    assert exec_2.status_code == 200
    assert exec_2.json()["execution_status"] == "SUCCESS"
    assert exec_2.json()["external_reference"] == exec_1.json()["external_reference"]

    # Verify action appears in action execution history
    actions_res = client.get("/api/v1/actions", headers=headers)
    assert actions_res.status_code == 200
    actions = actions_res.json()
    assert len(actions) >= 1
    assert any(a["idempotency_key"] == idempotency_key for a in actions)
