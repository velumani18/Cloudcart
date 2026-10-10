"""CloudCart Application Configuration."""
import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """System configuration parameters for CloudCart."""

    # External AWS API Gateway Endpoint
    AWS_NOTIFICATION_URL: str = os.getenv(
        "AWS_NOTIFICATION_URL",
        "https://zjergdi6he.execute-api.ap-south-1.amazonaws.com/notifications",
    )

    # FastAPI Backend Server
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Processing limits & concurrency
    REQUEST_TIMEOUT_SECONDS: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15.0"))
    OUTBOX_MAX_CONCURRENCY: int = int(os.getenv("OUTBOX_MAX_CONCURRENCY", "5"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./cloudcart.db")


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
