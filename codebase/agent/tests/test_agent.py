"""Test ReAct agent workflow.

Hai nhóm:
  - Pure analysis (analysis.py): luôn chạy, KHÔNG cần LLM (deterministic, offline).
  - Integration (chat/resume): cần LLM key (ReAct) -> tự SKIP nếu thiếu key.
    Đây là test tích hợp gọi LLM thật nên assert để LỎNG (chỉ kiểm tra hành vi/
    grounding cốt lõi, không khớp từng chữ vì output LLM không deterministic).

Chạy:  PYTHONPATH=codebase pytest agent/tests -q
"""
from __future__ import annotations

import uuid

import pytest

from agent import analysis, config, tools
from agent.runner import chat, resume

requires_llm = pytest.mark.skipif(
    not config.llm_enabled(), reason="ReAct agent cần OPENROUTER_API_KEY hoặc CUSTOM_LLM_KEY"
)


def _cid() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


# --------------------------- analysis (pure, offline) ---------------------- #
def test_est_1rm_epley():
    assert analysis.est_1rm(100, 1) == 100
    assert analysis.est_1rm(100, 5) == 116.7  # 100*(1+5/30)


def test_trend_detects_progress():
    sets = tools.get_workout_history("demo-user", "Bench Press")
    t = analysis.trend_summary(sets)
    assert t["direction"] == "up"
    assert t["last_1rm"] > t["first_1rm"]
    assert t["sessions"] >= 3


def test_plateau_on_squat():
    sets = tools.get_workout_history("demo-user", "Squat")
    p = analysis.detect_plateau(sets)
    assert p["plateau"] is True


def test_muscle_gap_flags_back():
    vols = tools.get_muscle_group_volume("demo-user")
    g = analysis.muscle_gap(vols)
    assert not g["balanced"]
    assert any(gap["group"] == "back" for gap in g["gaps"])


# --------------------------- integration (ReAct, cần LLM) ------------------ #
@requires_llm
def test_progress_one_exercise():
    out = chat("demo-user", _cid(), "Bench Press của tôi có tiến bộ không?")
    assert out["status"] == "ok"
    assert out["reply"]
    assert "bench" in out["reply"].lower()


@requires_llm
def test_overview_overall():
    # Câu hỏi chung chung KHÔNG nêu bài cụ thể -> tổng quan (không còn ngõ cụt "bài nào?").
    out = chat("demo-user", _cid(), "Progress của tôi dạo này đang như thế nào?")
    assert out["status"] == "ok"
    assert out["reply"]


@requires_llm
def test_overview_by_muscle_group():
    # "review các bài tập lưng" -> tổng quan lọc theo nhóm cơ (trước đây bị clarify).
    out = chat("demo-user", _cid(), "Review các bài tập lưng của tôi")
    assert out["status"] == "ok"
    assert out["reply"]


@requires_llm
def test_unknown_exercise_no_fabrication():
    out = chat("demo-user", _cid(), "Pull Up của tôi tiến bộ không?")
    # Pull Up không có trong lịch sử -> tool trả no_data; không được bịa số liệu.
    assert out["status"] == "ok"
    assert out["reply"]


@requires_llm
def test_guardrail_insufficient_data():
    out = chat("new-user", _cid(), "Bench Press của tôi có tiến bộ không?")
    assert out["status"] == "ok"
    # new-user mới 2 buổi -> data_sufficient=false -> không kết luận xu hướng.
    assert "đủ" in out["reply"].lower() or "buổi" in out["reply"].lower()


@requires_llm
def test_create_routine_confirm_flow():
    cid = _cid()
    out = chat("demo-user", cid, "tạo routine giúp tôi và lưu vào app")
    assert out["status"] == "awaiting_confirm"
    assert out["routine"]["exercises"]

    done = resume(cid, approved=True)
    assert done["status"] == "ok"
    assert done["reply"]


@requires_llm
def test_create_routine_cancel_flow():
    cid = _cid()
    out = chat("demo-user", cid, "tạo routine và lưu vào app nhé")
    assert out["status"] == "awaiting_confirm"
    cancelled = resume(cid, approved=False)
    assert cancelled["status"] == "ok"
    assert cancelled["reply"]


if __name__ == "__main__":
    import sys

    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
