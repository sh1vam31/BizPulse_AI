import io
import pandas as pd
from app.models.entities import Customer, Product, Supplier
from app.models.supply_chain import Sales


def test_validate_products_csv_success(client, admin_auth_headers):
    csv_content = """sku,name,category,unit_cost,selling_price,reorder_threshold,safety_stock
PROD-001,MacBook Pro 16,Electronics,1800.00,2499.00,20,10
PROD-002,Dell XPS 15,Electronics,1200.00,1799.00,15,5
"""
    files = {"file": ("products.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/data/validate", files=files, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["detected_entity_type"] == "products"
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 2
    assert data["invalid_rows"] == 0


def test_validate_products_csv_with_errors(client, admin_auth_headers):
    csv_content = """sku,name,category,unit_cost,selling_price
,Invalid SKU Product,Electronics,-50.00,0.00
PROD-003,Valid Product,Electronics,100.00,150.00
"""
    files = {"file": ("products_with_errors.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/data/validate", files=files, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["total_rows"] == 2
    assert data["invalid_rows"] == 1
    assert data["valid_rows"] == 1
    assert len(data["errors"]) > 0


def test_upload_products_csv_and_verify(client, admin_auth_headers, db, test_organization):
    csv_content = """sku,name,category,unit_cost,selling_price,reorder_threshold,safety_stock
SKU-LAPTOP-101,Pro Laptop 14,Computers,1100.00,1599.00,30,10
SKU-PHONE-202,SmartPhone X,Mobile,600.00,899.00,40,15
"""
    files = {"file": ("products_catalog.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/data/upload", files=files, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["records_processed"] == 2
    assert data["records_failed"] == 0

    # Verify directly in database
    products = db.query(Product).filter(Product.organization_id == test_organization.id).all()
    skus = [p.sku for p in products]
    assert "SKU-LAPTOP-101" in skus
    assert "SKU-PHONE-202" in skus


def test_upload_customers_csv(client, admin_auth_headers, db, test_organization):
    csv_content = """customer_code,name,email,phone,current_segment
CUST-1001,John Smith,john@example.com,555-0101,High-Value Customers
CUST-1002,Alice Walker,alice@example.com,555-0102,Loyal Customers
"""
    files = {"file": ("customers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/data/upload", files=files, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["records_processed"] == 2

    custs = db.query(Customer).filter(Customer.organization_id == test_organization.id).all()
    codes = [c.customer_code for c in custs]
    assert "CUST-1001" in codes
    assert "CUST-1002" in codes


def test_upload_suppliers_csv(client, admin_auth_headers, db, test_organization):
    csv_content = """supplier_code,name,contact_email,reliability_score,average_lead_days
SUPP-001,Global Tech Logistics,orders@globaltech.com,96.5,4
SUPP-002,FastParts Corp,support@fastparts.com,88.0,7
"""
    files = {"file": ("suppliers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/data/upload", files=files, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["records_processed"] == 2

    suppliers = db.query(Supplier).filter(Supplier.organization_id == test_organization.id).all()
    codes = [s.supplier_code for s in suppliers]
    assert "SUPP-001" in codes
    assert "SUPP-002" in codes


def test_upload_sales_csv(client, admin_auth_headers, db, test_organization):
    csv_content = """customer_code,sku,quantity,unit_price,total_amount,transaction_date
CUST-1001,SKU-LAPTOP-101,2,1599.00,3198.00,2026-11-20 14:30:00
CUST-1002,SKU-PHONE-202,1,899.00,899.00,2026-11-21 09:15:00
"""
    files = {"file": ("transactions.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/data/upload", files=files, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["records_processed"] == 2

    sales = db.query(Sales).all()
    assert len(sales) >= 2


def test_upload_excel_file(client, admin_auth_headers):
    df = pd.DataFrame([
        {"sku": "SKU-EXCEL-1", "name": "Excel Tablet", "category": "Gadgets", "unit_cost": 200.0, "selling_price": 350.0},
        {"sku": "SKU-EXCEL-2", "name": "Excel Stylus", "category": "Accessories", "unit_cost": 25.0, "selling_price": 60.0},
    ])
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine="openpyxl")
    excel_buffer.seek(0)

    files = {"file": ("products_catalog.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/api/v1/data/upload", files=files, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["records_processed"] == 2


def test_get_data_sources_and_import_history(client, admin_auth_headers):
    # Perform an upload first to populate data sources and import jobs in this session
    csv_content = """sku,name,category,unit_cost,selling_price
SKU-SRC-01,Source Item,General,10.0,20.0
"""
    files = {"file": ("source_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/data/upload", files=files, headers=admin_auth_headers)
    assert upload_res.status_code == 201

    # Test sources
    src_res = client.get("/api/v1/data/sources", headers=admin_auth_headers)
    assert src_res.status_code == 200
    sources = src_res.json()
    assert len(sources) > 0

    # Test imports
    imp_res = client.get("/api/v1/data/imports", headers=admin_auth_headers)
    assert imp_res.status_code == 200
    imports = imp_res.json()
    assert len(imports) > 0

    # Test single import detail
    job_id = imports[0]["id"]
    detail_res = client.get(f"/api/v1/data/imports/{job_id}", headers=admin_auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == job_id


def test_upload_unauthenticated_fails(client):
    csv_content = "sku,name,category,unit_cost,selling_price\nPROD-1,Item,Cat,10,20\n"
    files = {"file": ("products.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/data/upload", files=files)
    assert response.status_code == 401
