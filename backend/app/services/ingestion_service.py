import io
import math
import re
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from app.models.data import DataImportJob, ImportErrorLog
from app.models.entities import Customer, Product, Supplier, Warehouse
from app.models.supply_chain import Inventory, PurchaseOrder, Sales
from app.schemas.data import DataValidationResponse

# Canonical entity schemas and known aliases
ENTITY_CANONICAL_COLUMNS: Dict[str, Dict[str, List[str]]] = {
    "products": {
        "sku": ["sku", "stock_code", "stockcode", "product_sku", "product_code", "item_code", "product_id", "productid", "item_id", "id"],
        "name": ["name", "product_name", "title", "item_name", "description", "item_description"],
        "category": ["category", "product_category", "type", "department"],
        "unit_cost": ["unit_cost", "cost", "purchase_price", "cost_price"],
        "selling_price": ["selling_price", "price", "unit_price", "unitprice", "retail_price"],
        "reorder_threshold": ["reorder_threshold", "reorder_point", "threshold", "min_stock"],
        "safety_stock": ["safety_stock", "buffer_stock", "safety_quantity"],
    },
    "customers": {
        "customer_code": ["customer_code", "customer_id", "customerid", "client_id", "clientid", "code", "id", "user_id"],
        "name": ["name", "customer_name", "full_name", "client_name"],
        "email": ["email", "email_address", "contact_email"],
        "phone": ["phone", "phone_number", "mobile", "contact_number"],
        "current_segment": ["current_segment", "segment", "customer_segment", "tier"],
    },
    "suppliers": {
        "supplier_code": ["supplier_code", "supplier_id", "supplierid", "vendor_id", "code", "id"],
        "name": ["name", "supplier_name", "vendor_name", "company_name"],
        "contact_email": ["contact_email", "email", "supplier_email"],
        "reliability_score": ["reliability_score", "reliability", "score", "rating"],
        "average_lead_days": ["average_lead_days", "lead_days", "lead_time", "delivery_days"],
    },
    "warehouses": {
        "name": ["name", "warehouse_name", "location_name"],
        "location": ["location", "address", "city", "region", "country"],
    },
    "inventory": {
        "sku": ["sku", "stock_code", "stockcode", "product_sku", "product_code", "item_code"],
        "warehouse_name": ["warehouse_name", "warehouse", "location"],
        "available_quantity": ["available_quantity", "available", "stock", "quantity", "qty"],
        "reserved_quantity": ["reserved_quantity", "reserved", "allocated"],
    },
    "sales": {
        "customer_code": ["customer_code", "customer_id", "customerid", "client_id", "clientid", "code", "id", "user_id"],
        "sku": ["sku", "stock_code", "stockcode", "product_sku", "product_code", "item_code", "product_id", "productid"],
        "quantity": ["quantity", "qty", "units_sold", "units", "count"],
        "unit_price": ["unit_price", "unitprice", "price", "selling_price", "sellingprice", "cost", "unit_cost"],
        "total_amount": ["total_amount", "totalamount", "amount", "total", "revenue", "sales"],
        "transaction_date": ["transaction_date", "transactiondate", "date", "invoice_date", "invoicedate", "order_date", "orderdate", "sale_date", "timestamp", "datetime"],
    },
    "purchase_orders": {
        "supplier_code": ["supplier_code", "supplier_id", "supplierid", "vendor_id"],
        "sku": ["sku", "stock_code", "stockcode", "product_sku", "product_code"],
        "quantity": ["quantity", "qty", "order_quantity"],
        "total_cost": ["total_cost", "cost", "total_amount", "amount"],
        "order_date": ["order_date", "date", "created_date"],
        "expected_delivery": ["expected_delivery", "expected_date", "due_date"],
        "actual_delivery": ["actual_delivery", "delivered_date", "actual_date"],
        "status": ["status", "order_status"],
    },
}

REQUIRED_CANONICAL_FIELDS: Dict[str, List[str]] = {
    "products": ["sku", "name", "category", "unit_cost", "selling_price"],
    "customers": ["customer_code", "name"],
    "suppliers": ["supplier_code", "name"],
    "warehouses": ["name", "location"],
    "inventory": ["sku", "warehouse_name", "available_quantity"],
    "sales": ["customer_code", "sku", "quantity", "unit_price", "transaction_date"],
    "purchase_orders": ["supplier_code", "sku", "quantity", "total_cost", "order_date", "expected_delivery"],
}


def normalize_col(name: str) -> str:
    s = str(name).strip()
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'([A-Z]+)([A-Z][a-z0-9])', r'\1_\2', s)
    return s.lower().replace(" ", "_").replace("-", "_")


def parse_file_to_dataframe(file_bytes: bytes, filename: str) -> pd.DataFrame:
    filename_lower = filename.lower()
    if filename_lower.endswith(".csv") or filename_lower.endswith(".txt"):
        try:
            return pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8", encoding_errors="replace")
        except Exception:
            return pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")
    elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
        return pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError(f"Unsupported file format for file: {filename}. Supported: CSV, Excel (.xlsx, .xls)")


def detect_schema(columns: List[str]) -> Tuple[Optional[str], Dict[str, str]]:
    cleaned_columns = {col: normalize_col(col) for col in columns}
    best_entity = None
    best_match_score = -1
    best_mapping: Dict[str, str] = {}

    for entity, canonical_fields in ENTITY_CANONICAL_COLUMNS.items():
        matched_canonical = {}
        for orig_col, cleaned in cleaned_columns.items():
            for can_field, aliases in canonical_fields.items():
                if (cleaned in aliases or cleaned.replace("_", "") in [a.replace("_", "") for a in aliases]) and can_field not in matched_canonical.values():
                    matched_canonical[orig_col] = can_field
                    break

        required = REQUIRED_CANONICAL_FIELDS[entity]
        required_matched = sum(1 for req in required if req in matched_canonical.values())
        score = required_matched / len(required)

        if score > best_match_score and score >= 0.5:
            best_match_score = score
            best_entity = entity
            best_mapping = matched_canonical

    return best_entity, best_mapping


def validate_dataframe(
    df: pd.DataFrame, entity_type: str, mapping: Dict[str, str]
) -> DataValidationResponse:
    if entity_type not in REQUIRED_CANONICAL_FIELDS:
        return DataValidationResponse(
            is_valid=False,
            detected_entity_type=entity_type,
            total_rows=len(df),
            valid_rows=0,
            invalid_rows=len(df),
            column_mappings=mapping,
            errors=[{"error": f"Unknown entity type: {entity_type}"}],
        )

    # Invert mapping to find canonical -> original col
    inv_mapping = {v: k for k, v in mapping.items()}
    required = REQUIRED_CANONICAL_FIELDS[entity_type]
    missing_required = [req for req in required if req not in inv_mapping]

    if missing_required:
        return DataValidationResponse(
            is_valid=False,
            detected_entity_type=entity_type,
            total_rows=len(df),
            valid_rows=0,
            invalid_rows=len(df),
            column_mappings=mapping,
            errors=[{"error": f"Missing required columns for {entity_type}: {missing_required}"}],
        )

    errors = []

    # High performance vectorized validation for all entities
    if entity_type == "sales":
        sku_col = inv_mapping["sku"]
        qty_col = inv_mapping["quantity"]
        price_col = inv_mapping["unit_price"]
        date_col = inv_mapping["transaction_date"]

        sku_s = df[sku_col].fillna("").astype(str).str.strip()
        sku_invalid = (sku_s == "") | (sku_s.str.lower().isin(["nan", "none"]))
        qty_num = pd.to_numeric(df[qty_col], errors="coerce")
        qty_invalid = qty_num.isna() | (qty_num <= 0)
        price_num = pd.to_numeric(df[price_col], errors="coerce")
        price_invalid = price_num.isna() | (price_num < 0)
        date_num = pd.to_datetime(df[date_col], errors="coerce")
        date_invalid = date_num.isna()

        invalid_mask = sku_invalid | qty_invalid | price_invalid | date_invalid
        invalid_count = int(invalid_mask.sum())
        valid_count = len(df) - invalid_count

        if invalid_count > 0:
            sample_bad_indices = df.index[invalid_mask][:25]
            for idx in sample_bad_indices:
                row_num = int(idx) + 2
                if sku_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "sku", "message": "Product SKU cannot be empty"})
                if qty_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "quantity", "message": "Sales quantity must be positive"})
                if price_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "unit_price", "message": "Unit price must be non-negative"})
                if date_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "transaction_date", "message": "Invalid date format"})

    elif entity_type == "products":
        sku_col = inv_mapping["sku"]
        cost_col = inv_mapping["unit_cost"]
        price_col = inv_mapping["selling_price"]

        sku_s = df[sku_col].fillna("").astype(str).str.strip()
        sku_invalid = (sku_s == "") | (sku_s.str.lower().isin(["nan", "none"]))
        cost_num = pd.to_numeric(df[cost_col], errors="coerce")
        cost_invalid = cost_num.isna() | (cost_num < 0)
        price_num = pd.to_numeric(df[price_col], errors="coerce")
        price_invalid = price_num.isna() | (price_num <= 0)

        invalid_mask = sku_invalid | cost_invalid | price_invalid
        invalid_count = int(invalid_mask.sum())
        valid_count = len(df) - invalid_count

        if invalid_count > 0:
            sample_bad_indices = df.index[invalid_mask][:25]
            for idx in sample_bad_indices:
                row_num = int(idx) + 2
                if sku_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "sku", "message": "Product SKU cannot be empty"})
                if cost_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "unit_cost", "message": "Unit cost must be non-negative"})
                if price_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "selling_price", "message": "Selling price must be greater than zero"})

    elif entity_type == "customers":
        code_col = inv_mapping["customer_code"]
        code_s = df[code_col].fillna("").astype(str).str.strip()
        invalid_mask = (code_s == "") | (code_s.str.lower().isin(["nan", "none"]))
        invalid_count = int(invalid_mask.sum())
        valid_count = len(df) - invalid_count

        if invalid_count > 0:
            sample_bad_indices = df.index[invalid_mask][:25]
            for idx in sample_bad_indices:
                errors.append({"row": int(idx) + 2, "column": "customer_code", "message": "Customer code cannot be empty"})

    elif entity_type == "suppliers":
        code_col = inv_mapping["supplier_code"]
        code_s = df[code_col].fillna("").astype(str).str.strip()
        invalid_mask = (code_s == "") | (code_s.str.lower().isin(["nan", "none"]))
        invalid_count = int(invalid_mask.sum())
        valid_count = len(df) - invalid_count

        if invalid_count > 0:
            sample_bad_indices = df.index[invalid_mask][:25]
            for idx in sample_bad_indices:
                errors.append({"row": int(idx) + 2, "column": "supplier_code", "message": "Supplier code cannot be empty"})

    elif entity_type == "inventory":
        sku_col = inv_mapping["sku"]
        wh_col = inv_mapping["warehouse_name"]
        qty_col = inv_mapping["available_quantity"]

        sku_s = df[sku_col].fillna("").astype(str).str.strip()
        sku_invalid = (sku_s == "") | (sku_s.str.lower().isin(["nan", "none"]))
        wh_s = df[wh_col].fillna("").astype(str).str.strip()
        wh_invalid = (wh_s == "") | (wh_s.str.lower().isin(["nan", "none"]))
        qty_num = pd.to_numeric(df[qty_col], errors="coerce")
        qty_invalid = qty_num.isna() | (qty_num < 0)

        invalid_mask = sku_invalid | wh_invalid | qty_invalid
        invalid_count = int(invalid_mask.sum())
        valid_count = len(df) - invalid_count

        if invalid_count > 0:
            sample_bad_indices = df.index[invalid_mask][:25]
            for idx in sample_bad_indices:
                row_num = int(idx) + 2
                if sku_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "sku", "message": "SKU cannot be empty"})
                if wh_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "warehouse_name", "message": "Warehouse name cannot be empty"})
                if qty_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "available_quantity", "message": "Available quantity must be non-negative"})

    elif entity_type == "purchase_orders":
        supp_col = inv_mapping["supplier_code"]
        sku_col = inv_mapping["sku"]
        qty_col = inv_mapping["quantity"]
        cost_col = inv_mapping["total_cost"]

        supp_s = df[supp_col].fillna("").astype(str).str.strip()
        supp_invalid = (supp_s == "") | (supp_s.str.lower().isin(["nan", "none"]))
        sku_s = df[sku_col].fillna("").astype(str).str.strip()
        sku_invalid = (sku_s == "") | (sku_s.str.lower().isin(["nan", "none"]))
        qty_num = pd.to_numeric(df[qty_col], errors="coerce")
        qty_invalid = qty_num.isna() | (qty_num <= 0)
        cost_num = pd.to_numeric(df[cost_col], errors="coerce")
        cost_invalid = cost_num.isna() | (cost_num < 0)

        invalid_mask = supp_invalid | sku_invalid | qty_invalid | cost_invalid
        invalid_count = int(invalid_mask.sum())
        valid_count = len(df) - invalid_count

        if invalid_count > 0:
            sample_bad_indices = df.index[invalid_mask][:25]
            for idx in sample_bad_indices:
                row_num = int(idx) + 2
                if supp_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "supplier_code", "message": "Supplier code cannot be empty"})
                if sku_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "sku", "message": "SKU cannot be empty"})
                if qty_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "quantity", "message": "Order quantity must be positive"})
                if cost_invalid.loc[idx]:
                    errors.append({"row": row_num, "column": "total_cost", "message": "Total cost must be non-negative"})

    else:
        valid_count = len(df)
        invalid_count = 0

    sample_preview = df.head(5).to_dict(orient="records")
    return DataValidationResponse(
        is_valid=(invalid_count == 0),
        detected_entity_type=entity_type,
        total_rows=len(df),
        valid_rows=valid_count,
        invalid_rows=invalid_count,
        column_mappings=mapping,
        errors=errors[:50],
        sample_preview=sample_preview,
    )


def execute_ingestion(
    db: Session,
    organization_id: str,
    df: pd.DataFrame,
    entity_type: str,
    mapping: Dict[str, str],
    job: DataImportJob,
) -> Tuple[int, int]:
    inv_mapping = {v: k for k, v in mapping.items()}
    records_processed = 0
    records_failed = 0

    try:
        if entity_type == "products":
            sku_col = inv_mapping["sku"]
            name_col = inv_mapping["name"]
            cat_col = inv_mapping.get("category")
            cost_col = inv_mapping["unit_cost"]
            price_col = inv_mapping["selling_price"]
            reorder_col = inv_mapping.get("reorder_threshold")
            safety_col = inv_mapping.get("safety_stock")

            existing_prods = {
                p.sku: p
                for p in db.query(Product).filter(Product.organization_id == organization_id).all()
            }
            new_objs = []
            for row in df.to_dict(orient="records"):
                try:
                    sku = str(row[sku_col]).strip()
                    name = str(row[name_col]).strip()
                    cat = str(row.get(cat_col, "General") if cat_col else "General").strip()
                    cost = float(row[cost_col])
                    price = float(row[price_col])
                    reorder = int(row.get(reorder_col, 50) if reorder_col else 50)
                    safety = int(row.get(safety_col, 20) if safety_col else 20)

                    if sku in existing_prods:
                        p = existing_prods[sku]
                        p.name = name
                        p.category = cat
                        p.unit_cost = cost
                        p.selling_price = price
                        p.reorder_threshold = reorder
                        p.safety_stock = safety
                    else:
                        new_objs.append(Product(
                            organization_id=organization_id,
                            sku=sku,
                            name=name,
                            category=cat,
                            unit_cost=cost,
                            selling_price=price,
                            reorder_threshold=reorder,
                            safety_stock=safety,
                        ))
                    records_processed += 1
                except Exception as err:
                    records_failed += 1
            if new_objs:
                db.bulk_save_objects(new_objs)
            db.commit()

        elif entity_type == "customers":
            code_col = inv_mapping["customer_code"]
            name_col = inv_mapping["name"]
            email_col = inv_mapping.get("email")
            phone_col = inv_mapping.get("phone")
            seg_col = inv_mapping.get("current_segment")

            existing_custs = {
                c.customer_code: c
                for c in db.query(Customer).filter(Customer.organization_id == organization_id).all()
            }
            new_objs = []
            for row in df.to_dict(orient="records"):
                try:
                    code = str(row[code_col]).strip()
                    name = str(row[name_col]).strip()
                    email = str(row.get(email_col, "")).strip() if email_col and row.get(email_col) else None
                    phone = str(row.get(phone_col, "")).strip() if phone_col and row.get(phone_col) else None
                    seg = str(row.get(seg_col, "New Customers") if seg_col else "New Customers").strip()

                    if code in existing_custs:
                        c = existing_custs[code]
                        c.name = name
                        if email:
                            c.email = email
                        if phone:
                            c.phone = phone
                        c.current_segment = seg
                    else:
                        new_objs.append(Customer(
                            organization_id=organization_id,
                            customer_code=code,
                            name=name,
                            email=email,
                            phone=phone,
                            current_segment=seg,
                        ))
                    records_processed += 1
                except Exception as err:
                    records_failed += 1
            if new_objs:
                db.bulk_save_objects(new_objs)
            db.commit()

        elif entity_type == "suppliers":
            code_col = inv_mapping["supplier_code"]
            name_col = inv_mapping["name"]
            email_col = inv_mapping.get("contact_email")
            rel_col = inv_mapping.get("reliability_score")
            lead_col = inv_mapping.get("average_lead_days")

            existing_supps = {
                s.supplier_code: s
                for s in db.query(Supplier).filter(Supplier.organization_id == organization_id).all()
            }
            new_objs = []
            for row in df.to_dict(orient="records"):
                try:
                    code = str(row[code_col]).strip()
                    name = str(row[name_col]).strip()
                    email = str(row.get(email_col, "")).strip() if email_col and row.get(email_col) else None
                    rel = float(row.get(rel_col, 100.0) if rel_col else 100.0)
                    lead = int(row.get(lead_col, 5) if lead_col else 5)

                    if code in existing_supps:
                        s = existing_supps[code]
                        s.name = name
                        if email:
                            s.contact_email = email
                        s.reliability_score = rel
                        s.average_lead_days = lead
                    else:
                        new_objs.append(Supplier(
                            organization_id=organization_id,
                            supplier_code=code,
                            name=name,
                            contact_email=email,
                            reliability_score=rel,
                            average_lead_days=lead,
                        ))
                    records_processed += 1
                except Exception as err:
                    records_failed += 1
            if new_objs:
                db.bulk_save_objects(new_objs)
            db.commit()

        elif entity_type == "sales":
            # 1. Preload product and customer lookups for fast in-memory indexing
            prod_lookup = {
                p.sku: p.id
                for p in db.query(Product.sku, Product.id).filter(Product.organization_id == organization_id).all()
            }
            cust_lookup = {
                c.customer_code: c.id
                for c in db.query(Customer.customer_code, Customer.id).filter(Customer.organization_id == organization_id).all()
            }

            # 2. Extract and vectorize columns
            sku_col = inv_mapping["sku"]
            qty_col = inv_mapping["quantity"]
            price_col = inv_mapping["unit_price"]
            date_col = inv_mapping["transaction_date"]
            cust_col = inv_mapping.get("customer_code")
            tot_col = inv_mapping.get("total_amount")

            sku_s = df[sku_col].fillna("").astype(str).str.strip()
            if cust_col and cust_col in df:
                cust_s = df[cust_col].fillna("GUEST").astype(str).str.strip().replace({"": "GUEST", "nan": "GUEST", "none": "GUEST", "NaN": "GUEST", "None": "GUEST"})
            else:
                cust_s = pd.Series(["GUEST"] * len(df), index=df.index)

            qty_s = pd.to_numeric(df[qty_col], errors="coerce").fillna(0).astype(int)
            price_s = pd.to_numeric(df[price_col], errors="coerce").fillna(0.0).astype(float)
            date_s = pd.to_datetime(df[date_col], errors="coerce")

            # 3. Create boolean mask for valid rows (skips cancellations with negative quantity, empty skus, bad dates)
            valid_mask = (qty_s > 0) & (price_s >= 0) & (sku_s != "") & (sku_s.str.lower() != "nan") & (sku_s.str.lower() != "none") & pd.notna(date_s)
            invalid_count = int((~valid_mask).sum())
            records_failed += invalid_count

            # 4. Total amount vectorized
            if tot_col and tot_col in df:
                tot_s = pd.to_numeric(df[tot_col], errors="coerce").fillna(qty_s * price_s).astype(float)
            else:
                tot_s = (qty_s * price_s).astype(float)

            # 5. Pre-insert missing customers and products in bulk for valid rows only
            v_skus = sku_s[valid_mask].values
            v_custs = cust_s[valid_mask].values
            v_qtys = qty_s[valid_mask].values
            v_prices = price_s[valid_mask].values
            v_dates = date_s[valid_mask].dt.to_pydatetime()
            v_totals = tot_s[valid_mask].values

            unique_custs = set(v_custs)
            missing_custs = [c for c in unique_custs if c not in cust_lookup]
            if missing_custs:
                new_custs = [
                    Customer(
                        organization_id=organization_id,
                        customer_code=c,
                        name="Guest Customer" if c == "GUEST" else f"Customer {c}",
                        current_segment="New Customers",
                    )
                    for c in missing_custs
                ]
                db.bulk_save_objects(new_custs)
                db.commit()
                cust_lookup.update({
                    c.customer_code: c.id
                    for c in db.query(Customer.customer_code, Customer.id).filter(
                        Customer.organization_id == organization_id,
                        Customer.customer_code.in_(missing_custs)
                    ).all()
                })

            if "GUEST" not in cust_lookup:
                guest = Customer(
                    organization_id=organization_id,
                    customer_code="GUEST",
                    name="Guest Customer",
                    current_segment="New Customers",
                )
                db.add(guest)
                db.commit()
                cust_lookup["GUEST"] = guest.id

            unique_skus = set(v_skus)
            missing_skus = [s for s in unique_skus if s not in prod_lookup]
            if missing_skus:
                new_prods = [
                    Product(
                        organization_id=organization_id,
                        sku=s,
                        name=f"Product {s}",
                        category="General",
                        unit_cost=5.0,
                        selling_price=10.0,
                        reorder_threshold=50,
                        safety_stock=20,
                    )
                    for s in missing_skus
                ]
                db.bulk_save_objects(new_prods)
                db.commit()
                prod_lookup.update({
                    p.sku: p.id
                    for p in db.query(Product.sku, Product.id).filter(
                        Product.organization_id == organization_id,
                        Product.sku.in_(missing_skus)
                    ).all()
                })

            # 6. Map foreign key IDs in memory
            guest_id = cust_lookup["GUEST"]
            cust_ids = [cust_lookup.get(c, guest_id) for c in v_custs]
            prod_ids = [prod_lookup.get(s) for s in v_skus]

            # 7. Insert in high-speed batches of 25,000 using bulk_insert_mappings with a single commit
            chunk_size = 25000
            total_items = len(v_skus)
            for start in range(0, total_items, chunk_size):
                end = min(start + chunk_size, total_items)
                batch_rows = [
                    {
                        "id": uuid.uuid4().hex,
                        "customer_id": cust_ids[i],
                        "product_id": prod_ids[i],
                        "quantity": int(v_qtys[i]),
                        "unit_price": float(v_prices[i]),
                        "total_amount": float(v_totals[i]),
                        "transaction_date": v_dates[i],
                    }
                    for i in range(start, end)
                    if prod_ids[i]
                ]
                skipped = (end - start) - len(batch_rows)
                if skipped > 0:
                    records_failed += skipped
                if batch_rows:
                    db.bulk_insert_mappings(Sales, batch_rows)
                    records_processed += len(batch_rows)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e

    return records_processed, records_failed

    return records_processed, records_failed

