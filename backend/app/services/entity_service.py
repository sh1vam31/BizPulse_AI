from typing import List, Optional
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from app.models.entities import Customer, Product, Supplier, Warehouse
from app.models.revenue import CustomerFeatures
from app.models.supply_chain import Inventory, PurchaseOrder, Sales
from app.schemas.entities import (
    CustomerDetailResponse,
    CustomerResponse,
    ProductDetailResponse,
    ProductInventoryItem,
    ProductResponse,
    SupplierDetailResponse,
    SupplierResponse,
    WarehouseResponse,
)


def get_products_summary(
    db: Session,
    organization_id: str,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ProductResponse]:
    query = db.query(Product).filter(Product.organization_id == organization_id)

    if category:
        query = query.filter(Product.category == category)
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) | (Product.sku.ilike(f"%{search}%"))
        )

    products = query.offset(offset).limit(limit).all()
    results = []

    for p in products:
        sales_agg = (
            db.query(
                func.coalesce(func.sum(Sales.quantity), 0).label("total_qty"),
                func.coalesce(func.sum(Sales.total_amount), 0.0).label("total_rev"),
            )
            .filter(Sales.product_id == p.id)
            .first()
        )

        stock_agg = (
            db.query(func.coalesce(func.sum(Inventory.available_quantity), 0))
            .filter(Inventory.product_id == p.id)
            .scalar()
        )

        results.append(
            ProductResponse(
                id=p.id,
                organization_id=p.organization_id,
                sku=p.sku,
                name=p.name,
                category=p.category,
                unit_cost=float(p.unit_cost),
                selling_price=float(p.selling_price),
                reorder_threshold=p.reorder_threshold,
                safety_stock=p.safety_stock,
                created_at=p.created_at,
                total_sales_quantity=int(sales_agg.total_qty or 0),
                total_revenue=float(sales_agg.total_rev or 0.0),
                available_stock=int(stock_agg or 0),
            )
        )

    return results


def get_product_detail(db: Session, organization_id: str, product_id: str) -> Optional[ProductDetailResponse]:
    p = db.query(Product).filter(
        Product.id == product_id, Product.organization_id == organization_id
    ).first()
    if not p:
        return None

    sales_agg = (
        db.query(
            func.coalesce(func.sum(Sales.quantity), 0).label("total_qty"),
            func.coalesce(func.sum(Sales.total_amount), 0.0).label("total_rev"),
            func.count(Sales.id).label("sales_count"),
        )
        .filter(Sales.product_id == p.id)
        .first()
    )

    stock_agg = (
        db.query(func.coalesce(func.sum(Inventory.available_quantity), 0))
        .filter(Inventory.product_id == p.id)
        .scalar()
    )

    inventory_items = (
        db.query(Inventory, Warehouse.name)
        .join(Warehouse, Inventory.warehouse_id == Warehouse.id)
        .filter(Inventory.product_id == p.id)
        .all()
    )

    inv_breakdown = [
        ProductInventoryItem(
            warehouse_id=inv.warehouse_id,
            warehouse_name=w_name,
            available_quantity=inv.available_quantity,
            reserved_quantity=inv.reserved_quantity,
        )
        for inv, w_name in inventory_items
    ]

    outstanding_orders = (
        db.query(func.count(PurchaseOrder.id))
        .filter(PurchaseOrder.product_id == p.id, PurchaseOrder.status.in_(["PLACED", "SHIPPED"]))
        .scalar()
    )

    return ProductDetailResponse(
        id=p.id,
        organization_id=p.organization_id,
        sku=p.sku,
        name=p.name,
        category=p.category,
        unit_cost=float(p.unit_cost),
        selling_price=float(p.selling_price),
        reorder_threshold=p.reorder_threshold,
        safety_stock=p.safety_stock,
        created_at=p.created_at,
        total_sales_quantity=int(sales_agg.total_qty or 0),
        total_revenue=float(sales_agg.total_rev or 0.0),
        available_stock=int(stock_agg or 0),
        inventory_by_warehouse=inv_breakdown,
        recent_sales_count=int(sales_agg.sales_count or 0),
        outstanding_orders_count=int(outstanding_orders or 0),
    )


def get_customers_summary(
    db: Session,
    organization_id: str,
    segment: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[CustomerResponse]:
    query = db.query(Customer).filter(Customer.organization_id == organization_id)

    if segment:
        query = query.filter(Customer.current_segment == segment)
    if search:
        query = query.filter(
            (Customer.name.ilike(f"%{search}%")) | (Customer.customer_code.ilike(f"%{search}%"))
        )

    customers = query.offset(offset).limit(limit).all()
    results = []

    for c in customers:
        sales_agg = (
            db.query(
                func.coalesce(func.sum(Sales.total_amount), 0.0).label("total_spend"),
                func.count(Sales.id).label("total_orders"),
            )
            .filter(Sales.customer_id == c.id)
            .first()
        )

        results.append(
            CustomerResponse(
                id=c.id,
                organization_id=c.organization_id,
                customer_code=c.customer_code,
                name=c.name,
                email=c.email,
                phone=c.phone,
                current_segment=c.current_segment,
                created_at=c.created_at,
                total_spend=float(sales_agg.total_spend or 0.0),
                total_orders=int(sales_agg.total_orders or 0),
            )
        )

    return results


def get_customer_detail(db: Session, organization_id: str, customer_id: str) -> Optional[CustomerDetailResponse]:
    c = db.query(Customer).filter(
        Customer.id == customer_id, Customer.organization_id == organization_id
    ).first()
    if not c:
        return None

    sales_agg = (
        db.query(
            func.coalesce(func.sum(Sales.total_amount), 0.0).label("total_spend"),
            func.count(Sales.id).label("total_orders"),
        )
        .filter(Sales.customer_id == c.id)
        .first()
    )

    transactions = (
        db.query(Sales, Product.name, Product.sku)
        .join(Product, Sales.product_id == Product.id)
        .filter(Sales.customer_id == c.id)
        .order_by(Sales.transaction_date.desc())
        .limit(20)
        .all()
    )

    recent_txs = [
        {
            "id": s.id,
            "sku": sku,
            "product_name": p_name,
            "quantity": s.quantity,
            "unit_price": float(s.unit_price),
            "total_amount": float(s.total_amount),
            "transaction_date": s.transaction_date.isoformat(),
        }
        for s, p_name, sku in transactions
    ]

    features = db.query(CustomerFeatures).filter(CustomerFeatures.customer_id == c.id).first()

    return CustomerDetailResponse(
        id=c.id,
        organization_id=c.organization_id,
        customer_code=c.customer_code,
        name=c.name,
        email=c.email,
        phone=c.phone,
        current_segment=c.current_segment,
        created_at=c.created_at,
        total_spend=float(sales_agg.total_spend or 0.0),
        total_orders=int(sales_agg.total_orders or 0),
        recent_transactions=recent_txs,
        recency_days=features.recency_days if features else None,
        frequency=features.frequency if features else None,
        monetary_value=float(features.monetary_value) if features else None,
    )


def get_suppliers_summary(
    db: Session,
    organization_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[SupplierResponse]:
    suppliers = (
        db.query(Supplier)
        .filter(Supplier.organization_id == organization_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    results = []

    for s in suppliers:
        po_agg = (
            db.query(
                func.count(PurchaseOrder.id).label("total_orders"),
                func.sum(
                    case(
                        (PurchaseOrder.actual_delivery > PurchaseOrder.expected_delivery, 1),
                        else_=0,
                    )
                ).label("delayed_orders"),
            )
            .filter(PurchaseOrder.supplier_id == s.id)
            .first()
        )

        total_orders = int(po_agg.total_orders or 0)
        delayed_orders = int(po_agg.delayed_orders or 0)
        on_time_rate = (
            round(((total_orders - delayed_orders) / total_orders) * 100.0, 1)
            if total_orders > 0
            else float(s.reliability_score)
        )

        results.append(
            SupplierResponse(
                id=s.id,
                organization_id=s.organization_id,
                supplier_code=s.supplier_code,
                name=s.name,
                contact_email=s.contact_email,
                reliability_score=float(s.reliability_score),
                average_lead_days=s.average_lead_days,
                created_at=s.created_at,
                total_orders=total_orders,
                delayed_orders=delayed_orders,
                on_time_delivery_rate=on_time_rate,
            )
        )

    return results


def get_supplier_detail(db: Session, organization_id: str, supplier_id: str) -> Optional[SupplierDetailResponse]:
    s = db.query(Supplier).filter(
        Supplier.id == supplier_id, Supplier.organization_id == organization_id
    ).first()
    if not s:
        return None

    orders = (
        db.query(PurchaseOrder, Product.name, Product.sku)
        .join(Product, PurchaseOrder.product_id == Product.id)
        .filter(PurchaseOrder.supplier_id == s.id)
        .order_by(PurchaseOrder.order_date.desc())
        .limit(20)
        .all()
    )

    po_records = [
        {
            "id": po.id,
            "sku": sku,
            "product_name": p_name,
            "quantity": po.quantity,
            "total_cost": float(po.total_cost),
            "order_date": po.order_date.isoformat(),
            "expected_delivery": po.expected_delivery.isoformat(),
            "actual_delivery": po.actual_delivery.isoformat() if po.actual_delivery else None,
            "status": po.status,
        }
        for po, p_name, sku in orders
    ]

    total_orders = len(orders)
    delayed_orders = sum(
        1 for po, _, _ in orders
        if po.actual_delivery and po.actual_delivery > po.expected_delivery
    )
    on_time_rate = (
        round(((total_orders - delayed_orders) / total_orders) * 100.0, 1)
        if total_orders > 0
        else float(s.reliability_score)
    )

    return SupplierDetailResponse(
        id=s.id,
        organization_id=s.organization_id,
        supplier_code=s.supplier_code,
        name=s.name,
        contact_email=s.contact_email,
        reliability_score=float(s.reliability_score),
        average_lead_days=s.average_lead_days,
        created_at=s.created_at,
        total_orders=total_orders,
        delayed_orders=delayed_orders,
        on_time_delivery_rate=on_time_rate,
        recent_purchase_orders=po_records,
    )


def get_warehouses_summary(db: Session, organization_id: str) -> List[WarehouseResponse]:
    warehouses = db.query(Warehouse).filter(Warehouse.organization_id == organization_id).all()
    results = []

    for w in warehouses:
        inv_agg = (
            db.query(
                func.count(func.distinct(Inventory.product_id)).label("products_stored"),
                func.coalesce(func.sum(Inventory.available_quantity), 0).label("total_qty"),
            )
            .filter(Inventory.warehouse_id == w.id)
            .first()
        )

        results.append(
            WarehouseResponse(
                id=w.id,
                organization_id=w.organization_id,
                name=w.name,
                location=w.location,
                created_at=w.created_at,
                total_products_stored=int(inv_agg.products_stored or 0),
                total_quantity=int(inv_agg.total_qty or 0),
            )
        )

    return results
