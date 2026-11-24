import os
import sys
import uuid
import random
from datetime import date, datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal, engine
from app.models.base import Base
import app.models  # register all models
from app.models.auth import Organization, User
from app.models.entities import Product, Customer, Supplier, Warehouse
from app.models.supply_chain import Inventory, PurchaseOrder, Sales
from app.core.security import get_password_hash
from ml.pipelines.demand_forecaster import DemandForecasterPipeline
from ml.pipelines.revenue_forecaster import RevenueForecasterPipeline
from ml.pipelines.churn_classifier import ChurnClassifierPipeline
from ml.pipelines.customer_segmenter import CustomerSegmenterPipeline
from app.services.decision_engine import evaluate_and_generate_recommendations


def generate_seed_data():
    print("=" * 70)
    print("  BUSINESSPULSE AI - SEEDING ENTERPRISE DEMO DATASET")
    print("=" * 70)
    
    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Organization & Admin User
        org = db.query(Organization).filter(Organization.name == "BizPulse Retail Enterprise").first()
        if not org:
            org = Organization(
                name="BizPulse Retail Enterprise"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"[+] Organization created: {org.name} ({org.id})")
        else:
            print(f"[*] Organization exists: {org.name} ({org.id})")

        admin_user = db.query(User).filter(User.email == "admin@bizpulse.ai").first()
        if not admin_user:
            admin_user = User(
                organization_id=org.id,
                email="admin@bizpulse.ai",
                name="Chief Operations Officer",
                password_hash=get_password_hash("AdminPass123!"),
                role="Admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("[+] Seed Admin User: admin@bizpulse.ai / AdminPass123!")

        # 2. Warehouses
        warehouse_names = [
            ("Main Distribution Center", "Chicago, IL"),
            ("West Coast Logistics Hub", "Reno, NV"),
            ("East Coast Terminal", "Newark, NJ"),
            ("Central Fulfilment Center", "Dallas, TX"),
            ("Southern Gateway", "Atlanta, GA"),
        ]
        warehouses = []
        for name, loc in warehouse_names:
            w = db.query(Warehouse).filter(Warehouse.organization_id == org.id, Warehouse.name == name).first()
            if not w:
                w = Warehouse(organization_id=org.id, name=name, location=loc)
                db.add(w)
                db.commit()
                db.refresh(w)
            warehouses.append(w)
        print(f"[+] Verified {len(warehouses)} distribution warehouses.")

        # 3. Suppliers
        suppliers_data = [
            ("Apex Global Electronics", "apex@apexglobal.com", 92.5, 5),
            ("Shenzhen Micro Optics", "contact@szoptics.cn", 68.0, 14), # Delayed / low reliability
            ("Nordic Ergonomics Mfg", "orders@nordic-ergo.se", 96.0, 7),
            ("Titan Heavy Logistics", "titan@titanmfg.com", 85.0, 10),
            ("Cascade Audio Tech", "b2b@cascadeaudio.com", 89.0, 6),
            ("Pacific Plastic Solutions", "sales@pacificplastics.com", 72.0, 12),
            ("Pinnacle Hardware Group", "support@pinnacle.com", 95.0, 4),
            ("Vanguard Display Corp", "vanguard@displaycorp.com", 64.0, 15), # Risky supplier
        ]
        suppliers = []
        for i, (s_name, email, rel, lead) in enumerate(suppliers_data, 1):
            code = f"SUP-{i:03d}"
            s = db.query(Supplier).filter(Supplier.organization_id == org.id, Supplier.supplier_code == code).first()
            if not s:
                s = Supplier(
                    organization_id=org.id,
                    supplier_code=code,
                    name=s_name,
                    contact_email=email,
                    reliability_score=rel,
                    average_lead_days=lead
                )
                db.add(s)
                db.commit()
                db.refresh(s)
            suppliers.append(s)
        print(f"[+] Verified {len(suppliers)} international suppliers.")

        # 4. Products across Categories
        categories = ["Electronics", "Office Furniture", "Audio & Visual", "Smart Home", "Accessories"]
        products_meta = [
            # Scenario A Product: High demand, critical stockout risk!
            ("PROD-ELEC-001", "Ultra HD Quantum 55 Display", "Electronics", 320.0, 599.0, 40, 20, 15),
            ("PROD-ELEC-002", "ProBook Carbon Laptop 16-inch", "Electronics", 750.0, 1299.0, 30, 15, 45),
            ("PROD-ELEC-003", "Noise-Cancelling Studio Pro Headphones", "Audio & Visual", 85.0, 199.0, 50, 25, 120),
            ("PROD-FURN-001", "Ergonomic Lumbar Office Chair", "Office Furniture", 140.0, 349.0, 25, 10, 80),
            ("PROD-FURN-002", "Motorized Dual-Motor Standing Desk", "Office Furniture", 220.0, 499.0, 20, 10, 35),
            ("PROD-HOME-001", "Smart Zigbee Environmental Hub", "Smart Home", 35.0, 89.0, 60, 30, 150),
            ("PROD-HOME-002", "Robotic LiDAR Floor Cleaner", "Smart Home", 180.0, 399.0, 30, 15, 22),
            ("PROD-ACCS-001", "Thunderbolt 4 Multi-Port Dock", "Accessories", 60.0, 149.0, 50, 25, 95),
            ("PROD-ACCS-002", "Braided High-Current USB-C Pack", "Accessories", 6.0, 24.99, 100, 50, 400),
            ("PROD-ACCS-003", "Wireless Mechanical Tactile Keyboard", "Accessories", 45.0, 119.0, 40, 20, 75),
        ]
        
        products = []
        for sku, p_name, cat, cost, price, reorder, safety, init_stock in products_meta:
            p = db.query(Product).filter(Product.organization_id == org.id, Product.sku == sku).first()
            if not p:
                p = Product(
                    organization_id=org.id,
                    sku=sku,
                    name=p_name,
                    category=cat,
                    unit_cost=cost,
                    selling_price=price,
                    reorder_threshold=reorder,
                    safety_stock=safety
                )
                db.add(p)
                db.commit()
                db.refresh(p)
                
                # Assign initial inventory in Main DC
                inv = Inventory(
                    product_id=p.id,
                    warehouse_id=warehouses[0].id,
                    available_quantity=init_stock,
                    reserved_quantity=2
                )
                db.add(inv)
                db.commit()
            products.append(p)
        print(f"[+] Verified {len(products)} core catalog SKUs with initial warehouse inventory.")

        # 5. Customers
        customer_meta = [
            # Scenario B Customer: Top historical spender who recently stopped buying (churn candidate!)
            ("CUST-ENT-001", "Acme Global Logistics Enterprise", "enterprise@acmeglobal.com", "Champions"),
            ("CUST-ENT-002", "NovaTech Cloud Systems", "procure@novatech.io", "Champions"),
            ("CUST-MID-001", "Apex Creative Studios", "billing@apexcreate.design", "Loyal"),
            ("CUST-MID-002", "Solstice Media Network", "ops@solsticemedia.com", "Loyal"),
            ("CUST-RET-001", "David Sterling", "d.sterling@gmail.com", "Potential"),
            ("CUST-RET-002", "Rachel Vance", "rvance@outlook.com", "Potential"),
            ("CUST-RET-003", "Marcus Aurelius Chen", "marcus.chen@techcorp.com", "At Risk"),
            ("CUST-RET-004", "Sophia Montgomery", "sophia.m@gmail.com", "Hibernating"),
        ]
        customers = []
        for c_code, c_name, email, seg in customer_meta:
            c = db.query(Customer).filter(Customer.organization_id == org.id, Customer.customer_code == c_code).first()
            if not c:
                c = Customer(
                    organization_id=org.id,
                    customer_code=c_code,
                    name=c_name,
                    email=email,
                    phone="+1-555-019-2834",
                    current_segment=seg
                )
                db.add(c)
                db.commit()
                db.refresh(c)
            customers.append(c)
        print(f"[+] Verified {len(customers)} business & consumer accounts.")

        # 6. Sales Transactions over the last 180 days
        tx_count = db.query(Sales).join(Customer).filter(Customer.organization_id == org.id).count()
        if tx_count < 200:
            print("[*] Synthesizing historical sales transactions across past 180 days...")
            now = datetime.utcnow()
            random.seed(42)
            
            transactions_to_add = []
            # Day-by-day generation
            for day_offset in range(180, 0, -1):
                tx_date = now - timedelta(days=day_offset)
                
                # Scenario A: Product 1 (Quantum 55 Display) demand increases strongly in last 30 days
                quantum_demand = random.randint(8, 14) if day_offset <= 30 else random.randint(3, 7)
                tx1 = Sales(
                    customer_id=customers[2].id, # Apex Creative
                    product_id=products[0].id, # Quantum 55
                    quantity=quantum_demand,
                    unit_price=products[0].selling_price,
                    total_amount=quantum_demand * products[0].selling_price,
                    transaction_date=tx_date
                )
                transactions_to_add.append(tx1)

                # Scenario B: Acme Global (Customer 0) bought heavily 180-60 days ago, then stopped completely
                if day_offset >= 50:
                    acme_qty = random.randint(5, 12)
                    tx2 = Sales(
                        customer_id=customers[0].id, # Acme Global
                        product_id=products[1].id, # ProBook
                        quantity=acme_qty,
                        unit_price=products[1].selling_price,
                        total_amount=acme_qty * products[1].selling_price,
                        transaction_date=tx_date
                    )
                    transactions_to_add.append(tx2)

                # Regular transactions across other customers & products
                for _ in range(random.randint(4, 9)):
                    cust = random.choice(customers[1:])
                    prod = random.choice(products)
                    qty = random.randint(1, 4)
                    tx_rand = Sales(
                        customer_id=cust.id,
                        product_id=prod.id,
                        quantity=qty,
                        unit_price=prod.selling_price,
                        total_amount=qty * prod.selling_price,
                        transaction_date=tx_date
                    )
                    transactions_to_add.append(tx_rand)

            db.bulk_save_objects(transactions_to_add)
            db.commit()
            print(f"[+] Successfully generated {len(transactions_to_add)} historical sales transactions.")
        else:
            print(f"[*] Found {tx_count} existing sales transactions.")

        # 7. Seed Purchase Orders for Suppliers
        po_count = db.query(PurchaseOrder).join(Supplier).filter(Supplier.organization_id == org.id).count()
        if po_count == 0:
            print("[*] Seeding historical purchase orders to compute supplier reliability metrics...")
            pos = []
            now_date = date.today()
            for s in suppliers:
                for idx in range(1, 6):
                    is_delayed = (s.reliability_score < 75) and (idx % 2 == 0)
                    lead = s.average_lead_days + (4 if is_delayed else 0)
                    order_d = now_date - timedelta(days=idx * 20)
                    expected_d = order_d + timedelta(days=s.average_lead_days)
                    actual_d = order_d + timedelta(days=lead)
                    
                    po = PurchaseOrder(
                        supplier_id=s.id,
                        product_id=random.choice(products).id,
                        quantity=100,
                        total_cost=5000.0,
                        order_date=order_d,
                        expected_delivery=expected_d,
                        actual_delivery=actual_d,
                        status="DELIVERED"
                    )
                    pos.append(po)
            db.bulk_save_objects(pos)
            db.commit()
            print(f"[+] Created {len(pos)} supplier purchase orders.")

        # 8. Run ML Demand Forecasting for all seeded products
        print("\n[*] Executing ML Demand Forecasting Pipeline (XGBoost)...")
        from app.services.supply_chain_service import generate_product_demand_forecast, calculate_inventory_risks, get_supplier_scorecards
        for p in products:
            try:
                generate_product_demand_forecast(db, org.id, p.id)
            except Exception as e:
                print(f"    [!] Forecast skipped for {p.sku}: {e}")
        inv_risks = calculate_inventory_risks(db, org.id)
        sup_scores = get_supplier_scorecards(db, org.id)
        print(f"    [+] Generated forecasts. Detected {len(inv_risks)} stockout risks and scored {len(sup_scores)} suppliers.")

        # 9. Run ML Revenue Forecasting Pipeline
        print("\n[*] Executing ML Revenue Cashflow Forecasting Pipeline (XGBoost)...")
        from app.services.revenue_service import generate_revenue_forecast, calculate_customer_churn_risks, calculate_customer_segments
        rev_fc = generate_revenue_forecast(db, org.id)
        fc_30 = rev_fc.forecasts.get("30_days") or rev_fc.forecasts.get("30d")
        total_30d = fc_30.total_predicted_revenue if fc_30 else 0.0
        print(f"    [+] 30D Forecast: ${total_30d:,.2f} (Beats baseline: {rev_fc.beats_baseline})")

        # 10. Run Customer Churn Classifier Pipeline
        print("\n[*] Executing XGBoost Customer Churn Classifier...")
        churn_items = calculate_customer_churn_risks(db, org.id)
        critical_churn = [c for c in churn_items if c.risk_category in ("CRITICAL", "HIGH")]
        print(f"    [+] Evaluated {len(churn_items)} accounts. {len(critical_churn)} flagged at Critical/High churn risk.")

        # 11. Run Customer Segmentation Pipeline
        print("\n[*] Executing K-Means RFM Customer Segmentation...")
        segments = calculate_customer_segments(db, org.id)
        print(f"    [+] Discovered {len(segments)} customer behavioral clusters.")

        # 12. Run Deterministic Decision & Recommendation Engine
        print("\n[*] Running Business Rules & Decision Engine...")
        recs, summary = evaluate_and_generate_recommendations(db, org.id)
        print(f"    [+] Decision Engine generated {len(recs)} grounded recommendations:")
        for r in recs:
            print(f"        - [{r.module.upper()}] ({r.priority}) {r.title}: Est Impact ${r.expected_financial_impact:,.0f}")

        print("\n" + "=" * 70)
        print("  DEMO DATASET & PREDICTIVE MODELS FULLY SEEDED & READY!")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[!] Error during seed data generation: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    generate_seed_data()
