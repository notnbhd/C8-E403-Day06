"""Supabase-backed implementation of the §5 tool contract.

This is the real Backend layer behind `tools.py`. It owns its OWN SQLAlchemy
engine built straight from `DATABASE_URL` (same env var the repo-root `db/`
package uses) so the agent stays decoupled from teammates' modules — exactly
like `config.py` reads env directly instead of importing `config/settings.py`.

Output shapes match `tools.py` EXACTLY so the agent doesn't care whether a call
was served by mock or Postgres:

  Set = {date, exercise_name, weight_kg, reps, set_number}

Error contract (§5.4): no data -> [] / {} (never raise). System failure (DB
down, write failed) -> raise ToolError.

Safe degrade: if DATABASE_URL is unset or the engine can't be built, `enabled()`
returns False and `tools.py` falls back to mock — so tests/CI/offline still run.
"""
from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger("agent.repo")


class ToolError(RuntimeError):
    """System error talking to the DB (kept name-compatible with tools.ToolError)."""


_engine = None
_failed = False


def _get_engine():
    """Lazy singleton engine. Returns None if DATABASE_URL missing / unbuildable."""
    global _engine, _failed
    if _engine is not None or _failed:
        return _engine
    url = os.getenv("DATABASE_URL")
    if not url:
        _failed = True
        log.info("repo offline: thiếu DATABASE_URL → fallback mock")
        return None
    try:
        from sqlalchemy import create_engine

        _engine = create_engine(url, future=True, pool_pre_ping=True)
        log.info("repo sẵn sàng: Supabase qua DATABASE_URL")
    except Exception as e:  # noqa: BLE001
        _failed = True
        log.warning("repo init lỗi (%s) → fallback mock", e)
    return _engine


def enabled() -> bool:
    return _get_engine() is not None


def _rows(sql: str, **params) -> list[dict[str, Any]]:
    from sqlalchemy import text

    eng = _get_engine()
    if eng is None:
        raise ToolError("DATABASE_URL chưa cấu hình.")
    try:
        with eng.connect() as c:
            res = c.execute(text(sql), params)
            return [dict(r._mapping) for r in res]
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"DB query lỗi: {e}") from e


# --------------------------------------------------------------------------- #
# CONTRACT §5.2 — Backend (Supabase)
# --------------------------------------------------------------------------- #
def get_workout_history(
    user_id: str,
    exercise_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    rows = _rows(
        """
        SELECT ws.performed_on AS date, e.name AS exercise_name,
               ws.weight_kg, ws.reps, ws.set_number
        FROM workout_sets ws
        JOIN exercises e ON e.exercise_id = ws.exercise_id
        WHERE ws.user_id = :uid
          AND (CAST(:ename AS text) IS NULL OR lower(e.name) = lower(:ename))
          AND (CAST(:start AS date) IS NULL OR ws.performed_on >= :start)
          AND (CAST(:end   AS date) IS NULL OR ws.performed_on <= :end)
        ORDER BY ws.performed_on ASC, ws.set_number ASC
        """,
        uid=user_id, ename=exercise_name, start=start_date, end=end_date,
    )
    for r in rows:
        r["date"] = r["date"].isoformat()
        r["weight_kg"] = float(r["weight_kg"])
        r["reps"] = int(r["reps"])
        r["set_number"] = int(r["set_number"])
    return rows


def get_exercise_summary(user_id: str) -> list[dict[str, Any]]:
    rows = _rows(
        """
        SELECT e.name AS exercise_name,
               max(ws.performed_on)                  AS last_performed,
               sum(ws.weight_kg * ws.reps)           AS total_volume_kg,
               count(DISTINCT ws.performed_on)       AS session_count
        FROM workout_sets ws
        JOIN exercises e ON e.exercise_id = ws.exercise_id
        WHERE ws.user_id = :uid
        GROUP BY e.name
        ORDER BY e.name
        """,
        uid=user_id,
    )
    for r in rows:
        r["last_performed"] = r["last_performed"].isoformat()
        r["total_volume_kg"] = round(float(r["total_volume_kg"]), 0)
        r["session_count"] = int(r["session_count"])
    return rows


def get_muscle_group_volume(user_id: str, time_range_days: int = 28) -> dict[str, float]:
    """{muscle_group: total_volume_kg} within the last N days.

    The window is anchored on the user's MOST RECENT session (not wall-clock
    today) so demo data with fixed dates stays meaningful over time.
    """
    rows = _rows(
        """
        WITH anchor AS (
            SELECT max(performed_on) AS d FROM workout_sets WHERE user_id = :uid
        )
        SELECT e.muscle_group AS muscle_group,
               sum(ws.weight_kg * ws.reps) AS vol
        FROM workout_sets ws
        JOIN exercises e ON e.exercise_id = ws.exercise_id, anchor
        WHERE ws.user_id = :uid
          AND ws.performed_on >= anchor.d - make_interval(days => :days)
        GROUP BY e.muscle_group
        """,
        uid=user_id, days=time_range_days,
    )
    return {r["muscle_group"]: round(float(r["vol"]), 1) for r in rows}


def list_exercise_catalog() -> list[dict[str, str]]:
    return _rows(
        "SELECT exercise_id, name, muscle_group FROM exercises ORDER BY name"
    )


def create_routine(user_id: str, routine: dict[str, Any]) -> dict[str, Any]:
    """Write a routine + its exercises in one transaction. Returns {routine_id}."""
    from sqlalchemy import text

    exercises = routine.get("exercises") or []
    if not exercises:
        raise ToolError("Routine rỗng, không có bài tập.")
    eng = _get_engine()
    if eng is None:
        raise ToolError("DATABASE_URL chưa cấu hình.")
    try:
        with eng.begin() as c:
            rid = c.execute(
                text("INSERT INTO routines (user_id, name) VALUES (:uid, :name) "
                     "RETURNING id"),
                {"uid": user_id, "name": routine.get("name", "Routine")},
            ).scalar_one()
            for pos, ex in enumerate(exercises):
                c.execute(
                    text("INSERT INTO routine_exercises "
                         "(routine_id, exercise_id, position, sets, reps, rest_sec) "
                         "VALUES (:rid, :eid, :pos, :sets, :reps, :rest)"),
                    {"rid": rid, "eid": ex["exercise_id"], "pos": pos,
                     "sets": ex.get("sets", 3), "reps": str(ex.get("reps", "8-12")),
                     "rest": ex.get("rest_sec", 90)},
                )
    except ToolError:
        raise
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"Ghi routine lỗi: {e}") from e
    return {"routine_id": f"rt_{rid:04d}"}


def list_routines(user_id: str) -> list[dict[str, Any]]:
    rows = _rows(
        """
        SELECT r.id AS rid, r.name AS name,
               re.exercise_id, e.name AS ex_name, re.sets, re.reps, re.rest_sec
        FROM routines r
        LEFT JOIN routine_exercises re ON re.routine_id = r.id
        LEFT JOIN exercises e ON e.exercise_id = re.exercise_id
        WHERE r.user_id = :uid
        ORDER BY r.id, re.position
        """,
        uid=user_id,
    )
    by_id: dict[int, dict[str, Any]] = {}
    for r in rows:
        rt = by_id.setdefault(r["rid"], {
            "routine_id": f"rt_{r['rid']:04d}",
            "user_id": user_id,
            "name": r["name"],
            "exercises": [],
        })
        if r["exercise_id"]:
            rt["exercises"].append({
                "exercise_id": r["exercise_id"],
                "name": r["ex_name"],
                "sets": int(r["sets"]),
                "reps": r["reps"],
                "rest_sec": int(r["rest_sec"]),
            })
    return list(by_id.values())


# --------------------------------------------------------------------------- #
# User helpers (the "user database" entry points UI can call)
# --------------------------------------------------------------------------- #
def get_user(user_id: str) -> dict[str, Any] | None:
    rows = _rows(
        "SELECT id AS user_id, display_name FROM users WHERE id = :uid",
        uid=user_id,
    )
    return rows[0] if rows else None


def list_users() -> list[dict[str, Any]]:
    return _rows("SELECT id AS user_id, display_name FROM users ORDER BY display_name")


def ensure_user(user_id: str, display_name: str | None = None) -> dict[str, Any]:
    """Upsert a user (create on first sight). Returns {user_id, display_name}."""
    from sqlalchemy import text

    eng = _get_engine()
    if eng is None:
        raise ToolError("DATABASE_URL chưa cấu hình.")
    name = display_name or user_id
    try:
        with eng.begin() as c:
            c.execute(
                text("INSERT INTO users (id, display_name) VALUES (:uid, :name) "
                     "ON CONFLICT (id) DO NOTHING"),
                {"uid": user_id, "name": name},
            )
    except Exception as e:  # noqa: BLE001
        raise ToolError(f"Tạo user lỗi: {e}") from e
    return get_user(user_id) or {"user_id": user_id, "display_name": name}
