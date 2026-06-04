"""Graph nodes — docs/agent-workflow §3.

Mỗi branch node: gọi tool -> tính analysis (Python) -> dựng `draft` chứa số liệu thật.
guardrail: kiểm tra đủ data + thêm disclaimer sức khỏe.
respond: (tuỳ chọn) LLM diễn đạt lại draft, rồi append vào messages.
"""
from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt

from agent import analysis, config, llm, tools
from agent.state import AgentState

DISCLAIMER = (
    "⚠️ Gợi ý dựa trên dữ liệu tập của bạn, không thay thế PT/bác sĩ. "
    "Nếu đang mệt hoặc có chấn thương, hãy ưu tiên hồi phục trước."
)


def _last_human(state: AgentState) -> str:
    for msg in reversed(state.get("messages", [])):
        if isinstance(msg, HumanMessage):
            return msg.content
        if isinstance(msg, dict) and msg.get("role") == "user":
            return msg.get("content", "")
    return ""


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
def router(state: AgentState) -> dict[str, Any]:
    msg = _last_human(state)
    intent = llm.classify_intent(msg)
    names = [e["name"] for e in tools.list_exercise_catalog()]
    target = llm.extract_exercise(msg, names)
    # Hỏi về 1 bài cụ thể nhưng câu lại chung chung -> vẫn analyze.
    return {"intent": intent, "target_exercise": target}


def route_intent(state: AgentState) -> str:
    """Conditional edge: map intent -> tên node."""
    return {
        "analyze": "analyze",
        "plateau": "analyze",
        "progression": "analyze",
        "muscle_gap": "muscle_gap",
        "build_plan": "build_plan",
        "create_routine": "create_routine",
        "clarify": "clarify",
        "general": "general",
    }.get(state.get("intent", "general"), "general")


# --------------------------------------------------------------------------- #
# Branch: analyze / plateau / progression  (đều xoay quanh 1 bài)
# --------------------------------------------------------------------------- #
def analyze(state: AgentState) -> dict[str, Any]:
    user_id = state["user_id"]
    intent = state.get("intent", "analyze")
    exercise = state.get("target_exercise")

    # Không xác định được bài -> chuyển sang hỏi lại (low-confidence path).
    if not exercise:
        return {
            "draft": "Bạn muốn mình kiểm tra bài nào cụ thể? (vd: Bench Press, Squat...) "
                     "Hoặc bạn muốn xem tổng quan nhóm cơ nào đang bị bỏ bê?",
            "data_sufficient": False,
        }

    sets = tools.get_workout_history(user_id, exercise_name=exercise)

    # Failure path: chưa có data bài này.
    if not sets:
        return {
            "workout_data": {"sets": []},
            "draft": f"Mình không thấy dữ liệu cho **{exercise}** trong lịch sử của bạn. "
                     f"Bạn đã log bài này trong Hevy chưa?",
            "data_sufficient": False,
        }

    trend = analysis.trend_summary(sets)
    plateau = analysis.detect_plateau(sets)
    enough = trend["sessions"] >= config.MIN_SESSIONS

    a = {"exercise": exercise, "trend": trend, "plateau": plateau}

    # Guardrail "đủ buổi": chưa đủ thì không kết luận.
    if not enough:
        return {
            "workout_data": {"sets": sets}, "analysis": a, "data_sufficient": False,
            "draft": f"Bạn mới có {trend['sessions']} buổi {exercise} — chưa đủ để kết luận "
                     f"xu hướng đáng tin (cần ≥ {config.MIN_SESSIONS}). Cứ log thêm vài buổi nữa nhé!",
        }

    if intent == "plateau":
        if plateau["plateau"]:
            draft = (f"**{exercise}** của bạn đang chững: {plateau['window_weeks']} tuần gần nhất "
                     f"1RM ước tính dao động quanh {plateau['stuck_at_1rm']}kg "
                     f"(biên độ chỉ {plateau['spread_pct']}%).")
            kb = tools.search_fitness_knowledge("plateau deload")
            if kb:
                draft += f" Gợi ý: {kb[0]['text']}"
        else:
            draft = (f"**{exercise}** chưa bị plateau — 1RM ước tính vẫn nhúc nhích "
                     f"(biên độ {plateau['spread_pct']}% trong {plateau['window_weeks']} tuần gần nhất).")
    elif intent == "progression":
        kb = tools.search_fitness_knowledge("progressive overload")
        tip = kb[0]["text"] if kb else ""
        if plateau["plateau"]:
            draft = (f"**{exercise}** đang đứng ở ~{plateau['stuck_at_1rm']}kg 1RM "
                     f"{plateau['window_weeks']} tuần liền — thời điểm hợp lý để đẩy tải. {tip}")
        else:
            draft = (f"**{exercise}** vẫn đang lên ({trend['pct_change']:+}% gần đây) — cứ giữ đà. "
                     f"Nguyên tắc tăng tải: {tip}")
    else:  # analyze
        arrow = {"up": "tiến bộ tốt 📈", "down": "đang đi xuống 📉", "flat": "đang đi ngang"}
        draft = (f"**{exercise}**: 1RM ước tính đi từ {trend['first_1rm']}kg → {trend['last_1rm']}kg "
                 f"qua {trend['weeks']} tuần ({trend['pct_change']:+}%, {trend['delta_kg']:+}kg) — "
                 f"{arrow.get(trend['direction'], '')}.")

    return {"workout_data": {"sets": sets}, "analysis": a, "data_sufficient": enough, "draft": draft}


# --------------------------------------------------------------------------- #
# Branch: muscle_gap
# --------------------------------------------------------------------------- #
def muscle_gap(state: AgentState) -> dict[str, Any]:
    user_id = state["user_id"]
    vols = tools.get_muscle_group_volume(user_id, time_range_days=28)
    if not vols:
        return {"draft": "Mình chưa thấy buổi tập nào trong 4 tuần gần đây để phân tích nhóm cơ.",
                "data_sufficient": False}

    gap = analysis.muscle_gap(vols)
    if gap["balanced"]:
        draft = "Các nhóm cơ của bạn 4 tuần qua khá cân bằng 👍 Không có nhóm nào bị bỏ rõ rệt."
    else:
        worst = gap["gaps"][0]
        draft = (f"Nhóm cơ đang bị bỏ bê nhất là **{worst['group']}** "
                 f"(chỉ ~{int(worst['ratio'] * 100)}% volume so với '{gap['top_group']}'). ")
        kb = tools.search_fitness_knowledge("muscle balance")
        if kb:
            draft += kb[0]["text"]
    return {"analysis": {"muscle_gap": gap}, "data_sufficient": True, "draft": draft}


# --------------------------------------------------------------------------- #
# Branch: build_plan (P1) + create_routine (P1, có confirm)
# --------------------------------------------------------------------------- #
def _draft_routine(user_id: str) -> dict[str, Any]:
    """Dựng một routine mẫu dựa trên muscle gap (ưu tiên nhóm bị bỏ bê)."""
    catalog = tools.list_exercise_catalog()
    gap = analysis.muscle_gap(tools.get_muscle_group_volume(user_id))
    weak = {g["group"] for g in gap.get("gaps", [])}
    picks = [e for e in catalog if e["muscle_group"] in weak] or catalog[:4]
    exercises = [
        {"exercise_id": e["exercise_id"], "name": e["name"],
         "sets": 3, "reps": "8-12", "rest_sec": 90}
        for e in picks[:5]
    ]
    return {"name": "Routine cân bằng nhóm cơ", "exercises": exercises}


def build_plan(state: AgentState) -> dict[str, Any]:
    routine = _draft_routine(state["user_id"])
    lines = "\n".join(f"  • {e['name']} — {e['sets']}×{e['reps']} (nghỉ {e['rest_sec']}s)"
                      for e in routine["exercises"])
    draft = (f"Mình đề xuất **{routine['name']}**:\n{lines}\n\n"
             f"Muốn mình lưu routine này vào app không?")
    return {"pending_routine": routine, "data_sufficient": True, "draft": draft}


def create_routine(state: AgentState) -> dict[str, Any]:
    """Augmentation: dừng lại chờ user confirm (interrupt) rồi mới ghi."""
    routine = state.get("pending_routine") or _draft_routine(state["user_id"])

    # interrupt() -> graph dừng, UI hiện preview + nút Confirm/Cancel,
    # rồi resume bằng Command(resume={"approved": bool, "edits": ...}).
    decision = interrupt({"type": "routine_preview", "routine": routine})

    if not decision or not decision.get("approved"):
        return {"draft": "Đã huỷ — chưa lưu routine nào. Bạn muốn chỉnh gì không?"}

    routine = decision.get("edits") or routine
    try:
        res = tools.create_routine(state["user_id"], routine)
    except tools.ToolError as e:
        return {"draft": f"Lưu routine thất bại ({e}). Bạn thử lại giúp mình nhé."}
    return {"pending_routine": None,
            "draft": f"✅ Đã lưu **{routine['name']}** (id `{res['routine_id']}`) vào app của bạn."}


# --------------------------------------------------------------------------- #
# Branch: clarify / general
# --------------------------------------------------------------------------- #
def clarify(state: AgentState) -> dict[str, Any]:
    return {"draft": "Mình chưa rõ ý bạn lắm 🤔 Bạn muốn kiểm tra **bài cụ thể** "
                     "(vd 'Bench Press có tiến bộ không?'), **plateau**, hay **nhóm cơ bỏ bê**?",
            "data_sufficient": False}


def general(state: AgentState) -> dict[str, Any]:
    return {"draft": "Mình là coach AI đọc dữ liệu Hevy của bạn. Mình có thể:\n"
                     "  • Xem một bài có tiến bộ không\n"
                     "  • Phát hiện bạn có đang plateau\n"
                     "  • Chỉ ra nhóm cơ đang bị bỏ bê\n"
                     "  • Gợi ý khi nào nên tăng tạ\n"
                     "Bạn muốn bắt đầu với cái nào?",
            "data_sufficient": True}


# --------------------------------------------------------------------------- #
# Guardrail + Respond
# --------------------------------------------------------------------------- #
_ADVICE_INTENTS = {"analyze", "plateau", "progression", "muscle_gap", "build_plan"}


def guardrail(state: AgentState) -> dict[str, Any]:
    """Thêm disclaimer sức khỏe cho các câu trả lời mang tính khuyên (thin-spec §7)."""
    intent = state.get("intent", "general")
    if intent in _ADVICE_INTENTS and state.get("data_sufficient"):
        return {"disclaimer": DISCLAIMER}
    return {}


def respond(state: AgentState) -> dict[str, Any]:
    draft = state.get("draft") or "Xin lỗi, mình chưa xử lý được yêu cầu này."
    text = llm.polish(draft)
    if state.get("disclaimer"):
        text = f"{text}\n\n{state['disclaimer']}"
    return {"messages": [AIMessage(content=text)]}
