"""Public API cho UI — Streamlit import thẳng, không cần HTTP.

    from agent.runner import chat, resume

    out = chat(user_id="demo-user", conversation_id="c1",
               message="Bench Press của tôi có tiến bộ không?")
    print(out["reply"])

Khi out["status"] == "awaiting_confirm" (luồng tạo routine), UI hiện preview
out["routine"] + nút Confirm/Cancel rồi gọi resume(...).
"""
from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from agent.graph import build_graph
from agent.logging_config import preview

log = logging.getLogger("agent.runner")

# Một checkpointer in-memory cho cả tiến trình (giữ memory theo thread_id).
# Production: thay bằng PostgresSaver(Supabase) — xem docs §3.
_checkpointer = MemorySaver()
_graph = None  # build lazy: tránh raise lúc import khi chưa có LLM key (vd pytest offline).


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph(checkpointer=_checkpointer)
    return _graph


def _last_ai_text(result: dict[str, Any]) -> str:
    """Nội dung AIMessage cuối có text (bỏ qua message chỉ chứa tool_calls)."""
    for msg in reversed(result.get("messages", [])):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return ""


def _format(result: dict[str, Any]) -> dict[str, Any]:
    """Chuẩn hoá output graph -> payload cho UI."""
    interrupts = result.get("__interrupt__")
    if interrupts:
        payload = interrupts[0].value
        # Text LLM viết NGAY TRONG message gọi save_routine (giải thích 'vì sao + cách
        # tập') -> hiện phía trên thẻ xác nhận. None nếu LLM không kèm lời nào.
        return {
            "status": "awaiting_confirm",
            "type": payload.get("type"),
            "routine": payload.get("routine"),
            "reply": _last_ai_text(result) or None,
        }
    return {"status": "ok", "reply": _last_ai_text(result)}


def _log_out(t0: float, out: dict[str, Any]) -> None:
    dt = (time.perf_counter() - t0) * 1000
    if out["status"] == "awaiting_confirm":
        name = (out.get("routine") or {}).get("name")
        log.info("◀ status=awaiting_confirm routine=%r (%.0fms)", name, dt)
    else:
        log.info("◀ status=%s reply=%r (%.0fms)",
                 out["status"], preview(out.get("reply")), dt)


def chat(user_id: str, conversation_id: str, message: str) -> dict[str, Any]:
    log.info("▶ chat user=%s conv=%s msg=%r", user_id, conversation_id, preview(message))
    t0 = time.perf_counter()
    cfg = {"configurable": {"thread_id": conversation_id}}
    result = _get_graph().invoke(
        {"messages": [HumanMessage(content=message)], "user_id": user_id}, cfg
    )
    out = _format(result)
    _log_out(t0, out)
    return out


def resume(conversation_id: str, approved: bool, edits: dict | None = None) -> dict[str, Any]:
    """Tiếp tục luồng tạo routine sau khi user bấm Confirm/Cancel."""
    log.info("▶ resume conv=%s approved=%s", conversation_id, approved)
    t0 = time.perf_counter()
    cfg = {"configurable": {"thread_id": conversation_id}}
    result = _get_graph().invoke(
        Command(resume={"approved": approved, "edits": edits}), cfg
    )
    out = _format(result)
    _log_out(t0, out)
    return out
