"""Health check router for CloudCart."""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check endpoint")
async def health_check():
    """Verify application backend is operational without sending notifications."""
    return {
        "status": "healthy",
        "service": "CloudCart Event-Driven Platform",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }
