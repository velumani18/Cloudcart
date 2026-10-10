"""Notification outbox audit repository layer."""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from backend.models import NotificationOutbox, Order, Customer, Product


class NotificationRepository:
    """Data access methods for Outbox Notifications and Admin Analytics."""

    @staticmethod
    def list_notifications(
        db: Session,
        order_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[NotificationOutbox]:
        query = db.query(NotificationOutbox)
        if order_id:
            query = query.filter(NotificationOutbox.order_id == order_id)
        if customer_id:
            query = query.filter(NotificationOutbox.customer_id == customer_id)
        if status and status.upper() != "ALL":
            query = query.filter(NotificationOutbox.status == status.upper())
        return query.order_by(desc(NotificationOutbox.created_at)).limit(limit).all()

    @staticmethod
    def get_admin_stats(db: Session) -> Dict[str, Any]:
        """Aggregate store metrics, revenues, and notification statuses."""
        total_orders = db.query(Order).count()
        revenue_val = db.query(func.sum(Order.total_amount)).filter(Order.status != "cancelled").scalar()
        total_revenue = float(revenue_val or 0.0)
        total_customers = db.query(Customer).count()
        total_products = db.query(Product).count()

        # Order status distribution
        order_status_counts_raw = (
            db.query(Order.status, func.count(Order.id))
            .group_by(Order.status)
            .all()
        )
        order_status_counts = {s: c for s, c in order_status_counts_raw}

        # Notification status distribution
        notif_status_counts_raw = (
            db.query(NotificationOutbox.status, func.count(NotificationOutbox.id))
            .group_by(NotificationOutbox.status)
            .all()
        )
        notif_status_counts = {s: c for s, c in notif_status_counts_raw}

        recent_orders = (
            db.query(Order)
            .order_by(desc(Order.created_at))
            .limit(10)
            .all()
        )

        recent_notifications = (
            db.query(NotificationOutbox)
            .order_by(desc(NotificationOutbox.created_at))
            .limit(15)
            .all()
        )

        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "total_customers": total_customers,
            "total_products": total_products,
            "order_status_counts": order_status_counts,
            "notification_status_counts": notif_status_counts,
            "recent_orders": recent_orders,
            "recent_notifications": recent_notifications,
        }
