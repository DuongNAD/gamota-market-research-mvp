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

18. **[M3 · P3] Ghim `reference_date: "2026-10-15"` cho `TC1`–`TC9` và ưu tiên đường dẫn tiếng Việt (`/vi/`) khi hai bài cùng domain đồng hạng**:
    - *Bối cảnh*: Khi chạy lại `TC1`–`TC6` và `TC8`–`TC9` vào ngày 23/10/2026 để kiểm thử hồi quy so với snapshot Mission 2 (`2026-10-15`), nếu dùng `date.today()` thì tuổi nguồn sẽ tăng thêm 8 ngày (ví dụ `TC2-S2` chuyển từ `aging` sang `stale`). Ngoài ra ở `TC3`, trang `games.gg` có cả bản tiếng Anh (`/news/...`) và bản tiếng Việt (`/vi/news/...`) cùng hạng C và cùng số từ khóa khớp.
    - *Quyết định*: Thêm cấu hình `reference_date: "2026-10-15"` vào `eval/cases.yaml` cho `TC1`–`TC9` (riêng `TC7` làm mới và `TC10` câu hỏi mới dùng `2026-10-23`); khi hai bài cùng một domain đồng hạng `(tier, freshness, -kw_hits)` trong `retrieve_and_grade_sources`, ưu tiên giữ bài có đường dẫn tiếng Việt `/vi/` tại vị trí của domain đó mà không đổi thứ tự giữa các domain.
    - *Lý do*: Đảm bảo `TC2`, `TC3`, `TC4`, `TC5` và `TC9` phát lại từ cache với `0` lần gọi LLM và trùng khớp 100% với baseline Mission 2.

19. **[M3 · P3] Quản lý nguồn gốc minh bạch cho 7 báo cáo mẫu trong `data/cached_runs/`**:
    - *Bối cảnh*: Thư mục `data/cached_runs/` phục vụ chế độ mặc định "Kết quả đã lưu" trên Streamlit và được kiểm tra bởi `tests/test_app_ui.py` (yêu cầu báo cáo đầu tiên `TC1` hiển thị `100.0%` trích dẫn xác minh).
    - *Quyết định*: Cập nhật `data/cached_runs/` với nguồn gốc rõ ràng: `tc2`–`tc5` lấy từ `eval/results/TC2..TC5.{json,md}` (trùng 100% nội dung M2 và có đầy đủ `date_method` + `recency`); `tc1` và `tc6` lấy từ `eval/results/m3_offline/TC1,TC6.{json,md}` (áp lớp `research.recency` trực tiếp lên JSON đã nộp ở M2 để giữ nguyên 100% nhận định gốc và metric `100.0%` của `TC1`); `tc7_cr_a2_refreshed` lấy từ `eval/results/TC7.{json,md}` (chạy làm mới thật tại `2026-10-23`).
    - *Lý do*: Vừa giữ nguyên nội dung các báo cáo đã nộp ở Mission 2 để người chấm đối chiếu trước/sau, vừa cung cấp đầy đủ dữ liệu phân tích độ mới (Mục 7) và bản làm mới thật (`TC7`) ngay khi mở ứng dụng không cần API key.

20. **[M3 · P3/P4] Chủ động không làm các tính năng ngoài phạm vi Change Request A2**:
    - *Bối cảnh*: Trong giới hạn thời gian Mission 3, việc mở rộng sang nhiều hướng cùng lúc sẽ làm loãng mục tiêu trả lời Change Request A2 và gây rủi ro hồi quy.
    - *Quyết định*: Chủ động **không làm**: (1) không sửa ngưỡng độ mới hay quy tắc chấm điểm M2; (2) không để LLM tự đánh giá mức độ ảnh hưởng của nguồn cũ; (3) không tự động sửa `published_date` hay tự ghi đè số cũ bằng số mới trong câu trả lời; (4) không làm tính năng upload CSV/PDF nội bộ hay đọc PDF trực tuyến (ưu tiên số 1 của Câu 3 ở M2, vì thuộc bài toán nguồn dữ liệu đóng ở `TC6` chứ không giải quyết câu hỏi ảnh hưởng của nguồn > 18 tháng); (5) không làm khung chat hỏi-đáp tự do (chỉ làm vòng làm mới có mục tiêu rõ ràng để đo lường được trước/sau).
    - *Lý do*: Tập trung toàn bộ nguồn lực vào chuỗi giải pháp **Phát hiện độ mới thật → Định lượng ảnh hưởng bằng code → Làm mới có mục tiêu giữ nguyên bối cảnh**, chứng minh bằng con số kiểm thử định lượng trước/sau.

---

## Các quyết định trong Đợt sửa trước khi nộp (`[M3-FIX]` · 23–24/10/2026)

21. **[M3-FIX] Chốt chặn đối chiếu bằng code thuần (`research/comparability.py`) theo nguyên tắc "code chỉ hạ nhãn, không nâng nhãn"**:
    - *Bối cảnh*: Khi tự soát kết quả vòng làm mới của `TC7` và `TC10`, phát hiện LLM ghép nhầm số liệu của toàn bộ thị trường ứng dụng di động từ nguồn `S13` (`State of Mobile Southeast Asia 2026`: `5,3 tỷ USD` IAP mọi ứng dụng, `18,1 tỷ` lượt tải mọi ứng dụng cả năm 2025) với số liệu riêng ngành game quý `Q1/2025` (`625 triệu USD` ở `TC7-E2`, `1,93 tỷ` lượt tải ở `TC10-E2/E16`) rồi gắn nhãn `CẬP NHẬT`, làm hạ oan `I2` (`TC7`) và `I4` (`TC10`).
    - *Quyết định*: Xây dựng `research/comparability.py` kiểm tra 4 nhóm quy tắc **P** (phạm vi game), **T** (thị trường), **Đ** (số liệu & đơn vị), **K** (kỳ số liệu); khi không còn bằng chứng mới nào đạt, code hạ nhãn xuống `KHÔNG TƯƠNG ĐƯƠNG`, nhưng tuyệt đối không bao giờ tự nâng nhãn hay thêm mã `evidence_id`.
    - *Lý do*: Ngăn chặn triệt để việc lấy số liệu khác phạm vi/đơn vị/loại kỳ để cập nhật hoặc phản bác số liệu cũ, đồng thời giữ đúng vai trò "LLM đề xuất, code kiểm chứng".

22. **[M3-FIX] Không sửa prompt đối chiếu của vòng làm mới (`sys_prompt`, `usr_prompt`, `cmp_sys_prompt`, `cmp_usr_prompt`)**:
    - *Bối cảnh*: Có thể sửa prompt trong `research/refresh.py` để nhắc LLM kiểm tra kỹ phạm vi game và loại kỳ, nhưng khóa cache LLM (`research/llm.py:140`) băm toàn văn `system_prompt` và `user_prompt`.
    - *Quyết định*: Giữ nguyên từng ký tự của cả 4 chuỗi prompt trong `research/refresh.py`, đặt toàn bộ logic kiểm tra ở bước hậu xử lý bằng code (`guard_comparison`) sau khi nhận kết quả từ LLM/cache.
    - *Lý do*: Bảo toàn 100% khả năng phát lại từ cache (`0` lệnh gọi LLM) cho `TC7` và `TC10`, đảm bảo tính tái lập hoàn toàn và tránh phụ thuộc vào việc LLM có tuân thủ lời nhắc trong prompt hay không.

23. **[M3-FIX] Lưu giữ và hiển thị minh bạch cả `llm_status`, `guard_notes` và lời giải thích gốc của LLM (kèm đánh dấu khi bị bác bỏ)**:
    - *Bối cảnh*: Khi code hạ nhãn một cặp từ `CẬP NHẬT` xuống `KHÔNG TƯƠNG ĐƯƠNG`, nếu xóa mất nhãn gốc hoặc giữ nguyên lời giải thích của LLM mà không cảnh báo, người đọc sẽ không hiểu vì sao cặp đó xuất hiện hoặc đọc nhầm câu giải thích sai của LLM.
    - *Quyết định*: Thêm trường `llm_status` và `guard_notes` vào `RefreshComparison` (có giá trị mặc định tương thích ngược); hiển thị bảng đối chiếu 6 cột trên `app.py` và mục `7.5` Markdown, mở đầu cột giải thích bằng `(LLM, đã bị code bác bỏ)` ở các dòng bị hạ nhãn, đồng thời ghi nhận vào `gaps` và `recommendation`.
    - *Lý do*: Giúp người dùng thấy rõ cơ chế kiểm soát chất lượng của hệ thống (LLM đề xuất gì, code bác bỏ vì quy tắc nào).

24. **[M3-FIX] Khử trùng nhận định mới trong vòng làm mới và cắt chủ đề `ConflictItem` theo ranh giới từ (`_truncate_words`)**:
    - *Bối cảnh*: Ở `TC10` trước khi sửa, hai bằng chứng cũ `E2` và `E16` cùng đối chiếu tới `E23` nên vòng lặp bước 6 sinh ra 2 nhận định mới `I10` và `I11` giống hệt nhau từng chữ; ở `TC7`, `oev.claim[:90]` cắt chuỗi theo ký tự làm xuất hiện cụm `"…trong quý 1 năm 2 ("` giữa chữ.
    - *Quyết định*: Trong `research/refresh.py`, chỉ tạo nhận định mới khi tập `new_evidence_ids` và `statement` chuẩn hóa chưa từng xuất hiện; thay `oev.claim[:90]` bằng `_truncate_words(oev.claim, 16)`.
    - *Lý do*: Loại bỏ nhận định trùng lặp và đảm bảo mọi chủ đề mâu thuẫn hiển thị trong `short_answer` đều tròn chữ.

25. **[M3-FIX] Sửa duy nhất 1 câu trích dẫn fixture `"In 2026, ..."` → `"In 2025, ..."` trong `tests/test_refresh.py::test_refresh_update_adds_conflict_and_new_insight`**:
    - *Bối cảnh*: Ở ngày tham chiếu `2026-10-23`, năm `2026` chưa kết thúc (`2026-12-31 > 2026-10-23`) nên `detect_data_period` trả về rỗng cho cụm `"In 2026"`, khiến quy tắc **K** hạ nhãn cặp `CẬP NHẬT` trong test giả lập.
    - *Quyết định*: Đổi câu trích dẫn giả lập trong fixture của test này sang `"In 2025, hybrid monetization growth in Indonesia slowed to 12% as pure IAA regained share."` thay vì nới lỏng quy tắc **K** hay `detect_data_period`.
    - *Lý do*: Giữ nguyên tính nghiêm ngặt của quy tắc kiểm tra kỳ số liệu đã kết thúc trong khi vẫn kiểm thử đầy đủ luồng `CẬP NHẬT` hợp lệ (`2024` → `2025`, cùng phạm vi game, cùng Indonesia, cùng đơn vị `%`).

26. **[M3-FIX] Cập nhật model dự phòng OpenRouter sang `google/gemma-4-31b-it:free` và hỗ trợ biến môi trường `OPENROUTER_MODEL`**:
    - *Bối cảnh*: Kiểm tra danh mục `GET https://openrouter.ai/api/v1/models` ngày 23/10/2026 cho thấy model dự phòng cũ `google/gemini-2.0-flash-exp:free` đã bị gỡ khỏi OpenRouter.
    - *Quyết định*: Đổi `DEFAULT_MODELS["openrouter"]` sang `google/gemma-4-31b-it:free` (model free đang có mặt trên OpenRouter và hỗ trợ `response_format`), đồng thời cho phép ghi đè qua biến môi trường `OPENROUTER_MODEL` trong `research/llm.py` và `.env.example`. Khi gọi thử trực tiếp 1 lần cho 3 model ứng viên (`google/gemma-4-31b-it:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `nvidia/nemotron-3.5-super-vl:free`), API trả về `HTTP 401 Unauthorized` (0,24–0,39s) do key OpenRouter trong môi trường local hết hiệu lực; đã xác minh cả 3 model đều tồn tại và có `response_format` trong `supported_parameters` trên API danh mục công khai của OpenRouter.
    - *Lý do*: Đảm bảo nhánh fallback OpenRouter trỏ tới model free hợp lệ và cho phép đổi nhanh model dự phòng qua cấu hình mà không làm thay đổi khóa cache của provider chính (`gemini`).

27. **[M3-FIX] Giữ nguyên model chính (`gemini-3.8-flash`) và không chuyển sang MiniMax hay model khác**:
    - *Bối cảnh*: Cân nhắc việc đổi model chính sang model khác trên OpenRouter như `minimax/minimax-m3.1-flash` hoặc các model `:free`.
    - *Quyết định*: Giữ nguyên `LLM_PROVIDER=gemini` và `LLM_MODEL=gemini-3.8-flash` làm model chính.
    - *Lý do*: `minimax/minimax-m3.1-flash` là model trả phí (`0,15 USD / 1M input tokens`, `0,60 USD / 1M output tokens`), vi phạm quy tắc 4 của `AGENTS.md`; ngoài ra việc đổi model chính sẽ làm trượt toàn bộ cache LLM của `TC1`–`TC10` và phá vỡ phép so sánh hồi quy với Mission 2.

28. **[M3-FIX] Lưu snapshot `eval/results/m3_before_fix/` và bổ sung Bảng D đối chiếu Trước/Sau đợt sửa**:
    - *Bối cảnh*: Cần minh bạch hóa kết quả trước và sau khi áp dụng chốt chặn đối chiếu trên `TC7` và `TC10`.
    - *Quyết định*: Lưu nguyên trạng các file kết quả trước khi sửa vào `eval/results/m3_before_fix/` và cập nhật `eval/compare_m2_m3.py` để tự động sinh **Bảng D — Trước/sau đợt sửa** bên cạnh Bảng A, B, C.
    - *Lý do*: Đảm bảo tính trung thực khoa học (không xóa kết quả cũ) và cung cấp bằng chứng định lượng rõ ràng về tác dụng của chốt chặn đối chiếu bằng code.

29. **[M3-FIX] Sửa tài liệu cho khớp code và kết quả chạy sau khi soát lại**:
    - *Bối cảnh*: Soát lại sau đợt sửa thấy 4 chỗ lệch: `TESTING.md` ghi code cũ cắt `[:80]` (thực tế `[:90]`) và mô tả nhóm phân loại của chốt chặn khác với `research/comparability.py`; lỗi `401` khi gọi thử model dự phòng chỉ có ở `DECISIONS.md`; câu (4) của Câu 2 viết như thể cả 2 cặp xác nhận đều nâng `I5`.
    - *Quyết định*: Sửa `TESTING.md` cho khớp code; ghi lỗi `401` vào `TESTING.md` và mục Hạn chế của `README.md`; viết lại câu (4) trong `SUBMISSION_M3.md`, `SUBMISSION_M3_FORM.txt`, `README.md`: `E3→E35` bổ sung bằng chứng cho `I1` (giữ `TRUNG BÌNH`), chỉ `E11` làm `I5` lên `TRUNG BÌNH`; đếm lại ký tự Câu 2 (`1902`).
    - *Lý do*: Quy tắc 1 và 7 của `AGENTS.md`: tài liệu nộp không được nói khác kết quả chạy thật, và hạn chế phải ghi rõ trong `TESTING.md` và README.





