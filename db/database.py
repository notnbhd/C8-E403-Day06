import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# Prefer an explicit DATABASE_URL; fall back to SUPABASE_DB_URL / SUPABASE_URL
DATABASE_URL = os.getenv("SUPABASE_URL")


def get_engine(echo: bool = False):
    """Return a SQLAlchemy Engine or None if DATABASE_URL is not configured."""
    if not DATABASE_URL:
        return None
    return create_engine(DATABASE_URL, echo=echo, future=True)
