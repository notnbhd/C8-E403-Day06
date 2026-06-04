"""Tool layer — INTERFACE CONTRACT (docs/agent-workflow §5).

Đây là *hợp đồng* giữa Agent và 2 team kia. Agent CHỈ gọi qua các signature dưới
đây và không quan tâm bên trong là Supabase hay vector search.

Hiện tại: implementation MOCK (deterministic) để chạy end-to-end ngày 1.
=> Backend thay 5 hàm get_*/create_routine bằng Supabase query.
=> RAG thay search_fitness_knowledge bằng vector search.
   Giữ NGUYÊN tên + input + shape output là không cần đổi gì phía Agent.

Hợp đồng lỗi (§5.4):
  - Không có data  -> trả [] / {} (KHÔNG raise). Agent tự lo failure path.
  - Lỗi hệ thống   -> raise ToolError.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from agent import config
from agent.analysis import set_volume


class ToolError(RuntimeError):
    """Lỗi hệ thống khi gọi tool (DB down, ghi thất bại...)."""


# --------------------------------------------------------------------------- #
# MOCK DATA  (Backend xoá phần này khi cắm Supabase thật)
# --------------------------------------------------------------------------- #
_ANCHOR = date(2026, 6, 4)  # "hôm nay" cho mock

EXERCISE_CATALOG: list[dict[str, str]] = [
    {"exercise_id": "ex_bench", "name": "Bench Press", "muscle_group": "chest"},
    {"exercise_id": "ex_incline", "name": "Incline Dumbbell Press", "muscle_group": "chest"},
    {"exercise_id": "ex_squat", "name": "Squat", "muscle_group": "legs"},
    {"exercise_id": "ex_dead", "name": "Deadlift", "muscle_group": "back"},
    {"exercise_id": "ex_row", "name": "Barbell Row", "muscle_group": "back"},
    {"exercise_id": "ex_ohp", "name": "Overhead Press", "muscle_group": "shoulders"},
    {"exercise_id": "ex_curl", "name": "Bicep Curl", "muscle_group": "arms"},
    {"exercise_id": "ex_pulldown", "name": "Lat Pulldown", "muscle_group": "back"},
]
_NAME_BY_ID = {e["exercise_id"]: e["name"] for e in EXERCISE_CATALOG}
_GROUP_BY_NAME = {e["name"]: e["muscle_group"] for e in EXERCISE_CATALOG}


def _sets_for(name: str, weeks: list[float], reps: int, sets_per_session: int = 3):
    """Tạo các set: mỗi tuần 1 buổi, lùi từ _ANCHOR. weeks[i] = top weight tuần i."""
    out: list[dict[str, Any]] = []
    n = len(weeks)
    for i, w in enumerate(weeks):
        d = _ANCHOR - timedelta(days=(n - 1 - i) * 7)
        for sn in range(1, sets_per_session + 1):
            out.append({
                "date": d.isoformat(),
                "exercise_name": name,
                "weight_kg": w,
                "reps": reps,
                "set_number": sn,
            })
    return out


# demo-user: bench tiến bộ, squat plateau, lưng/legs bị bỏ bê (muscle gap).
_MOCK_HISTORY: dict[str, list[dict[str, Any]]] = {
    "demo-user": (
        _sets_for("Bench Press", [60, 60, 62.5, 65, 65, 67.5, 70, 72.5], reps=5)
        + _sets_for("Squat", [100, 100, 100, 100], reps=5)  # 4 tuần đứng yên
        + _sets_for("Overhead Press", [40, 40, 42.5], reps=5)
        + _sets_for("Barbell Row", [50], reps=8)             # chỉ 1 buổi -> back bị bỏ bê rõ
    ),
    # user mới, chưa đủ data -> để test guardrail "đủ buổi chưa".
    "new-user": _sets_for("Bench Press", [50, 52.5], reps=5),
}

# routine đã ghi (mock của bảng Supabase `routines`).
_ROUTINE_STORE: list[dict[str, Any]] = []
_routine_seq = 0


# --------------------------------------------------------------------------- #
# CONTRACT §5.2 — Backend (Supabase)
# --------------------------------------------------------------------------- #
def get_workout_history(
    user_id: str,
    exercise_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """Các set đã log, sort theo date tăng dần. [] nếu không có."""
    rows = list(_MOCK_HISTORY.get(user_id, []))
    if exercise_name:
        key = exercise_name.strip().lower()
        rows = [r for r in rows if r["exercise_name"].lower() == key]
    if start_date:
        rows = [r for r in rows if r["date"] >= start_date]
    if end_date:
        rows = [r for r in rows if r["date"] <= end_date]
    return sorted(rows, key=lambda r: r["date"])


def get_exercise_summary(user_id: str) -> list[dict[str, Any]]:
    """Mỗi bài: {exercise_name, last_performed, total_volume_kg, session_count}."""
    rows = _MOCK_HISTORY.get(user_id, [])
    agg: dict[str, dict[str, Any]] = {}
    for r in rows:
        a = agg.setdefault(r["exercise_name"], {
            "exercise_name": r["exercise_name"],
            "last_performed": r["date"],
            "total_volume_kg": 0.0,
            "_days": set(),
        })
        a["total_volume_kg"] += set_volume(r)
        a["last_performed"] = max(a["last_performed"], r["date"])
        a["_days"].add(r["date"])
    out = []
    for a in agg.values():
        a["session_count"] = len(a.pop("_days"))
        a["total_volume_kg"] = round(a["total_volume_kg"], 0)
        out.append(a)
    return out


def get_muscle_group_volume(user_id: str, time_range_days: int = 28) -> dict[str, float]:
    """{muscle_group: total_volume_kg} trong N ngày gần nhất. {} nếu không có."""
    cutoff = (_ANCHOR - timedelta(days=time_range_days)).isoformat()
    vols: dict[str, float] = {}
    for r in _MOCK_HISTORY.get(user_id, []):
        if r["date"] < cutoff:
            continue
        group = _GROUP_BY_NAME.get(r["exercise_name"], "other")
        vols[group] = vols.get(group, 0.0) + set_volume(r)
    return vols


def list_exercise_catalog() -> list[dict[str, str]]:
    """Danh mục bài để map tên -> exercise_id khi tạo routine."""
    return list(EXERCISE_CATALOG)


def create_routine(user_id: str, routine: dict[str, Any]) -> dict[str, Any]:
    """GHI routine vào store (mock Supabase). CHỈ gọi sau khi user confirm.

    routine = {name, exercises:[{exercise_id, sets, reps, rest_sec}]}
    return {routine_id}
    """
    global _routine_seq
    if not routine.get("exercises"):
        raise ToolError("Routine rỗng, không có bài tập.")
    _routine_seq += 1
    rid = f"rt_{_routine_seq:04d}"
    _ROUTINE_STORE.append({"routine_id": rid, "user_id": user_id, **routine})
    return {"routine_id": rid}


# --------------------------------------------------------------------------- #
# CONTRACT §5.3 — RAG
# --------------------------------------------------------------------------- #
_KB = [
    ("progressive overload", "Tăng tải từ từ: khi đạt rep mục tiêu ở tất cả set với form tốt "
     "thì tăng 2.5kg (thân trên) hoặc 5kg (thân dưới)."),
    ("plateau deload", "Khi chững ≥3 tuần, thử deload 10% rồi build lại, hoặc đổi rep range."),
    ("hypertrophy rep range", "Phì đại cơ tối ưu ở 6–12 reps, 10–20 set/nhóm cơ mỗi tuần."),
    ("muscle balance", "Giữ cân bằng đẩy/kéo và trên/dưới để tránh mất cân bằng và chấn thương."),
]


def search_fitness_knowledge(query: str, k: int = 4) -> list[dict[str, str]]:
    """Vector search trên tài liệu fitness. Hiện mock bằng keyword overlap."""
    q = set(query.lower().split())
    scored = []
    for topic, text in _KB:
        score = len(q & set(topic.split()))
        scored.append((score, topic, text))
    scored.sort(reverse=True)
    return [{"text": t, "source": topic} for sc, topic, t in scored[:k]]


def resolve_exercise(name: str) -> dict[str, str] | None:
    """Tiện ích: tìm bài trong catalog theo tên (fuzzy nhẹ)."""
    key = name.strip().lower()
    for e in EXERCISE_CATALOG:
        if e["name"].lower() == key or key in e["name"].lower():
            return e
    return None
