"""Unit tests for paper position monitoring (service layer, SQLite)."""

from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select

from app.core.config import Settings
from app.market_data.adapter_factory import build_market_data_adapter
from app.models.enums import (
    OrderSide,
    OrderStatus,
    OrderType,
    PositionSide,
    PositionStatus,
    RecommendationSource,
    RecommendationStatus,
    TimeInForce,
)
from app.models.position import Position
from app.models.recommendation import Recommendation
from app.models.trade_order import TradeOrder
from app.services.paper_position_monitor_service import PaperPositionMonitorService


def _seed_long_paper_position(
    db,
    user_id: uuid.UUID,
    *,
    symbol: str = "AAPL",
    entry: Decimal = Decimal("100"),
    stop: Decimal = Decimal("95"),
    take_profit: Decimal = Decimal("110"),
) -> Position:
    rec = Recommendation(
        user_id=user_id,
        watchlist_item_id=None,
        related_position_id=None,
        symbol=symbol,
        side=OrderSide.BUY,
        confidence=Decimal("0.8000"),
        rationale="seed",
        status=RecommendationStatus.SUBMITTED,
        source=RecommendationSource.ENGINE,
        recommended_at=dt.datetime.now(tz=dt.timezone.utc),
        recommendation_action="BUY",
        trade_direction="LONG",
        entry_price=entry,
        stop_loss=stop,
        take_profit=take_profit,
        quantity=Decimal("10"),
        account_size_snapshot=Decimal("10000"),
        risk_percent_snapshot=Decimal("1.0000"),
        engine_snapshot=None,
    )
    db.add(rec)
    db.flush()
    order = TradeOrder(
        user_id=user_id,
        broker_connection_id=None,
        recommendation_id=rec.id,
        client_order_id=f"co-{uuid.uuid4().hex[:24]}",
        symbol=symbol,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        status=OrderStatus.FILLED,
        paper_trade=True,
        time_in_force=TimeInForce.DAY,
    )
    db.add(order)
    db.flush()
    pos = Position(
        user_id=user_id,
        broker_connection_id=None,
        opening_trade_order_id=order.id,
        symbol=symbol,
        side=PositionSide.LONG,
        quantity=Decimal("10"),
        avg_entry_price=entry,
        unrealized_pnl=None,
        status=PositionStatus.OPEN,
        opened_at=dt.datetime.now(tz=dt.timezone.utc),
    )
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


def test_monitor_updates_pnl_and_stop_loss_exit(monitor_db_session, monitor_user_id) -> None:
    db = monitor_db_session
    _seed_long_paper_position(db, monitor_user_id)
    adapter = build_market_data_adapter(Settings(MARKET_DATA_PROVIDER="stub"))
    svc = PaperPositionMonitorService(adapter)

    r = svc.run_cycle(db, price_overrides={"AAPL": Decimal("90")})
    db.commit()

    assert r.positions_scanned == 1
    assert r.positions_updated == 1
    assert r.exit_recommendations_created == 1

    pos = db.scalars(select(Position)).first()
    assert pos is not None
    assert pos.unrealized_pnl != Decimal("0")
    assert (pos.unrealized_pnl or Decimal("0")) < 0

    ex = db.scalars(
        select(Recommendation).where(Recommendation.source == RecommendationSource.POSITION_MONITOR)
    ).first()
    assert ex is not None
    assert ex.related_position_id == pos.id
    assert ex.side == OrderSide.SELL


def test_monitor_idempotent_exit(monitor_db_session, monitor_user_id) -> None:
    db = monitor_db_session
    _seed_long_paper_position(db, monitor_user_id)
    svc = PaperPositionMonitorService(build_market_data_adapter(Settings(MARKET_DATA_PROVIDER="stub")))

    svc.run_cycle(db, price_overrides={"AAPL": Decimal("90")})
    db.commit()
    r2 = svc.run_cycle(db, price_overrides={"AAPL": Decimal("90")})
    db.commit()

    assert r2.exit_recommendations_created == 0
    assert r2.positions_updated == 0

    n = db.scalars(
        select(Recommendation).where(Recommendation.source == RecommendationSource.POSITION_MONITOR)
    ).all()
    assert len(n) == 1


def test_take_profit_triggers_exit(monitor_db_session, monitor_user_id) -> None:
    db = monitor_db_session
    _seed_long_paper_position(db, monitor_user_id)
    svc = PaperPositionMonitorService(build_market_data_adapter(Settings(MARKET_DATA_PROVIDER="stub")))

    r = svc.run_cycle(db, price_overrides={"AAPL": Decimal("115")})
    db.commit()

    assert r.exit_recommendations_created == 1
    ex = db.scalars(
        select(Recommendation).where(Recommendation.source == RecommendationSource.POSITION_MONITOR)
    ).first()
    assert ex is not None
    assert "Take profit" in (ex.rationale or "")
