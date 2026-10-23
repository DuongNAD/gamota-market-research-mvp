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

---

## Các quyết định thiết kế ở Mission 3 (Change Request A2: Dữ liệu cũ)

11. **[M3 · P1] Ngưỡng "hơn 18 tháng" (`alert_months: 18`) đóng vai trò lớp phân tích hậu xử lý, giữ nguyên 100% quy tắc chấm điểm Mission 2**:
    - *Bối cảnh*: Change Request A2 hỏi *"Một nguồn quan trọng được phát hành cách đây hơn 18 tháng. Người dùng muốn biết điều đó ảnh hưởng thế nào tới độ tin cậy của kết quả"*. Nếu tự ý sửa ngưỡng trong `compute_freshness` hoặc hạ thẳng mọi nhận định có nguồn > 18 tháng xuống `THẤP`, ta sẽ làm hỏng khả năng so sánh trực tiếp trước/sau và phá vỡ bộ kiểm thử regression của Mission 2.
    - *Quyết định*: Giữ nguyên bất biến `score_single_insight` và `compute_freshness` (`<=366` ngày là mới, `<=731` ngày là cũ dần) của Mission 2; xây dựng `RecencyImpact` (`research/recency.py`) như một lớp hậu xử lý tất định không bao giờ tự thay đổi `Insight.confidence`.
    - *Lý do*: Trả lời trực tiếp câu hỏi "ảnh hưởng thế nào" bằng phân tích minh bạch đồng thời bảo toàn 100% tính tương thích ngược với 6 báo cáo Mission 2.

12. **[M3 · P1] Xác định nguồn then chốt (`is_key`) và định lượng ảnh hưởng bằng mô phỏng phản thực tế (Counterfactual Scoring) bằng code**:
    - *Bối cảnh*: Nếu hỏi LLM "nguồn cũ này ảnh hưởng nhiều hay ít", LLM sẽ trả lời cảm tính và không nhất quán với quy tắc chấm điểm của hệ thống.
    - *Quyết định*: Với mỗi cặp `(nguồn S#, nhận định I#)`, code chạy lại chính hàm `score_single_insight` trong hai kịch bản phản thực tế: (1) *Nếu bỏ nguồn này* (`if_source_removed`, trả về `MẤT CĂN CỨ` nếu nhận định không còn bằng chứng nào khác) và (2) *Nếu nguồn này còn mới (`<= 12 tháng`)* (`if_source_fresh`).
    - *Lý do*: Cho người ra quyết định thấy chính xác nhận định nào sẽ sụp đổ nếu nguồn cũ không còn giá trị (ví dụ bỏ `S5`/`S6` ở `TC2` làm `I5`/`I6` mất căn cứ) và nhận định nào đang bị tuổi dữ liệu kìm hãm độ tin cậy (ví dụ nếu `S5` còn mới thì `I4` ở `TC2` tăng từ `THẤP` lên `CAO`).

13. **[M3 · P1] Minh bạch hóa độ chính xác ngày đăng (`date_precision`) và bóc tách kỳ số liệu thực tế (`data_period`) trong trích dẫn**:
    - *Bối cảnh*: Ở Mission 2, các báo cáo chỉ có năm trong URL/tiêu đề (như `AppsFlyer 2024` ở `TC2` hay `Sensor Tower 2025` ở `TC1`) được gán ngày ước tính `YYYY-06` nên hiển thị giống hệt một bài viết biết rõ tháng 6; ngoài ra có bài đăng tháng 8/2026 (`TC1-S6`) nhưng trích dẫn lại nói về số liệu năm 2024.
    - *Quyết định*: Trong `research/dates.py`, lưu rõ `date_method` và `date_precision` (`day`, `month`, `quarter`, `year`, `unknown`), hiển thị `2024 (chỉ biết năm)` kèm dải tuổi `22–34 tháng`; đồng thời dùng regex tất định `detect_data_period` tách kỳ số liệu trong câu trích dẫn (loại trừ năm dự báo/tương lai và từ khóa `since`/`by`/`forecast`).
    - *Lý do*: Giúp người dùng phân biệt rõ "tuổi bài báo" với "kỳ của con số thống kê", phát hiện cả nguồn mới trích số liệu cũ (`TC1-S6`) lẫn nguồn chỉ biết năm (`TC1-S3`, `TC2-S5/S6`).

14. **[M3 · P1] Gắn cờ mâu thuẫn ngày đăng (`date_conflict`) thay vì tự ý sửa `published_date` của nguồn**:
    - *Bối cảnh*: Ở `TC4-S10` (`icon-era.com`), ngày đăng suy từ URL/metadata là `03/2025`, nhưng câu trích dẫn nguyên văn lại nhắc tới kết quả `"Q2 2026"`, chứng tỏ ngày đăng `03/2025` gần như chắc chắn sai.
    - *Quyết định*: Khi nguồn không có độ chính xác cấp ngày (`precision != "day"`) mà trích dẫn chứa kỳ số liệu bắt đầu sau khoảng ngày đăng, hệ thống bật cờ `date_conflict = True` và ghi rõ lý do `"ngày đăng có thể sai"`, nhưng không tự động sửa `published_date`.
    - *Lý do*: Tự sửa ngày đăng bằng heuristic sẽ làm thay đổi điểm `confidence` gốc (vi phạm bất biến kỹ thuật); thay vào đó, hệ thống cảnh báo minh bạch và cung cấp tính năng "Thử giả định ngày đăng" trên UI để người dùng chủ động kiểm tra.

15. **[M3 · P1] Chỉ nối ghi chú `[Độ mới dữ liệu]` vào `short_answer` khi mức ảnh hưởng là `ĐÁNG KỂ` (và đảm bảo tính idempotent)**:
    - *Bối cảnh*: Nếu báo cáo nào cũng chèn cảnh báo độ mới vào `short_answer` (kể cả khi toàn bộ nguồn đều mới như `TC3` hoặc chỉ có 1 nhận định phụ mức `THẤP` thiếu ngày như `TC6`), người dùng sẽ bị cảnh báo giả (alert fatigue).
    - *Quyết định*: Chỉ nối `[Độ mới dữ liệu]` vào `short_answer` khi `impact_level == "ĐÁNG KỂ"`; ở các mức `VỪA PHẢI`/`NHỎ`, thông tin hiển thị ở Banner, badge nhận định và Mục 7. Mọi thao tác nối đều gỡ marker cũ trước khi nối mới (idempotent).
    - *Lý do*: Đảm bảo cảnh báo ở phần tóm tắt chỉ xuất hiện khi các nhận định cốt lõi (`CAO`/`TRUNG BÌNH`) thực sự phụ thuộc vào dữ liệu cũ.

16. **[M3 · P2] Giữ thứ tự ứng viên tất định khi tải trang song song (`ThreadPoolExecutor`) và đánh số nối tiếp `S#`/`E#`/`I#` trong vòng làm mới (`research/refresh.py`)**:
    - *Bối cảnh*: Khi tải nội dung 18 URL ứng viên bằng `ThreadPoolExecutor`, việc lặp theo `as_completed` làm thứ tự hoàn thành phụ thuộc tốc độ I/O từng luồng; nếu 2 nguồn hạng C có cùng độ mới và số từ khóa khớp (như `brandsvietnam.com` và `dantri.com.vn` ở `TC2`), thứ tự tie-break có thể đảo nhau làm lệch cache. Ngoài ra, khi chạy vòng làm mới, nếu đánh số lại `S1..Sn` từ đầu thì mọi tham chiếu cũ trong báo cáo sẽ bị đứt gãy.
    - *Quyết định*: Thu kết quả `ThreadPoolExecutor` theo đúng thứ tự danh sách `fetch_pool` tất định; trong `refresh_old_sources`, chỉ lấy tối đa 2 nguồn then chốt cũ đầu tiên (`refresh_max_targets: 2`), lọc nghiêm ngặt nguồn mới phải có ngày đăng rõ ràng mới hơn nguồn cũ, đánh mã nối tiếp `S{len+1}` / `E{max+1}`, giữ nguyên nhận định cũ (chỉ gắn thêm `E#` mới khi `XÁC NHẬN`, hoặc gắn `has_conflict=True` + thêm `ConflictItem` + thêm nhận định mới ở cuối khi `CẬP NHẬT`/`MÂU THUẪN`).
    - *Lý do*: Đảm bảo phát lại `TC2` từ cache tốn đúng `0` lệnh gọi LLM, đồng thời giữ nguyên 100% bối cảnh báo cáo cũ để so sánh trực tiếp độ tin cậy trước → sau làm mới.

17. **[M3 · P2] Tích hợp Tab "3. Độ mới & Ảnh hưởng (A2)", bộ mô phỏng giả định ngày đăng (What-if Simulator) và khớp nút chọn nhanh theo `stem` trước `question`**:
    - *Bối cảnh*: Trên giao diện Streamlit (`app.py`), `TC7` (bản làm mới của `TC2`) có cùng câu hỏi nghiên cứu với `TC2`; nếu nút chọn nhanh khớp theo `question` như cũ thì bấm `TC7` sẽ mở nhầm `TC2`. Đồng thời, nếu tính `apply_recency_layer` cho toàn bộ file trong `data/cached_runs/` ngay khi khởi động thì `AppTest` có nguy cơ chậm.
    - *Quyết định*: Đổi hàm `_find_cached_run_for_preset` ưu tiên khớp `c_path.stem.lower() == preset["stem"]` trước khi fallback sang `question`; chỉ tính `ensure_report_recency` cho `active_report` đang hiển thị kèm `@st.cache_data`; bổ sung What-if Simulator cho phép người dùng thử đổi ngày đăng giả định của bất kỳ nguồn nào trên bản sao trong bộ nhớ mà không ghi đè báo cáo gốc.
    - *Lý do*: Giúp người dùng kiểm chứng trực tiếp cả 2 báo cáo `TC2` (trước làm mới) và `TC7` (sau làm mới) không cần API key, vẫn giữ nguyên đúng 1 `st.title` và 4 `st.metric` tương thích 100% với bộ test UI của Mission 2.



