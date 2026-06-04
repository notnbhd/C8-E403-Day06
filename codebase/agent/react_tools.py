"""Tools cho ReAct agent — wrap analysis.py + tools.py, GIỮ NGUYÊN grounding.

LLM (qua create_react_agent) tự chọn gọi tool nào. Nhưng MỌI con số vẫn do Python
tính trong các tool dưới đây — LLM chỉ đọc kết quả và diễn đạt, không tự bịa số.

`user_id` được inject qua InjectedState (state của graph, sống xuyên suốt
interrupt/resume nhờ checkpointer) nên LLM không nhìn thấy / không tự chọn user.
"""
from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.types import interrupt

from agent import analysis, config, tools

log = logging.getLogger("agent.react_tools")


class CoachState(AgentState):
    """State của ReAct agent: messages (+ remaining_steps) + user_id bền vững."""
    user_id: str


def _uid(state: dict) -> str:
    uid = state.get("user_id")
    if not uid:
        raise ValueError("Thiếu user_id trong state.")
    return uid


def _json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


# Nhóm cơ tiếng Việt -> id trong catalog (để filter overview).
_VN_GROUP = {
    "ngực": "chest", "lưng": "back", "xô": "back", "chân": "legs", "đùi": "legs",
    "mông": "legs", "vai": "shoulders", "tay": "arms", "tay trước": "arms", "tay sau": "arms",
}


@tool
def list_exercises() -> str:
    """Liệt kê danh mục bài tập (tên + nhóm cơ). Dùng khi cần tên bài chính xác."""
    cat = tools.list_exercise_catalog()
    return _json([{"name": e["name"], "muscle_group": e["muscle_group"]} for e in cat])


@tool
def get_exercise_progress(exercise_name: str, state: Annotated[dict, InjectedState]) -> str:
    """Tiến độ MỘT bài tập: xu hướng 1RM, % thay đổi, có đang plateau không.

    Mọi con số do Python tính (Epley 1RM). Trả status=no_data nếu chưa log bài này;
    data_sufficient=false nghĩa là CHƯA đủ buổi để kết luận xu hướng.
    """
    uid = _uid(state)
    sets = tools.get_workout_history(uid, exercise_name=exercise_name)
    if not sets:
        return _json({"exercise": exercise_name, "status": "no_data"})
    trend = analysis.trend_summary(sets)
    plateau = analysis.detect_plateau(sets)
    return _json({
        "exercise": exercise_name,
        "sessions": trend["sessions"],
        "weeks": trend["weeks"],
        "first_1rm": trend["first_1rm"],
        "last_1rm": trend["last_1rm"],
        "delta_kg": trend["delta_kg"],
        "pct_change": trend["pct_change"],
        "direction": trend["direction"],
        "plateau": plateau.get("plateau"),
        "spread_pct": plateau.get("spread_pct"),
        "stuck_at_1rm": plateau.get("stuck_at_1rm"),
        "data_sufficient": trend["sessions"] >= config.MIN_SESSIONS,
        "min_sessions_needed": config.MIN_SESSIONS,
    })


@tool
def get_progress_overview(
    state: Annotated[dict, InjectedState], muscle_group: str | None = None
) -> str:
    """Tổng quan tiến độ NHIỀU bài cùng lúc (review chung), có thể lọc theo nhóm cơ.

    muscle_group: chest/back/legs/shoulders/arms (hoặc tiếng Việt ngực/lưng/chân/vai/tay).
    Bỏ trống = tất cả bài user đang tập. Mọi con số do Python tính.
    """
    uid = _uid(state)
    summary = tools.get_exercise_summary(uid)
    if not summary:
        return _json({"status": "no_data"})
    grp = muscle_group
    if grp:
        grp = _VN_GROUP.get(grp.strip().lower(), grp.strip().lower())
        names = {e["name"] for e in tools.list_exercise_catalog() if e["muscle_group"] == grp}
        summary = [s for s in summary if s["exercise_name"] in names]
        if not summary:
            return _json({"status": "no_data", "muscle_group": grp})
    out = []
    for s in summary:
        sets = tools.get_workout_history(uid, exercise_name=s["exercise_name"])
        t = analysis.trend_summary(sets)
        out.append({
            "exercise": s["exercise_name"],
            "sessions": t["sessions"],
            "first_1rm": t.get("first_1rm"),
            "last_1rm": t.get("last_1rm"),
            "pct_change": t.get("pct_change"),
            "direction": t.get("direction"),
            "data_sufficient": t["sessions"] >= config.MIN_SESSIONS,
        })
    return _json({"muscle_group": grp, "exercises": out})


@tool
def find_muscle_gaps(state: Annotated[dict, InjectedState]) -> str:
    """Nhóm cơ nào đang bị bỏ bê trong 4 tuần qua (so volume giữa các nhóm). Python tính."""
    uid = _uid(state)
    vols = tools.get_muscle_group_volume(uid, time_range_days=28)
    if not vols:
        return _json({"status": "no_data"})
    return _json(analysis.muscle_gap(vols))


@tool
def search_knowledge(query: str) -> str:
    """Tra cứu KIẾN THỨC tập luyện trong tài liệu (RAG). Trả các đoạn liên quan + nguồn.

    CHỈ được trả lời dựa trên các đoạn này; nếu không có thông tin phù hợp thì nói rõ
    'Tài liệu không đề cập đến điều này' (đừng bịa).
    """
    chunks = tools.search_fitness_knowledge(query, k=4)
    return _json([{"text": c["text"], "source": c.get("source")} for c in chunks])


def _build_routine(
    user_id: str,
    *,
    muscle_groups: list[str] | None = None,
    exercise_names: list[str] | None = None,
    name: str | None = None,
) -> dict[str, Any]:
    """Dựng routine theo Ý NGƯỜI DÙNG (deterministic, bài lấy từ catalog).

    Ưu tiên: exercise_names cụ thể -> muscle_groups -> (fallback) nhóm cơ bị bỏ bê.
    Mọi bài đều resolve qua catalog nên exercise_id luôn hợp lệ (không để LLM bịa).
    Giải thích 'vì sao + cách tập' do LLM tự viết (qua search_knowledge), KHÔNG nhồi
    chunk thô vào đây — giữ thẻ preview gọn, chỉ cấu trúc bài tập.
    """
    catalog = tools.list_exercise_catalog()
    if exercise_names:
        picks, seen = [], set()
        for n in exercise_names:
            e = tools.resolve_exercise(n)
            if e and e["exercise_id"] not in seen:
                picks.append(e)
                seen.add(e["exercise_id"])
    elif muscle_groups:
        groups = {_VN_GROUP.get(g.strip().lower(), g.strip().lower()) for g in muscle_groups}
        picks = [e for e in catalog if e["muscle_group"] in groups]
    else:
        gap = analysis.muscle_gap(tools.get_muscle_group_volume(user_id))
        weak = {g["group"] for g in gap.get("gaps", [])}
        picks = [e for e in catalog if e["muscle_group"] in weak] or catalog[:4]
    exercises = [
        {"exercise_id": e["exercise_id"], "name": e["name"],
         "sets": 3, "reps": "8-12", "rest_sec": 90}
        for e in picks[:6]
    ]
    return {"name": name or "Routine của tôi", "exercises": exercises}


@tool
def save_routine(
    state: Annotated[dict, InjectedState],
    exercise_names: list[str] | None = None,
    muscle_groups: list[str] | None = None,
    name: str | None = None,
) -> str:
    """Tạo & lưu routine vào app Hevy. Đây là TOOL DUY NHẤT cho MỌI yêu cầu routine
    (tạo / cần / gợi ý / lên lịch / lưu) — KHÔNG mô tả routine bằng text rồi hỏi suông.

    Tool sẽ DỪNG, hiện preview cho user bấm xác nhận; CHƯA xác nhận thì CHƯA ghi DB.
    Truyền đúng Ý NGƯỜI DÙNG:
    - exercise_names: danh sách bài cụ thể (tên trong catalog) nếu user/bạn đã chọn;
    - muscle_groups: nhóm cơ cần tập trung nếu user nêu (vd ['tay'] cho 'tập trung tay');
    - name: tên routine.
    Bỏ trống cả hai = routine cân bằng theo nhóm cơ đang bị bỏ bê.
    """
    uid = _uid(state)
    routine = _build_routine(uid, exercise_names=exercise_names,
                             muscle_groups=muscle_groups, name=name)
    if not routine["exercises"]:
        return _json({"status": "error",
                      "error": "Không khớp được bài nào trong catalog. Hãy gọi list_exercises "
                               "để lấy tên bài hợp lệ rồi thử lại."})
    # interrupt -> graph dừng, UI hiện preview + Confirm/Cancel, rồi resume bằng
    # Command(resume={"approved": bool, "edits": ...}).
    decision = interrupt({"type": "routine_preview", "routine": routine})
    if not decision or not decision.get("approved"):
        return _json({"status": "cancelled",
                      "note": "Người dùng đã HUỶ. KHÔNG có routine nào được lưu. "
                              "Báo user rõ là chưa lưu gì và hỏi có muốn chỉnh lại không. "
                              "ĐỪNG liệt kê routine như thể đã tạo."})
    routine = decision.get("edits") or routine
    try:
        res = tools.create_routine(uid, routine)
    except tools.ToolError as e:
        log.warning("save_routine THẤT BẠI: %s", e)
        return _json({"status": "error", "error": str(e)})
    log.info("save_routine → đã lưu id=%s", res["routine_id"])
    return _json({
        "status": "saved",
        "routine_id": res["routine_id"],
        "name": routine["name"],
        # Trả lại danh sách bài để LLM giải thích ĐÚNG các bài trong routine này
        # (đừng nhắc bài ngoài routine khi diễn giải KB).
        "exercises": [e["name"] for e in routine["exercises"]],
    })


TOOLS = [
    list_exercises, get_exercise_progress, get_progress_overview,
    find_muscle_gaps, search_knowledge, save_routine,
]


SYSTEM_PROMPT = (
    "Bạn là Coach AI 🏋️ — huấn luyện viên thể hình nói tiếng Việt, đọc dữ liệu tập "
    "Hevy của người dùng.\n"
    "\nNGUYÊN TẮC BẮT BUỘC:\n"
    "1. MỌI con số (1RM, %, kg, số buổi, volume) PHẢI lấy từ tool. TUYỆT ĐỐI không tự "
    "bịa hay phỏng đoán số.\n"
    "2. Chọn tool: tiến độ 1 bài → get_exercise_progress; tổng quan / nhiều bài / theo "
    "nhóm cơ → get_progress_overview; nhóm cơ bị bỏ bê → find_muscle_gaps; kiến thức "
    "tập luyện chung → search_knowledge; cần tên bài chính xác → list_exercises.\n"
    "3. Tool trả status=no_data → nói thẳng là chưa có dữ liệu, KHÔNG đoán.\n"
    "4. data_sufficient=false → CHƯA đủ buổi, KHÔNG kết luận xu hướng; khuyên user log thêm.\n"
    "5. search_knowledge: chỉ trả lời dựa trên đoạn trả về và trích nguồn; không có thì "
    "nói 'Tài liệu không đề cập đến điều này'. Đừng kèm nguồn nếu tài liệu không đề cập.\n"
    "6. BẤT KỲ yêu cầu routine nào (tạo / cần / gợi ý / lên lịch / lưu,...) → kết thúc bằng "
    "GỌI save_routine để hiện preview cho user bấm xác nhận (đừng tự liệt kê routine bằng "
    "text rồi hỏi 'có muốn lưu không?'). Bám đúng yêu cầu: user muốn tập trung nhóm cơ nào "
    "(vd 'tay') thì truyền muscle_groups=['tay'] (hoặc exercise_names cụ thể) + name phù hợp; "
    "ĐỪNG để mặc định 'cân bằng nhóm cơ'. Sau khi save_routine trả status=saved, viết "
    "giải thích NGẮN vì sao các bài hiệu quả + lưu ý kỹ thuật, dựa trên search_knowledge "
    "(diễn đạt lại, KHÔNG dán nguyên văn). CHỈ nói về ĐÚNG các bài trong trường 'exercises' "
    "mà save_routine trả về — TUYỆT ĐỐI không nhắc bài không có trong routine.\n"
    "7. Khi đưa lời khuyên tập luyện, kết thúc bằng:\n"
    "   '⚠️ Gợi ý dựa trên dữ liệu tập của bạn, không thay thế PT/bác sĩ.'\n"
    "\nLÀM GIÀU BẰNG KIẾN THỨC (chủ động gọi thêm search_knowledge để giải thích "
    "'vì sao' / 'cách làm', đừng chỉ đưa số khô khan):\n"
    "- Sau khi có kết quả từ tool dữ liệu, nếu câu trả lời mang tính KHUYÊN/GIẢI THÍCH, "
    "GỌI THÊM search_knowledge rồi lồng kiến thức vào (có trích nguồn).\n"
    "- Phát hiện plateau → search_knowledge('phá plateau deload'); muscle gap → "
    "search_knowledge('cân bằng nhóm cơ đẩy kéo'); hỏi khi nào tăng tạ → "
    "search_knowledge('progressive overload tăng tải').\n"
    "- Routine: trước khi gọi save_routine, dùng search_knowledge để tự viết 'vì sao + "
    "cách tập' (xem mục 6). Luôn diễn đạt lại từ tài liệu, KHÔNG dán nguyên văn chunk.\n"
    "\nTrả lời ngắn gọn, thân thiện, khích lệ, bằng tiếng Việt."
)
