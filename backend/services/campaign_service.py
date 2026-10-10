"""Service managing campaign execution with bounded concurrency and persistence."""
import asyncio
import io
import csv
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx
from backend.config import get_settings
from backend.models import (
    Campaign,
    NotificationSubmission,
    SubmissionStatus,
    CampaignStatus,
)
from backend.services.notification_service import send_to_aws_gateway
from backend.repositories.campaign_repository import CampaignRepository
from backend.database import SessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()


async def process_single_campaign_recipient(
    semaphore: asyncio.Semaphore,
    client: httpx.AsyncClient,
    campaign_id: str,
    recipient: str,
    subject: str,
    body: str,
    event_type: str,
) -> Dict[str, Any]:
    """Process a single recipient under concurrency semaphore and persist directly to DB."""
    async with semaphore:
        result = await send_to_aws_gateway(
            recipient=recipient,
            subject=subject,
            body=body,
            event_type=event_type,
            client=client,
        )

        # Persist submission result immediately in an isolated DB session
        db = SessionLocal()
        try:
            submission = CampaignRepository.create_submission(
                db=db,
                recipient=recipient,
                subject=subject,
                body=body,
                event_type=event_type,
                campaign_id=campaign_id,
                submission_status=result.submission_status.value,
                external_http_status=result.external_http_status,
                notification_id=result.notification_id,
                error_message=result.error_message,
            )
            CampaignRepository.update_campaign_tally(
                db=db,
                campaign_id=campaign_id,
                status_type=result.submission_status,
            )
            submission_id = submission.id
        except Exception as exc:
            logger.exception("Failed to persist submission for %s", recipient)
            submission_id = None
        finally:
            db.close()

        return {
            "id": submission_id,
            "campaign_id": campaign_id,
            "recipient": recipient,
            "submission_status": result.submission_status.value,
            "external_http_status": result.external_http_status,
            "notification_id": result.notification_id,
            "error_message": result.error_message,
            "message": result.message,
        }


async def run_campaign_processing(
    campaign_id: str,
    recipients: List[str],
    subject: str,
    body: str,
    event_type: str,
    concurrency_limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Execute campaign submissions across all recipients using bounded concurrency.
    Guarantees that individual recipient failures do not halt the rest of the campaign.
    """
    limit = concurrency_limit or settings.MAX_CONCURRENT_REQUESTS
    semaphore = asyncio.Semaphore(limit)

    # Update campaign status to PROCESSING
    db = SessionLocal()
    try:
        CampaignRepository.update_campaign_status(db, campaign_id, CampaignStatus.PROCESSING.value)
    finally:
        db.close()

    limits = httpx.Limits(max_keepalive_connections=limit, max_connections=limit * 2)
    timeout = httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS)

    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        tasks = [
            process_single_campaign_recipient(
                semaphore=semaphore,
                client=client,
                campaign_id=campaign_id,
                recipient=recipient,
                subject=subject,
                body=body,
                event_type=event_type,
            )
            for recipient in recipients
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    # Finalize campaign processing status and counts
    db = SessionLocal()
    try:
        campaign = CampaignRepository.get_campaign(db, campaign_id)
        if campaign:
            from sqlalchemy import func
            status_counts = (
                db.query(NotificationSubmission.submission_status, func.count(NotificationSubmission.id))
                .filter(NotificationSubmission.campaign_id == campaign_id)
                .group_by(NotificationSubmission.submission_status)
                .all()
            )
            counts = {s: c for s, c in status_counts}
            campaign.accepted_count = counts.get(SubmissionStatus.ACCEPTED.value, 0)
            campaign.rejected_count = counts.get(SubmissionStatus.REJECTED.value, 0)
            campaign.failed_count = counts.get(SubmissionStatus.FAILED.value, 0)
            campaign.uncertain_count = counts.get(SubmissionStatus.UNCERTAIN.value, 0)

            if campaign.accepted_count == campaign.total_recipients and campaign.total_recipients > 0:
                final_status = CampaignStatus.COMPLETED.value
            elif campaign.accepted_count > 0:
                final_status = CampaignStatus.PARTIALLY_FAILED.value
            elif campaign.total_recipients > 0:
                final_status = CampaignStatus.FAILED.value
            else:
                final_status = CampaignStatus.COMPLETED.value

            campaign.processing_status = final_status
            db.commit()
    finally:
        db.close()

    return results


def generate_campaign_csv_report(campaign: Campaign, submissions: List[NotificationSubmission]) -> str:
    """Generate a sanitized CSV string detailing recipient outcomes for export."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Recipient Email",
        "Submission Status",
        "HTTP Status Code",
        "Notification ID",
        "Error / Note",
        "Submission Timestamp (UTC)",
    ])

    for sub in submissions:
        writer.writerow([
            sub.recipient,
            sub.submission_status,
            sub.external_http_status if sub.external_http_status is not None else "",
            sub.notification_id or "",
            sub.error_message or "",
            sub.created_at.strftime("%Y-%m-%d %H:%M:%S") if sub.created_at else "",
        ])

    return output.getvalue()
