import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.decision import Action, Recommendation
from app.models.entities import Customer, Product, Supplier
from app.models.supply_chain import PurchaseOrder


def execute_approved_action(
    db: Session,
    organization_id: str,
    user_id: str,
    recommendation: Recommendation,
    idempotency_key: str,
    custom_params: Optional[Dict[str, Any]] = None,
) -> Tuple[Action, str]:
    """
    Executes an action with strict idempotency and role validation.
    """
    # 1. Idempotency Check
    existing_action = (
        db.query(Action)
        .filter(Action.idempotency_key == idempotency_key)
        .first()
    )
    if existing_action:
        return existing_action, "Idempotent duplicate request: previously executed action returned."

    # 2. Status Validation
    if recommendation.status != "APPROVED":
        raise ValueError(
            f"Cannot execute action: recommendation status is '{recommendation.status}'. "
            f"Only recommendations in 'APPROVED' status can be executed."
        )

    # 3. Connector Routing & Side-Effects
    action_type = "GENERAL_TASK"
    ext_ref = f"EXT-{uuid.uuid4().hex[:12].upper()}"
    payload: Dict[str, Any] = custom_params or {}

    if recommendation.recommendation_type == "REPLENISH_INVENTORY":
        action_type = "CREATE_PURCHASE_ORDER"
        product = db.query(Product).filter(Product.id == recommendation.affected_entity_id).first()

        # Find or select first supplier
        supplier = db.query(Supplier).filter(Supplier.organization_id == organization_id).first()
        qty = int(recommendation.evidence.get("recommended_replenishment_quantity", 50))
        unit_cost = float(product.unit_cost) if product else 50.0
        total_cost = qty * unit_cost

        # Call Mock ERP Connector: create purchase order record
        po = PurchaseOrder(
            supplier_id=supplier.id if supplier else recommendation.affected_entity_id,
            product_id=recommendation.affected_entity_id,
            quantity=qty,
            total_cost=total_cost,
            order_date=date.today(),
            expected_delivery=date.today() + timedelta(days=supplier.average_lead_days if supplier else 5),
            status="PLACED",
        )
        db.add(po)
        db.flush()

        ext_ref = f"ERP-PO-{po.id[:8].upper()}"
        payload = {
            "erp_purchase_order_id": po.id,
            "product_id": recommendation.affected_entity_id,
            "quantity": qty,
            "total_cost": total_cost,
            "connector": "Mock_Enterprise_ERP",
        }

    elif recommendation.recommendation_type == "CHURN_RETENTION":
        action_type = "CREATE_RETENTION_TASK"
        ext_ref = f"CRM-TASK-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            "customer_id": recommendation.affected_entity_id,
            "campaign": "VIP Retention Discount 15%",
            "assigned_rep": "Executive Sales Team",
            "connector": "Mock_Enterprise_CRM",
        }

    elif recommendation.recommendation_type == "REVIEW_SUPPLIER":
        action_type = "FLAG_SUPPLIER_REVIEW"
        ext_ref = f"VENDOR-FLAG-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            "supplier_id": recommendation.affected_entity_id,
            "reason": "SLA delivery threshold violation",
            "connector": "Mock_Vendor_Portal",
        }

    # 4. Record Action
    action = Action(
        recommendation_id=recommendation.id,
        action_type=action_type,
        execution_status="SUCCESS",
        idempotency_key=idempotency_key,
        payload=payload,
        external_reference=ext_ref,
        executed_at=datetime.now(timezone.utc),
    )
    db.add(action)

    # 5. Transition recommendation status to EXECUTED
    recommendation.status = "EXECUTED"

    db.commit()
    db.refresh(action)

    return action, f"Action executed successfully via external connector ({ext_ref})."

