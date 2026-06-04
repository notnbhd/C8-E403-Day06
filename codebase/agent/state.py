"""LangGraph state schema — xem docs/agent-workflow §3."""
from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph.message import add_messages

Intent = Literal[
    "analyze",        # bài này có tiến bộ không
    "plateau",        # có đang chững không
    "muscle_gap",     # nhóm cơ nào bỏ bê
    "progression",    # khi nào nên tăng tạ
    "build_plan",     # build workout plan (P1)
    "create_routine", # ghi routine vào Supabase, có confirm (P1)
    "knowledge",      # hỏi kiến thức tập luyện chung -> RAG trên tài liệu
    "clarify",        # query mơ hồ -> hỏi lại
    "general",        # chitchat / giới thiệu năng lực
]


class AgentState(TypedDict, total=False):
    # Lịch sử hội thoại (reducer add_messages tự gộp).
    messages: Annotated[list, add_messages]

    # Định danh user (UI truyền vào).
    user_id: str

    # Kết quả router.
    intent: Intent
    target_exercise: str | None   # bài user nhắc tới (nếu có)

    # Dữ liệu lấy từ tool.
    workout_data: dict[str, Any] | None
    knowledge: list[dict[str, Any]] | None

    # Phân tích đã tính bằng Python (grounded — không để LLM bịa số).
    analysis: dict[str, Any] | None

    # Guardrail.
    data_sufficient: bool
    disclaimer: str | None

    # Luồng ghi (create_routine) — chờ user confirm.
    pending_routine: dict[str, Any] | None

    # Draft câu trả lời do branch node dựng (chứa số liệu thật).
    draft: str | None

    # True khi draft đã là câu trả lời cuối (vd RAG) -> respond không polish lại.
    no_polish: bool
