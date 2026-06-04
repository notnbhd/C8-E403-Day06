from typing import Optional, Dict, Any
from config.settings import settings

try:
    from supabase import create_client
except Exception:
    create_client = None


def get_client():
    """Return a Supabase client or None if not available.

    For demos, this wraps `supabase.create_client`. If the package is missing,
    the function returns `None` but the rest of the demo stays functional.
    """
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        return None
    if create_client is None:
        return None
    return create_client(url, key)


def insert_row(client, table: str, row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if client is None:
        return None
    res = client.table(table).insert(row).execute()
    return res


def fetch_table(client, table: str, limit: int = 100):
    if client is None:
        return []
    res = client.table(table).select("*").limit(limit).execute()
    return res.data if hasattr(res, "data") else []
