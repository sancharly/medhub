"""Database session factory and FastAPI dependency."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create the application-wide SQLAlchemy engine (one connection pool, cached)."""
    return create_engine(str(get_settings().database_url))


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for request-scoped sessions."""
    SessionLocal = get_session_factory(get_engine())
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
