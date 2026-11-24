from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.db.session import engine
from app.models.base import Base
# Import all models to ensure metadata is populated
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing BusinessPulse AI Backend...")
    # Initialize DB schema tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified and initialized.")
    yield
    logger.info("Shutting down BusinessPulse AI Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Unified Business Intelligence & Predictive Decision Platform API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0"
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API. Visit {settings.API_V1_STR}/docs for API documentation."
    }

