"""Product catalog business service."""
from typing import List, Optional
from sqlalchemy.orm import Session
from backend.models import Product
from backend.repositories.product_repository import ProductRepository


class ProductService:
    """Business operations for product catalog."""

    @staticmethod
    def list_products(
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Product]:
        return ProductRepository.list_products(db, category=category, search=search, active_only=active_only)

    @staticmethod
    def get_product(db: Session, product_id: str) -> Optional[Product]:
        return ProductRepository.get_product(db, product_id)

    @staticmethod
    def create_product(
        db: Session,
        name: str,
        description: str,
        category: str,
        price: float,
        stock_quantity: int,
        image_url: Optional[str] = None,
        is_active: bool = True,
    ) -> Product:
        return ProductRepository.create_product(
            db=db,
            name=name,
            description=description,
            category=category,
            price=price,
            stock_quantity=stock_quantity,
            image_url=image_url,
            is_active=is_active,
        )

    @staticmethod
    def update_product(db: Session, product_id: str, **kwargs) -> Optional[Product]:
        return ProductRepository.update_product(db, product_id, **kwargs)

    @staticmethod
    def get_categories(db: Session) -> List[str]:
        return ProductRepository.list_categories(db)
