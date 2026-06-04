"""Test agent workflow — chạy OFFLINE (không cần OPENROUTER_API_KEY).

Bao phủ:
  - Phân tích thuần (analysis.py): 1RM, trend, plateau, muscle gap
  - 4 failure paths (thin-spec §6): happy / low-confidence / failure / correction
  - Guardrail: chưa đủ buổi -> không kết luận; disclaimer xuất hiện
  - Luồng create_routine với interrupt + resume

Chạy:  pytest agent/tests -q   (hoặc: python -m agent.tests.test_agent)
"""
from __future__ import annotations

import uuid

from agent import analysis, tools
from agent.runner import chat, resume


def _cid() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


# --------------------------- analysis (pure) ------------------------------- #
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


# --------------------------- 4 failure paths ------------------------------- #
def test_happy_path():
    out = chat("demo-user", _cid(), "Bench Press của tôi có tiến bộ không?")
    assert out["status"] == "ok"
    assert out["intent"] == "analyze"
    assert "Bench Press" in out["reply"]
    assert "kg" in out["reply"]            # có số liệu thật
    assert "⚠️" in out["reply"]            # guardrail disclaimer


def test_low_confidence_path():
    out = chat("demo-user", _cid(), "tôi tập tốt không?")
    assert out["status"] == "ok"
    assert out["intent"] == "clarify"
    assert "?" in out["reply"]


def test_failure_path_unknown_exercise():
    out = chat("demo-user", _cid(), "Pull Up của tôi tiến bộ không?")
    # Pull Up không có trong catalog -> không trích được bài -> hỏi lại,
    # hoặc nếu trích được mà rỗng data -> báo chưa log. Cả hai đều không bịa số.
    assert out["status"] == "ok"
    assert "kg →" not in out["reply"]


def test_correction_path_keeps_context():
    cid = _cid()
    chat("demo-user", cid, "Squat của tôi thế nào?")
    out = chat("demo-user", cid, "à tháng trước tôi nghỉ ốm nên đừng tính")
    # Vẫn trả lời được, không lỗi (memory theo thread_id hoạt động).
    assert out["status"] == "ok"
    assert out["reply"]


# --------------------------- guardrail ------------------------------------- #
def test_guardrail_insufficient_data():
    out = chat("new-user", _cid(), "Bench Press của tôi có tiến bộ không?")
    assert out["status"] == "ok"
    assert "chưa đủ" in out["reply"].lower() or "buổi" in out["reply"].lower()
    assert "⚠️" not in out["reply"]        # không khuyên khi thiếu data


# --------------------------- create_routine (interrupt) -------------------- #
def test_create_routine_confirm_flow():
    cid = _cid()
    out = chat("demo-user", cid, "tạo routine giúp tôi và lưu vào app")
    assert out["status"] == "awaiting_confirm"
    assert out["routine"]["exercises"]

    done = resume(cid, approved=True)
    assert done["status"] == "ok"
    assert "Đã lưu" in done["reply"]


def test_create_routine_cancel_flow():
    cid = _cid()
    chat("demo-user", cid, "tạo routine và lưu vào app nhé")
    out = resume(cid, approved=False)
    assert out["status"] == "ok"
    assert "huỷ" in out["reply"].lower() or "hủy" in out["reply"].lower()


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
