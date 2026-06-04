# Thin SPEC — Hevy AI Insight Chatbot

## 1. Track, product/app và user

**Track:** Healthcare  
**Product/app thật:** Hevy 
**User cụ thể:** Người tập gym 3-5 buổi/tuần, đã dùng Hevy ≥ 1 tháng, có data lịch sử nhưng không biết cách đọc để ra quyết định tập  
**Nhóm có phải user thật không?** Có — các thành viên tự dùng Hevy hoặc app workout tương tự; khác ở chỗ nhóm biết đọc biểu đồ, user thông thường thì không.

---

## 2. Evidence summary

| Evidence | Nguồn | User/pain nói lên điều gì? | SPEC phải đổi gì? |
|---|---|---|---|
| "App có đủ số liệu nhưng không nói gì — tôi tự đoán mình có tiến bộ không" | Đăng (self-use) | User có data nhưng không có insight | Build slice phải trả lời câu hỏi tự nhiên, không redirect sang biểu đồ |
| "Không biết khi nào nên tăng tạ — không có gì nhắc hay gợi ý" | Sỉ (self-use) | Thiếu trigger để ra quyết định progressive overload | AI phải chủ động gợi ý dựa trên trend, không chờ user hỏi |
| "3 tháng data mà không rút ra được gì — chỉ thấy một đống con số" | Tuấn Anh (self-use) | Long-term data tích lũy nhưng không actionable | Cần lớp interpretation tự nhiên trên data có sẵn |

---

## 3. Pain statement

```
User gym thường xuyên đang gặp khó ở bước diễn giải data tập luyện của chính mình,
vì Hevy chỉ hiển thị số liệu thô và biểu đồ mà không có nhận xét hay gợi ý,
dẫn tới user không biết mình có đang tiến bộ không, không biết khi nào tăng tạ,
và phải dùng workaround (copy data sang ChatGPT) để có câu trả lời.
Bằng chứng chính là App Store review "tells me nothing" và observation ChatGPT workaround.
```

---

## 4. Build slice

```
Cho user gym đã có ≥ 1 tháng lịch sử tập trong Hevy,
prototype sẽ dùng AI để phân tích data lịch sử và trả lời câu hỏi tự nhiên về tiến độ,
tạo ra nhận xét có dẫn số liệu thực tế (ví dụ: "Bench press của bạn tăng 8% trong 4 tuần qua"),
và xử lý failure mode "query quá mơ hồ hoặc không đủ data" bằng cách hỏi lại hoặc nói rõ giới hạn.
```

---

## 5. Auto/Aug decision

- [x] **Augmentation:** AI phân tích và đưa ra nhận xét/gợi ý, user quyết định có làm theo không.
- [ ] **Conditional automation:** AI tự làm trong case hẹp; case mơ hồ/rủi ro chuyển người.
- [ ] **Automation:** AI tự quyết và tự hành động.

**Lý do chọn:** Quyết định tập luyện (tăng tạ, thay bài) ảnh hưởng đến sức khoẻ — AI chỉ nên gợi ý, không tự áp đặt. User giữ quyền quyết định cuối.  
**Human role:** decider — AI cung cấp analysis, user quyết định có làm theo không.

---

## 6. Four paths

| Path | Prototype phải thể hiện gì? |
|---|---|
| Happy | User hỏi "bench press của tôi có tiến bộ không?" → AI trả lời với số liệu thực: "4 tuần qua bạn tăng từ 70kg lên 80kg 1RM (+14%). Tiến bộ tốt." |
| Low-confidence | User hỏi "tôi có đang tập tốt không?" → AI không đủ context, hỏi lại: "Bạn muốn check bài nào cụ thể? Hoặc nhóm cơ nào?" |
| Failure | User hỏi về bài tập chưa từng log trong Hevy → AI nói rõ: "Tôi không thấy data cho bài này trong lịch sử của bạn. Bạn đã log chưa?" |
| Correction | AI đưa ra nhận xét sai về trend → User nói "không đúng, tháng trước tôi bị nghỉ ốm" → AI acknowledge và điều chỉnh nhận xét |

---

## 7. Failure mode nguy hiểm nhất

```
Nếu user hỏi "tôi có nên tăng tạ không?" mà AI không biết context (mệt mỏi, chấn thương),
AI có thể đưa ra gợi ý tăng tạ không phù hợp với tình trạng thực tế của user,
hậu quả là user làm theo và bị chấn thương, mất trust hoàn toàn vào feature.
Prototype sẽ xử lý bằng: AI luôn frame gợi ý là "dựa trên data" và thêm disclaimer
"nếu bạn đang mệt hoặc có chấn thương, hãy ưu tiên recovery trước."
Owner kiểm thử path này là Tuấn Anh.
```

---

## 8. Owner plan cho sáng Day 06

| Thành viên | Việc phụ trách | Bằng chứng cần có trong repo |
|---|---|---|
| Đăng | Research / evidence — tìm thêm review Hevy và xác nhận workaround ChatGPT | evidence-pack cập nhật với ≥ 3 external quotes |
| Sỉ | SPEC — hoàn thiện thin-spec, cập nhật 4 paths sau khi test prototype | thin-spec final version |
| Tuấn Anh | Prototype + test failure path — build chat UI, test case plateau và query mơ hồ | prototype/ folder + ≥ 5 test cases |
| Văn | Demo script / repo — chuẩn bị flow demo 3-5 phút với mock Hevy data | demo-script.md |
