"""Demo server cho webapp Hevy (codebase/frontend).

Phục vụ index.html/styles.css/app.js + REST API /api/* mà app.js gọi.
Dữ liệu lấy từ agent MOCK tools => chạy OFFLINE, KHÔNG cần Supabase / API key.

Chạy:
    PYTHONPATH=codebase uvicorn frontend.server:app --reload --port 8000
hoặc đơn giản:
    python codebase/frontend/server.py
=> mở http://localhost:8000
"""
from __future__ import annotations

import sys
from collections import OrderedDict, defaultdict
from datetime import date, timedelta
from pathlib import Path

# Cho phép `import agent` khi chạy trực tiếp file này (codebase/ lên sys.path).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import analysis, runner, tools

FRONTEND_DIR = Path(__file__).resolve().parent

# Tên hiển thị cho demo (mock không có bảng users).
_DISPLAY_NAME = {"demo-user": "Alex Nguyen", "new-user": "Newbie"}

app = FastAPI(title="Hevy AI — Demo webapp")


# --------------------------------------------------------------------------- #
# Chat (nối thẳng agent.runner)
# --------------------------------------------------------------------------- #
class ChatIn(BaseModel):
    user_id: str
    conversation_id: str
    message: str


class ResumeIn(BaseModel):
    conversation_id: str
    approved: bool
    edits: dict | None = None


@app.post("/api/chat")
def chat(body: ChatIn) -> dict:
    return runner.chat(body.user_id, body.conversation_id, body.message)


@app.post("/api/chat/resume")
def chat_resume(body: ResumeIn) -> dict:
    return runner.resume(body.conversation_id, body.approved, body.edits)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _name(user_id: str) -> str:
    u = tools.get_user(user_id)
    if u and u.get("display_name"):
        return u["display_name"]
    return _DISPLAY_NAME.get(user_id, "Athlete")


def _group_map() -> dict[str, str]:
    """{exercise_name: muscle_group} từ catalog."""
    return {e["name"]: e.get("muscle_group", "other") for e in tools.list_exercise_catalog()}


def _distinct_days(sets: list[dict]) -> set[str]:
    return {s["date"] for s in sets}


def _minus_days(iso_date: str, days: int) -> str:
    y, m, d = map(int, iso_date.split("-"))
    return (date(y, m, d) - timedelta(days=days)).isoformat()


def _fmt_duration(minutes: int) -> str:
    minutes = int(round(minutes))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}min"
    if h:
        return f"{h}h"
    return f"{m}min"


# ~3.5 phút cho mỗi set (nghỉ + thực hiện) — ước lượng demo cho "Time".
_MIN_PER_SET = 3.5


def _workout_title(vol_by_group: dict[str, float]) -> str:
    """Đặt tên buổi tập từ nhóm cơ chiếm volume lớn nhất (demo)."""
    if not vol_by_group:
        return "Workout"
    ranked = sorted(vol_by_group.items(), key=lambda kv: -kv[1])
    total = sum(vol_by_group.values()) or 1
    if len(ranked) == 1:
        return ranked[0][0].capitalize()
    top2 = ranked[:2]
    if sum(v for _, v in top2) / total > 0.7:
        return f"{top2[0][0].capitalize()} & {top2[1][0].capitalize()}"
    return "Full Body"


def _last_weights(user_id: str) -> dict[str, float]:
    """{exercise_name: weight_kg gần nhất} để gợi ý KG trong routine."""
    last: dict[str, float] = {}
    for s in sorted(tools.get_workout_history(user_id), key=lambda x: x["date"]):
        last[s["exercise_name"]] = s["weight_kg"]
    return last


def _build_workouts(user_id: str) -> list[dict]:
    """Mỗi ngày tập -> 1 'buổi tập' đầy đủ (set theo bài + muscle split + time)."""
    sets = tools.get_workout_history(user_id)
    gmap = _group_map()

    by_day: dict[str, list[dict]] = defaultdict(list)
    for s in sets:
        by_day[s["date"]].append(s)

    out: list[dict] = []
    for day in sorted(by_day, reverse=True):
        day_sets = by_day[day]

        by_ex: "OrderedDict[str, list[dict]]" = OrderedDict()
        for s in day_sets:
            by_ex.setdefault(s["exercise_name"], []).append(s)

        exercises = []
        vol_by_group: dict[str, float] = defaultdict(float)
        total_volume = 0.0
        for name, ss in by_ex.items():
            g = gmap.get(name, "other")
            rows = [
                {"weight_kg": s["weight_kg"], "reps": s["reps"]}
                for s in sorted(ss, key=lambda x: x["set_number"])
            ]
            for s in ss:
                v = analysis.set_volume(s)
                total_volume += v
                vol_by_group[g] += v
            exercises.append({"name": name, "muscle_group": g, "sets": rows})

        total_sets = len(day_sets)
        split = []
        if total_volume:
            for g, v in sorted(vol_by_group.items(), key=lambda kv: -kv[1]):
                split.append({"group": g, "pct": round(v / total_volume * 100)})

        out.append({
            "id": day,
            "date": day,
            "title": _workout_title(vol_by_group),
            "volume_kg": round(total_volume),
            "total_sets": total_sets,
            "duration_min": round(total_sets * _MIN_PER_SET),
            "muscle_split": split,
            "exercises": exercises,
        })
    return out


def _weekly_series(user_id: str) -> list[dict]:
    """Chuỗi theo tuần (bắt đầu thứ 2) cho chart: volume / reps / duration."""
    buckets: dict[str, dict] = {}
    for s in tools.get_workout_history(user_id):
        d = date.fromisoformat(s["date"])
        ws = d - timedelta(days=d.weekday())
        b = buckets.setdefault(ws.isoformat(), {"date": ws, "volume": 0.0, "reps": 0, "sets": 0})
        b["volume"] += analysis.set_volume(s)
        b["reps"] += int(s["reps"])
        b["sets"] += 1

    series = []
    for key in sorted(buckets):
        b = buckets[key]
        series.append({
            "label": b["date"].strftime("%b %d"),
            "volume_kg": round(b["volume"]),
            "reps": b["reps"],
            "duration_min": round(b["sets"] * _MIN_PER_SET),
        })
    return series


# --------------------------------------------------------------------------- #
# Read endpoints (dựng từ mock tools)
# --------------------------------------------------------------------------- #
@app.get("/api/home/{user_id}")
def home(user_id: str) -> dict:
    summary = tools.get_exercise_summary(user_id)
    sets = tools.get_workout_history(user_id)

    week_vols = tools.get_muscle_group_volume(user_id, time_range_days=7)
    if sets:
        last = max(s["date"] for s in sets)
        week_sets = [s for s in sets if s["date"] >= _minus_days(last, 7)]
    else:
        week_sets = []

    gap = analysis.muscle_gap(tools.get_muscle_group_volume(user_id, 28))
    if not gap["gaps"]:
        insight = "Các nhóm cơ của bạn khá cân bằng 👍 Tiếp tục duy trì!"
    else:
        worst = gap["gaps"][0]
        insight = (
            f"Nhóm cơ '{worst['group']}' đang bị bỏ bê — chỉ ~{int(worst['ratio'] * 100)}% "
            f"volume so với '{gap['top_group']}'."
        )

    return {
        "name": _name(user_id),
        "week_sessions": len(_distinct_days(week_sets)),
        "week_volume": round(sum(week_vols.values())),
        "tracked_exercises": len(summary),
        "insight": insight,
        "muscle_volume": tools.get_muscle_group_volume(user_id, 28),
    }


@app.get("/api/workouts/{user_id}")
def workouts(user_id: str) -> list[dict]:
    return _build_workouts(user_id)


@app.get("/api/workout/{user_id}/{workout_id}")
def workout_detail(user_id: str, workout_id: str) -> dict:
    for w in _build_workouts(user_id):
        if w["id"] == workout_id:
            return {**w, "athlete": _name(user_id)}
    return {}


@app.get("/api/routines/{user_id}")
def routines(user_id: str) -> list[dict]:
    last_w = _last_weights(user_id)
    out = []
    for idx, r in enumerate(tools.list_routines(user_id)):
        exercises = []
        for e in r["exercises"]:
            n = int(e.get("sets", 1) or 1)
            kg = last_w.get(e["name"])
            exercises.append({
                "name": e["name"],
                "reps": str(e.get("reps", "")),
                "sets_count": n,
                "kg": kg,
                "sets": [{"kg": kg, "reps": str(e.get("reps", ""))} for _ in range(n)],
            })
        out.append({
            "index": idx,
            "name": r["name"],
            "created_by": _name(user_id),
            "exercises": exercises,
            "series": _weekly_series(user_id),
        })
    return out


@app.get("/api/routine/{user_id}/{index}")
def routine_detail(user_id: str, index: int) -> dict:
    rs = routines(user_id)
    if 0 <= index < len(rs):
        return rs[index]
    return {}


@app.get("/api/profile/{user_id}")
def profile(user_id: str) -> dict:
    sets = tools.get_workout_history(user_id)
    summary = tools.get_exercise_summary(user_id)
    sessions = len(_distinct_days(sets))
    return {
        "name": _name(user_id),
        "user_id": user_id,
        "workouts_count": sessions,
        "total_sessions": sessions,
        "tracked_exercises": len(summary),
        "routines": len(tools.list_routines(user_id)),
        "followers": 2,
        "following": 2,
        "profile_pct": 80,
        "series": _weekly_series(user_id),
        "recent_workouts": _build_workouts(user_id)[:5],
    }


# --------------------------------------------------------------------------- #
# Static webapp — mount CUỐI để /api/* được match trước.
# --------------------------------------------------------------------------- #
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="webapp")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
