import uuid
from app.models.decision import Recommendation
from app.models.entities import Product, Supplier
from app.models.supply_chain import PurchaseOrder


def test_approval_and_execution_lifecycle(client, admin_auth_headers, viewer_auth_headers, db, test_organization):
    p = Product(
        organization_id=test_organization.id,
        sku="SKU-EXEC-01",
        name="Industrial Switch",
        category="Hardware",
        unit_cost=150.0,
        selling_price=250.0,
    )
    s = Supplier(
        organization_id=test_organization.id,
        supplier_code="SUPP-EXEC-01",
        name="ElectroSupply Inc",
        reliability_score=95.0,
        average_lead_days=5,
    )
    db.add_all([p, s])
    db.commit()

    rec = Recommendation(
        organization_id=test_organization.id,
        module="SupplyChain",
        recommendation_type="REPLENISH_INVENTORY",
        title="Replenish Industrial Switch",
        description="Inventory shortage projected in 5 days.",
        affected_entity_type="Product",
        affected_entity_id=p.id,
        evidence={"recommended_replenishment_quantity": 40},
        expected_financial_impact=4000.0,
        priority="HIGH",
        status="PENDING",
    )
    db.add(rec)
    db.commit()

    # 1. Viewer cannot approve (RBAC check -> 403 Forbidden)
    viewer_res = client.post(
        f"/api/v1/approvals/{rec.id}/approve",
        json={"comments": "Looks good"},
        headers=viewer_auth_headers,
    )
    assert viewer_res.status_code == 403

    # 2. Cannot execute while in PENDING status (-> 400 Bad Request)
    exec_pending = client.post(
        f"/api/v1/actions/{rec.id}/execute",
        json={"idempotency_key": "KEY-PENDING-FAIL-1"},
        headers=admin_auth_headers,
    )
    assert exec_pending.status_code == 400
    assert "Only recommendations in 'APPROVED' status can be executed" in exec_pending.json()["detail"]

    # 3. Admin approves recommendation
    appr_res = client.post(
        f"/api/v1/approvals/{rec.id}/approve",
        json={"comments": "Approved for immediate procurement"},
        headers=admin_auth_headers,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["decision"] == "APPROVED"

    # Verify rec status in DB
    db.refresh(rec)
    assert rec.status == "APPROVED"

    # 4. Execute approved action with unique idempotency key
    idemp_key = f"IDEMP-KEY-{uuid.uuid4().hex[:12]}"
    exec_res = client.post(
        f"/api/v1/actions/{rec.id}/execute",
        json={"idempotency_key": idemp_key},
        headers=admin_auth_headers,
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["execution_status"] == "SUCCESS"
    assert exec_data["action_type"] == "CREATE_PURCHASE_ORDER"
    assert "ERP-PO-" in exec_data["external_reference"]
    first_action_id = exec_data["id"]

    # 5. Idempotency test: Re-send exact same execution request
    retry_res = client.post(
        f"/api/v1/actions/{rec.id}/execute",
        json={"idempotency_key": idemp_key},
        headers=admin_auth_headers,
    )
    assert retry_res.status_code == 200
    retry_data = retry_res.json()
    assert retry_data["id"] == first_action_id
    assert "Idempotent duplicate" in retry_data["message"]

    # Verify purchase orders count in DB did NOT duplicate
    po_count = db.query(PurchaseOrder).filter(PurchaseOrder.product_id == p.id).count()
    assert po_count == 1


def test_rejection_workflow(client, admin_auth_headers, db, test_organization):
    rec = Recommendation(
        organization_id=test_organization.id,
        module="Revenue",
        recommendation_type="CHURN_RETENTION",
        title="Retention Outreach for Inactive Account",
        description="Customer churn risk flagged.",
        affected_entity_type="Customer",
        affected_entity_id="dummy-cust-id",
        evidence={},
        expected_financial_impact=500.0,
        priority="LOW",
        status="PENDING",
    )
    db.add(rec)
    db.commit()

    # Reject
    rej_res = client.post(
        f"/api/v1/approvals/{rec.id}/reject",
        json={"reason": "Customer is already in restructuring; skip outreach"},
        headers=admin_auth_headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["decision"] == "REJECTED"

    # Attempting to execute rejected recommendation must be strictly blocked
    exec_res = client.post(
        f"/api/v1/actions/{rec.id}/execute",
        json={"idempotency_key": "IDEMP-REJECT-BLOCKED"},
        headers=admin_auth_headers,
    )
    assert exec_res.status_code == 400
    assert "Only recommendations in 'APPROVED' status can be executed" in exec_res.json()["detail"]

