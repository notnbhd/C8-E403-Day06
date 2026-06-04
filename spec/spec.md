# SPEC — Hevy AI Insight Chatbot

**Track:** Healthcare · **Product nền:** Hevy (workout tracker) · **Nhóm:** Hevy Chatbot

> Một câu: *Người tập gym đã có hàng tháng dữ liệu trong Hevy nhưng không tự đọc được — chatbot này là **lớp diễn giải bằng AI** trả lời câu hỏi tự nhiên về tiến độ và gợi ý hành động, với **mọi con số do code tính** (AI không bịa) và **mọi thao tác ghi đều cần người xác nhận**.*

---

## 1. Bằng chứng

### 1.1 Trải nghiệm trực tiếp (self-use)
Thành viên nhóm tự dùng Hevy và chụp lại các màn hình cho thấy **dữ liệu rất giàu nhưng không có nhận xét** (xem `team_plan/image*.png`):

| Quan sát (ảnh) | Hevy hiển thị | Chỗ vướng |
|---|---|---|
| Workout Detail | Từng set: `40kg × 9`, `50kg × 10`… | Số thô, không nói buổi này tốt/xấu |
| Muscle Split | Arms 38% · Back 36% · Chest 21% | Có % nhưng **không** gợi ý nên bù nhóm nào |
| Profile / Statistics | Biểu đồ volume theo tuần, "Last 3 months" | User phải tự nhìn biểu đồ tự kết luận |
| Routine | Biểu đồ volume 4218kg lên xuống | Không nói đang tiến bộ hay chững |

### 1.2 Quote từ thành viên (evidence-pack)
- **Đăng** (Hevy 2 tháng): *"App có đủ số liệu nhưng không nói gì — tôi phải tự nhìn biểu đồ và tự đoán mình có đang tiến bộ không."*
- **Sỉ** (3 buổi/tuần, không PT): *"Không biết khi nào nên tăng tạ — không có gì nhắc hay gợi ý."*
- **Tuấn Anh** (>3 tháng data): *"Nhìn lại 3 tháng data mà không rút ra được gì — chỉ thấy một đống con số."*
- **Văn** (tập full body): *"Muốn biết nhóm cơ nào đang bỏ bê nhưng phải tự đếm tay từng bài."*

### 1.3 Nguồn ngoài nhóm
| Nguồn | Cho thấy điều gì | Trạng thái |
|---|---|---|
| App Store review *"tells me nothing"* | User khác cũng thấy app không đưa nhận xét | ⚠️ **Cần đính link/screenshot** trước demo |
| ChatGPT workaround | Nhiều user copy data sang ChatGPT để hỏi "tôi có tiến bộ không?" | Observation — signal nhu cầu thật |
| Fitbod (analog) | AI gợi ý bài theo fatigue model nhưng **không giải thích vì sao** → giảm trust | Pattern: recommendation phải kèm transparency |

> Theo hướng dẫn README: quote App Store/Reddit hiện là **nhận định cần bổ sung nguồn** — nhóm phải gắn link hoặc ảnh chụp; nếu không tìm được thì hạ xuống thành giả định.

**Insight rút ra:** User không cần thêm chỗ lưu số — họ cần **lớp ra quyết định trên data đã có**: tôi có tiến bộ không, khi nào tăng tạ, cơ nào đang bỏ bê.

---

## 2. Lát cắt để build

```
Cho một user gym đã có ≥ 1 tháng lịch sử trong Hevy,
chatbot dùng AI để ĐỌC data lịch sử và TRẢ LỜI câu hỏi tự nhiên về tiến độ
(tiến bộ / plateau / nhóm cơ bỏ bê) — mỗi nhận xét đều DẪN số liệu thật do code tính,
và có thể ĐỀ XUẤT một routine để user xác nhận lưu vào app chỉ bằng một thao tác.
```

- **Một user:** người tập đều, có data, không biết đọc.
- **Một việc:** diễn giải data tập của chính họ.
- **Một quyết định AI:** chọn công cụ phân tích phù hợp + diễn đạt kết quả; (mở rộng) đề xuất routine.
- **Một kết quả:** câu trả lời có số liệu thật + (tuỳ chọn) routine chờ xác nhận.

Đã loại khỏi slice: log workout bằng chat (không giảm friction so với tap), so sánh với user khác (cần social data), voice input.

---

## 3. AI Product Canvas

| Ô | Trả lời |
|---|---|
| **Value** | Dành cho người tập gym có data Hevy nhưng "data rich, insight poor". AI lấp đúng lớp diễn giải mà app gốc và cách tự-nhìn-biểu-đồ không làm được — trả lời bằng ngôn ngữ tự nhiên, chủ động chỉ ra plateau/mất cân bằng. |
| **Trust** | (1) **Số do Python tính, không phải LLM** → không bịa số. (2) Khi thiếu data → nói thẳng "chưa đủ buổi", không kết luận. (3) Lời khuyên luôn kèm **disclaimer sức khoẻ**. (4) RAG chỉ trả lời theo tài liệu + trích nguồn; không có thì nói "tài liệu không đề cập" (không bịa nguồn). (5) Mọi thao tác **ghi DB** (lưu routine) phải qua **nút xác nhận** — huỷ là không ghi gì. |
| **Feasibility** | LLM qua OpenRouter (gpt-4o-mini), ~1–3 lượt gọi/câu; phân tích chạy local nên rẻ & nhanh. Dữ liệu: bảng workout_sets/exercises/routines trên Supabase (Postgres); có mock fallback chạy offline. Rủi ro lớn nhất: lời khuyên tập sai gây chấn thương → chặn bằng disclaimer + ngưỡng đủ-buổi + người xác nhận. Ngưỡng dừng: nếu LLM bịa số (dù đã grounding) thì cắt tính năng khuyên. |
| **Tín hiệu học** | Khi user **sửa** yêu cầu (vd "không, tập trung tay sau"), agent honor ngay nhờ **conversation memory** (checkpointer theo `thread_id`). Toàn bộ lượt chat được log (`logging_config`). **Roadmap (chưa đóng vòng):** gom các lần user huỷ/sửa routine thành **bộ test hồi quy** + tinh chỉnh prompt — hiện chưa có pipeline tự động. |

---

## 4. Tăng năng lực hay tự động hóa

**Lựa chọn: Augmentation (tăng năng lực), có một thao tác ghi được kiểm soát.**

- AI **phân tích & gợi ý**, user là **người quyết định** có làm theo không — không có tính năng nào tự áp đặt thay đổi tập luyện.
- Thao tác duy nhất chạm dữ liệu (lưu routine) chạy theo **human-in-the-loop**: AI dựng preview → `interrupt()` dừng → user bấm **Lưu/Huỷ** → chỉ ghi DB sau khi xác nhận.
- **Vì sao mức này:** quyết định tập (tăng tạ, đổi bài) ảnh hưởng sức khoẻ — sai thì hậu quả nặng. Nhưng vì AI chỉ gợi ý và mọi ghi đều **dễ hoàn tác (chưa bấm Lưu là chưa có gì)** nên augmentation là mức đúng, không cần leo lên automation.

---

## 5. Bốn đường đi của trải nghiệm

Map trực tiếp vào hệ thống đã build hôm nay (ReAct agent + tools grounding + confirm routine):

| Đường đi | User làm gì | Hệ thống xử lý (đã chạy thật) |
|---|---|---|
| **Đường thuận** (AI đúng & tự tin) | "Bench Press của tôi tiến bộ không?" | "1RM 70→84.6kg qua 8 tuần (**+20.9%**) 📈" + disclaimer. Đề xuất routine → **bấm Lưu (1 thao tác)** là xong. |
| **Khi AI không chắc** | "Barbell Row tôi tiến bộ chưa?" (mới 1 buổi) | `data_sufficient=false` → "Mới 1 buổi, **chưa đủ** để kết luận (cần ≥3). Cứ log thêm nhé" — không bịa xu hướng, gợi mở hướng khác. |
| **Khi AI sai / không vừa ý** | AI đề xuất routine không đúng ý | Thẻ preview có nút **Huỷ** → "Chưa lưu gì cả" (gỡ ra an toàn vì chưa ghi DB). |
| **Khi người dùng sửa** | "À không, tôi muốn tập trung ngực" | Agent dựng lại routine đúng ý nhờ **memory**; preview mới → Lưu. (Chỉnh được honor live.) |

---

## 6. Những kiểu lỗi đáng lo nhất

| # | Kiểu lỗi | Xuất hiện khi nào / ai chịu thiệt | Prototype chặn bằng |
|---|---|---|---|
| **1** | **Khuyên tăng tạ sai ngữ cảnh** (user đang mệt/chấn thương) → user làm theo → chấn thương | Khi user hỏi "có nên tăng tạ?" mà AI không biết tình trạng cơ thể. Người dùng chịu thiệt nặng nhất. | AI luôn frame "dựa trên dữ liệu" + **disclaimer** "nếu đang mệt/chấn thương, ưu tiên hồi phục". Owner test: **Đăng**. |
| **2** | **Bịa số liệu** (sai 1RM/%, nói tiến bộ khi đang plateau) → mất trust hoàn toàn | Khi LLM tự suy số thay vì đọc tool. | **Grounding cứng**: số do `analysis.py` tính; LLM chỉ diễn đạt. Test: so số trong reply với số tool. Owner: **Đăng**. |
| **3** | **Bịa kiến thức / nguồn** (RAG trả lời ngoài tài liệu, gắn nguồn giả) | Câu hỏi ngoài phạm vi tài liệu KB. | RAG chỉ trả lời theo chunk + trích nguồn thật; không có thì nói "tài liệu không đề cập" (đã bỏ logic gắn nguồn giả). Owner: **Tuấn Anh**. |

---

## 7. Kế hoạch kiểm thử và bằng chứng demo

**Hai đầu vào chuẩn bị sẵn khi demo:**
- *Đường thuận (bình thường):* `"Bench Press của tôi dạo này thế nào?"` → trả số tăng trưởng thật + 📈.
- *Đầu vào khó / gây nhiễu:* `"Barbell Row tiến bộ chưa?"` (thiếu data) **và** `"hướng dẫn bài tập X"` (ngoài KB) → cho thấy agent phục hồi: nói thiếu data / "tài liệu không đề cập" thay vì bịa.

**Kịch bản demo 8 bước (một mạch, user `demo-user`):** Bench (happy) → "nó plateau không?" (memory + KB) → muscle gap (RAG) → Barbell Row (thiếu data) → "tạo lịch tập" (preview + **Lưu**) → **Huỷ** (undo) → "tập trung ngực" (sửa) → **Lưu** (ghi + giải thích vì sao + cách tập). Chi tiết ở `team_plan` / demo script.

**Bằng chứng giữ trong repo:**
- Test tự động: `codebase/agent/tests/` — 4 test phân tích chạy offline (deterministic) + 7 test integration (gọi LLM thật, tự skip khi không có key).
- Screenshot Hevy gốc (`team_plan/image*.png`) làm bằng chứng pain.
- Log lượt chat (`logging_config`) cho các case đã test.

---

## 8. Phân công

Slice được chia theo **4 lớp kỹ thuật**, mỗi người sở hữu một lớp đủ để tự giải thích khi demo:

| Thành viên | Lớp phụ trách | File chính | Tự giải thích được gì khi demo |
|---|---|---|---|
| **Đăng** | **Agent** (ReAct orchestration + grounding) | `codebase/agent/` — `graph.py`, `react_tools.py`, `analysis.py`, `runner.py` | Vì sao số không bị bịa (Python tính), agent chọn tool ra sao, guardrail đủ-buổi + disclaimer, luồng confirm routine (interrupt/resume). |
| **Tuấn Anh** | **RAG** (tra cứu kiến thức) | `codebase/agent/rag.py`, `codebase/ingest.py`, ChromaDB `gym_docs` | Pipeline embed/search, cách enrich "vì sao + cách tập", và vì sao không bịa nguồn (degrade an toàn về KB mock khi thiếu key). |
| **Văn** | **Frontend** (giao diện chat + demo) | `codebase/frontend/` — `server.py`, `app.js`, `index.html`, `styles.css` | Luồng chat, thẻ preview routine + nút Lưu/Huỷ, memory giữ hội thoại qua reload (localStorage CID). |
| **Sỉ** | **Database** (Supabase + contract) | `codebase/agent/repo.py`, `codebase/agent/tools.py` (schema bảng `users/exercises/workout_sets/routines` nằm trên Supabase, thể hiện qua SQL trong `repo.py`) | Hợp đồng tool (mock ↔ Supabase), cách đọc/ghi data, và degrade an toàn khi DB lỗi. |

> Lưu ý vận hành: trước demo kiểm tra Supabase còn sống (log gần đây báo pooler đóng kết nối); nếu cần chạy chắc thì đặt `AGENT_USE_MOCK_TOOLS=1` để dùng mock offline.
