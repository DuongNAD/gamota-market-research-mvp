# Nhật ký Quyết định Thiết kế & Kỹ thuật (DECISIONS.md)

Mỗi quyết định được ghi nhận liên tục trong quá trình xây dựng MVP theo định dạng: **Bối cảnh → Quyết định → Lý do**.

1. **[P0] Thu gọn phạm vi từ ý tưởng hệ thống rộng (Mission 1) về lớp "Nhận định có căn cứ"**:
   - *Bối cảnh*: Một hệ thống nghiên cứu thị trường đầy đủ thường gồm thu thập đa kênh tự động, cơ sở dữ liệu lịch sử, dashboard theo dõi định kỳ và nhiều agent chuyên biệt, nhưng làm dàn trải trong thời gian ngắn sẽ không chứng minh sâu được độ tin cậy.
   - *Quyết định*: Tập trung 100% MVP vào **lớp "nhận định có căn cứ"** (`Plan → Retrieve → Grade → Extract & Verify → Synthesize → Score`) bằng Python thuần, không dùng LangChain/CrewAI hay database.
   - *Lý do*: Tìm kiếm và tóm tắt thì chatbot nào cũng làm được; người ra quyết định tại Gamota chỉ dám dùng kết quả khi tự kiểm chứng được từng nhận định về đúng câu trích dẫn gốc, hạng nguồn và quy tắc tính điểm minh bạch.

2. **[P0] Chuẩn hóa dấu câu Unicode và giữ ngữ cảnh chứa từ khóa/số liệu trước khi xác minh trích dẫn (`verify_quote`)**:
   - *Bối cảnh*: LLM khi xuất JSON thường tự chuyển dấu ngoặc kép/gạch ngang cong (`“”‘’–—`) thành ký tự ASCII thẳng (`"'--`), và nếu cắt cứng 6.000 ký tự đầu trang web thì các đoạn chứa số liệu ở giữa bài dễ bị mất.
   - *Quyết định*: Khi cắt văn bản nguồn còn ~6.000 ký tự, ưu tiên giữ các đoạn chứa từ khóa câu hỏi và con số thống kê (`%`, `$`, `million`, `billion`, năm `2024–2026`); đồng thời chuẩn hóa Unicode (`NFKC`) và dấu câu trước khi tính `rapidfuzz.fuzz.partial_ratio >= 90`.
   - *Lý do*: Giảm tỷ lệ loại nhầm trích dẫn nguyên văn thật (false-negative) mà vẫn giữ nguyên ngưỡng khắt khe `>= 90` và không lưu toàn văn bài báo vào repo.

3. **[P0] Tách bạch hoàn toàn việc tổng hợp nội dung (LLM) và việc gán URL / chấm độ tin cậy (Code)**:
   - *Bối cảnh*: LLM rất dễ bịa URL hoặc tự đánh giá độ tin cậy "Cao" một cách cảm tính ngay cả khi chỉ dựa trên 1 bài blog không rõ nguồn gốc.
   - *Quyết định*: Cấm LLM sinh URL trong prompt (và dùng regex lọc bỏ nếu LLM vi phạm); LLM chỉ được gắn mã `evidence_id`. Module `research/score.py` tự gắn URL có Text Fragment (`#:~:text=...`) từ `Source` gốc và tính `CAO / TRUNG BÌNH / THẤP` bằng quy tắc tất định.
   - *Lý do*: Đảm bảo tuyệt đối `0` URL tự chế và `0` nhận định `CAO` dựa trên nguồn hạng `C`.

4. **[P0] Cơ chế dự phòng kép cho cả Search (`Tavily → ddgs`) và LLM (`Gemini Flash → Groq/OpenRouter`)**:
   - *Bối cảnh*: Free tier của các dịch vụ LLM và Search có giới hạn RPM/quota, dễ gây gián đoạn khi chạy liên tiếp bộ kiểm thử hoặc khi giám khảo chạy thử bản demo.
   - *Quyết định*: Tự động fallback từ Tavily sang `ddgs` + `trafilatura` khi thiếu key/hết quota, và hỗ trợ đổi model/provider qua biến môi trường kèm chế độ "Kết quả đã lưu" (`data/cached_runs/`).
   - *Lý do*: Đảm bảo sản phẩm và bản demo online luôn vận hành ổn định, không tiêu tốn chi phí trả phí.
