# Từ Evidence Đến Build Slice — Hevy Chatbot

## 1. Cụm pain (theo workflow, không theo feature)

- "Tôi không biết mình có đang tiến bộ không"
- "App không nói gì khi tôi bị plateau"
- "Tôi không biết khi nào nên tăng tạ"
- "Tôi có data nhưng phải tự copy sang ChatGPT để hỏi"

---

## 2. Insight

```
User gym thường xuyên không chỉ cần một chỗ lưu số liệu tập luyện.
Họ thật ra cần lớp ra quyết định trên data đó,
vì tất cả evidence (review, self-use, workaround ChatGPT) đều cho thấy
user có data nhưng không biết phải làm gì với nó.
```

---

## 3. Opportunity

```
Cơ hội là dùng AI để augment lớp interpretation trên data Hevy có sẵn,
giúp user trả lời được câu hỏi "tôi có đang tiến bộ không / khi nào tăng tạ",
trong khi vẫn kiểm soát failure bằng cách AI luôn dẫn số liệu thực tế kèm theo nhận xét.
```

---

## 4. Build slice

Build slice đã qua 5 câu hỏi kiểm tra:

| Câu hỏi | Trả lời |
|---|---|
| User cụ thể chưa? | Người tập gym 3-5 buổi/tuần, đã dùng Hevy ≥ 1 tháng, có data lịch sử |
| Task đủ hẹp chưa? | Chatbot trả lời 3 loại query: progress, plateau detection, muscle gap — demo được trong 3-5 phút |
| AI decision rõ chưa? | AI phân tích trend từ data thực và đưa ra nhận xét + gợi ý cụ thể |
| Failure path rõ chưa? | Case AI không đủ data (< 3 buổi) hoặc query quá mơ hồ — hỏi lại |
| Có evidence không? | Có: App Store review, Reddit, self-use observation, ChatGPT workaround |

---

## 5. Quyết định: giữ hướng AI insight layer

Không giảm scope thêm — "trả lời câu hỏi về progress" đã đủ hẹp để demo trong 1 ngày.  
Loại bỏ: logging bằng chat (friction không giảm đáng kể), gợi ý workout plan (cần data recovery ngoài scope Hevy).

---

## 6. Câu chốt

```
Dựa trên evidence từ App Store review, Reddit, và self-use (data có nhưng không actionable),
nhóm sẽ build prototype chatbot insight layer trên Hevy data,
cho user gym đã có lịch sử tập ≥ 1 tháng,
để giải quyết pain "có data nhưng không biết mình đang tiến bộ hay plateau",
bằng cách AI augment lớp interpretation: trả lời câu hỏi tự nhiên từ data thực,
và sẽ test failure path: AI không đủ data hoặc query quá mơ hồ để trả lời.
```

---

## 7. Backlog (không build trong Day 06)

- Chatbot logging: gõ workout vào chat thay vì tap UI
- AI gợi ý workout plan cá nhân hóa (cần fatigue/recovery data)
- Tích hợp voice input
- So sánh progress với user khác (cần social data)
