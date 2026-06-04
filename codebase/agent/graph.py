"""ReAct agent (create_react_agent) — LLM tự chọn tool.

Quyết định kiến trúc: ReAct TỰ DO thay cho router tường minh + branch node cũ.
LLM tự suy luận gọi tool nào (xem react_tools.TOOLS). Grounding vẫn giữ nguyên:
mọi con số do Python tính bên trong tool, LLM không bịa.

BẮT BUỘC có LLM key (OPENROUTER_API_KEY hoặc CUSTOM_LLM_KEY) — không còn chế độ
offline/template. Luồng tạo routine vẫn human-in-the-loop qua interrupt() trong
tool save_routine.
"""
from __future__ import annotations

from langgraph.prebuilt import create_react_agent

from agent import llm
from agent.react_tools import SYSTEM_PROMPT, TOOLS, CoachState


def build_graph(checkpointer=None):
    """Dựng & compile ReAct agent. Truyền checkpointer để có memory + interrupt/resume."""
    model = llm.get_llm()
    if model is None:
        raise RuntimeError(
            "ReAct agent cần LLM. Hãy set OPENROUTER_API_KEY hoặc CUSTOM_LLM_KEY "
            "(xem agent/config.py)."
        )
    return create_react_agent(
        model,
        TOOLS,
        prompt=SYSTEM_PROMPT,
        state_schema=CoachState,
        checkpointer=checkpointer,
    )
