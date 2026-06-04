"""Seed Supabase with demo data — the same fixtures the agent used to mock.

Reproduces exactly what `codebase/agent/tools.py` faked so the demo and the
analysis/guardrail behaviour stay identical after switching to the DB:

  - demo-user: Bench Press progressing, Squat plateaued, back/legs undertrained
  - new-user:  only 2 Bench sessions (triggers the "not enough sessions" guardrail)
  - one saved routine ("Push Day A") for demo-user

Idempotent: wipes the seeded tables first, so re-running is safe.

    python -m db.seed          # from repo root, with DATABASE_URL set
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import delete

from db.models import Exercise, Routine, RoutineExercise, User, WorkoutSet
from db.session import SessionLocal

# "Today" anchor for the demo timeline (matches the old mock).
ANCHOR = date(2026, 6, 4)

EXERCISE_CATALOG = [
    {"exercise_id": "ex_bench", "name": "Bench Press", "muscle_group": "chest"},
    {"exercise_id": "ex_incline", "name": "Incline Dumbbell Press", "muscle_group": "chest"},
    {"exercise_id": "ex_squat", "name": "Squat", "muscle_group": "legs"},
    {"exercise_id": "ex_dead", "name": "Deadlift", "muscle_group": "back"},
    {"exercise_id": "ex_row", "name": "Barbell Row", "muscle_group": "back"},
    {"exercise_id": "ex_ohp", "name": "Overhead Press", "muscle_group": "shoulders"},
    {"exercise_id": "ex_curl", "name": "Bicep Curl", "muscle_group": "arms"},
    {"exercise_id": "ex_pulldown", "name": "Lat Pulldown", "muscle_group": "back"},
]
_ID_BY_NAME = {e["name"]: e["exercise_id"] for e in EXERCISE_CATALOG}

USERS = [
    {"id": "demo-user", "display_name": "Alex Nguyen"},
    {"id": "new-user", "display_name": "Newbie"},
]


def _sets_for(user_id, name, weeks, reps, sets_per_session=3):
    """One session per week, walking back from ANCHOR. weeks[i] = top weight."""
    rows = []
    n = len(weeks)
    for i, w in enumerate(weeks):
        d = ANCHOR - timedelta(days=(n - 1 - i) * 7)
        for sn in range(1, sets_per_session + 1):
            rows.append(WorkoutSet(
                user_id=user_id,
                exercise_id=_ID_BY_NAME[name],
                performed_on=d,
                weight_kg=w,
                reps=reps,
                set_number=sn,
            ))
    return rows


def _workout_rows():
    rows = []
    rows += _sets_for("demo-user", "Bench Press", [60, 60, 62.5, 65, 65, 67.5, 70, 72.5], reps=5)
    rows += _sets_for("demo-user", "Squat", [100, 100, 100, 100], reps=5)
    rows += _sets_for("demo-user", "Overhead Press", [40, 40, 42.5], reps=5)
    rows += _sets_for("demo-user", "Barbell Row", [50], reps=8)
    rows += _sets_for("new-user", "Bench Press", [50, 52.5], reps=5)
    return rows


def _routine():
    # No explicit id: let the identity sequence assign it (first row -> 1) so the
    # sequence advances and later create_routine() writes don't collide.
    r = Routine(user_id="demo-user", name="Push Day A")
    r.exercises = [
        RoutineExercise(exercise_id="ex_bench", position=0, sets=4, reps="5", rest_sec=120),
        RoutineExercise(exercise_id="ex_ohp", position=1, sets=3, reps="8", rest_sec=90),
        RoutineExercise(exercise_id="ex_incline", position=2, sets=3, reps="10-12", rest_sec=90),
    ]
    return r


def seed() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured; cannot seed.")
    s = SessionLocal()
    try:
        # Clean slate (children first to respect FKs).
        s.execute(delete(RoutineExercise))
        s.execute(delete(Routine))
        s.execute(delete(WorkoutSet))
        s.execute(delete(Exercise))
        s.execute(delete(User))
        s.flush()

        s.add_all([User(**u) for u in USERS])
        s.add_all([Exercise(**e) for e in EXERCISE_CATALOG])
        s.flush()
        s.add_all(_workout_rows())
        s.add(_routine())
        s.commit()

        sets = s.query(WorkoutSet).count()
        print(f"✅ Seeded {len(USERS)} users, {len(EXERCISE_CATALOG)} exercises, "
              f"{sets} sets, 1 routine.")
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


if __name__ == "__main__":
    seed()
