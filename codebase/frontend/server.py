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
from collections import defaultdict
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
# Read endpoints (dựng từ mock tools)
# --------------------------------------------------------------------------- #
def _distinct_days(sets: list[dict]) -> set[str]:
    return {s["date"] for s in sets}


@app.get("/api/home/{user_id}")
def home(user_id: str) -> dict:
    summary = tools.get_exercise_summary(user_id)
    sets = tools.get_workout_history(user_id)

    # "Tuần này" = 7 ngày gần nhất.
    week_vols = tools.get_muscle_group_volume(user_id, time_range_days=7)
    if sets:
        last = max(s["date"] for s in sets)
        week_cut = last  # các buổi cùng tuần với buổi gần nhất
        week_sets = [s for s in sets if s["date"] >= _minus_days(week_cut, 7)]
    else:
        week_sets = []

    # Insight từ phân tích muscle gap (4 tuần).
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
        "week_sessions": len(_distinct_days(week_sets)),
        "week_volume": round(sum(week_vols.values())),
        "tracked_exercises": len(summary),
        "insight": insight,
        "muscle_volume": tools.get_muscle_group_volume(user_id, 28),
    }


@app.get("/api/history/{user_id}")
def history(user_id: str) -> list[dict]:
    sets = tools.get_workout_history(user_id)

    # Gom set theo ngày -> mỗi ngày là 1 "buổi tập".
    by_day: dict[str, list[dict]] = defaultdict(list)
    for s in sets:
        by_day[s["date"]].append(s)

    out: list[dict] = []
    for day in sorted(by_day, reverse=True):
        day_sets = by_day[day]
        by_ex: dict[str, list[dict]] = defaultdict(list)
        for s in day_sets:
            by_ex[s["exercise_name"]].append(s)

        exercises = []
        for name, ss in by_ex.items():
            top = max(ss, key=lambda x: x["weight_kg"])
            exercises.append({
                "name": name,
                "sets": len(ss),
                "top_set": f"{top['weight_kg']:g}kg × {top['reps']}",
            })

        out.append({
            "title": f"Buổi tập {day}",
            "volume_kg": round(sum(analysis.set_volume(s) for s in day_sets)),
            "exercises": exercises,
        })
    return out


@app.get("/api/routines/{user_id}")
def routines(user_id: str) -> list[dict]:
    return [
        {
            "name": r["name"],
            "exercises": [
                {"name": e["name"], "sets": e["sets"], "reps": e["reps"]}
                for e in r["exercises"]
            ],
        }
        for r in tools.list_routines(user_id)
    ]


@app.get("/api/profile/{user_id}")
def profile(user_id: str) -> dict:
    sets = tools.get_workout_history(user_id)
    summary = tools.get_exercise_summary(user_id)
    return {
        "name": _DISPLAY_NAME.get(user_id, "Athlete"),
        "user_id": user_id,
        "total_sessions": len(_distinct_days(sets)),
        "tracked_exercises": len(summary),
        "routines": len(tools.list_routines(user_id)),
    }


def _minus_days(iso_date: str, days: int) -> str:
    from datetime import date, timedelta

    y, m, d = map(int, iso_date.split("-"))
    return (date(y, m, d) - timedelta(days=days)).isoformat()


# --------------------------------------------------------------------------- #
# Static webapp — mount CUỐI để /api/* được match trước.
# --------------------------------------------------------------------------- #
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="webapp")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
