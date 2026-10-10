"""Admin analytics and oversight router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    AdminDashboardStats,
    NotificationOutboxResponse,
)
from backend.repositories.notification_repository import NotificationRepository
from backend.routers.orders import serialize_order

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Portal"])


@router.get(
    "/stats",
    response_model=AdminDashboardStats,
    summary="Get aggregated store metrics & notification statistics",
)
def get_admin_stats(db: Session = Depends(get_db)):
    """Fetch overview metrics for admin dashboard."""
    stats = NotificationRepository.get_admin_stats(db)

    recent_orders = [serialize_order(o) for o in stats["recent_orders"]]
    recent_notifications = [
        NotificationOutboxResponse(
            id=r.id,
            order_id=r.order_id,
            order_number=r.order.order_number if r.order else None,
            customer_id=r.customer_id,
            event_type=r.event_type,
            recipient=r.recipient,
            subject=r.subject,
            body=r.body,
            status=r.status,
            external_http_status=r.external_http_status,
            notification_id=r.notification_id,
            error_message=r.error_message,
            attempts=r.attempts,
            created_at=r.created_at,
            processed_at=r.processed_at,
        )
        for r in stats["recent_notifications"]
    ]

    return AdminDashboardStats(
        total_orders=stats["total_orders"],
        total_revenue=stats["total_revenue"],
        total_customers=stats["total_customers"],
        total_products=stats["total_products"],
        order_status_counts=stats["order_status_counts"],
        notification_status_counts=stats["notification_status_counts"],
        recent_orders=recent_orders,
        recent_notifications=recent_notifications,
    )
