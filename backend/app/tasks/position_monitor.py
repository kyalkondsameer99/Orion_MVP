"""RQ job: scan paper positions, refresh marks / PnL, emit exit recommendations."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.market_data.adapter_factory import build_market_data_adapter
from app.services.paper_position_monitor_service import PaperPositionMonitorService

logger = logging.getLogger(__name__)


def run_position_monitor_cycle() -> dict[str, object]:
    """
    Entry point for `rq worker` — one DB session per invocation, commit on success.
    """
    settings = get_settings()
    adapter = build_market_data_adapter(settings)
    svc = PaperPositionMonitorService(adapter)
    db = SessionLocal()
    try:
        result = svc.run_cycle(db)
        db.commit()
        out: dict[str, object] = {
            "positions_scanned": result.positions_scanned,
            "positions_updated": result.positions_updated,
            "exit_recommendations_created": result.exit_recommendations_created,
            "errors": result.errors,
        }
        if result.errors:
            logger.warning("Paper position monitor completed with errors: %s", result.errors)
        return out
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
