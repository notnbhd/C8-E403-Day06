# Task 0 — Kiến trúc Agent & Interface Contract

> **Owner:** Agent workflow
> **Mục đích:** Chốt scope, kiến trúc agent, và *hợp đồng giao tiếp* (interface) giữa 4 vai trò.
> Đây là tài liệu cả nhóm phải đọc & confirm trước khi mỗi người code phần của mình.
> **Stack:** LangGraph + FastAPI + Supabase (Postgres). Webapp mô phỏng Hevy mobile.

---

## 1. Chốt scope (giải quyết mâu thuẫn spec vs. images)

Thin-spec mô tả phạm vi hẹp (insight layer, chỉ trả lời câu hỏi). Các ảnh chatbot lại hứa nhiều hơn (build plan, tạo routine). Để không vỡ timeline, ta chia **3 tầng**:

| Tầng | Năng lực | Trạng thái | Lý do |
|---|---|---|---|
| **P0 — Phải demo** | `analyze_progress`, `detect_plateau`, `muscle_gap` | Bắt buộc | Đúng pain gốc trong spec: "có data nhưng không actionable". Demo được trong 3-5 phút. |
| **P1 — Stretch** | `build_plan`, `progression_advice`, `create_routine` (ghi Hevy có confirm) | Làm nếu P0 xong | Khớp ảnh. `create_routine` chỉ ghi sau khi user confirm (đúng mô hình Augmentation). |
| **P2 — Backlog** | Logging bằng chat, voice input, so sánh với user khác | Không làm | Đã loại trong synthesis-decide. |

**Quyết định Auto/Aug:** Augmentation — AI gợi ý, **user là decider**. Hệ quả kiến trúc: mọi hành động *ghi* (create_routine) phải dừng lại chờ user xác nhận, không bao giờ tự động ghi.

---

## 2. Vai trò Agent workflow nằm ở đâu

```
┌──────────┐     HTTP/SSE      ┌─────────────────────────┐
│  UI/UX   │ ◄───────────────► │   AGENT WORKFLOW (LangGraph)  │
│ (webapp) │                   │   - router/intent             │
└──────────┘                   │   - reasoning loop            │
                               │   - failure paths + guardrail │
                               └───────┬─────────────┬─────────┘
                                       │ tool call   │ tool call
                                ┌──────▼──────┐ ┌────▼─────────┐
                                │ Backend/DB  │ │     RAG      │
                                │ (Supabase)  │ │ (knowledge)  │
                                └─────────────┘ └──────────────┘
```

Agent **không** sở hữu: UI components, schema bảng Supabase, vector store. Agent **sở hữu**: graph orchestration, prompt, và *định nghĩa signature tool* mà Backend/RAG phải implement (mục 5).

---

## 3. Sơ đồ graph (LangGraph StateGraph)

```
                    ┌─────────────┐
   /chat  ─────────►│   router    │  intent classification
                    └──────┬──────┘
       ┌───────────┬───────┼────────────┬──────────────┐
       ▼           ▼       ▼            ▼              ▼
 ┌──────────┐ ┌────────┐ ┌────────┐ ┌─────────┐  ┌──────────┐
 │fetch_data│ │  rag   │ │clarify │ │ general │  │  (P1)    │
 │(Supabase)│ │        │ │ (hỏi   │ │  chat   │  │build_plan│
 └────┬─────┘ └───┬────┘ │  lại)  │ └────┬────┘  └────┬─────┘
      ▼           │      └───┬────┘      │            │
 ┌──────────┐     │          │           │            ▼
 │ analyze  │     │          │           │     ┌──────────────┐
 │ (trend/  │     │          │           │     │ confirm_write│
 │ plateau) │     │          │           │     │ interrupt()  │ ◄─ chờ user OK
 └────┬─────┘     │          │           │     └──────┬───────┘
      └─────┬─────┴──────────┼───────────┼────────────┘
            ▼                │           │
     ┌──────────────┐        │           │
     │  guardrail   │        │           │   (check đủ data, thêm disclaimer)
     └──────┬───────┘        │           │
            ▼                ▼           ▼
     ┌─────────────────────────────────────┐
     │              respond                 │  stream về UI
     └─────────────────────────────────────┘
```

### State schema
```python
from typing import TypedDict, Literal, Annotated
from langgraph.graph.message import add_messages

Intent = Literal["analyze","plateau","muscle_gap","build_plan",
                 "create_routine","progression","clarify","general"]

class AgentState(TypedDict):
    messages:        Annotated[list, add_messages]
    user_id:         str
    intent:          Intent
    workout_data:    dict | None      # output từ tool Backend
    knowledge:       list | None      # output từ tool RAG
    pending_routine: dict | None      # routine chờ user confirm ghi
    data_sufficient: bool             # guardrail: có ≥3 buổi tập không
```

**Memory:** dùng `PostgresSaver` của LangGraph trỏ vào Supabase. `thread_id = conversation_id`. → memory đa lượt + resume hội thoại miễn phí, không tự code.

---

## 4. Mapping 4 failure paths → node

| Path (thin-spec §6) | Node xử lý | Hành vi |
|---|---|---|
| Happy | `analyze` → `respond` | Trả lời kèm số liệu thực ("Bench +14% trong 4 tuần") |
| Low-confidence | `router` → `clarify` | Query mơ hồ → hỏi lại bài/nhóm cơ nào |
| Failure | `fetch_data` (rỗng) → `respond` | "Không thấy data bài này trong lịch sử của bạn" |
| Correction | `router` (đọc messages) → re-`analyze` | User sửa ("tháng trước nghỉ ốm") → acknowledge & điều chỉnh |

**Guardrail sức khỏe** (failure mode nguy hiểm nhất): node `guardrail` luôn (1) check `data_sufficient`, nếu < 3 buổi thì từ chối kết luận; (2) frame gợi ý là "dựa trên data" + thêm disclaimer chấn thương/mệt mỏi.

---

## 5. ⭐ INTERFACE CONTRACT — phần cả nhóm phải chốt

Agent gọi các function dưới đây qua LangGraph `ToolNode`. **Backend và RAG implement đúng signature này.** Agent không quan tâm bên trong làm gì (Supabase query hay vector search) — chỉ cần đúng I/O.

### 5.1 Kiểu dữ liệu chung
```python
# Một set đã log
Set = {
    "date": "2026-05-30",        # ISO date
    "exercise_name": "Bench Press",
    "weight_kg": 80.0,
    "reps": 5,
    "set_number": 1,
}
```

### 5.2 Tool đọc/ghi → **Backend team (Supabase)**

```python
def get_workout_history(
    user_id: str,
    exercise_name: str | None = None,   # None = tất cả bài
    start_date: str | None = None,      # ISO; None = từ đầu
    end_date: str | None = None,
) -> list[Set]:
    """Trả về các set đã log, sort theo date tăng dần."""

def get_exercise_summary(user_id: str) -> list[dict]:
    """Mỗi bài: {exercise_name, last_performed (ISO), total_volume_kg,
                 best_est_1rm_kg, session_count}."""

def get_muscle_group_volume(user_id: str, time_range_days: int = 28) -> dict:
    """{muscle_group: total_volume_kg} trong N ngày gần nhất.
       Dùng cho muscle_gap. VD {'chest': 12000, 'back': 4000, ...}"""

def list_exercise_catalog() -> list[dict]:
    """Danh mục bài Hevy: [{exercise_id, name, muscle_group}].
       Dùng khi tạo routine để map tên -> exercise_id."""

def create_routine(user_id: str, routine: dict) -> dict:
    """Ghi routine vào Hevy. CHỈ gọi sau khi user confirm.
       routine = {
         'name': str,
         'exercises': [{'exercise_id': str, 'sets': int,
                        'reps': str, 'rest_sec': int}]
       }
       return {'routine_id': str}"""
```

### 5.3 Tool kiến thức → **RAG team**

```python
def search_fitness_knowledge(query: str, k: int = 4) -> list[dict]:
    """Vector search trên tài liệu fitness (progressive overload,
       hypertrophy, rep ranges, deload...).
       return [{'text': str, 'source': str}]"""
```

### 5.4 Hợp đồng lỗi (mọi tool)
- Không có data → trả về **rỗng** (`[]` / `{}`), **không** raise. Agent tự xử lý path Failure.
- Lỗi hệ thống (DB down) → raise `ToolError`; agent trả lời degrade lịch sự.
- `create_routine` lỗi ghi → raise; agent báo user thử lại, **không** giả vờ thành công.

---

## 6. API surface (FastAPI) — hợp đồng với UI/UX

```
POST /chat
  body:  { user_id: str, conversation_id: str, message: str }
  resp:  text/event-stream (SSE) — token-by-token

POST /chat/resume        # user bấm confirm/cancel routine
  body:  { conversation_id: str, approved: bool, edits?: {...} }
  resp:  text/event-stream

GET  /conversations/{user_id}     # list lịch sử (optional P1)
```

**Sự kiện đặc biệt cho UI:** khi graph chạm `interrupt()` ở `confirm_write`, stream phát một event `type: "routine_preview"` chứa routine đề xuất → UI render nút **Confirm / Edit / Cancel** → gọi `/chat/resume`.

---

## 7. Ranh giới trách nhiệm (RACI gọn)

| Hạng mục | UI/UX | Backend | RAG | Agent (bạn) |
|---|---|---|---|---|
| Chat interface, render preview routine | **R** | | | C |
| Schema Supabase, seed mock Hevy data | | **R** | | C |
| Implement 6 tool ở §5.2 | | **R** | | A (định nghĩa) |
| Vector store + `search_fitness_knowledge` | | | **R** | A (định nghĩa) |
| LangGraph graph, router, prompt, failure paths | | | | **R** |
| FastAPI endpoints §6 | C | C | | **R** |
| Checkpointer (Supabase URL) | | **C** (cấp URL) | | **R** |

> R = làm, A = chịu trách nhiệm/định nghĩa, C = phối hợp.

---

## 8. Critical path & thứ tự

```
Task 0 (doc này) ──► chốt §5 + §6
        │
        ├──► Backend bắt đầu: tạo schema + implement 6 tool (mock data trước)
        ├──► RAG bắt đầu: nạp tài liệu + search_fitness_knowledge
        ├──► UI bắt đầu: chat UI + routine preview component
        └──► Agent: dựng graph với MOCK tool, thay dần bằng tool thật
```

Mọi người **không bị block** vì cùng code theo interface ở §5/§6. Agent dùng mock tool để chạy end-to-end ngay ngày 1, Backend/RAG thay implementation thật vào sau mà không đổi signature.

---

## 9. Câu hỏi cần nhóm confirm (chốt trong standup)

1. **Scope:** Đồng ý P0 = analyze/plateau/muscle_gap là must-demo, build_plan/create_routine là P1? ✅/❌
2. **Mock Hevy data:** Backend seed bao nhiêu user mẫu, mỗi user mấy tháng lịch sử? (cần ≥1 user có ≥3 tháng để demo trend)
3. ✅ **CHỐT — Model LLM:** Dùng **OpenRouter** (gateway OpenAI-compatible). LangGraph/LangChain dùng `ChatOpenAI` với `base_url="https://openrouter.ai/api/v1"` + `OPENROUTER_API_KEY`. Đổi model chỉ cần đổi tên model string → linh hoạt thử nhiều model.
4. ✅ **CHỐT — Mô phỏng Hevy:** `create_routine` **ghi vào Supabase** của nhóm, **không** gọi Hevy API thật. Backend làm bảng `routines`/`routine_exercises`.
5. **Exercise catalog:** Lấy danh mục bài từ đâu — seed cứng một list ~50 bài phổ biến? (Backend chủ trì)

---

## 10. Định nghĩa "xong" cho Task 0
- [x] Scope phân tầng P0/P1/P2
- [x] Sơ đồ graph + state schema
- [x] 4 failure paths map vào node
- [x] Interface contract §5 (6 tool + RAG) với I/O rõ ràng
- [x] API surface §6
- [x] Bảng trách nhiệm + critical path
- [ ] **Nhóm confirm §9** ← việc còn lại, làm ở standup
