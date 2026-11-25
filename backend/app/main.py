import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

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


# Static and SPA frontend serving (Single-service deployment like Tumor_Detection)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

if FRONTEND_DIST.exists():
    from starlette.exceptions import HTTPException as StarletteHTTPException
    from fastapi.responses import JSONResponse

    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", tags=["UI"], include_in_schema=False)
    async def serve_root():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file))
        return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request, exc):
        if exc.status_code == 404 and request.method == "GET":
            req_path = request.url.path
            # Do not hijack API or system endpoints
            if not req_path.startswith("/api") and not req_path.startswith("/health") and not req_path.startswith("/docs") and not req_path.startswith("/redoc"):
                # Check for static assets in frontend/dist (e.g. vite.svg, favicon.ico)
                relative_path = req_path.lstrip("/")
                file_path = FRONTEND_DIST / relative_path
                if file_path.is_file():
                    return FileResponse(str(file_path))

                # SPA fallback for client-side routing
                index_file = FRONTEND_DIST / "index.html"
                if index_file.is_file():
                    return FileResponse(str(index_file))
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
else:
    @app.get("/", tags=["System"])
    def root():
        return {
            "message": f"Welcome to {settings.PROJECT_NAME} API. Visit {settings.API_V1_STR}/docs for API documentation."
        }


