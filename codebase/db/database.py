import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(override=True)

# SQLAlchemy needs the Postgres connection string, not the Supabase API URL.
DATABASE_URL = os.getenv("DATABASE_URL")


def get_engine(echo: bool = False):
    """Return a SQLAlchemy Engine or None if DATABASE_URL is not configured."""
    if not DATABASE_URL:
        return None
    return create_engine(DATABASE_URL, echo=echo, future=True)
