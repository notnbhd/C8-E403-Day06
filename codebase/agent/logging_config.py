"""Logging tập trung cho agent — bật/tắt & đổi mức qua env.

    AGENT_LOG_LEVEL = DEBUG | INFO | WARNING   (mặc định INFO)
    AGENT_LOG_FILE  = đường dẫn file            (tuỳ chọn -> ghi thêm ra file)

Gọi `setup_logging()` 1 lần (config.py tự gọi khi import). Mỗi module dùng
`logging.getLogger("agent.<tên>")` để log theo namespace.
"""
from __future__ import annotations

import logging
import os

_CONFIGURED = False


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = os.getenv("AGENT_LOG_LEVEL", "INFO").upper()
    logger = logging.getLogger("agent")
    logger.setLevel(level)
    logger.propagate = False  # không nhân đôi qua root logger

    fmt = logging.Formatter("%(asctime)s %(levelname)-5s %(name)s | %(message)s", "%H:%M:%S")

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    path = os.getenv("AGENT_LOG_FILE")
    if path:
        fh = logging.FileHandler(path, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    _CONFIGURED = True


def preview(text: str | None, n: int = 90) -> str:
    """Rút gọn chuỗi dài (cho log gọn 1 dòng)."""
    s = (text or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[:n] + "…"
