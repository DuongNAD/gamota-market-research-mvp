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

5. **[P1] Đổi model mặc định từ `gemini-2.5-flash` sang `gemini-3.8-flash`**:
   - *Bối cảnh*: Theo chính sách cập nhật của Google AI Studio (năm 2026), các model dòng 2.5 bị giới hạn cho project mới, trong khi `gemini-3.8-flash` là model Flash hiện hành hỗ trợ free tier cho project mới.
   - *Quyết định*: Đặt mặc định `LLM_MODEL=gemini-3.8-flash` trong `.env.example`, `research/llm.py` và `README.md`.
   - *Lý do*: Đảm bảo API key mới tạo trên Google AI Studio gọi thành công ngay ở free tier mà không gặp lỗi chặn model cũ.

6. **[P1] Xoay vòng nhiều API key (`GEMINI_API_KEYS`), chuyển model tức thì khi gặp `HTTP 503` và tắt `thinkingBudget` ở bước tổng hợp dài**:
   - *Bối cảnh*: Khi chạy thử câu hỏi thực tế qua CLI, endpoint `gemini-3.8-flash` của Google đôi lúc trả về `HTTP 503 (Service Unavailable)`, và `gemini-2.5-flash` bật chế độ suy nghĩ mặc định khiến bước `Synthesize` tốn >35 giây.
   - *Quyết định*: Trong `research/llm.py`, hỗ trợ xoay vòng danh sách key `GEMINI_API_KEYS`; nếu một model trả về `503/404` thì đánh dấu tạm ngưng model đó trong phiên để chuyển ngay sang model Flash dự phòng kế tiếp (`gemini-2.5-flash` / `gemini-2.5-flash-lite`) kèm `thinkingBudget=0`.
   - *Lý do*: Giảm thời gian phản hồi của mỗi lệnh gọi LLM từ >35s xuống ~2,7s và đưa tổng thời gian chạy toàn bộ pipeline 6 bước về mức 28–59s (< 90s mục tiêu).

7. **[P2] Thiết kế giao diện Streamlit một trang ưu tiên chế độ "Kết quả đã lưu" mặc định**:
   - *Bối cảnh*: Người chấm bài cần kiểm tra ngay cả 6 cấu phần báo cáo, bảng phương án × tiêu chí, link tô sáng `#:~:text=` và chỉ số tự kiểm mà không bắt buộc phải cấu hình API key cá nhân.
   - *Quyết định*: Mặc định mở chế độ "Kết quả đã lưu" đọc trực tiếp từ `data/cached_runs/*.json` (kèm timestamp thực tế), gắn 4 nút câu hỏi mẫu thuộc 4 loại quyết định khác nhau và giới hạn số lượt chạy Live mỗi phiên (`MAX_LIVE_RUNS_PER_SESSION=5`).
   - *Lý do*: Loại bỏ hoàn toàn rủi ro gián đoạn khi hết quota free-tier hoặc khi người chấm mở link demo ẩn danh.

8. **[P3 · Vòng cải tiến Before → After #1] Mở rộng nhận diện ngày đăng (`_extract_date_fallback`), ưu tiên đa dạng domain và siết điều kiện chấm điểm `CAO`**:
   - *Bối cảnh*: Ở lượt chạy kiểm thử đầu tiên (Before), nhiều bài báo ngành uy tín (`sensortower.com`, `newzoo.com`, `statista.com`) thiếu thẻ HTML meta date nên bị gán `Không rõ ngày` (`stale`) khiến các nhận định thực chứng bị tụt xuống `THẤP`; đồng thời tại `TC6`, một nhận định báo "không có dữ liệu" kết hợp 1 nguồn `A` cũ và 1 nguồn `C` mới lại bị chấm nhầm là `CAO`.
   - *Quyết định*: Bổ sung regex tách tháng/quý/năm báo cáo từ URL slug & tiêu đề trong `research/retrieve.py`, giới hạn tối đa 1–2 bài mỗi domain ở vòng lọc đầu để tăng độ phủ nguồn độc lập, và sửa `research/score.py` yêu cầu nhận định `CAO` phải có ít nhất 1 nguồn hạng `A/B` còn mới (`fresh`) cùng ≥ 2 domain không cũ và không phải câu thông báo thiếu dữ liệu.
   - *Lý do*: Giảm số nguồn bị mất ngày đăng từ 3–8 nguồn/case xuống 0–5 nguồn/case, giúp `TC3` có 3 nhận định thực chứng đạt `CAO` thật sự và loại bỏ hoàn toàn điểm `CAO` giả ở `TC6`.

9. **[P3 · Vòng cải tiến Before → After #2] Tự động hiển thị dải số liệu mâu thuẫn ngay trong `short_answer` và gom nhóm bằng chứng đồng thuận**:
   - *Bối cảnh*: Ở lượt chạy Before của `TC3` (Quy mô thị trường game mobile Việt Nam), mục 3.2 đã phát hiện các con số khác nhau (`500 triệu USD` năm 2024 theo IMARC, `315 triệu USD` doanh thu xuất khẩu, `825 triệu USD` năm 2025), nhưng phần `short_answer` ở mục 1 chỉ nêu một con số `825 triệu USD`, dễ làm người đọc hiểu lầm chỉ có một đáp số duy nhất.
   - *Quyết định*: Cập nhật prompt `synthesize_report` để gom các bằng chứng đồng thuận thành 8–10 nhận định cô đọng và bổ sung quy tắc tất định trong `score_and_finalize_report` (`research/score.py`): nếu `report.conflicts` có mâu thuẫn mà `short_answer` chưa nêu đủ các giá trị, code tự động nối cảnh báo dải số liệu kèm giải thích phạm vi/kỳ vào ngay `short_answer`.
   - *Lý do*: Đảm bảo 100% báo cáo có mâu thuẫn nguồn (`TC1`, `TC2`, `TC3`, `TC5`, `TC6`) luôn trình bày minh bạch nhiều con số kèm lý do chênh lệch ngay từ phần tóm tắt đầu trang.

10. **[P2/P3] Escape ký tự `$` (`\$`) khi xuất bảng Markdown (`render_report_markdown`) sau khi kiểm tra giao diện bằng trình duyệt**:
    - *Bối cảnh*: Khi chụp màn hình kiểm tra bảng `Verified Insights` trên trình duyệt, các câu trích dẫn nguyên văn chứa nhiều ký hiệu tiền tệ USD (ví dụ `$625 million` và `$825M` trong cùng một ô bảng) bị bộ dựng KaTeX của Streamlit hiểu nhầm là cặp dấu `$ ... $` công thức toán học và hiển thị sai phông chữ.
    - *Quyết định*: Bổ sung hàm `_esc_md()` trong `research/pipeline.py` để tự động chuyển `$` thành `\$` trong toàn bộ nội dung văn bản và ô bảng trước khi render Markdown.
    - *Lý do*: Giữ nguyên độ chính xác của câu trích dẫn số liệu tiền tệ đồng thời đảm bảo hiển thị chuẩn xác trên cả Streamlit UI và GitHub Markdown.


