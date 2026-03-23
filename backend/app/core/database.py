"""
SQLAlchemy engine and session factory.

Uses a synchronous engine for broad Alembic compatibility and straightforward
deployment; swap to async engine + `async_sessionmaker` if you standardize on
async routes end-to-end.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Engine: pool_pre_ping avoids handing out dead connections after idle timeouts.
engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a DB session, commits on success, rolls back on errors.

    Usage:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
