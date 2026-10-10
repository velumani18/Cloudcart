"""Transactional Outbox service for durable, event-driven notification dispatching."""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
import httpx
from backend.database import SessionLocal
from backend.models import NotificationOutbox, NotificationEventStatus, utc_now
from backend.services.notification_service import send_to_aws_gateway
from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def enqueue_outbox_event(
    db: Session,
    recipient: str,
    event_type: str,
    subject: str,
    body: str,
    order_id: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> NotificationOutbox:
    """
    Persist an event to the transactional outbox table in the SAME database transaction
    as the business operation. Guarantees zero lost notification events.
    """
    import uuid
    event = NotificationOutbox(
        id=str(uuid.uuid4()),
        order_id=order_id,
        customer_id=customer_id,
        event_type=event_type,
        recipient=recipient,
        subject=subject,
        body=body,
        status=NotificationEventStatus.PENDING.value,
        attempts=0,
    )
    db.add(event)
    db.flush()
    return event


async def dispatch_single_outbox_event(event_id: str, client: Optional[httpx.AsyncClient] = None) -> None:
    """Read a pending outbox event and deliver it to the AWS API Gateway."""
    db = SessionLocal()
    event: Optional[NotificationOutbox] = None
    try:
        event = db.query(NotificationOutbox).filter(NotificationOutbox.id == event_id).first()
        if not event:
            logger.warning("Outbox event %s not found for dispatch", event_id)
            return

        event.attempts += 1
        recipient = event.recipient
        subject = event.subject
        body = event.body
        event_type = event.event_type
    finally:
        db.close()

    # Dispatch to AWS Gateway
    result = await send_to_aws_gateway(
        recipient=recipient,
        subject=subject,
        body=body,
        event_type=event_type,
        client=client,
    )

    # Persist the final outcome
    db = SessionLocal()
    try:
        event = db.query(NotificationOutbox).filter(NotificationOutbox.id == event_id).first()
        if event:
            event.status = result.status.value
            event.external_http_status = result.external_http_status
            event.notification_id = result.notification_id
            event.error_message = result.error_message
            event.processed_at = utc_now()
            db.commit()
            logger.info(
                "Outbox event %s (%s) processed with status %s (HTTP %s, id=%s)",
                event_id,
                event_type,
                result.status.value,
                result.external_http_status,
                result.notification_id,
            )
    except Exception as exc:
        logger.exception("Failed to update outbox event %s: %s", event_id, exc)
    finally:
        db.close()


async def process_all_pending_outbox(concurrency_limit: int = 5) -> int:
    """Process all pending outbox records with bounded concurrency."""
    db = SessionLocal()
    pending_ids: List[str] = []
    try:
        events = (
            db.query(NotificationOutbox.id)
            .filter(NotificationOutbox.status == NotificationEventStatus.PENDING.value)
            .order_by(NotificationOutbox.created_at)
            .limit(50)
            .all()
        )
        pending_ids = [e[0] for e in events]
    finally:
        db.close()

    if not pending_ids:
        return 0

    semaphore = asyncio.Semaphore(concurrency_limit)
    async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
        async def worker(eid: str):
            async with semaphore:
                await dispatch_single_outbox_event(eid, client=client)

        await asyncio.gather(*[worker(eid) for eid in pending_ids], return_exceptions=True)

    return len(pending_ids)
