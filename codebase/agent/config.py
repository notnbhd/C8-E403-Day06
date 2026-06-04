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

# --- LLM fallback: tái dùng CUSTOM_LLM_* của RAG chatbot (OpenAI-compatible) ---
# Nếu không có OPENROUTER_API_KEY nhưng có CUSTOM_LLM_KEY (vd Mistral đã cấu hình
# cho app.py) thì agent dùng luôn nó -> không cần thêm key riêng.
CUSTOM_LLM_KEY: str = os.getenv("CUSTOM_LLM_KEY", "")
CUSTOM_LLM_URL: str = os.getenv("CUSTOM_LLM_URL", "")
CUSTOM_LLM_MODEL: str = os.getenv("CUSTOM_LLM_MODEL", "mistral-small-latest")

# --- Guardrail ---
# Số buổi tối thiểu cho 1 bài trước khi agent dám kết luận về trend (thin-spec §7).
MIN_SESSIONS: int = int(os.getenv("AGENT_MIN_SESSIONS", "3"))

# Khi True, các tool dùng mock data thay vì Supabase thật (Backend chưa cắm).
USE_MOCK_TOOLS: bool = os.getenv("AGENT_USE_MOCK_TOOLS", "1") == "1"


def llm_enabled() -> bool:
    """Có LLM để gọi không (OpenRouter HOẶC custom). Không thì chạy template offline."""
    return bool(OPENROUTER_API_KEY or CUSTOM_LLM_KEY)


# Cấu hình logging ngay khi import (an toàn nếu gọi nhiều lần — idempotent).
from agent.logging_config import setup_logging  # noqa: E402

setup_logging()
