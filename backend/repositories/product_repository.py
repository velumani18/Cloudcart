"""Product catalog repository layer."""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.models import Product


class ProductRepository:
    """Data access methods for Products."""

    @staticmethod
    def list_products(
        db: Session,
        category: Optional[str] = None,
        search: Optional[str] = None,
        active_only: bool = True,
    ) -> List[Product]:
        query = db.query(Product)
        if active_only:
            query = query.filter(Product.is_active.is_(True))
        if category and category.lower() != "all":
            query = query.filter(Product.category.ilike(category))
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                    Product.category.ilike(f"%{search}%"),
                )
            )
        return query.order_by(Product.name).all()

    @staticmethod
    def get_product(db: Session, product_id: str) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id).first()

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
        product = Product(
            name=name,
            description=description,
            category=category,
            price=price,
            stock_quantity=stock_quantity,
            image_url=image_url,
            is_active=is_active,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def update_product(
        db: Session,
        product_id: str,
        **kwargs,
    ) -> Optional[Product]:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None
        for key, val in kwargs.items():
            if val is not None and hasattr(product, key):
                setattr(product, key, val)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def list_categories(db: Session) -> List[str]:
        results = db.query(Product.category).distinct().filter(Product.is_active.is_(True)).all()
        return [r[0] for r in results if r[0]]
