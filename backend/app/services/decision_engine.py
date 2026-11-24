from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session

from app.models.decision import BusinessPolicy, Recommendation
from app.models.entities import Customer, Product, Supplier
from app.schemas.decision import RecommendationResponse
from app.services.llm_explainer import generate_recommendation_explanation
from app.services.revenue_service import calculate_customer_churn_risks, get_revenue_overview
from app.services.supply_chain_service import calculate_inventory_risks, get_supplier_scorecards


def evaluate_and_generate_recommendations(
    db: Session, organization_id: str
) -> Tuple[List[Recommendation], Dict[str, Any]]:
    new_or_updated: List[Recommendation] = []
    summary_stats = {
        "supply_chain_policies_evaluated": 2,
        "revenue_policies_evaluated": 2,
        "connected_policies_evaluated": 1,
        "total_recommendations_active": 0,
    }

    # 1. Supply Chain Policy: Replenishment on Stockout Risk
    inv_risks = calculate_inventory_risks(db, organization_id)
    for risk in inv_risks:
        if risk.risk_level in ["CRITICAL", "HIGH"] and risk.recommended_replenishment_quantity > 0:
            prod = db.query(Product).filter(Product.id == risk.product_id).first()
            if not prod:
                continue

            impact = round(float(risk.expected_shortage) * float(prod.selling_price), 2)
            evidence = {
                "product_name": prod.name,
                "sku": prod.sku,
                "available_stock": risk.available_stock,
                "safety_stock": risk.safety_stock,
                "expected_14d_demand": risk.expected_14d_demand,
                "days_of_stock_left": risk.days_of_stock_left,
                "recommended_replenishment_quantity": risk.recommended_replenishment_quantity,
            }

            title = f"Replenish Inventory: {prod.name} ({risk.risk_level})"
            desc, _ = generate_recommendation_explanation(
                "REPLENISH_INVENTORY", title, evidence, impact
            )

            # Deduplicate by entity and pending status
            rec = (
                db.query(Recommendation)
                .filter(
                    Recommendation.organization_id == organization_id,
                    Recommendation.affected_entity_id == prod.id,
                    Recommendation.recommendation_type == "REPLENISH_INVENTORY",
                    Recommendation.status == "PENDING",
                )
                .first()
            )

            if rec:
                rec.evidence = evidence
                rec.expected_financial_impact = impact
                rec.priority = risk.risk_level
                rec.description = desc
            else:
                rec = Recommendation(
                    organization_id=organization_id,
                    module="SupplyChain",
                    recommendation_type="REPLENISH_INVENTORY",
                    title=title,
                    description=desc,
                    affected_entity_type="Product",
                    affected_entity_id=prod.id,
                    evidence=evidence,
                    expected_financial_impact=impact,
                    priority=risk.risk_level,
                    status="PENDING",
                )
                db.add(rec)
            new_or_updated.append(rec)

    # 2. Supply Chain Policy: Supplier SLA / Reliability Review
    scorecards = get_supplier_scorecards(db, organization_id)
    for card in scorecards:
        if card.risk_level in ["CRITICAL", "HIGH"]:
            evidence = {
                "supplier_name": card.name,
                "supplier_code": card.supplier_code,
                "on_time_delivery_rate": card.on_time_delivery_rate,
                "delayed_orders_count": card.delayed_orders,
                "average_lead_days": card.average_lead_days,
            }
            impact = 5000.0 if card.risk_level == "CRITICAL" else 2000.0
            title = f"Review Supplier Reliability: {card.name}"
            desc, _ = generate_recommendation_explanation("REVIEW_SUPPLIER", title, evidence, impact)

            rec = (
                db.query(Recommendation)
                .filter(
                    Recommendation.organization_id == organization_id,
                    Recommendation.affected_entity_id == card.supplier_id,
                    Recommendation.recommendation_type == "REVIEW_SUPPLIER",
                    Recommendation.status == "PENDING",
                )
                .first()
            )

            if rec:
                rec.evidence = evidence
                rec.priority = card.risk_level
                rec.description = desc
            else:
                rec = Recommendation(
                    organization_id=organization_id,
                    module="SupplyChain",
                    recommendation_type="REVIEW_SUPPLIER",
                    title=title,
                    description=desc,
                    affected_entity_type="Supplier",
                    affected_entity_id=card.supplier_id,
                    evidence=evidence,
                    expected_financial_impact=impact,
                    priority=card.risk_level,
                    status="PENDING",
                )
                db.add(rec)
            new_or_updated.append(rec)

    # 3. Revenue Policy: High-Value Customer Churn Prevention
    churn_items = calculate_customer_churn_risks(db, organization_id)
    for c_churn in churn_items:
        if c_churn.risk_category in ["CRITICAL", "HIGH"] and c_churn.monetary_value >= 500.0:
            evidence = {
                "customer_name": c_churn.name,
                "customer_code": c_churn.customer_code,
                "churn_probability": c_churn.churn_probability,
                "historical_spend": c_churn.monetary_value,
                "recency_days": c_churn.recency_days,
                "velocity_slope": c_churn.velocity_slope,
            }
            impact = round(c_churn.monetary_value * 0.75, 2)
            title = f"Initiate Churn Retention Outreach: {c_churn.name}"
            desc, _ = generate_recommendation_explanation("CHURN_RETENTION", title, evidence, impact)

            rec = (
                db.query(Recommendation)
                .filter(
                    Recommendation.organization_id == organization_id,
                    Recommendation.affected_entity_id == c_churn.customer_id,
                    Recommendation.recommendation_type == "CHURN_RETENTION",
                    Recommendation.status == "PENDING",
                )
                .first()
            )

            if rec:
                rec.evidence = evidence
                rec.priority = c_churn.risk_category
                rec.description = desc
            else:
                rec = Recommendation(
                    organization_id=organization_id,
                    module="Revenue",
                    recommendation_type="CHURN_RETENTION",
                    title=title,
                    description=desc,
                    affected_entity_type="Customer",
                    affected_entity_id=c_churn.customer_id,
                    evidence=evidence,
                    expected_financial_impact=impact,
                    priority=c_churn.risk_category,
                    status="PENDING",
                )
                db.add(rec)
            new_or_updated.append(rec)

    # 4. Revenue Policy: Monthly Revenue Contraction Investigation
    rev_overview = get_revenue_overview(db, organization_id)
    if rev_overview.monthly_growth_rate <= -20.0 and rev_overview.previous_month_revenue > 0:
        drop_amount = rev_overview.previous_month_revenue - rev_overview.current_month_revenue
        evidence = {
            "monthly_drop_pct": abs(rev_overview.monthly_growth_rate),
            "monthly_revenue_drop": drop_amount,
            "current_month_revenue": rev_overview.current_month_revenue,
            "previous_month_revenue": rev_overview.previous_month_revenue,
        }
        title = "Investigate Significant Monthly Revenue Decline"
        desc, _ = generate_recommendation_explanation("REVENUE_INVESTIGATION", title, evidence, drop_amount)

        rec = (
            db.query(Recommendation)
            .filter(
                Recommendation.organization_id == organization_id,
                Recommendation.recommendation_type == "REVENUE_INVESTIGATION",
                Recommendation.status == "PENDING",
            )
            .first()
        )

        if rec:
            rec.evidence = evidence
            rec.description = desc
            rec.expected_financial_impact = drop_amount
        else:
            rec = Recommendation(
                organization_id=organization_id,
                module="Revenue",
                recommendation_type="REVENUE_INVESTIGATION",
                title=title,
                description=desc,
                affected_entity_type="Organization",
                affected_entity_id=organization_id,
                evidence=evidence,
                expected_financial_impact=drop_amount,
                priority="HIGH",
                status="PENDING",
            )
            db.add(rec)
        new_or_updated.append(rec)

    db.commit()

    total_active = (
        db.query(Recommendation)
        .filter(Recommendation.organization_id == organization_id, Recommendation.status == "PENDING")
        .count()
    )
    summary_stats["total_recommendations_active"] = total_active

    return new_or_updated, summary_stats

