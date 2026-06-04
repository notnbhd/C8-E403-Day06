"""LLM access qua OpenRouter + fallback offline.

Nếu CÓ OPENROUTER_API_KEY: dùng ChatOpenAI trỏ vào OpenRouter để (a) phân loại
intent, (b) diễn đạt lại câu trả lời cho tự nhiên.

Nếu KHÔNG có key: rơi về chế độ offline — intent bằng keyword, câu trả lời dùng
thẳng draft template. Nhờ vậy graph chạy + test được mà không cần API key.

LƯU Ý GROUNDING: kể cả khi có LLM, mọi CON SỐ đều do agent/analysis.py tính sẵn
và nằm trong draft; LLM chỉ được diễn đạt lại, không được tạo số mới.
"""
from __future__ import annotations

import logging
import re

from agent import config
from agent.state import Intent

log = logging.getLogger("agent.llm")

_LLM = None  # cache


def get_llm():
    """Trả ChatOpenAI (OpenRouter) hoặc None nếu chưa cấu hình key."""
    global _LLM
    if not config.llm_enabled():
        return None
    if _LLM is None:
        from langchain_openai import ChatOpenAI

        if config.OPENROUTER_API_KEY:
            _LLM = ChatOpenAI(
                model=config.AGENT_MODEL,
                api_key=config.OPENROUTER_API_KEY,
                base_url=config.OPENROUTER_BASE_URL,
                temperature=config.LLM_TEMPERATURE,
            )
            log.info("LLM: provider=openrouter model=%s", config.AGENT_MODEL)
        else:  # fallback: custom LLM (vd Mistral) đã cấu hình cho RAG chatbot
            _LLM = ChatOpenAI(
                model=config.CUSTOM_LLM_MODEL,
                api_key=config.CUSTOM_LLM_KEY,
                base_url=config.CUSTOM_LLM_URL or None,
                temperature=config.LLM_TEMPERATURE,
            )
            log.info("LLM: provider=custom model=%s url=%s",
                     config.CUSTOM_LLM_MODEL, config.CUSTOM_LLM_URL)
    return _LLM


# --------------------------------------------------------------------------- #
# Intent classification
# --------------------------------------------------------------------------- #
_INTENT_KEYWORDS: list[tuple[Intent, tuple[str, ...]]] = [
    ("muscle_gap", ("nhóm cơ", "muscle", "bỏ bê", "cân bằng", "undertrained", "bỏ quên")),
    ("plateau", ("plateau", "chững", "đứng yên", "không tăng", "dậm chân", "stuck")),
    ("progression", ("tăng tạ", "khi nào nên", "progression", "tăng mức", "nặng hơn")),
    ("create_routine", ("tạo routine", "lưu routine", "thêm vào hevy", "save routine", "ghi routine")),
    ("build_plan", ("lên lịch", "build", "chương trình", "giáo án", "plan", "program", "lộ trình")),
    ("knowledge", ("dinh dưỡng", "protein", "đạm", "calo", "thời gian nghỉ", "nghỉ giữa",
                   "rep range", "khởi động", "giãn cơ", "hồi phục", "ngủ", "cardio",
                   "kỹ thuật", "nên ăn", "tần suất", "deload", "overload")),
    ("analyze", ("tiến bộ", "progress", "có tăng", "cải thiện", "phong độ", "thế nào")),
]

_VAGUE = ("tập tốt không", "ổn không", "thế nào nhỉ", "sao rồi")

_ROUTER_SYS = (
    "Bạn là router của một fitness coach AI. Phân loại tin nhắn user vào ĐÚNG MỘT intent:\n"
    "- analyze: hỏi một bài cụ thể có tiến bộ không\n"
    "- plateau: hỏi có đang chững lại không\n"
    "- muscle_gap: hỏi nhóm cơ nào đang bỏ bê / mất cân bằng\n"
    "- progression: hỏi khi nào nên tăng tạ / cách tăng tải\n"
    "- build_plan: muốn được build chương trình tập\n"
    "- create_routine: muốn lưu/tạo routine vào app\n"
    "- knowledge: hỏi KIẾN THỨC tập luyện chung (dinh dưỡng, thời gian nghỉ, kỹ thuật, "
    "tần suất, hồi phục...) KHÔNG gắn với dữ liệu cá nhân của user\n"
    "- clarify: câu hỏi quá mơ hồ, thiếu bài/nhóm cơ cụ thể để trả lời\n"
    "- general: chào hỏi, hỏi 'bạn làm được gì'\n"
    "Chỉ trả về đúng một từ intent, không giải thích."
)
_VALID = {"analyze", "plateau", "muscle_gap", "progression",
          "build_plan", "create_routine", "knowledge", "clarify", "general"}


def keyword_intent(message: str) -> Intent:
    m = message.lower()
    if any(v in m for v in _VAGUE):
        return "clarify"
    for intent, kws in _INTENT_KEYWORDS:
        if any(k in m for k in kws):
            return intent
    # quá ngắn / không có tín hiệu -> general
    return "general"


def classify_intent(message: str) -> Intent:
    llm = get_llm()
    if llm is None:
        return keyword_intent(message)
    try:
        resp = llm.invoke([("system", _ROUTER_SYS), ("human", message)])
        word = re.sub(r"[^a-z_]", "", resp.content.strip().lower())
        return word if word in _VALID else keyword_intent(message)  # type: ignore[return-value]
    except Exception:
        return keyword_intent(message)


def extract_exercise(message: str, catalog_names: list[str]) -> str | None:
    """Tìm tên bài user nhắc tới (match trên catalog)."""
    m = message.lower()
    for name in catalog_names:
        if name.lower() in m:
            return name
    return None


# --------------------------------------------------------------------------- #
# Diễn đạt câu trả lời
# --------------------------------------------------------------------------- #
_POLISH_SYS = (
    "Bạn là một fitness coach AI thân thiện, nói tiếng Việt. Dưới đây là một bản nháp "
    "câu trả lời đã chứa SẴN số liệu thật từ dữ liệu tập của user. Hãy viết lại cho tự "
    "nhiên, ngắn gọn, khích lệ. TUYỆT ĐỐI giữ nguyên mọi con số; KHÔNG thêm số/sự kiện "
    "mới ngoài bản nháp."
)


def polish(draft: str) -> str:
    """Diễn đạt lại draft cho tự nhiên (nếu có LLM); offline thì trả nguyên draft."""
    llm = get_llm()
    if llm is None or not draft:
        return draft
    try:
        resp = llm.invoke([("system", _POLISH_SYS), ("human", draft)])
        return resp.content.strip() or draft
    except Exception:
        return draft


# --------------------------------------------------------------------------- #
# RAG — trả lời câu hỏi kiến thức dựa trên tài liệu (grounded trên chunks)
# --------------------------------------------------------------------------- #
_RAG_SYS = (
    "Bạn là HLV thể hình AI nói tiếng Việt. Chỉ trả lời dựa trên TÀI LIỆU THAM KHẢO "
    "được cung cấp. Nếu tài liệu không đề cập, nói rõ 'Tài liệu không đề cập đến điều "
    "này'. Trả lời ngắn gọn, thực tế, thân thiện. KHÔNG bịa thông tin ngoài tài liệu."
)


def answer_with_context(question: str, chunks: list[dict]) -> str:
    """Sinh câu trả lời cho `question` chỉ dựa trên `chunks` (RAG).

    Có LLM: tổng hợp từ context. Offline: trả thẳng đoạn liên quan nhất (vẫn grounded).
    """
    if not chunks:
        return "Mình chưa tìm thấy thông tin phù hợp trong tài liệu."
    llm = get_llm()
    if llm is None:
        return chunks[0]["text"]
    context = "\n\n".join(f"[Đoạn {i + 1}] {c['text']}" for i, c in enumerate(chunks))
    prompt = (
        f"TÀI LIỆU THAM KHẢO:\n{context}\n\n"
        f"CÂU HỎI: {question}\n\nHãy trả lời dựa trên tài liệu tham khảo."
    )
    try:
        resp = llm.invoke([("system", _RAG_SYS), ("human", prompt)])
        return resp.content.strip() or chunks[0]["text"]
    except Exception:
        return chunks[0]["text"]
