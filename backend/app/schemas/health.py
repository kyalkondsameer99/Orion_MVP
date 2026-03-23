"""Health / readiness response shapes."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Standard liveness payload for probes and dashboards."""

    status: str = Field(..., examples=["healthy"])
    service: str = Field(..., description="Logical service name")
    environment: str = Field(..., description="Deployment environment label")
    version: str = Field(..., description="Application semver or build label")
