import pandas as pd
from typing import Optional


def read_csv_bytes(uploaded_file) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(uploaded_file)
    except Exception:
        return None
