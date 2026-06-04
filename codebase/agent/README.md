# Agent Workflow — Hevy AI Insight Chatbot

LangGraph agent đọc dữ liệu tập Hevy và trả lời câu hỏi về tiến độ.
Thiết kế & interface đầy đủ: [`../docs/agent-workflow/00-architecture-and-contracts.md`](../docs/agent-workflow/00-architecture-and-contracts.md).

## Cài & chạy

```bash
uv pip install -r codebase/agent/requirements.txt      # vào .venv hiện tại
PYTHONPATH=codebase python -m pytest codebase/agent/tests -q   # 11 test, chạy offline
```

Không cần `OPENROUTER_API_KEY` để test: thiếu key thì agent chạy ở chế độ
template offline (router bằng keyword, câu trả lời dùng thẳng draft). Có key thì
LLM diễn đạt lại cho tự nhiên — **mọi con số vẫn do Python tính, LLM không bịa**.

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
| `state.py` | AgentState (schema LangGraph) |
| `analysis.py` | **Pure functions** tính 1RM/trend/plateau/muscle-gap (lớp grounding) |
| `tools.py` | **Interface contract** §5 — hiện mock; Backend/RAG thay impl, giữ nguyên signature |
| `llm.py` | OpenRouter + fallback offline (router + diễn đạt) |
| `nodes.py` | Các node graph + guardrail sức khoẻ |
| `graph.py` | Lắp StateGraph |
| `runner.py` | API public cho UI (`chat`, `resume`) |
| `api.py` | FastAPI (tuỳ chọn) |

## Cho Backend & RAG

Chỉ cần implement đúng các hàm trong `tools.py` (signature + shape output giữ
nguyên), agent không phải đổi gì:
- **Backend:** `get_workout_history`, `get_exercise_summary`,
  `get_muscle_group_volume`, `list_exercise_catalog`, `create_routine` (ghi Supabase).
- **RAG:** `search_fitness_knowledge`.

Memory hội thoại hiện dùng `MemorySaver` (in-process). Production đổi sang
`PostgresSaver` trỏ Supabase — chỉ sửa `runner.py`.
