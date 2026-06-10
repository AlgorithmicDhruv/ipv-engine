import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise EnvironmentError("DATABASE_URL environment variable is not set.")
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


def get_session_factory(engine=None):
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


_engine = None
_SessionFactory = None


def get_db_session():
    global _engine, _SessionFactory
    if _engine is None:
        _engine = get_engine()
        _SessionFactory = get_session_factory(_engine)
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
