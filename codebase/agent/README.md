# Agent Workflow — Hevy AI Insight Chatbot

**ReAct agent** (LangGraph `create_react_agent`) đọc dữ liệu tập Hevy và trả lời câu
hỏi về tiến độ. LLM tự chọn tool; **mọi con số do Python tính trong tool, LLM không
bịa** (grounding). Thiết kế & interface:
[`../docs/agent-workflow/00-architecture-and-contracts.md`](../docs/agent-workflow/00-architecture-and-contracts.md).

## Cài & chạy

```bash
uv pip install -r codebase/agent/requirements.txt      # vào .venv hiện tại
PYTHONPATH=codebase python -m pytest codebase/agent/tests -q
```

Test gồm 2 nhóm: **analysis thuần** (deterministic, chạy offline không cần key) +
**integration** gọi LLM thật (tự `skip` nếu thiếu key — `conftest.py` chủ động xoá
key để CI chạy offline).

ReAct **bắt buộc có LLM** để hoạt động (không còn chế độ template offline). Cấu hình
một trong hai: `OPENROUTER_API_KEY` hoặc `CUSTOM_LLM_KEY` (OpenAI-compatible).

```bash
# Bật LLM thật:
export OPENROUTER_API_KEY=sk-or-...
export AGENT_MODEL=anthropic/claude-3.5-sonnet   # đổi model tuỳ ý
```

## Dùng từ UI (Streamlit import trực tiếp, không cần HTTP)

```python
from agent.runner import chat, resume

out = chat(user_id="demo-user", conversation_id="c1",
           message="Bench Press của tôi có tiến bộ không?")
# out = {"status": "ok", "reply": "...", "intent": "analyze"}

# Luồng tạo routine cần xác nhận:
out = chat("demo-user", "c1", "tạo routine và lưu vào app")
# out["status"] == "awaiting_confirm", out["routine"] = preview
done = resume("c1", approved=True)        # hoặc approved=False để huỷ
```

Hoặc chạy HTTP API: `uvicorn agent.api:app --reload` → `POST /chat`, `POST /chat/resume`.

## Cấu trúc

| File | Vai trò |
|---|---|
| `analysis.py` | **Pure functions** tính 1RM/trend/plateau/muscle-gap (lớp grounding) |
| `tools.py` | **Interface contract** §5 — data layer (mock ↔ Supabase); Backend/RAG thay impl, giữ signature |
| `react_tools.py` | Các `@tool` ReAct (wrap analysis+tools, giữ grounding) + system prompt + `CoachState` |
| `llm.py` | Khởi tạo model LLM (OpenRouter / custom) cho ReAct |
| `graph.py` | Dựng ReAct agent (`create_react_agent`) |
| `runner.py` | API public cho UI (`chat`, `resume`) |
| `api.py` | FastAPI (tuỳ chọn) |

Routine có **human-in-the-loop**: tool `save_routine` gọi `interrupt()` → graph dừng,
UI hiện preview + nút Lưu/Huỷ → `resume(approved=...)` mới ghi DB.

## Cho Backend & RAG

Chỉ cần implement đúng các hàm trong `tools.py` (signature + shape output giữ
nguyên), agent không phải đổi gì:
- **Backend:** `get_workout_history`, `get_exercise_summary`,
  `get_muscle_group_volume`, `list_exercise_catalog`, `create_routine` (ghi Supabase).
- **RAG:** `search_fitness_knowledge`.

Memory hội thoại hiện dùng `MemorySaver` (in-process). Production đổi sang
`PostgresSaver` trỏ Supabase — chỉ sửa `runner.py`.
