"""Product catalog router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
)
from backend.services.product_service import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List available products",
)
def list_products(
    category: Optional[str] = Query(None, description="Category filter"),
    search: Optional[str] = Query(None, description="Search keyword"),
    include_inactive: bool = Query(False, description="Whether to include inactive products"),
    db: Session = Depends(get_db),
):
    """Browse catalog with optional search and category filters."""
    return ProductService.list_products(
        db,
        category=category,
        search=search,
        active_only=not include_inactive,
    )


@router.get(
    "/categories",
    response_model=List[str],
    summary="List distinct product categories",
)
def get_categories(db: Session = Depends(get_db)):
    """Return distinct active categories."""
    return ProductService.get_categories(db)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product details",
)
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = ProductService.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin)",
)
def create_product(payload: ProductCreateRequest, db: Session = Depends(get_db)):
    """Add a new product to the catalog."""
    return ProductService.create_product(
        db=db,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        image_url=payload.image_url,
        is_active=payload.is_active,
    )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product details or inventory (Admin)",
)
def update_product(
    product_id: str,
    payload: ProductUpdateRequest,
    db: Session = Depends(get_db),
):
    """Modify product information, update stock, or toggle active status."""
    updated = ProductService.update_product(
        db=db,
        product_id=product_id,
        **payload.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return updated
