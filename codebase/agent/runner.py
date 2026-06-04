"""Public API cho UI — Streamlit import thẳng, không cần HTTP.

    from agent.runner import chat, resume

    out = chat(user_id="demo-user", conversation_id="c1",
               message="Bench Press của tôi có tiến bộ không?")
    print(out["reply"])

Khi out["status"] == "awaiting_confirm" (luồng tạo routine), UI hiện preview
out["routine"] + nút Confirm/Cancel rồi gọi resume(...).
"""
from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from agent.graph import build_graph

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


def chat(user_id: str, conversation_id: str, message: str) -> dict[str, Any]:
    cfg = {"configurable": {"thread_id": conversation_id}}
    result = _graph.invoke(
        {"messages": [HumanMessage(content=message)], "user_id": user_id}, cfg
    )
    return _format(result)


def resume(conversation_id: str, approved: bool, edits: dict | None = None) -> dict[str, Any]:
    """Tiếp tục luồng tạo routine sau khi user bấm Confirm/Cancel."""
    cfg = {"configurable": {"thread_id": conversation_id}}
    result = _graph.invoke(
        Command(resume={"approved": approved, "edits": edits}), cfg
    )
    return _format(result)
