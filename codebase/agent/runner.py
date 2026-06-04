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
_graph = build_graph(checkpointer=_checkpointer)


def _format(result: dict[str, Any]) -> dict[str, Any]:
    """Chuẩn hoá output graph -> payload cho UI."""
    interrupts = result.get("__interrupt__")
    if interrupts:
        payload = interrupts[0].value
        return {
            "status": "awaiting_confirm",
            "type": payload.get("type"),
            "routine": payload.get("routine"),
            "reply": None,
        }
    reply = ""
    for msg in reversed(result.get("messages", [])):
        if isinstance(msg, AIMessage):
            reply = msg.content
            break
    return {"status": "ok", "reply": reply, "intent": result.get("intent")}


def _log_out(t0: float, out: dict[str, Any]) -> None:
    dt = (time.perf_counter() - t0) * 1000
    if out["status"] == "awaiting_confirm":
        name = (out.get("routine") or {}).get("name")
        log.info("◀ status=awaiting_confirm routine=%r (%.0fms)", name, dt)
    else:
        log.info("◀ status=%s intent=%s reply=%r (%.0fms)",
                 out["status"], out.get("intent"), preview(out.get("reply")), dt)


def chat(user_id: str, conversation_id: str, message: str) -> dict[str, Any]:
    log.info("▶ chat user=%s conv=%s msg=%r", user_id, conversation_id, preview(message))
    t0 = time.perf_counter()
    cfg = {"configurable": {"thread_id": conversation_id}}
    result = _graph.invoke(
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
    result = _graph.invoke(
        Command(resume={"approved": approved, "edits": edits}), cfg
    )
    out = _format(result)
    _log_out(t0, out)
    return out
