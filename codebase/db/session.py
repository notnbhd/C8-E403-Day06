from typing import Generator
from sqlalchemy.orm import sessionmaker
from .database import get_engine

engine = get_engine()

SessionLocal = None
if engine is not None:
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Generator:
    """Yield a SQLAlchemy session. Raises RuntimeError if engine not configured."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured; SessionLocal is None")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
