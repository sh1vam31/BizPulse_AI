from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import Customer, Product
from app.models.ml import ModelVersion
from app.models.revenue import ChurnPrediction, CustomerFeatures, CustomerSegment, RevenueForecast
from app.models.supply_chain import Sales
from app.schemas.revenue import (
    CustomerChurnItem,
    CustomerLifetimeValueItem,
    CustomerSegmentDistribution,
    RevenueForecastDailyItem,
    RevenueForecastHorizonData,
    RevenueForecastResponse,
    RevenueOverviewResponse,
    RevenueSimulateRequest,
    RevenueSimulateResponse,
)
from ml.features.revenue_features import compute_customer_rfm_features
from ml.pipelines.churn_classifier import ChurnClassifierPipeline
from ml.pipelines.customer_segmenter import CustomerSegmenterPipeline
from ml.pipelines.revenue_forecaster import RevenueForecasterPipeline


def get_revenue_overview(db: Session, organization_id: str) -> RevenueOverviewResponse:
    # Aggregated revenue
    sales_query = (
        db.query(Sales)
        .join(Customer, Sales.customer_id == Customer.id)
        .filter(Customer.organization_id == organization_id)
    )

    tot_agg = (
        sales_query.with_entities(
            func.coalesce(func.sum(Sales.total_amount), 0.0).label("tot_rev"),
            func.count(Sales.id).label("tot_tx"),
        ).first()
    )
    total_rev = float(tot_agg.tot_rev or 0.0)
    total_tx = int(tot_agg.tot_tx or 0)
    aov = total_rev / total_tx if total_tx > 0 else 0.0

    # Monthly revenue comparison
    now = datetime.now(timezone.utc)
    curr_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    if now.month == 1:
        prev_month_start = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
    else:
        prev_month_start = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)

    curr_month_rev = (
        sales_query.filter(Sales.transaction_date >= curr_month_start)
        .with_entities(func.coalesce(func.sum(Sales.total_amount), 0.0))
        .scalar()
    )
    prev_month_rev = (
        sales_query.filter(
            Sales.transaction_date >= prev_month_start,
            Sales.transaction_date < curr_month_start,
        )
        .with_entities(func.coalesce(func.sum(Sales.total_amount), 0.0))
        .scalar()
    )

    c_rev = float(curr_month_rev or 0.0)
    p_rev = float(prev_month_rev or 0.0)
    growth_pct = round(((c_rev - p_rev) / p_rev) * 100.0, 2) if p_rev > 0 else 0.0

    # Monthly trend aggregated in SQL
    day_col = func.date(Sales.transaction_date).label("day")
    daily_rows = (
        db.query(
            day_col,
            func.coalesce(func.sum(Sales.total_amount), 0.0).label("revenue"),
            func.count(Sales.id).label("transactions"),
        )
        .join(Customer, Sales.customer_id == Customer.id)
        .filter(Customer.organization_id == organization_id)
        .group_by(day_col)
        .order_by(day_col.asc())
        .all()
    )

    trend = []
    if daily_rows:
        df_s = pd.DataFrame(
            [(str(r.day)[:7], float(r.revenue), int(r.transactions)) for r in daily_rows],
            columns=["month", "revenue", "transactions"],
        )
        monthly_grp = df_s.groupby("month", sort=True).agg(
            revenue=("revenue", "sum"),
            transactions=("transactions", "sum"),
        ).reset_index()

        trend = [
            {
                "month": r["month"],
                "revenue": round(float(r["revenue"]), 2),
                "transactions": int(r["transactions"]),
            }
            for _, r in monthly_grp.tail(12).iterrows()
        ]

    return RevenueOverviewResponse(
        total_revenue=round(total_rev, 2),
        current_month_revenue=round(c_rev, 2),
        previous_month_revenue=round(p_rev, 2),
        monthly_growth_rate=growth_pct,
        average_order_value=round(aov, 2),
        total_transactions=total_tx,
        historical_monthly_trend=trend,
    )


def generate_revenue_forecast(db: Session, organization_id: str) -> RevenueForecastResponse:
    day_col = func.date(Sales.transaction_date).label("day")
    daily_rows = (
        db.query(day_col, func.coalesce(func.sum(Sales.total_amount), 0.0).label("revenue"))
        .join(Customer, Sales.customer_id == Customer.id)
        .filter(Customer.organization_id == organization_id)
        .group_by(day_col)
        .order_by(day_col.asc())
        .all()
    )

    if not daily_rows:
        base_date = datetime.now(timezone.utc).date()
        daily_df = pd.DataFrame([
            {"date": (base_date - timedelta(days=i)).strftime("%Y-%m-%d"), "revenue": 1000.0 + (i % 7) * 150.0}
            for i in range(30, 0, -1)
        ])
    else:
        daily_df = pd.DataFrame(
            [(str(r.day)[:10], float(r.revenue)) for r in daily_rows],
            columns=["date", "revenue"],
        )

    pipeline = RevenueForecasterPipeline(model_version="v1.0.0")
    train_res = pipeline.train_and_evaluate(daily_df)
    forecast_res = pipeline.predict_future(daily_df, horizons=[7, 30, 90])

    horizons_dict = {}
    for k, v in forecast_res["forecasts"].items():
        daily_items = [
            RevenueForecastDailyItem(
                date=d["date"],
                predicted_revenue=d["predicted_revenue"],
                lower_bound=d["lower_bound"],
                upper_bound=d["upper_bound"],
            )
            for d in v["daily_breakdown"]
        ]
        horizons_dict[k] = RevenueForecastHorizonData(
            horizon_days=v["horizon_days"],
            total_predicted_revenue=v["total_predicted_revenue"],
            daily_average=v["daily_average"],
            daily_breakdown=daily_items,
        )

    # Persist or update model_version and revenue_forecasts
    mv = db.query(ModelVersion).filter(
        ModelVersion.model_name == "RevenueForecaster",
        ModelVersion.version == "v1.0.0",
    ).first()
    if not mv:
        mv = ModelVersion(
            model_name="RevenueForecaster",
            version="v1.0.0",
            algorithm="XGBoostRegressor + MovingAverageBaseline",
            metrics=train_res.get("xgboost_metrics", {}),
            status="ACTIVE",
        )
        db.add(mv)
        db.flush()

    for item in forecast_res["forecasts"]["30_days"]["daily_breakdown"][:7]:
        rf = RevenueForecast(
            organization_id=organization_id,
            model_version_id=mv.id,
            forecast_date=datetime.strptime(item["date"], "%Y-%m-%d").date(),
            period_type="DAILY",
            predicted_revenue=item["predicted_revenue"],
            lower_bound=item["lower_bound"],
            upper_bound=item["upper_bound"],
        )
        db.add(rf)
    db.commit()

    return RevenueForecastResponse(
        organization_id=organization_id,
        forecasts=horizons_dict,
        metrics=train_res.get("xgboost_metrics", {}),
        beats_baseline=train_res.get("beats_baseline", True),
        generated_at=datetime.now(timezone.utc),
    )


def calculate_customer_churn_risks(db: Session, organization_id: str) -> List[CustomerChurnItem]:
    # Query customer sales
    sales = (
        db.query(Sales.customer_id, Sales.transaction_date, Sales.total_amount)
        .join(Customer, Sales.customer_id == Customer.id)
        .filter(Customer.organization_id == organization_id)
        .all()
    )

    if not sales:
        return []

    df_tx = pd.DataFrame(sales, columns=["customer_id", "transaction_date", "total_amount"])
    df_tx["total_amount"] = df_tx["total_amount"].astype(float)

    df_rfm = compute_customer_rfm_features(df_tx)
    pipeline = ChurnClassifierPipeline(model_version="v1.0.0")
    pipeline.train_and_evaluate(df_rfm)
    churn_predictions = pipeline.predict_churn(df_rfm)

    # Persist to customer_features and churn_predictions
    mv = db.query(ModelVersion).filter(
        ModelVersion.model_name == "CustomerChurnClassifier",
        ModelVersion.version == "v1.0.0",
    ).first()
    if not mv:
        mv = ModelVersion(
            model_name="CustomerChurnClassifier",
            version="v1.0.0",
            algorithm="XGBoostClassifier + ClassWeighting",
            metrics=pipeline.metrics,
            status="ACTIVE",
        )
        db.add(mv)
        db.flush()

    customer_map = {
        c.id: c
        for c in db.query(Customer).filter(Customer.organization_id == organization_id).all()
    }
    existing_cf_map = {
        cf.customer_id: cf
        for cf in db.query(CustomerFeatures)
        .join(Customer, CustomerFeatures.customer_id == Customer.id)
        .filter(Customer.organization_id == organization_id)
        .all()
    }

    new_cfs = []
    new_cps = []
    results = []
    for pred in churn_predictions:
        c_id = pred["customer_id"]
        cust = customer_map.get(c_id)
        if not cust:
            continue

        feats = pred["contributing_features"]

        # Update or stage customer_features
        cf = existing_cf_map.get(c_id)
        if not cf:
            new_cfs.append(CustomerFeatures(
                customer_id=c_id,
                recency_days=feats["recency_days"],
                frequency=feats["frequency"],
                monetary_value=feats["monetary_value"],
                avg_order_value=feats["monetary_value"] / max(1, feats["frequency"]),
                tenure_days=100,
                frequency_trend_slope=feats["velocity_slope"],
            ))
        else:
            cf.recency_days = feats["recency_days"]
            cf.frequency = feats["frequency"]
            cf.monetary_value = feats["monetary_value"]
            cf.frequency_trend_slope = feats["velocity_slope"]

        new_cps.append(ChurnPrediction(
            customer_id=c_id,
            model_version_id=mv.id,
            churn_probability=pred["churn_probability"],
            risk_category=pred["risk_category"],
            contributing_features=feats,
        ))

        results.append(
            CustomerChurnItem(
                customer_id=c_id,
                customer_code=cust.customer_code,
                name=cust.name,
                email=cust.email,
                churn_probability=pred["churn_probability"],
                risk_category=pred["risk_category"],
                monetary_value=float(feats["monetary_value"]),
                recency_days=int(feats["recency_days"]),
                velocity_slope=float(feats["velocity_slope"]),
                contributing_features=feats,
            )
        )

    if new_cfs:
        db.bulk_save_objects(new_cfs)
    if new_cps:
        db.bulk_save_objects(new_cps)
    db.commit()
    return results


def calculate_customer_segments(db: Session, organization_id: str) -> List[CustomerSegmentDistribution]:
    sales = (
        db.query(Sales.customer_id, Sales.transaction_date, Sales.total_amount)
        .join(Customer, Sales.customer_id == Customer.id)
        .filter(Customer.organization_id == organization_id)
        .all()
    )
    if not sales:
        return []

    df_tx = pd.DataFrame(sales, columns=["customer_id", "transaction_date", "total_amount"])
    df_tx["total_amount"] = df_tx["total_amount"].astype(float)
    df_rfm = compute_customer_rfm_features(df_tx)

    pipeline = CustomerSegmenterPipeline(n_clusters=5)
    df_segmented, meta = pipeline.fit_and_segment(df_rfm)

    total_org_revenue = df_segmented["monetary_value"].sum()
    segment_stats = df_segmented.groupby("segment").agg(
        count=("customer_id", "count"),
        total_rev=("monetary_value", "sum"),
        avg_spend=("monetary_value", "mean"),
    ).reset_index()

    # Update customer segment values in database in bulk
    cust_map = {
        c.id: c
        for c in db.query(Customer).filter(Customer.organization_id == organization_id).all()
    }
    seg_entries = []
    for cid, seg in zip(df_segmented["customer_id"], df_segmented["segment"]):
        c = cust_map.get(cid)
        if c:
            c.current_segment = seg
            seg_entries.append(CustomerSegment(customer_id=c.id, segment_name=seg))
    if seg_entries:
        db.bulk_save_objects(seg_entries)
    db.commit()

    distributions = []
    for _, s in segment_stats.iterrows():
        tot_s = float(s["total_rev"])
        pct = (tot_s / total_org_revenue * 100.0) if total_org_revenue > 0 else 0.0
        distributions.append(
            CustomerSegmentDistribution(
                segment_name=s["segment"],
                customer_count=int(s["count"]),
                total_revenue=round(tot_s, 2),
                average_spend=round(float(s["avg_spend"]), 2),
                revenue_contribution_pct=round(pct, 2),
            )
        )

    return sorted(distributions, key=lambda x: x.total_revenue, reverse=True)


def simulate_revenue_scenario(
    db: Session, organization_id: str, req: RevenueSimulateRequest
) -> RevenueSimulateResponse:
    # Baseline 30-day revenue
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    baseline_rev = (
        db.query(func.coalesce(func.sum(Sales.total_amount), 0.0))
        .join(Customer, Sales.customer_id == Customer.id)
        .filter(
            Customer.organization_id == organization_id,
            Sales.transaction_date >= thirty_days_ago,
        )
        .scalar()
    )
    baseline = float(baseline_rev or 100000.0)

    # High-value customers contribution
    high_val_rev = baseline * 0.60  # Pareto approximation

    churn_loss = high_val_rev * (req.high_value_churn_pct / 100.0)
    aov_gain = baseline * (req.aov_change_pct / 100.0)
    retention_gain = baseline * (req.retention_improvement_pct / 100.0) * 0.5

    simulated = max(0.0, baseline - churn_loss + aov_gain + retention_gain)
    diff = round(simulated - baseline, 2)
    pct_impact = round((diff / baseline) * 100.0, 2) if baseline > 0 else 0.0

    if diff < 0:
        recovery = (
            f"Mitigate potential ${abs(diff):,.2f} drop by initiating personalized retention outreach "
            f"to top {int(req.high_value_churn_pct)}% at-risk accounts."
        )
    else:
        recovery = f"Simulated upside of ${diff:,.2f} through AOV expansion and improved retention."

    return RevenueSimulateResponse(
        scenario_parameters={
            "high_value_churn_pct": req.high_value_churn_pct,
            "aov_change_pct": req.aov_change_pct,
            "retention_improvement_pct": req.retention_improvement_pct,
        },
        baseline_expected_revenue=round(baseline, 2),
        simulated_expected_revenue=round(simulated, 2),
        revenue_difference=diff,
        percentage_impact=pct_impact,
        estimated_financial_loss_or_gain=diff,
        potential_recovery_opportunities=recovery,
        assumptions_summary=(
            f"Simulated {req.high_value_churn_pct}% high-value churn, {req.aov_change_pct}% AOV adjustment, "
            f"and {req.retention_improvement_pct}% retention lift over 30 days."
        ),
    )
