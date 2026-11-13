"""Database session factory and FastAPI dependency."""

from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create the application-wide SQLAlchemy engine (one connection pool, cached).

    The pool is sized with the API thread limit (ADR-0022): at most ``pool_size + max_overflow``
    connections, and a request waits ``pool_timeout`` seconds for one.
    """
    settings = get_settings()
    return create_engine(
        str(settings.database_url),
        hide_parameters=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
    )


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for request-scoped sessions."""
    SessionLocal = get_session_factory(get_engine())
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ADR-0023 / PRB-080: scope="function" tears the dependency down (commit or rollback) when the
# endpoint has returned, before the response is sent, so a success status means a committed change
# and a failed commit is a 5xx. The dependency cache key includes the scope: every use of get_db
# must go through this alias, or one request gets two sessions (tests/api/test_db_dependency_scope).
DbSession = Annotated[Session, Depends(get_db, scope="function")]
