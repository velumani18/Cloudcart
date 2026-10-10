"""Order and order history repository layer."""
import random
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models import Order, OrderItem, OrderStatusHistory, OrderStatus, utc_now


class OrderRepository:
    """Data access methods for Orders."""

    @staticmethod
    def generate_order_number(db: Session) -> str:
        """Generate a sequential/unique e-commerce order code."""
        count = db.query(Order).count()
        rnd = random.randint(100, 999)
        return f"ORD-{1000 + count + 1}-{rnd}"

    @staticmethod
    def get_order(db: Session, order_id: str) -> Optional[Order]:
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
        return db.query(Order).filter(Order.order_number == order_number.strip().upper()).first()

    @staticmethod
    def list_orders(
        db: Session,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Order]:
        query = db.query(Order)
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        if status and status.lower() != "all":
            query = query.filter(Order.status == status.lower())
        return query.order_by(desc(Order.created_at)).limit(limit).all()

    @staticmethod
    def add_status_history(
        db: Session,
        order_id: str,
        to_status: str,
        from_status: Optional[str] = None,
        notes: Optional[str] = None,
        changed_by: str = "system",
    ) -> OrderStatusHistory:
        history = OrderStatusHistory(
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
            notes=notes,
            changed_by=changed_by,
        )
        db.add(history)
        return history
