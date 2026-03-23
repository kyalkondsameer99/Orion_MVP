"""Recommendation engine HTTP API."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import (
    get_current_user_id,
    get_recommendation_service,
    get_recommendation_workflow_service,
)
from app.recommendation.service import RecommendationService
from app.schemas.recommendation_engine import RecommendationRequest, RecommendationResponse
from app.schemas.recommendation_workflow import (
    PersistRecommendationRequest,
    RecommendationActionResult,
    RecommendationListResponse,
    RecommendationSubmitResult,
)
from app.models.enums import RecommendationStatus
from app.services.recommendation_workflow_service import RecommendationWorkflowService

router = APIRouter()


@router.post(
    "/analyze",
    response_model=RecommendationResponse,
    summary="Deterministic BUY/SELL/HOLD from OHLCV, indicators, news, and risk budget",
)
def analyze_recommendation(
    body: RecommendationRequest,
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
) -> RecommendationResponse:
    return service.analyze(body)


@router.post(
    "/generate",
    response_model=RecommendationResponse,
    summary="Alias for `/analyze` (starter-pack compatibility)",
)
def generate_recommendation(
    body: RecommendationRequest,
    service: Annotated[RecommendationService, Depends(get_recommendation_service)],
) -> RecommendationResponse:
    return service.analyze(body)


@router.post(
    "/",
    response_model=RecommendationActionResult,
    summary="Persist engine output for approval workflow (status=pending)",
)
def persist_recommendation(
    body: PersistRecommendationRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    workflow: Annotated[RecommendationWorkflowService, Depends(get_recommendation_workflow_service)],
) -> RecommendationActionResult:
    return workflow.persist(user_id, body)


@router.get(
    "/",
    response_model=RecommendationListResponse,
    summary="List persisted recommendations for the current user",
)
def list_recommendations(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    workflow: Annotated[RecommendationWorkflowService, Depends(get_recommendation_workflow_service)],
    status: RecommendationStatus | None = Query(
        default=None,
        description="Filter by workflow status (e.g. pending, approved).",
    ),
    symbol: str | None = Query(
        default=None,
        max_length=32,
        description="Filter by ticker (normalized to uppercase).",
    ),
    limit: int = Query(default=50, ge=1, le=100),
) -> RecommendationListResponse:
    return workflow.list_recommendations(user_id, status=status, symbol=symbol, limit=limit)


@router.post(
    "/{recommendation_id}/approve",
    response_model=RecommendationActionResult,
    summary="Approve a pending recommendation and create an internal order record",
)
def approve_recommendation(
    recommendation_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    workflow: Annotated[RecommendationWorkflowService, Depends(get_recommendation_workflow_service)],
) -> RecommendationActionResult:
    return workflow.approve(user_id, recommendation_id)


@router.post(
    "/{recommendation_id}/reject",
    response_model=RecommendationActionResult,
    summary="Reject a pending recommendation",
)
def reject_recommendation(
    recommendation_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    workflow: Annotated[RecommendationWorkflowService, Depends(get_recommendation_workflow_service)],
) -> RecommendationActionResult:
    return workflow.reject(user_id, recommendation_id)


@router.post(
    "/{recommendation_id}/submit",
    response_model=RecommendationSubmitResult,
    summary="Submit approved recommendation to broker (requires approved status + broker config)",
)
def submit_recommendation_to_broker(
    recommendation_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    workflow: Annotated[RecommendationWorkflowService, Depends(get_recommendation_workflow_service)],
) -> RecommendationSubmitResult:
    return workflow.submit_to_broker(user_id, recommendation_id)
