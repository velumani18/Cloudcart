"""Notification outbox audit and manual trigger router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import NotificationOutboxResponse
from backend.repositories.notification_repository import NotificationRepository
from backend.services.outbox_service import process_all_pending_outbox

router = APIRouter(prefix="/api/v1/notifications", tags=["Notification Outbox Audit"])


@router.get(
    "/audit",
    response_model=List[NotificationOutboxResponse],
    summary="List event-driven notifications from outbox",
)
def list_outbox_audit(
    order_id: Optional[str] = Query(None, description="Filter by Order ID"),
    customer_id: Optional[str] = Query(None, description="Filter by Customer ID"),
    status: Optional[str] = Query(None, description="Filter by outbox status (PENDING, ACCEPTED, FAILED)"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve full audit log of event-driven notification attempts and AWS responses."""
    records = NotificationRepository.list_notifications(
        db, order_id=order_id, customer_id=customer_id, status=status, limit=limit
    )

    results = []
    for r in records:
        results.append(
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
        )
    return results


@router.post(
    "/process-pending",
    summary="Process pending outbox notifications (Worker Sweep)",
)
async def process_pending():
    """Trigger an outbox worker sweep to dispatch any pending notifications to AWS."""
    processed_count = await process_all_pending_outbox()
    return {"message": "Outbox sweep completed", "processed_count": processed_count}
