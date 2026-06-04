"""LLM provider cho ReAct agent — OpenRouter hoặc custom (OpenAI-compatible).

ReAct dùng MỘT model có tool-calling; toàn bộ phân loại intent / diễn đạt giờ do
chính LLM lo trong vòng lặp ReAct (không còn router keyword / polish thủ công).
"""
from __future__ import annotations

import logging

from agent import config

log = logging.getLogger("agent.llm")

_LLM = None  # cache


def get_llm():
    """ChatOpenAI (OpenRouter hoặc custom). None nếu chưa cấu hình key nào."""
    global _LLM
    if not config.llm_enabled():
        return None
    if _LLM is None:
        from langchain_openai import ChatOpenAI

        if config.OPENROUTER_API_KEY:
            _LLM = ChatOpenAI(
                model=config.AGENT_MODEL,
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL,
                temperature=config.LLM_TEMPERATURE,
            )
            log.info("LLM: provider=openrouter model=%s", config.AGENT_MODEL)
        else:  # fallback: custom LLM (vd Mistral/gpt-4o-mini) đã cấu hình cho RAG chatbot
            _LLM = ChatOpenAI(
                model=config.CUSTOM_LLM_MODEL,
                api_key=config.CUSTOM_LLM_KEY,
                base_url=config.CUSTOM_LLM_URL or None,
                temperature=config.LLM_TEMPERATURE,
            )
            log.info("LLM: provider=custom model=%s url=%s",
                     config.CUSTOM_LLM_MODEL, config.CUSTOM_LLM_URL)
    return _LLM
