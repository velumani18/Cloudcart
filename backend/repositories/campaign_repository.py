"""Data repository layer for campaign and submission database operations."""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from backend.models import Campaign, NotificationSubmission, CampaignStatus, SubmissionStatus, utc_now


class CampaignRepository:
    """Repository handling all database queries and transactions."""

    @staticmethod
    def create_campaign(
        db: Session,
        campaign_name: str,
        subject: str,
        body: str,
        event_type: str,
        total_recipients: int,
    ) -> Campaign:
        campaign = Campaign(
            campaign_name=campaign_name,
            subject=subject,
            body=body,
            event_type=event_type,
            total_recipients=total_recipients,
            processing_status=CampaignStatus.PENDING.value,
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)
        return campaign

    @staticmethod
    def get_campaign(db: Session, campaign_id: str) -> Optional[Campaign]:
        return db.query(Campaign).filter(Campaign.id == campaign_id).first()

    @staticmethod
    def list_campaigns(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Campaign]:
        query = db.query(Campaign)
        if status and status.upper() != "ALL":
            query = query.filter(Campaign.processing_status == status.upper())
        if search:
            query = query.filter(
                or_(
                    Campaign.campaign_name.ilike(f"%{search}%"),
                    Campaign.subject.ilike(f"%{search}%"),
                    Campaign.event_type.ilike(f"%{search}%"),
                )
            )
        return query.order_by(desc(Campaign.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def count_campaigns(db: Session) -> int:
        return db.query(Campaign).count()

    @staticmethod
    def update_campaign_status(
        db: Session,
        campaign_id: str,
        status: str,
    ) -> Optional[Campaign]:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.processing_status = status
            db.commit()
            db.refresh(campaign)
        return campaign

    @staticmethod
    def update_campaign_tally(
        db: Session,
        campaign_id: str,
        status_type: SubmissionStatus,
    ) -> None:
        """Increment count for a specific status immediately."""
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return

        if status_type == SubmissionStatus.ACCEPTED:
            campaign.accepted_count += 1
        elif status_type == SubmissionStatus.REJECTED:
            campaign.rejected_count += 1
        elif status_type == SubmissionStatus.FAILED:
            campaign.failed_count += 1
        elif status_type == SubmissionStatus.UNCERTAIN:
            campaign.uncertain_count += 1

        db.commit()

    @staticmethod
    def create_submission(
        db: Session,
        recipient: str,
        subject: str,
        event_type: str,
        body: Optional[str] = None,
        campaign_id: Optional[str] = None,
        submission_status: str = SubmissionStatus.PENDING.value,
        external_http_status: Optional[int] = None,
        notification_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> NotificationSubmission:
        submission = NotificationSubmission(
            campaign_id=campaign_id,
            recipient=recipient,
            subject=subject,
            body=body,
            event_type=event_type,
            submission_status=submission_status,
            external_http_status=external_http_status,
            notification_id=notification_id,
            error_message=error_message,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    @staticmethod
    def update_submission(
        db: Session,
        submission_id: str,
        submission_status: str,
        external_http_status: Optional[int] = None,
        notification_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[NotificationSubmission]:
        submission = db.query(NotificationSubmission).filter(NotificationSubmission.id == submission_id).first()
        if submission:
            submission.submission_status = submission_status
            submission.external_http_status = external_http_status
            submission.notification_id = notification_id
            submission.error_message = error_message
            submission.updated_at = utc_now()
            db.commit()
            db.refresh(submission)
        return submission

    @staticmethod
    def get_campaign_submissions(
        db: Session,
        campaign_id: str,
    ) -> List[NotificationSubmission]:
        return (
            db.query(NotificationSubmission)
            .filter(NotificationSubmission.campaign_id == campaign_id)
            .order_by(NotificationSubmission.created_at)
            .all()
        )

    @staticmethod
    def get_recent_submissions(db: Session, limit: int = 10) -> List[NotificationSubmission]:
        return (
            db.query(NotificationSubmission)
            .order_by(desc(NotificationSubmission.created_at))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """Compute aggregate metrics purely from actual database records."""
        total_campaigns = db.query(Campaign).count()
        total_recipients = db.query(NotificationSubmission).count()

        status_counts = (
            db.query(NotificationSubmission.submission_status, func.count(NotificationSubmission.id))
            .group_by(NotificationSubmission.submission_status)
            .all()
        )
        counts_dict = {status: count for status, count in status_counts}

        total_accepted = counts_dict.get(SubmissionStatus.ACCEPTED.value, 0)
        total_rejected = counts_dict.get(SubmissionStatus.REJECTED.value, 0)
        total_failed = counts_dict.get(SubmissionStatus.FAILED.value, 0)
        total_uncertain = counts_dict.get(SubmissionStatus.UNCERTAIN.value, 0)

        recent_campaigns = (
            db.query(Campaign)
            .order_by(desc(Campaign.created_at))
            .limit(5)
            .all()
        )

        recent_submissions = (
            db.query(NotificationSubmission)
            .order_by(desc(NotificationSubmission.created_at))
            .limit(10)
            .all()
        )

        return {
            "total_campaigns": total_campaigns,
            "total_recipients": total_recipients,
            "total_accepted": total_accepted,
            "total_rejected": total_rejected,
            "total_failed": total_failed,
            "total_uncertain": total_uncertain,
            "recent_campaigns": recent_campaigns,
            "recent_submissions": recent_submissions,
        }
