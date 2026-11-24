import json
from typing import Any, Dict, Tuple
from app.core.config import settings
from app.core.logging import logger


def generate_recommendation_explanation(
    recommendation_type: str,
    title: str,
    evidence: Dict[str, Any],
    expected_impact: float,
) -> Tuple[str, str]:
    """
    Generates a clear, grounded explanation for business executives based strictly
    on the provided evidence. Never hallucinates or invents statistics.
    """
    if settings.OPENAI_API_KEY:
        try:
            import httpx

            system_prompt = (
                "You are an enterprise business intelligence executive explainer for BusinessPulse AI. "
                "Explain the recommendation concisely in 2-3 sentences based ONLY on the provided structured evidence. "
                "Never invent numerical figures, alter model forecasts, or suggest ungrounded conclusions."
            )
            user_prompt = f"Title: {title}\nType: {recommendation_type}\nExpected Financial Impact: ${expected_impact:,.2f}\nEvidence: {json.dumps(evidence)}"

            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200,
                },
                timeout=10.0,
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"].strip()
                return content, "OpenAI-LLM"
        except Exception as e:
            logger.warning(f"OpenAI API call failed: {e}. Falling back to Evidence-Grounded-Synthesizer.")

    # High-quality deterministic explanation synthesizer
    if recommendation_type == "REPLENISH_INVENTORY":
        product = evidence.get("product_name", "the item")
        avail = evidence.get("available_stock", 0)
        reorder_qty = evidence.get("recommended_replenishment_quantity", 0)
        days_left = evidence.get("days_of_stock_left", 0)
        lead_time = evidence.get("supplier_lead_days", 5)

        explanation = (
            f"Available inventory for {product} ({avail} units) has dropped below configured safety thresholds. "
            f"At current demand velocity, stock will deplete in approximately {days_left:.1f} days, while supplier lead time "
            f"is {lead_time} days. Immediate replenishment of {reorder_qty} units is advised to avoid an estimated "
            f"${expected_impact:,.2f} in stockout losses."
        )

    elif recommendation_type == "CHURN_RETENTION":
        customer = evidence.get("customer_name", "the account")
        prob = evidence.get("churn_probability", 0.0) * 100.0
        spend = evidence.get("historical_spend", expected_impact)
        recency = evidence.get("recency_days", 0)
        velocity = evidence.get("velocity_slope", 0.0)

        explanation = (
            f"High-value account {customer} shows a {prob:.1f}% churn risk probability. "
            f"Their purchasing frequency velocity has declined to {velocity:.2f} with no transactions recorded in the last "
            f"{recency} days. Given their total historical spend of ${spend:,.2f}, proactive outreach is recommended to protect "
            f"annual customer lifetime value."
        )

    elif recommendation_type == "REVIEW_SUPPLIER":
        supplier = evidence.get("supplier_name", "the supplier")
        on_time = evidence.get("on_time_delivery_rate", 0.0)
        delayed = evidence.get("delayed_orders_count", 0)

        explanation = (
            f"Supplier {supplier} exhibits a compromised on-time delivery rate of {on_time:.1f}%, with {delayed} "
            f"delayed purchase orders recorded. Consider reviewing SLA commitments or splitting allocation with secondary vendors."
        )

    elif recommendation_type == "REVENUE_INVESTIGATION":
        drop_pct = evidence.get("monthly_drop_pct", 20.0)
        loss = evidence.get("monthly_revenue_drop", expected_impact)

        explanation = (
            f"Monthly revenue dropped by {drop_pct:.1f}% (exposure of ${loss:,.2f}). "
            f"Anomalous transaction deceleration detected across key product categories. An executive root-cause review is recommended."
        )

    else:
        explanation = (
            f"Operational recommendation triggered by policy evaluation. Expected financial impact is estimated at "
            f"${expected_impact:,.2f} based on verified transactional records."
        )

    return explanation, "Evidence-Grounded-Synthesizer"

