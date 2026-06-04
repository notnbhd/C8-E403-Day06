"""Phân tích training — PURE FUNCTIONS, không gọi LLM, không I/O.

Đây là lớp "grounding": mọi con số trong câu trả lời đến từ đây, không phải
do LLM bịa. Vì thuần Python nên test được offline và deterministic.

Input chung: list[Set] với mỗi Set = {date, exercise_name, weight_kg, reps, set_number}.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any


def _parse_date(d: str | date) -> date:
    if isinstance(d, date):
        return d
    return datetime.fromisoformat(d).date()


def est_1rm(weight_kg: float, reps: int) -> float:
    """Ước lượng 1RM theo công thức Epley. reps<=1 -> chính weight."""
    if reps <= 1:
        return float(weight_kg)
    return round(weight_kg * (1 + reps / 30.0), 1)


def _iso_week(d: date) -> tuple[int, int]:
    y, w, _ = d.isocalendar()
    return (y, w)


def weekly_best_1rm(sets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Gom theo tuần ISO, lấy est_1rm cao nhất mỗi tuần. Sort tăng dần theo tuần."""
    best: dict[tuple[int, int], dict[str, Any]] = {}
    for s in sets:
        wk = _iso_week(_parse_date(s["date"]))
        e = est_1rm(s["weight_kg"], s["reps"])
        cur = best.get(wk)
        if cur is None or e > cur["est_1rm"]:
            best[wk] = {"week": wk, "est_1rm": e, "date": _parse_date(s["date"]).isoformat()}
    return [best[k] for k in sorted(best.keys())]


def session_count(sets: list[dict[str, Any]]) -> int:
    """Số buổi (số ngày khác nhau) đã tập bài này."""
    return len({_parse_date(s["date"]) for s in sets})


def trend_summary(sets: list[dict[str, Any]]) -> dict[str, Any]:
    """Tóm tắt xu hướng 1RM: đầu kỳ vs cuối kỳ + % thay đổi."""
    weekly = weekly_best_1rm(sets)
    if not weekly:
        return {"weeks": 0, "sessions": 0}
    first, last = weekly[0]["est_1rm"], weekly[-1]["est_1rm"]
    pct = round((last - first) / first * 100, 1) if first else 0.0
    return {
        "weeks": len(weekly),
        "sessions": session_count(sets),
        "first_1rm": first,
        "last_1rm": last,
        "delta_kg": round(last - first, 1),
        "pct_change": pct,
        "direction": "up" if pct > 1 else ("down" if pct < -1 else "flat"),
        "weekly": weekly,
    }


def detect_plateau(
    sets: list[dict[str, Any]], window_weeks: int = 3, threshold_pct: float = 2.0
) -> dict[str, Any]:
    """Plateau nếu trong `window_weeks` tuần gần nhất, biên độ 1RM < threshold_pct%."""
    weekly = weekly_best_1rm(sets)
    if len(weekly) < window_weeks:
        return {"plateau": False, "reason": "not_enough_weeks", "weeks_available": len(weekly)}
    recent = [w["est_1rm"] for w in weekly[-window_weeks:]]
    lo, hi = min(recent), max(recent)
    spread = (hi - lo) / lo * 100 if lo else 0.0
    return {
        "plateau": spread < threshold_pct,
        "window_weeks": window_weeks,
        "spread_pct": round(spread, 1),
        "stuck_at_1rm": round(sum(recent) / len(recent), 1),
        "recent": recent,
    }


def set_volume(s: dict[str, Any]) -> float:
    return float(s["weight_kg"]) * int(s["reps"])


def muscle_gap(
    volume_by_group: dict[str, float], low_ratio: float = 0.4
) -> dict[str, Any]:
    """So sánh volume các nhóm cơ; nhóm < low_ratio * max bị coi là 'bỏ bê'."""
    if not volume_by_group:
        return {"gaps": [], "balanced": True, "by_group": {}}
    top = max(volume_by_group.values())
    gaps = [
        {"group": g, "volume": round(v, 0), "ratio": round(v / top, 2)}
        for g, v in sorted(volume_by_group.items(), key=lambda kv: kv[1])
        if top and v < low_ratio * top
    ]
    return {
        "gaps": gaps,
        "balanced": len(gaps) == 0,
        "top_group": max(volume_by_group, key=volume_by_group.get),
        "by_group": {g: round(v, 0) for g, v in volume_by_group.items()},
    }
