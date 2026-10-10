"""FastAPI application entry point for CloudCart."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import get_settings
from backend.database import init_db, SessionLocal
from backend.seed import seed_database
from backend.routers import health, auth, products, orders, notifications, admin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cloudcart")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: creates tables and seeds demo catalog."""
    logger.info("Initializing CloudCart database tables...")
    init_db()

    # Seed demo customers and products if empty
    db = SessionLocal()
    try:
        seed_database(db)
        logger.info("CloudCart database verified and demo catalog seeded.")
    except Exception as exc:
        logger.exception("Error seeding database: %s", exc)
    finally:
        db.close()

    yield
    logger.info("CloudCart backend shutting down.")


app = FastAPI(
    title="CloudCart API",
    description=(
        "Event-Driven E-commerce Platform with Automatic Cloud Email Notifications. "
        "Orders and business events automatically trigger AWS API Gateway notification dispatches via a Transactional Outbox."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global safe exception handler to avoid leaking raw tracebacks
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please consult backend logs.",
            "path": request.url.path,
        },
    )

# Include Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(notifications.router)
app.include_router(admin.router)


@app.get("/", summary="Root endpoint")
async def root():
    return {
        "service": "CloudCart Event-Driven Platform",
        "documentation": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
