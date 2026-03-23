"""
Health checks.

- *Liveness* (`/health`): process is up; cheap and safe behind load balancers.
- *Readiness* (optional future `/ready`): verify DB, queues, etc. before traffic.
"""

from app import __version__
from app.core.config import settings
from app.schemas.health import HealthResponse


class HealthService:
    """Small façade so routes stay declarative and testable."""

    @staticmethod
    def liveness() -> HealthResponse:
        """Return a stable JSON body for orchestrator health probes."""
        return HealthResponse(
            status="healthy",
            service="orion-paper-trading-api",
            environment=settings.ENVIRONMENT,
            version=__version__,
        )
