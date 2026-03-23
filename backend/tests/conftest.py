"""
Test fixtures: in-memory SQLite, minimal metadata (users + watchlist only).

Imports avoid loading unrelated models (e.g. JSONB) so `create_all` works.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, create_engine, delete, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Register only the tables needed for watchlist tests — avoid importing `app.main`
# at module import time so `AuditLog` (JSONB) is not registered before SQLite DDL.
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.broker_connection import BrokerConnection
from app.models.position import Position
from app.models.recommendation import Recommendation
from app.models.recommendation_status_event import RecommendationStatusEvent
from app.models.trade_order import TradeOrder
from app.models.user import User
from app.models.watchlist_item import WatchlistItem


def _patch_jsonb_to_json_for_sqlite(*tables: object) -> None:
    """SQLite cannot create PostgreSQL JSONB columns; swap to JSON for DDL only."""
    for table in tables:
        for col in table.columns:  # type: ignore[attr-defined]
            if isinstance(col.type, JSONB):
                col.type = JSON()


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create FK parent first — avoids depending on `Base.metadata.create_all`, which
    # would compile every mapped table (including PostgreSQL-only types).
    User.__table__.create(bind=eng, checkfirst=True)
    WatchlistItem.__table__.create(bind=eng, checkfirst=True)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine) -> Session:
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    sess = SessionLocal()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture(autouse=True)
def _clean_tables(db_session: Session) -> None:
    db_session.execute(delete(WatchlistItem))
    db_session.execute(delete(User))
    db_session.commit()
    yield


@pytest.fixture
def client(db_session: Session) -> TestClient:
    from app.main import app

    def _get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def user_id(db_session: Session) -> uuid.UUID:
    u = User(
        email=f"user-{uuid.uuid4()}@example.com",
        is_active=True,
        is_verified=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u.id


@pytest.fixture
def auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return {"X-User-Id": str(user_id)}


@pytest.fixture(scope="session")
def workflow_engine():
    """SQLite engine for recommendation workflow + audit + orders (JSONB patched)."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    _patch_jsonb_to_json_for_sqlite(Recommendation.__table__, AuditLog.__table__)

    User.__table__.create(bind=eng, checkfirst=True)
    WatchlistItem.__table__.create(bind=eng, checkfirst=True)
    BrokerConnection.__table__.create(bind=eng, checkfirst=True)
    Recommendation.__table__.create(bind=eng, checkfirst=True)
    TradeOrder.__table__.create(bind=eng, checkfirst=True)
    Position.__table__.create(bind=eng, checkfirst=True)
    AuditLog.__table__.create(bind=eng, checkfirst=True)
    RecommendationStatusEvent.__table__.create(bind=eng, checkfirst=True)
    yield eng
    eng.dispose()


def _workflow_cleanup(sess: Session) -> None:
    sess.execute(delete(RecommendationStatusEvent))
    sess.execute(delete(Position))
    sess.execute(delete(TradeOrder))
    sess.execute(delete(Recommendation))
    sess.execute(delete(AuditLog))
    sess.execute(delete(WatchlistItem))
    sess.execute(delete(BrokerConnection))
    sess.execute(delete(User))
    sess.commit()


@pytest.fixture
def workflow_db_session(workflow_engine) -> Session:
    SessionLocal = sessionmaker(bind=workflow_engine, autocommit=False, autoflush=False, class_=Session)
    sess = SessionLocal()
    _workflow_cleanup(sess)
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture
def workflow_user_id(workflow_db_session: Session) -> uuid.UUID:
    u = User(
        email=f"user-{uuid.uuid4()}@example.com",
        is_active=True,
        is_verified=True,
    )
    workflow_db_session.add(u)
    workflow_db_session.commit()
    workflow_db_session.refresh(u)
    return u.id


@pytest.fixture
def workflow_auth_headers(workflow_user_id: uuid.UUID) -> dict[str, str]:
    return {"X-User-Id": str(workflow_user_id)}


@pytest.fixture(scope="session")
def monitor_engine():
    """SQLite for paper position monitor tests (positions + orders + recommendations)."""
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def _pragma(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
        c = dbapi_conn.cursor()
        c.execute("PRAGMA foreign_keys=ON")
        c.close()

    _patch_jsonb_to_json_for_sqlite(Recommendation.__table__)
    User.__table__.create(bind=eng, checkfirst=True)
    WatchlistItem.__table__.create(bind=eng, checkfirst=True)
    BrokerConnection.__table__.create(bind=eng, checkfirst=True)
    Recommendation.__table__.create(bind=eng, checkfirst=True)
    TradeOrder.__table__.create(bind=eng, checkfirst=True)
    Position.__table__.create(bind=eng, checkfirst=True)
    yield eng
    eng.dispose()


def _monitor_cleanup(sess: Session) -> None:
    sess.execute(delete(Position))
    sess.execute(delete(TradeOrder))
    sess.execute(delete(Recommendation))
    sess.execute(delete(WatchlistItem))
    sess.execute(delete(BrokerConnection))
    sess.execute(delete(User))
    sess.commit()


@pytest.fixture
def monitor_db_session(monitor_engine) -> Session:
    SessionLocal = sessionmaker(bind=monitor_engine, autocommit=False, autoflush=False, class_=Session)
    sess = SessionLocal()
    _monitor_cleanup(sess)
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture
def monitor_user_id(monitor_db_session: Session) -> uuid.UUID:
    u = User(
        email=f"mon-{uuid.uuid4()}@example.com",
        is_active=True,
        is_verified=True,
    )
    monitor_db_session.add(u)
    monitor_db_session.commit()
    monitor_db_session.refresh(u)
    return u.id


@pytest.fixture
def workflow_client(workflow_db_session: Session) -> TestClient:
    from app.main import app

    def _get_db():
        try:
            yield workflow_db_session
            workflow_db_session.commit()
        except Exception:
            workflow_db_session.rollback()
            raise

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
