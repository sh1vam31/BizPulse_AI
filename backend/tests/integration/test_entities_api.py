from datetime import date, datetime, timezone
from app.models.entities import Customer, Product, Supplier, Warehouse
from app.models.supply_chain import Inventory, PurchaseOrder, Sales


def test_list_and_get_products(client, admin_auth_headers, db, test_organization):
    p = Product(
        organization_id=test_organization.id,
        sku="SKU-ENTITY-TEST-1",
        name="Ultra Monitor 27",
        category="Monitors",
        unit_cost=250.00,
        selling_price=399.00,
        reorder_threshold=15,
        safety_stock=5,
    )
    db.add(p)
    db.commit()

    # Add warehouse & inventory
    w = Warehouse(
        organization_id=test_organization.id,
        name="Central Warehouse",
        location="Chicago, IL",
    )
    db.add(w)
    db.commit()

    inv = Inventory(
        product_id=p.id,
        warehouse_id=w.id,
        available_quantity=45,
        reserved_quantity=5,
    )
    db.add(inv)

    # Add customer & sale
    c = Customer(
        organization_id=test_organization.id,
        customer_code="CUST-ENT-1",
        name="Tech Buyer Inc",
    )
    db.add(c)
    db.commit()

    sale = Sales(
        customer_id=c.id,
        product_id=p.id,
        quantity=3,
        unit_price=399.00,
        total_amount=1197.00,
        transaction_date=datetime.now(timezone.utc),
    )
    db.add(sale)
    db.commit()

    # Test list products
    res = client.get("/api/v1/entities/products", headers=admin_auth_headers)
    assert res.status_code == 200
    products = res.json()
    assert len(products) > 0
    target = next((item for item in products if item["id"] == p.id), None)
    assert target is not None
    assert target["sku"] == "SKU-ENTITY-TEST-1"
    assert target["available_stock"] == 45
    assert target["total_sales_quantity"] == 3
    assert target["total_revenue"] == 1197.00

    # Test get product detail
    detail_res = client.get(f"/api/v1/entities/products/{p.id}", headers=admin_auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == p.id
    assert len(detail["inventory_by_warehouse"]) == 1
    assert detail["inventory_by_warehouse"][0]["warehouse_name"] == "Central Warehouse"
    assert detail["inventory_by_warehouse"][0]["available_quantity"] == 45
    assert detail["recent_sales_count"] == 1


def test_list_and_get_customers(client, admin_auth_headers, db, test_organization):
    c = Customer(
        organization_id=test_organization.id,
        customer_code="CUST-ENT-VIP",
        name="Enterprise Client",
        email="buyer@enterprise.com",
        current_segment="High-Value Customers",
    )
    db.add(c)
    db.commit()

    p = Product(
        organization_id=test_organization.id,
        sku="SKU-ENT-SERVER",
        name="Rack Server X",
        category="Servers",
        unit_cost=3000.0,
        selling_price=4500.0,
    )
    db.add(p)
    db.commit()

    s = Sales(
        customer_id=c.id,
        product_id=p.id,
        quantity=2,
        unit_price=4500.0,
        total_amount=9000.0,
        transaction_date=datetime.now(timezone.utc),
    )
    db.add(s)
    db.commit()

    # Test list customers
    res = client.get("/api/v1/entities/customers", headers=admin_auth_headers)
    assert res.status_code == 200
    customers = res.json()
    target = next((item for item in customers if item["id"] == c.id), None)
    assert target is not None
    assert target["customer_code"] == "CUST-ENT-VIP"
    assert target["total_spend"] == 9000.0
    assert target["total_orders"] == 1

    # Test customer detail
    detail_res = client.get(f"/api/v1/entities/customers/{c.id}", headers=admin_auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == c.id
    assert len(detail["recent_transactions"]) == 1
    assert detail["recent_transactions"][0]["sku"] == "SKU-ENT-SERVER"


def test_list_and_get_suppliers(client, admin_auth_headers, db, test_organization):
    s = Supplier(
        organization_id=test_organization.id,
        supplier_code="SUPP-ENT-FAST",
        name="FastLine Hardware",
        contact_email="supply@fastline.com",
        reliability_score=95.0,
        average_lead_days=3,
    )
    db.add(s)
    db.commit()

    p = Product(
        organization_id=test_organization.id,
        sku="SKU-ENT-CHIP",
        name="CPU Chipset",
        category="Components",
        unit_cost=150.0,
        selling_price=220.0,
    )
    db.add(p)
    db.commit()

    po = PurchaseOrder(
        supplier_id=s.id,
        product_id=p.id,
        quantity=100,
        total_cost=15000.0,
        order_date=date(2026, 11, 1),
        expected_delivery=date(2026, 11, 5),
        actual_delivery=date(2026, 11, 4),  # On time!
        status="DELIVERED",
    )
    db.add(po)
    db.commit()

    # Test list suppliers
    res = client.get("/api/v1/entities/suppliers", headers=admin_auth_headers)
    assert res.status_code == 200
    suppliers = res.json()
    target = next((item for item in suppliers if item["id"] == s.id), None)
    assert target is not None
    assert target["supplier_code"] == "SUPP-ENT-FAST"
    assert target["total_orders"] == 1
    assert target["on_time_delivery_rate"] == 100.0

    # Test supplier detail
    detail_res = client.get(f"/api/v1/entities/suppliers/{s.id}", headers=admin_auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == s.id
    assert len(detail["recent_purchase_orders"]) == 1


def test_entity_not_found(client, admin_auth_headers):
    res = client.get("/api/v1/entities/products/non-existent-id", headers=admin_auth_headers)
    assert res.status_code == 404
    res2 = client.get("/api/v1/entities/customers/non-existent-id", headers=admin_auth_headers)
    assert res2.status_code == 404
    res3 = client.get("/api/v1/entities/suppliers/non-existent-id", headers=admin_auth_headers)
    assert res3.status_code == 404

