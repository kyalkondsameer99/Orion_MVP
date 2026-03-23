"""Internal order history (`trade_orders` table — not Alpaca's remote list)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_user_id,
    get_db,
    get_recommendation_workflow_service,
)
from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.models.enums import OrderStatus
from app.models.trade_order import TradeOrder
from app.schemas.recommendation_workflow import (
    PlaceOrderByRecommendationRequest,
    RecommendationSubmitResult,
)
from app.schemas.trade_order import TradeOrderListResponse, TradeOrderRead
from app.services.recommendation_workflow_service import RecommendationWorkflowService

router = APIRouter()


@router.post(
    "/place",
    response_model=RecommendationSubmitResult,
    summary="Submit approved recommendation to broker (starter-pack alias for workflow submit)",
)
def place_order_from_recommendation(
    body: PlaceOrderByRecommendationRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    workflow: Annotated[RecommendationWorkflowService, Depends(get_recommendation_workflow_service)],
) -> RecommendationSubmitResult:
    return workflow.submit_to_broker(user_id, body.recommendation_id)


@router.get(
    "/",
    response_model=TradeOrderListResponse,
    summary="List internal orders for the current user",
)
def list_internal_orders(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
    order_status: OrderStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by order status (new, pending, filled, …).",
    ),
    symbol: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=50, ge=1, le=200),
) -> TradeOrderListResponse:
    stmt = select(TradeOrder).where(TradeOrder.user_id == user_id)
    if order_status is not None:
        stmt = stmt.where(TradeOrder.status == order_status)
    if symbol is not None and symbol.strip():
        try:
            sym = normalize_symbol(symbol)
        except InvalidSymbolError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            ) from e
        stmt = stmt.where(TradeOrder.symbol == sym)
    stmt = stmt.order_by(TradeOrder.created_at.desc()).limit(limit)
    rows = list(db.scalars(stmt).all())
    return TradeOrderListResponse(items=[TradeOrderRead.model_validate(r) for r in rows])
