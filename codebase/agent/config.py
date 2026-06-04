"""Agent-workflow config.

Đọc env trực tiếp để KHÔNG phụ thuộc / không sửa `config/settings.py` của teammate.
LLM đi qua OpenRouter (OpenAI-compatible gateway) — xem docs §9.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv optional
    pass

# --- LLM (OpenRouter) ---
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
AGENT_MODEL: str = os.getenv("AGENT_MODEL", "anthropic/claude-3.5-sonnet")
LLM_TEMPERATURE: float = float(os.getenv("AGENT_TEMPERATURE", "0.3"))

# --- Guardrail ---
# Số buổi tối thiểu cho 1 bài trước khi agent dám kết luận về trend (thin-spec §7).
MIN_SESSIONS: int = int(os.getenv("AGENT_MIN_SESSIONS", "3"))

# Khi True, các tool dùng mock data thay vì Supabase thật (Backend chưa cắm).
USE_MOCK_TOOLS: bool = os.getenv("AGENT_USE_MOCK_TOOLS", "1") == "1"


def llm_enabled() -> bool:
    """Có key OpenRouter không. Nếu không, agent chạy ở chế độ template offline."""
    return bool(OPENROUTER_API_KEY)
