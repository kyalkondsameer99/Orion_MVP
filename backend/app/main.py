"""
ASGI entrypoint — Uvicorn/Gunicorn import path: `app.main:app`.
"""

from fastapi import FastAPI

from app import __version__
from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=__version__,
    debug=settings.DEBUG,
)

# Root-level health for load balancers / orchestrators (common convention).
app.include_router(health_router)

# Versioned API surface for product endpoints.
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
