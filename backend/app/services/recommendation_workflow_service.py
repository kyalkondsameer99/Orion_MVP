"""Persist recommendations, approval/reject, internal order rows, broker submit, audit."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.broker.errors import BrokerAPIError
from app.core.config import get_settings
from app.broker.service import BrokerService
from app.models.audit_log import AuditLog
from app.core.symbols import InvalidSymbolError, normalize_symbol
from app.models.enums import (
    AuditActorType,
    OrderSide,
    OrderStatus,
    OrderType,
    RecommendationSource,
    RecommendationStatus,
    TimeInForce,
)
from app.models.recommendation import Recommendation
from app.models.recommendation_status_event import RecommendationStatusEvent
from app.models.trade_order import TradeOrder
from app.schemas.broker import PlaceOrderRequest
from app.schemas.recommendation_engine import RecommendationResponse
from app.schemas.recommendation_workflow import (
    PersistRecommendationRequest,
    RecommendationActionResult,
    RecommendationListResponse,
    RecommendationRecordOut,
    RecommendationSubmitResult,
)


def _audit(
    db: Session,
    *,
    user_id: uuid.UUID,
    action: str,
    resource_id: uuid.UUID,
    payload: dict,
) -> None:
    db.add(
        AuditLog(
            user_id=user_id,
            actor_type=AuditActorType.USER,
            action=action,
            resource_type="recommendation",
            resource_id=resource_id,
            payload=payload,
        )
    )


def _transition(
    db: Session,
    *,
    recommendation_id: uuid.UUID,
    from_status: RecommendationStatus,
    to_status: RecommendationStatus,
    user_id: uuid.UUID,
) -> None:
    db.add(
        RecommendationStatusEvent(
            recommendation_id=recommendation_id,
            from_status=from_status.value,
            to_status=to_status.value,
            user_id=user_id,
        )
    )


def _to_record_out(rec: Recommendation, trade_order_id: uuid.UUID | None) -> RecommendationRecordOut:
    snap: dict[str, Any] = rec.engine_snapshot if isinstance(rec.engine_snapshot, dict) else {}
    conf: float | None = None
    if snap.get("confidence") is not None:
        try:
            conf = float(snap["confidence"])
        except (TypeError, ValueError):
            conf = None
    if conf is None and rec.confidence is not None:
        conf = float(rec.confidence)
    tech = snap.get("technical_summary") if snap else None
    news = snap.get("news_summary") if snap else None
    reason = (snap.get("reason_summary") if snap else None) or rec.rationale
    prc = snap.get("passed_risk_checks") if snap else None
    rr = snap.get("reward_risk_ratio") if snap else None
    passed_out: bool | None = None
    if prc is not None:
        if isinstance(prc, bool):
            passed_out = prc
        elif isinstance(prc, str):
            passed_out = prc.lower() in ("true", "1", "yes")
        else:
            passed_out = bool(prc)
    if rr is not None:
        try:
            rr = float(rr)
        except (TypeError, ValueError):
            rr = None
    return RecommendationRecordOut(
        id=rec.id,
        user_id=rec.user_id,
        symbol=rec.symbol,
        status=rec.status.value if isinstance(rec.status, RecommendationStatus) else str(rec.status),
        recommendation_action=rec.recommendation_action,
        trade_direction=rec.trade_direction,
        entry_price=rec.entry_price,
        stop_loss=rec.stop_loss,
        take_profit=rec.take_profit,
        quantity=rec.quantity,
        trade_order_id=trade_order_id,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        confidence=conf,
        technical_summary=str(tech) if tech is not None else None,
        news_summary=str(news) if news is not None else None,
        reason_summary=str(reason) if reason is not None else None,
        passed_risk_checks=passed_out,
        reward_risk_ratio=rr,
    )


def _map_action_to_side(action: str) -> OrderSide:
    a = action.upper()
    if a == "BUY":
        return OrderSide.BUY
    if a == "SELL":
        return OrderSide.SELL
    raise ValueError("unsupported action")


def _require_trading_enabled() -> None:
    if not get_settings().TRADING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trading is disabled (TRADING_ENABLED=false).",
        )


def compute_position_quantity(
    *,
    entry: Decimal,
    stop: Decimal,
    account_size: Decimal,
    risk_percent: float,
) -> Decimal:
    risk_budget = account_size * (Decimal(str(risk_percent)) / Decimal("100"))
    risk_per_share = abs(entry - stop)
    if risk_per_share <= 0:
        raise ValueError("stop must differ from entry to size risk")
    q = risk_budget / risk_per_share
    return q.quantize(Decimal("0.0001"))


class RecommendationWorkflowService:
    def __init__(self, db: Session, broker: BrokerService | None = None) -> None:
        self._db = db
        self._broker = broker

    def list_recommendations(
        self,
        user_id: uuid.UUID,
        *,
        workflow_status: RecommendationStatus | None,
        symbol: str | None,
        limit: int,
    ) -> RecommendationListResponse:
        sym_filter: str | None = None
        if symbol is not None and symbol.strip():
            try:
                sym_filter = normalize_symbol(symbol)
            except InvalidSymbolError as e:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

        stmt = select(Recommendation).where(Recommendation.user_id == user_id)
        if workflow_status is not None:
            stmt = stmt.where(Recommendation.status == workflow_status)
        if sym_filter is not None:
            stmt = stmt.where(Recommendation.symbol == sym_filter)
        stmt = (
            stmt.order_by(Recommendation.recommended_at.desc(), Recommendation.created_at.desc()).limit(limit)
        )
        recs = list(self._db.scalars(stmt).all())
        if not recs:
            return RecommendationListResponse(items=[])

        rec_ids = [r.id for r in recs]
        orders = list(
            self._db.scalars(select(TradeOrder).where(TradeOrder.recommendation_id.in_(rec_ids))).all()
        )
        latest_order_by_rec: dict[uuid.UUID, TradeOrder] = {}
        for o in orders:
            rid = o.recommendation_id
            if rid is None:
                continue
            prev = latest_order_by_rec.get(rid)
            if prev is None or o.created_at > prev.created_at:
                latest_order_by_rec[rid] = o

        items = [
            _to_record_out(
                r,
                latest_order_by_rec[r.id].id if r.id in latest_order_by_rec else None,
            )
            for r in recs
        ]
        return RecommendationListResponse(items=items)

    def persist(self, user_id: uuid.UUID, body: PersistRecommendationRequest) -> RecommendationActionResult:
        _require_trading_enabled()
        eng: RecommendationResponse = body.engine
        if eng.action == "HOLD":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot persist HOLD recommendations for approval.",
            )
        if eng.entry_price is None or eng.stop_loss is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="entry_price and stop_loss are required to persist a trade idea.",
            )

        side = _map_action_to_side(eng.action)
        qty = body.quantity
        if qty is None:
            try:
                qty = compute_position_quantity(
                    entry=Decimal(str(eng.entry_price)),
                    stop=Decimal(str(eng.stop_loss)),
                    account_size=body.account_size,
                    risk_percent=body.risk_percent,
                )
            except ValueError as e:
                raise HTTPException(status_code=422, detail=str(e)) from e

        snap = eng.model_dump(mode="json")
        sym = body.symbol.strip().upper()
        rec = Recommendation(
            user_id=user_id,
            watchlist_item_id=None,
            symbol=sym,
            side=side,
            confidence=Decimal(str(min(1.0, max(0.0, float(eng.confidence))))),
            rationale=eng.reason_summary,
            status=RecommendationStatus.PENDING,
            source=RecommendationSource.ENGINE,
            recommended_at=dt.datetime.now(tz=dt.timezone.utc),
            recommendation_action=eng.action,
            trade_direction=eng.direction,
            entry_price=Decimal(str(eng.entry_price)),
            stop_loss=Decimal(str(eng.stop_loss)),
            take_profit=Decimal(str(eng.take_profit)) if eng.take_profit is not None else None,
            quantity=qty,
            account_size_snapshot=body.account_size,
            risk_percent_snapshot=Decimal(str(body.risk_percent)),
            engine_snapshot=snap,
        )
        self._db.add(rec)
        self._db.flush()
        self._db.add(
            RecommendationStatusEvent(
                recommendation_id=rec.id,
                from_status="none",
                to_status=RecommendationStatus.PENDING.value,
                user_id=user_id,
            )
        )
        _audit(
            self._db,
            user_id=user_id,
            action="recommendation.created",
            resource_id=rec.id,
            payload={"status": RecommendationStatus.PENDING.value},
        )
        self._db.commit()
        self._db.refresh(rec)
        return RecommendationActionResult(
            recommendation=_to_record_out(rec, None),
            message="Recommendation stored as pending.",
        )

    def approve(self, user_id: uuid.UUID, recommendation_id: uuid.UUID) -> RecommendationActionResult:
        _require_trading_enabled()
        rec = self._get_owned(user_id, recommendation_id)
        if rec.status != RecommendationStatus.PENDING:
            raise HTTPException(status_code=409, detail="Only pending recommendations can be approved.")
        if (rec.recommendation_action or "").upper() == "HOLD":
            raise HTTPException(status_code=422, detail="HOLD cannot be approved into an order.")

        qty = rec.quantity
        if qty is None or qty <= 0:
            raise HTTPException(status_code=422, detail="Quantity must be set before approval.")

        client_oid = f"rec-{rec.id.hex[:12]}-{uuid.uuid4().hex[:10]}"
        order = TradeOrder(
            user_id=user_id,
            broker_connection_id=None,
            recommendation_id=rec.id,
            client_order_id=client_oid,
            symbol=rec.symbol,
            side=rec.side,
            order_type=OrderType.MARKET,
            quantity=qty,
            status=OrderStatus.NEW,
            paper_trade=True,
            time_in_force=TimeInForce.DAY,
        )
        self._db.add(order)
        prev = rec.status
        rec.status = RecommendationStatus.APPROVED
        _transition(
            self._db,
            recommendation_id=rec.id,
            from_status=prev,
            to_status=RecommendationStatus.APPROVED,
            user_id=user_id,
        )
        _audit(
            self._db,
            user_id=user_id,
            action="recommendation.approved",
            resource_id=rec.id,
            payload={"trade_order_client_id": client_oid},
        )
        self._db.flush()
        self._db.commit()
        self._db.refresh(rec)
        self._db.refresh(order)
        return RecommendationActionResult(
            recommendation=_to_record_out(rec, order.id),
            trade_order_id=order.id,
            message="Recommendation approved; internal order created (submit to broker separately).",
        )

    def reject(self, user_id: uuid.UUID, recommendation_id: uuid.UUID) -> RecommendationActionResult:
        rec = self._get_owned(user_id, recommendation_id)
        if rec.status != RecommendationStatus.PENDING:
            raise HTTPException(status_code=409, detail="Only pending recommendations can be rejected.")
        prev = rec.status
        rec.status = RecommendationStatus.REJECTED
        _transition(
            self._db,
            recommendation_id=rec.id,
            from_status=prev,
            to_status=RecommendationStatus.REJECTED,
            user_id=user_id,
        )
        _audit(
            self._db,
            user_id=user_id,
            action="recommendation.rejected",
            resource_id=rec.id,
            payload={},
        )
        self._db.flush()
        self._db.commit()
        self._db.refresh(rec)
        return RecommendationActionResult(
            recommendation=_to_record_out(rec, None),
            message="Recommendation rejected.",
        )

    def submit_to_broker(self, user_id: uuid.UUID, recommendation_id: uuid.UUID) -> RecommendationSubmitResult:
        _require_trading_enabled()
        if self._broker is None:
            raise HTTPException(
                status_code=503,
                detail="Broker is not configured; cannot submit to Alpaca.",
            )
        lim = get_settings().MAX_OPEN_POSITIONS
        try:
            plist = self._broker.list_positions()
            if len(plist.positions) >= lim:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Maximum open positions ({lim}) reached at broker.",
                )
        except HTTPException:
            raise
        except BrokerAPIError:
            pass

        rec = self._get_owned(user_id, recommendation_id)
        if rec.status != RecommendationStatus.APPROVED:
            raise HTTPException(
                status_code=409,
                detail="Only approved recommendations can be submitted to the broker.",
            )
        stmt = (
            select(TradeOrder)
            .where(TradeOrder.recommendation_id == rec.id)
            .order_by(TradeOrder.created_at.desc())
            .limit(1)
        )
        order = self._db.scalars(stmt).first()
        if order is None:
            raise HTTPException(status_code=404, detail="No trade order linked to this recommendation.")

        if order.submitted_at is not None:
            raise HTTPException(status_code=409, detail="This recommendation was already submitted.")

        body = PlaceOrderRequest(
            symbol=order.symbol,
            side=order.side.value,  # type: ignore[arg-type]
            order_type="market",
            qty=order.quantity,
            time_in_force="day",
        )
        try:
            out = self._broker.place_order(body)
        except BrokerAPIError as e:
            _audit(
                self._db,
                user_id=user_id,
                action="recommendation.broker_submit_failed",
                resource_id=rec.id,
                payload={"error": str(e), "status_code": getattr(e, "status_code", None)},
            )
            self._db.commit()
            raise HTTPException(status_code=502, detail=str(e)) from e

        order.submitted_at = dt.datetime.now(tz=dt.timezone.utc)
        order.status = OrderStatus.SUBMITTED
        prev = rec.status
        rec.status = RecommendationStatus.SUBMITTED
        _transition(
            self._db,
            recommendation_id=rec.id,
            from_status=prev,
            to_status=RecommendationStatus.SUBMITTED,
            user_id=user_id,
        )
        _audit(
            self._db,
            user_id=user_id,
            action="recommendation.submitted_broker",
            resource_id=rec.id,
            payload={"broker_order_id": out.id},
        )
        self._db.flush()
        self._db.commit()
        return RecommendationSubmitResult(
            recommendation_id=rec.id,
            broker_order_id=out.id,
            message="Order submitted to broker.",
        )

    def _get_owned(self, user_id: uuid.UUID, recommendation_id: uuid.UUID) -> Recommendation:
        rec = self._db.get(Recommendation, recommendation_id)
        if rec is None or rec.user_id != user_id:
            raise HTTPException(status_code=404, detail="Recommendation not found.")
        return rec
