"""Liveness endpoint — mounted at `/health` (see `app.main`)."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """
    Liveness probe: returns 200 if the API process can respond.

    For Kubernetes, use this for `livenessProbe`. Add a separate `/ready`
    later if you need DB or queue checks before receiving traffic.
    """
    return HealthService.liveness()
