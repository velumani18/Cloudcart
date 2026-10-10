"""Router for bulk campaigns and analytics."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Response, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import (
    CampaignCreateRequest,
    CampaignSummaryResponse,
    CampaignDetailResponse,
    RecipientResultResponse,
    DashboardStatsResponse,
    CSVParseSummary,
)
from backend.repositories.campaign_repository import CampaignRepository
from backend.services.campaign_service import run_campaign_processing, generate_campaign_csv_report
from backend.services.csv_service import parse_and_validate_csv
from backend.config import get_settings

router = APIRouter(prefix="/api/v1/campaigns", tags=["Campaigns"])
settings = get_settings()


@router.post(
    "",
    response_model=CampaignDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and process a bulk email campaign",
)
async def create_campaign(
    payload: CampaignCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Create a bulk campaign and process submissions to the external AWS endpoint
    using bounded concurrency. Returns campaign details and recipient results.
    """
    # Deduplicate recipients if requested
    recipients = payload.recipients
    if payload.deduplicate:
        # Maintain order while deduplicating
        seen = set()
        deduped = []
        for r in recipients:
            r_str = str(r).lower()
            if r_str not in seen:
                seen.add(r_str)
                deduped.append(r)
        recipients = deduped

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one valid recipient is required to launch a campaign.",
        )

    if len(recipients) > settings.MAX_CAMPAIGN_RECIPIENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campaign exceeds maximum recipient limit of {settings.MAX_CAMPAIGN_RECIPIENTS}.",
        )

    # 1. Create the campaign entry in the database
    campaign = CampaignRepository.create_campaign(
        db=db,
        campaign_name=payload.campaign_name,
        subject=payload.subject,
        body=payload.body,
        event_type=payload.event_type,
        total_recipients=len(recipients),
    )

    # 2. Run bounded concurrency processing
    await run_campaign_processing(
        campaign_id=campaign.id,
        recipients=[str(r) for r in recipients],
        subject=payload.subject,
        body=payload.body,
        event_type=payload.event_type,
        concurrency_limit=settings.MAX_CONCURRENT_REQUESTS,
    )

    # 3. Reload campaign and its submissions
    db.expire_all()
    refreshed_campaign = CampaignRepository.get_campaign(db, campaign.id)
    submissions = CampaignRepository.get_campaign_submissions(db, campaign.id)

    return CampaignDetailResponse(
        id=refreshed_campaign.id,
        campaign_name=refreshed_campaign.campaign_name,
        subject=refreshed_campaign.subject,
        body=refreshed_campaign.body,
        event_type=refreshed_campaign.event_type,
        created_at=refreshed_campaign.created_at,
        total_recipients=refreshed_campaign.total_recipients,
        accepted_count=refreshed_campaign.accepted_count,
        rejected_count=refreshed_campaign.rejected_count,
        failed_count=refreshed_campaign.failed_count,
        uncertain_count=refreshed_campaign.uncertain_count,
        processing_status=refreshed_campaign.processing_status,
        results=[RecipientResultResponse.model_validate(sub) for sub in submissions],
    )


@router.get(
    "",
    response_model=List[CampaignSummaryResponse],
    summary="List saved campaigns",
)
def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status (e.g. COMPLETED, FAILED)"),
    search: Optional[str] = Query(None, description="Search by name, subject, or event_type"),
    db: Session = Depends(get_db),
):
    """Retrieve saved campaigns with pagination, status filtering, and search."""
    campaigns = CampaignRepository.list_campaigns(
        db=db, skip=skip, limit=limit, status=status, search=search
    )
    return [CampaignSummaryResponse.model_validate(c) for c in campaigns]


@router.get(
    "/stats/dashboard",
    response_model=DashboardStatsResponse,
    summary="Get aggregated dashboard metrics",
)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Return dashboard metrics and activity calculated directly from database records."""
    stats = CampaignRepository.get_dashboard_stats(db)
    return DashboardStatsResponse(
        total_campaigns=stats["total_campaigns"],
        total_recipients=stats["total_recipients"],
        total_accepted=stats["total_accepted"],
        total_rejected=stats["total_rejected"],
        total_failed=stats["total_failed"],
        total_uncertain=stats["total_uncertain"],
        recent_campaigns=[CampaignSummaryResponse.model_validate(c) for c in stats["recent_campaigns"]],
        recent_submissions=[RecipientResultResponse.model_validate(s) for s in stats["recent_submissions"]],
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignDetailResponse,
    summary="Get campaign details and recipient results",
)
def get_campaign_detail(
    campaign_id: str,
    db: Session = Depends(get_db),
):
    """Fetch campaign metadata and individual recipient execution records."""
    campaign = CampaignRepository.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID '{campaign_id}' not found.",
        )
    submissions = CampaignRepository.get_campaign_submissions(db, campaign_id)

    return CampaignDetailResponse(
        id=campaign.id,
        campaign_name=campaign.campaign_name,
        subject=campaign.subject,
        body=campaign.body,
        event_type=campaign.event_type,
        created_at=campaign.created_at,
        total_recipients=campaign.total_recipients,
        accepted_count=campaign.accepted_count,
        rejected_count=campaign.rejected_count,
        failed_count=campaign.failed_count,
        uncertain_count=campaign.uncertain_count,
        processing_status=campaign.processing_status,
        results=[RecipientResultResponse.model_validate(sub) for sub in submissions],
    )


@router.get(
    "/{campaign_id}/results",
    response_model=List[RecipientResultResponse],
    summary="Get recipient-level results for a campaign",
)
def get_campaign_results(
    campaign_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve recipient-level outcome rows for a specific campaign."""
    campaign = CampaignRepository.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID '{campaign_id}' not found.",
        )
    submissions = CampaignRepository.get_campaign_submissions(db, campaign_id)
    return [RecipientResultResponse.model_validate(sub) for sub in submissions]


@router.get(
    "/{campaign_id}/export",
    summary="Download campaign results as CSV",
)
def export_campaign_results(
    campaign_id: str,
    db: Session = Depends(get_db),
):
    """Generate and return a downloadable CSV report of recipient submission outcomes."""
    campaign = CampaignRepository.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID '{campaign_id}' not found.",
        )
    submissions = CampaignRepository.get_campaign_submissions(db, campaign_id)
    csv_content = generate_campaign_csv_report(campaign, submissions)

    filename = f"campaign_{campaign.campaign_name.replace(' ', '_')}_{campaign_id[:8]}_results.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post(
    "/parse-csv",
    response_model=CSVParseSummary,
    summary="Upload and validate a recipient CSV file",
)
async def parse_csv_file(
    file: UploadFile = File(...),
    column_name: Optional[str] = Form(None),
    deduplicate: bool = Form(True),
):
    """
    Validate uploaded CSV file, extract recipient addresses, and produce analytics
    on valid, invalid, and duplicate emails.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a .csv file.",
        )

    content = await file.read()
    try:
        summary = parse_and_validate_csv(
            file_content=content,
            preferred_column=column_name if column_name else None,
            deduplicate=deduplicate,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return CSVParseSummary(
        total_rows=summary["total_rows"],
        valid_count=summary["valid_count"],
        invalid_count=summary["invalid_count"],
        duplicate_count=summary["duplicate_count"],
        empty_rows_count=summary["empty_rows_count"],
        valid_recipients=summary["valid_recipients"],
        invalid_recipients=summary["invalid_recipients"],
        detected_email_column=summary["detected_column"] or "",
    )
