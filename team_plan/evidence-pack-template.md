# Evidence Pack — Hevy Chatbot

## 1. Nhóm và track

**Tên nhóm:** Hevy chatbot  
**Track:** Healthcare  
**Product/app đã chọn:** Hevy 
**Build slice đang nghĩ:** AI insight layer — chatbot trả lời câu hỏi về lịch sử tập bằng ngôn ngữ tự nhiên, dựa trên data Hevy đã có

---

## 2. Self-use evidence

| Observation | Path liên quan | Điều học được |
|---|---|---|
| Hevy show biểu đồ 1RM và volume theo tuần nhưng không có nhận xét. Người dùng phải tự đọc số và tự kết luận mình có đang tiến bộ không | Failure | Data có nhưng không actionable — thiếu lớp interpretation |
| Sau 3 tuần tập bench cùng 1 mức tạ, app không cảnh báo hay gợi ý gì — user không biết mình đang plateau | Failure | App không chủ động. User chỉ biết mình bị plateau khi đã lâu, không có trigger để hành động |
| Hỏi "khi nào thì nên tăng tạ?" — không có tính năng này trong app; user phải tự googling nguyên tắc progressive overload | Failure | Gap rõ nhất: dữ liệu ở đây, nhưng knowledge để ra quyết định thì không |

---

## 3. Observation từ thành viên nhóm khi dùng app

| Quote / observation | Thành viên | Bối cảnh | Pain/failure mode |
|---|---|---|---|
| "App có đủ số liệu nhưng không nói gì — tôi phải tự nhìn biểu đồ và tự đoán mình có đang tiến bộ không" | Đăng | Dùng Hevy 2 tháng, tập bench và squat đều đặn | Data rich, insight poor |
| "Tôi không biết khi nào nên tăng tạ — cứ tập đến khi cảm giác dễ thì tăng, không có gì nhắc hay gợi ý" |  | Tập gym 3 buổi/tuần, không có PT | Thiếu trigger để ra quyết định progressive overload |
| "Nhìn lại 3 tháng data mà không rút ra được gì — chỉ thấy một đống con số" |  | Dùng app hơn 3 tháng, có lịch sử đầy đủ | Long-term data tích lũy nhưng không actionable |
| "Muốn biết nhóm cơ nào mình đang bỏ bê nhưng phải tự đếm tay từng bài trong lịch sử" |  | Tập full body, lo ngại mất cân bằng cơ thể | Không có lớp phân tích tự động trên data có sẵn |

---

## 4. Competitor / analog evidence

| App / mô hình tham khảo | Họ xử lý task này thế nào? | Pattern học được |
|---|---|---|
| Fitbod | AI gợi ý bài tập dựa trên fatigue model và lịch sử — nhưng không giải thích tại sao | AI recommendation có giá trị, nhưng thiếu transparency làm giảm trust |
| ChatGPT + manual data | User copy-paste data vào ChatGPT để hỏi "tôi có tiến bộ không?" | Workaround hiện tại của nhiều user — đây chính là pain đang chờ được giải |

---

## 5. Evidence → Insight

```
Evidence nổi bật nhất:
User đã có data (tháng, năm lịch sử tập) nhưng không tự khai thác được.
Workaround hiện tại là copy data sang ChatGPT — đây là signal rõ về nhu cầu thật.

Insight:
User không chỉ cần một chỗ để lưu số liệu tập luyện.
Thật ra họ cần một lớp ra quyết định trên data đó:
khi nào tăng tạ, mình có đang tiến bộ không, cơ nào đang bỏ bê.

Opportunity:
AI có thể augment lớp này bằng cách trả lời câu hỏi tự nhiên từ data Hevy đã có,
thay vì yêu cầu user tự đọc biểu đồ và tự kết luận.
```

---

## 6. Evidence đổi SPEC như thế nào?

```
Trước evidence, nhóm định build chatbot để log workout bằng ngôn ngữ tự nhiên.
Sau evidence, nhóm đổi sang AI insight layer: chatbot trả lời câu hỏi về data có sẵn.
Lý do: logging bằng chat không giảm đáng kể friction so với tap UI.
Pain thật là user không khai thác được data họ đã có — đây là gap AI có thể lấp được rõ ràng hơn.
```
