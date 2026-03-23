"""
ORM models — import side effects register tables on `Base.metadata`.

Alembic's `env.py` imports this module so autogenerate sees every model.
"""

from app.models.audit_log import AuditLog
from app.models.base import Base
from app.models.broker_connection import BrokerConnection
from app.models.position import Position
from app.models.recommendation import Recommendation
from app.models.recommendation_status_event import RecommendationStatusEvent
from app.models.trade_order import TradeOrder
from app.models.user import User
from app.models.watchlist_item import WatchlistItem

__all__ = [
    "Base",
    "User",
    "BrokerConnection",
    "WatchlistItem",
    "Recommendation",
    "RecommendationStatusEvent",
    "TradeOrder",
    "Position",
    "AuditLog",
]
