"""
Monitor open paper positions: marks, unrealized PnL, SL/TP, exit recommendations.

Used by RQ workers only — keep HTTP routes thin and call into this module if needed.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.market_data.adapters.base import MarketDataAdapter
from app.market_data.prices import fetch_last_price
from app.models.enums import (
    OrderSide,
    PositionSide,
    PositionStatus,
    RecommendationSource,
    RecommendationStatus,
)
from app.models.position import Position
from app.models.recommendation import Recommendation
from app.models.trade_order import TradeOrder

logger = logging.getLogger(__name__)


@dataclass
class PaperPositionMonitorResult:
    positions_scanned: int = 0
    positions_updated: int = 0
    exit_recommendations_created: int = 0
    errors: list[str] = field(default_factory=list)


def _compute_unrealized_pnl(
    *,
    side: PositionSide,
    quantity: Decimal,
    avg_entry: Decimal,
    mark: Decimal,
) -> Decimal:
    if side == PositionSide.LONG:
        return (mark - avg_entry) * quantity
    return (avg_entry - mark) * quantity


def _resolve_sl_tp(db: Session, position: Position) -> tuple[Decimal | None, Decimal | None]:
    if position.stop_loss_price is not None or position.take_profit_price is not None:
        return position.stop_loss_price, position.take_profit_price
    if position.opening_trade_order_id is None:
        return None, None
    order = db.get(TradeOrder, position.opening_trade_order_id)
    if order is None or order.recommendation_id is None:
        return None, None
    rec = db.get(Recommendation, order.recommendation_id)
    if rec is None:
        return None, None
    return rec.stop_loss, rec.take_profit


def _sl_tp_triggered(
    *,
    side: PositionSide,
    mark: Decimal,
    stop_loss: Decimal | None,
    take_profit: Decimal | None,
) -> str | None:
    if side == PositionSide.LONG:
        if stop_loss is not None and mark <= stop_loss:
            return "stop_loss"
        if take_profit is not None and mark >= take_profit:
            return "take_profit"
        return None
    if stop_loss is not None and mark >= stop_loss:
        return "stop_loss"
    if take_profit is not None and mark <= take_profit:
        return "take_profit"
    return None


def _exit_order_side(position_side: PositionSide) -> OrderSide:
    return OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY


def _has_active_exit_alert(db: Session, position_id: uuid.UUID) -> bool:
    stmt = (
        select(Recommendation.id)
        .where(
            Recommendation.related_position_id == position_id,
            Recommendation.source == RecommendationSource.POSITION_MONITOR,
            Recommendation.status.in_(
                (
                    RecommendationStatus.PENDING,
                    RecommendationStatus.APPROVED,
                )
            ),
        )
        .limit(1)
    )
    return db.scalars(stmt).first() is not None


def _load_open_paper_positions(db: Session) -> list[Position]:
    stmt = (
        select(Position)
        .join(TradeOrder, Position.opening_trade_order_id == TradeOrder.id)
        .where(
            Position.status == PositionStatus.OPEN,
            TradeOrder.paper_trade.is_(True),
        )
    )
    return list(db.scalars(stmt).all())


class PaperPositionMonitorService:
    """Application service — batching price lookups and DB updates."""

    def __init__(self, adapter: MarketDataAdapter) -> None:
        self._adapter = adapter

    def run_cycle(
        self,
        db: Session,
        *,
        price_overrides: dict[str, Decimal] | None = None,
    ) -> PaperPositionMonitorResult:
        """
        Poll marks for all open paper positions, refresh unrealized PnL, emit exit recs.

        `price_overrides` maps normalized symbol -> mark (tests / deterministic runs).

        Does not commit. The caller must ``commit()`` the same ``Session`` when the
        cycle succeeds (e.g. ``run_position_monitor_cycle`` in ``app.tasks.position_monitor``).
        """
        result = PaperPositionMonitorResult()
        overrides = price_overrides or {}
        cache: dict[str, Decimal] = {}

        def resolve_price(sym: str) -> Decimal:
            key = sym.upper()
            if key in overrides:
                return overrides[key]
            if key not in cache:
                cache[key] = fetch_last_price(self._adapter, key)
            return cache[key]

        positions = _load_open_paper_positions(db)
        result.positions_scanned = len(positions)

        for pos in positions:
            try:
                mark = resolve_price(pos.symbol)
                pnl = _compute_unrealized_pnl(
                    side=pos.side,
                    quantity=pos.quantity,
                    avg_entry=pos.avg_entry_price,
                    mark=mark,
                )
                if pos.unrealized_pnl != pnl:
                    pos.unrealized_pnl = pnl
                    result.positions_updated += 1

                sl, tp = _resolve_sl_tp(db, pos)
                trigger = _sl_tp_triggered(side=pos.side, mark=mark, stop_loss=sl, take_profit=tp)
                if trigger and not _has_active_exit_alert(db, pos.id):
                    PaperPositionMonitorService._create_exit_recommendation(
                        db,
                        position=pos,
                        mark=mark,
                        trigger=trigger,
                        stop_loss=sl,
                        take_profit=tp,
                    )
                    result.exit_recommendations_created += 1
            except Exception as e:  # noqa: BLE001 — log and continue other symbols
                msg = f"{pos.symbol} ({pos.id}): {e}"
                logger.exception("Paper position monitor row failed: %s", msg)
                result.errors.append(msg)

        return result

    @staticmethod
    def _create_exit_recommendation(
        db: Session,
        *,
        position: Position,
        mark: Decimal,
        trigger: str,
        stop_loss: Decimal | None,
        take_profit: Decimal | None,
    ) -> None:
        """
        Stage a new pending recommendation for SL/TP exit.

        Uses ``flush()`` so the row exists in-session before the caller's ``commit()``;
        committing here would break one atomic transaction for the whole ``run_cycle``.
        """
        exit_side = _exit_order_side(position.side)
        if trigger == "stop_loss":
            detail = f"Stop loss level reached (mark {mark}, stop {stop_loss})."
        else:
            detail = f"Take profit target reached (mark {mark}, target {take_profit})."
        summary = f"Paper position exit: {detail}"
        rec = Recommendation(
            user_id=position.user_id,
            watchlist_item_id=None,
            related_position_id=position.id,
            symbol=position.symbol,
            side=exit_side,
            confidence=Decimal("0.9900"),
            rationale=summary,
            status=RecommendationStatus.PENDING,
            source=RecommendationSource.POSITION_MONITOR,
            recommended_at=dt.datetime.now(tz=dt.timezone.utc),
            recommendation_action="SELL" if exit_side == OrderSide.SELL else "BUY",
            trade_direction="NONE",
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            quantity=position.quantity,
            account_size_snapshot=None,
            risk_percent_snapshot=None,
            engine_snapshot={"trigger": trigger, "mark": str(mark), "position_id": str(position.id)},
        )
        db.add(rec)
        db.flush()
