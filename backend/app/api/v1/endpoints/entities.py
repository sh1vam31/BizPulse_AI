from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_active_user, get_db
from app.models.auth import User
from app.schemas.entities import (
    CustomerDetailResponse,
    CustomerResponse,
    ProductDetailResponse,
    ProductResponse,
    SupplierDetailResponse,
    SupplierResponse,
    WarehouseResponse,
)
from app.services.entity_service import (
    get_customer_detail,
    get_customers_summary,
    get_product_detail,
    get_products_summary,
    get_supplier_detail,
    get_suppliers_summary,
    get_warehouses_summary,
)

router = APIRouter()


@router.get("/products", response_model=List[ProductResponse])
def list_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_products_summary(
        db=db,
        organization_id=current_user.organization_id,
        category=category,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    product = get_product_detail(
        db=db, organization_id=current_user.organization_id, product_id=product_id
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )
    return product


@router.get("/customers", response_model=List[CustomerResponse])
def list_customers(
    segment: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_customers_summary(
        db=db,
        organization_id=current_user.organization_id,
        segment=segment,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    customer = get_customer_detail(
        db=db, organization_id=current_user.organization_id, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found",
        )
    return customer


@router.get("/suppliers", response_model=List[SupplierResponse])
def list_suppliers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_suppliers_summary(
        db=db,
        organization_id=current_user.organization_id,
        limit=limit,
        offset=offset,
    )


@router.get("/suppliers/{supplier_id}", response_model=SupplierDetailResponse)
def get_supplier(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    supplier = get_supplier_detail(
        db=db, organization_id=current_user.organization_id, supplier_id=supplier_id
    )
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found",
        )
    return supplier


@router.get("/warehouses", response_model=List[WarehouseResponse])
def list_warehouses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return get_warehouses_summary(
        db=db, organization_id=current_user.organization_id
    )

