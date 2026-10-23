# BRIEF — Gamota · Bài test A · Mission 3: Cải tiến (Change Request A2 — Dữ liệu cũ)

> Bản giao việc cho AI agent (Google Antigravity). Đọc hết trước khi làm. Hôm nay là 23/10/2026. Hạn nộp bài: **11:49 ngày 25/10/2026**. Mọi phần việc của bạn phải xong trước **16:00 ngày 24/10/2026** để tôi còn quay video và nộp form.
>
> Các con số ở mục 2 và bảng tham chiếu ở mục 4.5 là kết quả chạy thật trên repo ngày 23/10/2026 (đọc code, chạy `pytest`, chạy lại pipeline từ cache, chạy nguyên mẫu quy tắc trên JSON thật của Mission 2), không phải ước đoán.

## 0. Vai trò, thứ tự tài liệu, nguyên tắc

- Bạn là kỹ sư AI/full-stack senior, tiếp tục trên chính sản phẩm Mission 2 trong repo này. Tôi là người nộp bài và duyệt ở các CHECKPOINT.
- **Thứ tự ưu tiên tài liệu cho Mission 3:** `BRIEF_M3.md` (file này) > `AGENTS.md` > `BRIEF.md`.
  - `BRIEF.md` là đặc tả Mission 2: chỉ dùng để tra quy tắc gốc (hạng nguồn, độ tin cậy, định dạng báo cáo). Mục 2 của `BRIEF.md` (các ô `{{...}}`) **không áp dụng** cho Mission 3, không cần hỏi lại.
  - `AGENTS.md` đã được cập nhật cho Mission 3 (ngày 23/10/2026): trỏ sang file này, kế hoạch ở mục 7, thứ tự cắt ở mục 9, hạn 16:00 ngày 24/10/2026.
  - Mọi quy tắc khác trong `AGENTS.md` giữ nguyên: không bịa, không lộ key, không dùng model trả phí trong code, hỏi trước khi push/xóa file/cài công cụ toàn cục, ghi `DECISIONS.md`, kiểm tra UI bằng trình duyệt tích hợp.
- Thứ tự ưu tiên khi phải đánh đổi: **trả lời đúng change request bằng kết quả chạy thật > không làm hỏng chức năng cũ (regression) > trung thực về hạn chế > đẹp**.
- Không làm lại từ đầu, không đổi kiến trúc pipeline 6 bước. Mission 3 là một lớp cải tiến đặt lên sản phẩm Mission 2.
- Tài liệu nộp viết tiếng Việt có dấu; code, tên biến, commit message viết tiếng Anh. `BRIEF_M3.md` được commit cùng repo, không đưa vào `.gitignore`.

## 1. Đề bài Mission 3 (nguồn sự thật, chép từ trang đề)

**Mục tiêu vòng cải tiến.** Không làm lại từ đầu; Mission 3 vẫn là sản phẩm đã nộp ở Mission 2. Vòng này có thêm một yêu cầu mới: xử lý ngay trên sản phẩm cũ, rồi cho thấy bản sau dùng tốt hơn bản trước, **bằng kết quả chạy thật**. Câu dẫn của đề: *"Nếu có thêm thời gian, bạn sẽ muốn cải tiến giải pháp đã làm ở Mission 2 như thế nào? Vì sao?"*

**Các điểm được chấm.** Phiên bản Mission 3 cần thể hiện tốt hơn khả năng:
- **C1** Xử lý nguồn yếu, cũ, thiếu hoặc mâu thuẫn.
- **C2** Cho người dùng kiểm chứng căn cứ của nhận định.
- **C3** Phân biệt điều đã có đủ cơ sở với điều còn chưa chắc chắn.
- **C4** Cho phép tiếp tục nghiên cứu sâu hơn mà vẫn giữ được bối cảnh phù hợp.

**Change request A2 — Dữ liệu cũ:** *"Một nguồn quan trọng được phát hành cách đây hơn 18 tháng. Người dùng muốn biết điều đó ảnh hưởng thế nào tới độ tin cậy của kết quả."*

**Thời gian:** 5 ngày kể từ khi Mission 3 mở (11:49 20/10 → 11:49 25/10/2026). Không làm lại sản phẩm từ đầu; Mission 3 phải tiếp tục trên sản phẩm Mission 2.

**Bộ kiểm thử.** Chạy lại các test quan trọng của Mission 2 để kiểm tra regression. Bổ sung **tối thiểu 3 test** cho phần cải tiến, trong đó có ít nhất **1 test cho change request**, **1 edge case/tình huống khó**, **1 regression test cho chức năng cũ**.

**Nộp bài.** (1) GitHub repo, phiên bản cập nhật: ưu tiên tiếp tục trên chính repo Mission 2 và **giữ commit history**; (2) link demo phiên bản Mission 3; (3) link video trình bày phần cải tiến; (4) trả lời 3 câu:
- **Câu 1.** Sau khi nhận yêu cầu mới, bạn đã ưu tiên thay đổi điều gì và chủ động chưa làm điều gì? Vì sao?
- **Câu 2.** Thay đổi nào tạo ra khác biệt lớn nhất giữa sản phẩm Mission 2 và Mission 3? Bạn dùng bằng chứng nào để kết luận phiên bản mới tốt hơn?
- **Câu 3.** Nếu sản phẩm này được đưa cho người dùng thật vào ngày mai, rủi ro hoặc giới hạn lớn nhất còn lại là gì? Bạn sẽ ưu tiên xử lý nó như thế nào?

**Chính sách AI:** được dùng AI, nhưng người nộp phải hiểu và chịu trách nhiệm với mọi thứ mình nộp. Vì vậy Walkthrough ở mỗi checkpoint phải giải thích đủ rõ để tôi trình bày lại được.

## 2. Hiện trạng Mission 2 (đã kiểm tra trên repo ngày 23/10/2026)

### 2.1 Sản phẩm
- Pipeline `run(question) -> Report` 6 bước: Plan → Retrieve → Grade → Extract & Verify → Synthesize → Score (`research/`). Giao diện Streamlit `app.py` (6 tab, mặc định xem 6 báo cáo đã lưu trong `data/cached_runs/`). Eval: `python -m eval.run_eval` với `eval/cases.yaml` (TC1–TC6), kết quả ở `eval/results/`.
- `pytest -q`: **21 passed** (7,0 giây).
- Search thực tế dùng `ddgs` (không có Tavily key ⇒ công cụ tìm kiếm không trả ngày đăng). Ngày đăng lấy từ metadata trang (trafilatura) hoặc regex dự phòng `_extract_date_fallback` trong `research/retrieve.py`. LLM mặc định `gemini-3.8-flash` (có fallback). Key trong `.env` (chỉ kiểm có/không): GEMINI có, OPENROUTER có, TAVILY không, GROQ không.
- Demo: https://gamota-market-research-mvp.streamlit.app. Theo `SUBMISSION.md`, app deploy từ nhánh `main`. Remote có `main` và `master` cùng trỏ commit `58a6fba`; nhánh local là `master`.
- `.cache/` (gitignored, chỉ có trên máy này): 87 file cache LLM, 120 file cache search/fetch. **Không được xóa**: đây là thứ cho phép chạy lại Mission 2 để so sánh.

### 2.2 Vấn đề "dữ liệu cũ" có thật trong output Mission 2
Tính trên `eval/results/TC*.json`, ngày tham chiếu 15/10/2026 (ngày chạy Mission 2), dùng chính `score_single_insight` của repo:

| Case | Nguồn | Ngày M2 hiển thị | Thực tế | Ảnh hưởng (code tính) |
|---|---|---|---|---|
| TC2 (kiếm tiền casual) | S5, S6 `appsflyer.com` (báo cáo 2024) | `2024-06` | Chỉ biết **năm 2024**: regex lấy "2024" trong URL rồi gán tháng 06. Tuổi thật 22–34 tháng | S5 là căn cứ duy nhất của I5, S6 của I6: bỏ nguồn thì I5, I6 mất căn cứ. Nếu nguồn còn mới: I4 THẤP → **CAO**, I5 và I6 THẤP → TRUNG BÌNH |
| TC2 | S1 `sensortower.com` | `2025-05` | Trích dẫn nói số liệu **Q1/2025** (≈ 18,5 tháng) | Căn cứ duy nhất của I2 (TRUNG BÌNH). Nếu S1 hoặc S2 còn mới: I1 → CAO |
| TC1 (thể loại ĐNÁ) | S2, S3 `sensortower.com`, S12 `investgame.net` | `2025-05`, `2025-06`, `2025-06` | S2, S12: số liệu **Q1/2025**. S3, S12: **chỉ biết năm 2025** | I1, I2, I3 (TRUNG BÌNH, phần lõi của khuyến nghị) **không có bằng chứng nào chắc chắn trong 18 tháng gần đây**. Nguồn hạng A mới duy nhất (Newzoo S1, 06/2026) không hỗ trợ nhận định nào. Nếu S2 còn mới: I1, I2 → CAO |
| TC1 | S6 `thegamersmag.com` | `2026-08-05` (mới) | Trích dẫn được dùng nói về **năm 2024** | Nguồn mới nhưng số liệu cũ |
| TC4, TC5 | `icon-era.com` | `2025-03` | Trích dẫn nhắc "Garena's Q2 2026 results", "$825 million in 2025": ngày đăng suy từ "Q1 2025" trong URL/tiêu đề **gần như chắc chắn sai** | M2 xếp nguồn này "cũ dần" dựa trên ngày sai |
| TC3 (quy mô VN) | phần lớn nguồn 2026 | | Số liệu năm 2025 | Không có vấn đề độ mới, **không được cảnh báo thừa** |
| TC6 | 5/12 nguồn | không rõ ngày | | |

**Mission 2 đã làm được:** nhãn độ mới theo nguồn (≤ 12 / 12–24 / > 24 tháng); lý do độ tin cậy có ghi "dữ liệu cũ dần"; nguồn > 24 tháng không giúp nâng độ tin cậy.

**Mission 2 chưa làm được (chính là change request):**
1. Không có ngưỡng 18 tháng, không xác định nguồn nào là **then chốt**.
2. Không cho biết **nhận định nào** phụ thuộc nguồn cũ và **độ tin cậy sẽ đổi thế nào** nếu nguồn đó lỗi thời hoặc nếu có bản mới.
3. Ngày ước tính từ năm hiển thị như tháng cụ thể (`2024-06`); người dùng không biết ngày lấy từ đâu, chắc chắn đến đâu.
4. Không xét **kỳ số liệu** trong trích dẫn (nguồn 2026 trích số 2024; nguồn tháng 5/2025 nói về Q1/2025).
5. Trả lời ngắn và khuyến nghị không nhắc gì tới tuổi dữ liệu.
6. Không có cách đi tìm dữ liệu mới hơn mà vẫn giữ bối cảnh báo cáo cũ.

### 2.3 Cơ sở cho regression (đã chạy thật ngày 23/10)
- Chấm lại 6 báo cáo M2 bằng `score_and_finalize_report` hiện tại, ngày tham chiếu = `trace.current_date` (2026-10-15), sau khi tính lại `freshness` bằng `compute_freshness`: **trùng 100%** độ tin cậy từng nhận định, `short_answer` và mọi chỉ số tự kiểm. Viết được golden regression test.
- Chạy lại `run(question, use_cache=True, reference_date=date(2026, 10, 15))` trong khi chặn mọi lệnh gọi LLM và mạng: **TC2, TC3, TC4, TC5 tái tạo y hệt output M2** (0 lần gọi LLM, 0 request mạng). **TC1 thiếu cache LLM ở bước `extract_batch_3`, TC6 ở `extract_batch_1`**, nên hai case này sẽ gọi LLM thật lại một phần và có thể lệch nhẹ so với M2: so sánh bằng bất biến, không đòi trùng từng chữ.
- Điều kiện để giữ khả năng tái tạo: **không đổi prompt** Plan/Extract/Synthesize và **ghim `reference_date`** (prompt chứa ngày hiện tại, đổi ngày là trượt cache).
- Ở ngày 23/10, TC2-S2 (`2024-10`) chuyển từ "cũ dần" sang "cũ" (> 731 ngày) nhưng chưa làm đổi mức nhận định nào: ví dụ thật cho việc độ tin cậy "hết hạn" theo thời gian.

## 3. Giả thuyết cải tiến cần chứng minh

**Lớp "Độ mới & Ảnh hưởng" (Recency Impact Layer).** Với *bất kỳ* báo cáo nào, code (không phải LLM) cho người dùng biết:
- **(a)** tuổi của từng nguồn, ngày đăng được xác định bằng cách nào và chắc chắn đến đâu;
- **(b)** kỳ số liệu thực sự được nhắc trong trích dẫn;
- **(c)** nguồn nào là **then chốt** với kết luận;
- **(d)** với nguồn then chốt hơn 18 tháng (hoặc chưa chắc tuổi): nhận định nào bị ảnh hưởng; độ tin cậy **sẽ đổi ra sao nếu bỏ nguồn đó** và **nếu nguồn đó còn mới**, tính bằng cách chạy lại chính quy tắc chấm điểm M2; mốc ngày độ tin cậy sẽ tự giảm nếu không có dữ liệu mới;
- **(e)** một hành động tiếp theo: **vòng làm mới dữ liệu** tìm bản mới hơn cho đúng các nguồn đó, giữ nguyên câu hỏi, bằng chứng và mã S#/E# cũ, chấm lại bằng quy tắc cũ, cho thấy trước → sau.

Lớp này **không sửa quy tắc chấm điểm M2**: nó giải thích và bổ sung bằng chứng. Nhờ vậy chứng minh được "tốt hơn mà không làm hỏng cái cũ".

Ánh xạ tới điểm chấm:
- **C1**: (a), (b), (d); vòng làm mới ghi nhận số cũ ↔ số mới thành mâu thuẫn có giải thích; gắn cờ ngày đăng có thể sai.
- **C2**: hiển thị cách xác định ngày và kỳ số liệu ngay cạnh trích dẫn; mọi ảnh hưởng trỏ về E#/S# có link tô sáng; người dùng thử "nếu ngày đăng là …" và thấy kết quả ngay.
- **C3**: trạng thái độ mới từng nhận định; nhóm "Đủ cơ sở / Cần lưu ý / Chưa chắc chắn".
- **C4**: vòng làm mới giữ bối cảnh; phiên bản v1 → v2 có bảng thay đổi.

## 4. Thiết kế chi tiết

### 4.1 Bất biến kỹ thuật (sắp vi phạm thì dừng lại hỏi tôi)
1. Không đổi logic/ngưỡng của `score_single_insight`, `compute_freshness` (≤ 366 ngày là mới, ≤ 731 ngày là cũ dần), `verify_quote`, `build_text_fragment_url`, `strip_llm_urls`, `config/source_tiers.yaml`.
2. Không đổi system/user prompt của `plan_research`, `synthesize_report`, `extract_claims_from_sources`.
3. Lớp độ mới là **hậu xử lý**: không bao giờ thay đổi `Insight.confidence`. Độ tin cậy chỉ đổi khi vòng làm mới thêm bằng chứng mới, và luôn đi qua `score_and_finalize_report` cũ.
4. Không sửa 21 test cũ. Test cũ đỏ thì sửa code. Bắt buộc phải đổi test cũ thì dừng, hỏi tôi.
5. Giữ đúng nguyên văn tiêu đề mục 1–6 trong `render_report_markdown`. Không thêm `st.metric` hay `st.title` mới ở bất kỳ đâu trong `app.py` (test cũ kiểm đúng 4 metric và 1 title).
6. Mọi trường mới trong schema có giá trị mặc định (list/dict dùng `Field(default_factory=...)`), để JSON cũ (`data/cached_runs/`, `eval/results/` của M2) vẫn `Report.model_validate` được.
7. Ghi chú do code nối vào `short_answer`, `recommendation`, `confidence_reason` phải **idempotent**: dùng marker cố định, gỡ ghi chú cũ trước khi nối ghi chú mới; gọi 2 lần vẫn chỉ có 1 ghi chú.
8. LLM không bao giờ viết URL, ngày đăng hay tuổi nguồn. Ở vòng làm mới, LLM chỉ trả câu truy vấn, mã E#/S#, nhãn trạng thái và giải thích; code kiểm tra mã tồn tại và lọc URL.
9. `reference_date` luôn truyền tường minh. TC1–TC6 ghim 2026-10-15 khi so với M2.
10. Không lưu toàn văn trang nguồn vào repo; không xóa `.cache/`; không thêm dependency (cần thì hỏi). Windows: dùng `.venv\Scripts\python.exe`, ghi file UTF-8.

### 4.2 Schema (`research/schemas.py`)
Chỉ thêm, không đổi trường cũ:

```python
DatePrecision = Literal["day", "month", "quarter", "year", "unknown"]
RecencyStatus = Literal["MỚI", "KHÔNG CHẮC", "CŨ"]
InsightRecencyStatus = Literal["MỚI", "MỘT PHẦN CŨ", "KHÔNG CÓ BẰNG CHỨNG MỚI"]
ImpactLevel = Literal["KHÔNG", "NHỎ", "VỪA PHẢI", "ĐÁNG KỂ"]
CounterfactualLevel = Literal["CAO", "TRUNG BÌNH", "THẤP", "MẤT CĂN CỨ"]
RefreshStatus = Literal["ĐÃ LÀM MỚI", "KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN", "KHÔNG CẦN LÀM MỚI", "LỖI"]
ComparisonStatus = Literal["XÁC NHẬN", "CẬP NHẬT", "MÂU THUẪN", "KHÔNG TƯƠNG ĐƯƠNG", "KHÔNG TÌM THẤY DỮ LIỆU MỚI"]

# Source: thêm
date_method: str = ""                     # mã ở bảng 4.3; "" = báo cáo cũ chưa có
date_precision: DatePrecision = "unknown"
age_months: Optional[float] = None        # điểm ước tính theo reference_date
age_months_min: Optional[float] = None
age_months_max: Optional[float] = None

# Evidence: thêm
data_period: str = ""                     # vd "Q1/2025", "H1/2024", "08/2024", "2024"
data_period_end: Optional[str] = None     # ISO, ngày cuối kỳ

class SourceRecency(BaseModel):
    source_id: str
    status: RecencyStatus
    reasons: list[str]                    # tiếng Việt, vd "đăng 2024 (chỉ biết năm), 22–34 tháng"
    date_display: str                     # "14/05/2024" | "05/2025" | "Q1/2025" | "2025 (chỉ biết năm)" | "Không rõ ngày"
    date_method_label: str
    age_display: str                      # "~28 tháng" | "10–22 tháng" | "không rõ"
    older_than_alert: bool                # chắc chắn hơn alert_months theo ngày đăng
    possibly_older_than_alert: bool
    data_vintage: str                     # kỳ số liệu mới nhất trong các trích dẫn của nguồn
    date_conflict: bool                   # trích dẫn nhắc kỳ bắt đầu SAU ngày đăng → ngày đăng có thể sai
    supported_insight_ids: list[str]
    is_key: bool
    key_reasons: list[str]

class InsightImpact(BaseModel):
    insight_id: str
    current: ConfidenceLevel
    if_source_removed: CounterfactualLevel
    if_source_fresh: ConfidenceLevel

class KeySourceImpact(BaseModel):
    source_id: str
    impacts: list[InsightImpact]
    summary: str

class InsightRecency(BaseModel):
    insight_id: str
    status: InsightRecencyStatus
    non_recent_source_ids: list[str]
    note: str

class ThresholdEvent(BaseModel):
    date: str
    source_ids: list[str]
    changes: list[str]                    # "I1: TRUNG BÌNH → THẤP"

class RecencyImpact(BaseModel):
    reference_date: str
    alert_months: int = 18
    impact_level: ImpactLevel = "KHÔNG"
    summary: str = ""
    sources: list[SourceRecency]
    key_old_sources: list[KeySourceImpact]
    insights: list[InsightRecency]
    upcoming_changes: list[ThresholdEvent]
    suggested_refresh_queries: list[str]
    certainty_groups: dict[str, list[str]]  # "Đủ cơ sở" | "Cần lưu ý" | "Chưa chắc chắn" -> insight IDs

class RefreshComparison(BaseModel):
    old_evidence_id: str
    new_evidence_ids: list[str]
    status: ComparisonStatus
    explanation: str

class ConfidenceChange(BaseModel):
    insight_id: str
    before: str                           # mức trước (đã chấm lại cùng ngày tham chiếu) hoặc "—" nếu nhận định mới
    after: str
    reason: str

class RefreshResult(BaseModel):
    status: RefreshStatus
    refreshed_at: str
    reference_date: str
    target_source_ids: list[str]
    queries: list[str]
    new_source_ids: list[str]
    rejected_new_sources: list[RejectedItem]
    comparisons: list[RefreshComparison]
    confidence_changes: list[ConfidenceChange]
    llm_calls_count: int
    duration_seconds: float
    note: str

# Report: thêm
recency: Optional[RecencyImpact] = None
refresh: Optional[RefreshResult] = None

# PipelineTrace: thêm  keywords: list[str], version: int = 1, parent_run_timestamp: str = ""

# Schema LLM cho vòng làm mới
class RefreshQueriesLLMOutput(BaseModel):
    queries: list[str]
class RefreshComparisonItemLLM(BaseModel):
    old_evidence_id: str
    new_evidence_ids: list[str]
    status: Literal["XÁC NHẬN", "CẬP NHẬT", "MÂU THUẪN", "KHÔNG TƯƠNG ĐƯƠNG"]
    explanation: str
class RefreshComparisonLLMOutput(BaseModel):
    items: list[RefreshComparisonItemLLM]
```

### 4.3 Ngày đăng: cách xác định và độ chắc chắn (`research/dates.py`, `research/retrieve.py`)
Tạo module mới `research/dates.py` (không import từ `research/score.py` để tránh vòng import):
- `add_months(d, n) -> date` (kẹp về ngày cuối tháng).
- `detect_date_with_method(url, text, title="") -> tuple[Optional[str], str]`: cùng các quy tắc, cùng thứ tự với `_extract_date_fallback` hiện tại, trả thêm mã cách xác định. `_extract_date_fallback` trong `retrieve.py` trở thành wrapper trả phần tử đầu. **Trước khi refactor:** chạy hàm cũ trên ≥ 12 mẫu (URL + tiêu đề thật lấy từ `eval/results/*.json`, 2 mẫu trong `tests/test_grade.py`, vài đoạn text có "May 3, 2026" hoặc "2026-09-12") và đóng băng kết quả thành golden test; sau refactor phải khớp 100%.
- `infer_date_method(url, text, title, published_date, search_date) -> str`, gọi trong `retrieve_and_grade_sources` sau khi fetch, trước `grade_source`: ngày `None` → `unknown`; bằng ngày công cụ tìm kiếm trả → `search_metadata`; trùng kết quả `detect_date_with_method` → mã đó; còn lại → `html_metadata`.
- `infer_date_method_legacy(url, title, published_date) -> str` cho báo cáo cũ không có text: trùng `detect_date_with_method(url, "", title)` → `legacy_<mã>`; còn lại → `legacy_metadata`.
- `precision_of(method, published_date)`, `date_range(published_date, precision) -> (start, end)`, `format_date_display(...)`, `DATE_METHOD_LABELS` (nhãn tiếng Việt).

| Quy tắc (giữ nguyên thứ tự trong `_extract_date_fallback`) | `date_method` | `date_precision` | Khoảng ngày có thể |
|---|---|---|---|
| `/YYYY/MM/DD` hoặc `/YYYY-MM-DD` trong URL | `url_date` | day | đúng ngày |
| `/YYYY/MM/` trong URL | `url_month` | month | cả tháng |
| `YYYY-MM-DD` trong tiêu đề hoặc 1.500 ký tự đầu | `text_date` | day | đúng ngày |
| `Month DD, YYYY` trong tiêu đề hoặc đầu bài | `text_date` | day | đúng ngày |
| `Month YYYY` trong URL/tiêu đề/đầu bài | `month_year` | month | cả tháng |
| `Qn YYYY` trong URL/tiêu đề | `quarter` | quarter | cả quý (giá trị lưu là tháng cuối quý) |
| năm trong URL/tiêu đề | `year_only` | year | cả năm (giá trị lưu `YYYY-06` chỉ là ước tính) |
| ngày do công cụ tìm kiếm trả | `search_metadata` | 10 ký tự = day, 7 = month | |
| ngày trafilatura đọc từ metadata HTML | `html_metadata` | như trên | |
| không có | `unknown` | unknown | |
| báo cáo cũ, suy lại từ URL + tiêu đề | `legacy_<mã>`, `legacy_metadata` | như trên | |
| người dùng nhập ở UI (giả định) | `user_override` | day | |

Ví dụ nhãn: `year_only` → "chỉ có năm trong URL/tiêu đề (ước tính, sai số tới ±6 tháng)"; `quarter` → "suy từ quý ghi trong URL/tiêu đề"; `html_metadata` → "metadata của trang"; `legacy_metadata` → "metadata (báo cáo cũ không lưu chi tiết)"; `unknown` → "không xác định được".

Tuổi: `age_months = (ref - parse_published_date(d)).days / 30.4375`, làm tròn 1 chữ số; `age_months_min` tính từ cuối khoảng ngày, `age_months_max` từ đầu khoảng.
"Hơn 18 tháng" là **lớn hơn chặt**: `older_than_alert = add_months(range_end, alert) < ref`; `possibly_older_than_alert = (không rõ ngày) or add_months(range_start, alert) < ref`. Ví dụ với ref 2026-10-23: `2025-04-23` không "hơn 18 tháng", `2025-04-22` thì có.

### 4.4 Kỳ số liệu trong trích dẫn (`research/dates.py`)
`detect_data_period(text, ref, publication_bound=None) -> tuple[str, Optional[date]]` trả kỳ số liệu **mới nhất đã qua** được nhắc trong trích dẫn (nhãn, ngày cuối kỳ), hoặc `("", None)`. Không phân biệt hoa thường.

| Mẫu | Ví dụ thật trong M2 | Nhãn | Ngày cuối kỳ |
|---|---|---|---|
| `Q1 2025`, `Q2-2024`, `Q1'25` | TC2-E12 "Q2-2024", TC5-E28 "Q1'25" | `Q1/2025` | 31/03/2025 |
| `first quarter of 2025`, `quý 1/2025`, `quý I năm 2025` | TC1-E2 | `Q1/2025` | 31/03/2025 |
| `H1 2024`, `first half of 2024`, `nửa đầu năm 2024`, `6 tháng đầu năm 2024` | TC2-E5 | `H1/2024` | 30/06/2024 |
| `August 2024`, `Aug 2024`, `tháng 8/2024`, `tháng 8 năm 2024`; "January to August 2024" lấy tháng cuối | TC2-E8 | `08/2024` | 31/08/2024 |
| khoảng năm `2022–2027`, `2022 - 2025` (cho phép khoảng trắng quanh dấu gạch): năm cuối > năm của ref thì là dự báo, bỏ cả khoảng; ngược lại lấy năm cuối | TC4-E13 "giai đoạn 2022 – 2025" (nguồn đăng 14/05/2024, nên kỳ này bị loại theo quy tắc ngày đăng đáng tin bên dưới) | `2025` | 31/12/2025 |
| năm đứng riêng: `2024`, `năm 2024`, `in 2024`, `FY2025`, `năm tài chính 2025` | TC1-E17 "in 2024" | `2024` | 31/12/2024 |

Quy tắc loại:
- Bỏ năm đứng riêng nằm trong một cụm đã khớp mẫu cụ thể hơn ("2025" trong "first quarter of 2025" không được tính là "năm 2025").
- Bỏ năm đứng ngay sau `since`, `kể từ`, `từ năm`, `by`, `đến năm`, `forecast`, `dự báo` (trong 12 ký tự trước nó).
- Bỏ kỳ có ngày cuối > ref (tương lai).
- Ngày đăng có độ chính xác `day` (đáng tin): bỏ kỳ có ngày cuối > ngày đăng, vì đó là dự báo tại thời điểm viết (vd cafef 14/05/2024 viết "dự kiến … vào năm 2026").

Vintage của nguồn = kỳ mới nhất trong các trích dẫn đã xác minh của nguồn đó. Trích dẫn không nhắc kỳ thì dùng vintage của nguồn.

`date_conflict`: ngày đăng **không** ở độ chính xác `day` và có kỳ trong trích dẫn có **ngày bắt đầu** > cuối khoảng ngày đăng, nghĩa là ngày đăng có thể sai (ví dụ thật: TC4-S10 `icon-era.com` ghi `2025-03` nhưng trích dẫn nhắc "Q2 2026 results"). Chỉ gắn cờ và giải thích, **không tự sửa ngày** (sửa ngày sẽ làm đổi độ tin cậy, vi phạm bất biến 3; ghi vào hạn chế và DECISIONS).

Đây là heuristic regex: luôn hiển thị nhãn kỳ ngay cạnh trích dẫn để người dùng tự đối chiếu, và ghi rõ giới hạn trong README.

### 4.5 Phân tích độ mới và ảnh hưởng (`research/recency.py`)
API:

```python
def load_recency_policy() -> dict
def analyze_recency(report: Report, reference_date: date, alert_months: int = 18) -> RecencyImpact
def apply_recency_layer(report: Report, reference_date: date | None = None, alert_months: int | None = None) -> Report
def rescore_report_as_of(report: Report, as_of: date, alert_months: int | None = None) -> Report
def finalize_with_recency(report: Report, reference_date: date, total_quotes_extracted: int,
                          rejected_sources, rejected_quotes, urls_removed_floor: int = 0) -> Report
    # đường đi chung cho pipeline, rescore và refresh:
    # gỡ marker độ mới → score_and_finalize_report → apply_recency_layer
```

`apply_recency_layer` dùng `reference_date` truyền vào; nếu None thì lấy `report.trace["current_date"]`; vẫn thiếu thì `date.today()`.

Thuật toán `analyze_recency` (mọi bước là code tất định):
1. **Điền thông tin ngày** cho mỗi nguồn: `date_method == ""` thì dùng `infer_date_method_legacy`; tính precision, khoảng ngày, tuổi, `older_than_alert`, `possibly_older_than_alert`. Điền `data_period` cho mỗi evidence; tính vintage và `date_conflict` cho mỗi nguồn.
2. **Trạng thái của từng bằng chứng được nhận định trích dẫn**, xét theo thứ tự, điều đầu tiên đúng thì dừng. Gọi `p` là kỳ của chính trích dẫn, không có thì dùng vintage của nguồn:
   1. `p` có và `add_months(p_end, alert) < ref` ⇒ **CŨ** (lý do: "kỳ số liệu Q1/2025, ~19 tháng").
   2. Nguồn `older_than_alert`: có `p` gần đây ⇒ **KHÔNG CHẮC** ("ngày đăng có thể sai"); không có `p` ⇒ **CŨ** ("đăng 06/2024, ~28 tháng").
   3. Nguồn `possibly_older_than_alert` hoặc không rõ ngày: có `p` gần đây ⇒ **MỚI** ("kỳ số liệu gần đây cho thấy nguồn không quá cũ"); không có `p` ⇒ **KHÔNG CHẮC** ("chỉ biết năm 2025 → 10–22 tháng" / "không rõ ngày đăng").
   4. Còn lại ⇒ **MỚI**.
3. **Trạng thái nguồn** = trạng thái xấu nhất trong các bằng chứng của nó được trích dẫn (CŨ > KHÔNG CHẮC > MỚI). Nguồn không được trích dẫn: tính theo ngày đăng + vintage, `supported_insight_ids = []`, không bao giờ là then chốt.
4. **Trạng thái nhận định**: mọi bằng chứng MỚI ⇒ **MỚI**; có ≥ 1 MỚI và ≥ 1 không MỚI ⇒ **MỘT PHẦN CŨ**; không có bằng chứng MỚI nào ⇒ **KHÔNG CÓ BẰNG CHỨNG MỚI**.
5. **Phản thực tế**, dùng nguyên `score_single_insight` với cùng `evidence_map`/`source_map` của báo cáo, cho mỗi cặp (nguồn s, nhận định I có trích s):
   - *Nếu bỏ nguồn*: bỏ mọi evidence của s khỏi I; không còn evidence ⇒ `MẤT CĂN CỨ`; còn ⇒ chấm lại.
   - *Nếu nguồn còn mới*: đặt `s.freshness = "fresh"` trong một bản sao `source_map` rồi chấm lại.
6. **Nguồn then chốt**: nguồn được trích dẫn và thỏa ít nhất một điều sau (ghi `key_reasons` tiếng Việt cho từng điều thỏa):
   - (a) bỏ nguồn làm một nhận định đang CAO/TRUNG BÌNH giảm mức hoặc mất căn cứ;
   - (b) là nguồn hạng A/B duy nhất của một nhận định CAO/TRUNG BÌNH;
   - (c) hỗ trợ ≥ `max(2, ceil(25% × số nhận định))` nhận định;
   - (d) "nếu còn mới" làm ít nhất một nhận định tăng mức (tuổi của nó đang kéo độ tin cậy xuống).
7. `key_old_sources` = nguồn then chốt có trạng thái CŨ hoặc KHÔNG CHẮC, xếp theo: số nhận định CAO/TRUNG BÌNH bị ảnh hưởng (giảm khi bỏ, hoặc tăng khi mới) giảm dần → số nhận định hỗ trợ giảm dần → hạng A, B, C.
8. **Mức ảnh hưởng của báo cáo**:
   - **ĐÁNG KỂ**: có nhận định CAO/TRUNG BÌNH ở trạng thái KHÔNG CÓ BẰNG CHỨNG MỚI; hoặc có nguồn CŨ mà bỏ nó làm một nhận định CAO/TRUNG BÌNH giảm mức hoặc mất căn cứ.
   - **VỪA PHẢI**: có nhận định (mức THẤP) ở trạng thái KHÔNG CÓ BẰNG CHỨNG MỚI; hoặc ≥ 25% số nhận định ở trạng thái MỘT PHẦN CŨ.
   - **NHỎ**: có nguồn được trích dẫn ở trạng thái CŨ/KHÔNG CHẮC nhưng không rơi vào hai mức trên.
   - **KHÔNG**: mọi nguồn được trích dẫn đều MỚI.
9. **Câu tóm tắt** (tiếng Việt, tất định, ≤ 60 từ). Mẫu `summary`:
   > Mức ảnh hưởng: {MỨC}. {x}/{N} nhận định không có bằng chứng nào chắc chắn trong 18 tháng gần đây ({I…}); {y} nhận định dựa một phần vào dữ liệu cũ. Nguồn then chốt cần chú ý nhất: {S#} ({domain}, {date_display}, {age_display}{, kỳ số liệu {vintage}}). Chi tiết ở mục 7.

   Mẫu `KeySourceImpact.summary`:
   > {S#} ({domain}, hạng {tier}; đăng {date_display} — {cách xác định}; {age_display}{; kỳ số liệu mới nhất trong trích dẫn: {vintage}}) là căn cứ của {k}/{N} nhận định ({I…}). Nếu bỏ nguồn này: {I5 mất căn cứ; I2 TRUNG BÌNH → THẤP | không nhận định nào đổi mức}. Nếu nguồn này còn mới (≤ 12 tháng): {I4 THẤP → CAO | không đổi}.
10. **Mốc thời gian** `upcoming_changes` (nên có, cắt được): với mỗi nguồn được trích dẫn có ngày, mốc nó đổi nhóm độ mới (điểm ước tính + 367 ngày nếu đang "mới", + 732 ngày nếu đang "cũ dần"); lấy ≤ 3 mốc sớm nhất trong 12 tháng tới, mỗi mốc gọi `rescore_report_as_of` và ghi nhận định đổi mức. Mẫu: "Từ 15/05/2027 (S1 sang nhóm > 24 tháng), nếu chưa có dữ liệu mới: I1, I2, I3 TRUNG BÌNH → THẤP".
11. **Truy vấn gợi ý** `suggested_refresh_queries` (tất định): với mỗi nguồn trong `key_old_sources`, lấy tiêu đề và thay mọi năm 20xx bằng năm của ref (và năm trước đó); thêm biến thể `"{tiêu đề đã đổi năm} site:{domain}"`.
12. **Nhóm mức chắc chắn** `certainty_groups` (nên có): "Đủ cơ sở" = CAO, hoặc TRUNG BÌNH + `fact` + không mâu thuẫn + trạng thái MỚI; "Chưa chắc chắn" = THẤP, hoặc trạng thái KHÔNG CÓ BẰNG CHỨNG MỚI; còn lại là "Cần lưu ý".

`apply_recency_layer`: điền trường ngày/kỳ vào `sources`/`evidences`, gắn `recency`, rồi:
- `short_answer`: gỡ đoạn từ marker `[Độ mới dữ liệu]` tới hết; **chỉ khi mức = ĐÁNG KỂ** thì nối `" [Độ mới dữ liệu] " + summary`. Mức VỪA PHẢI/NHỎ chỉ hiện ở banner, mục 7 và badge, để tránh cảnh báo thừa.
- `confidence_reason` của mỗi nhận định không MỚI: gỡ phần từ `" · Độ mới:"` tới hết, nối `" · Độ mới: {trạng thái} ({S# tuổi/kỳ}; …)"`.
- Không đụng tới `confidence`.

`rescore_report_as_of(report, as_of)`: gỡ marker độ mới trong `short_answer` → tính lại `freshness`/`freshness_label` của từng nguồn bằng `compute_freshness(..., as_of)` → `score_and_finalize_report(report, total_quotes_extracted=report.quality.total_quotes_extracted, rejected_sources=report.quality.rejected_sources, rejected_quotes=report.quality.rejected_quotes)` → giữ `llm_invented_urls_removed_count` gốc (lấy max, vì URL đã được lọc từ lần trước) → `apply_recency_layer(..., as_of)` → `trace["rescored_as_of"] = as_of`. Không gọi LLM.

**Kết quả tham chiếu.** Nguyên mẫu ngoài repo chạy đúng các quy tắc trên trên `eval/results/TC*.json`, ref 2026-10-15. Dùng làm oracle cho test ở mục 6.2; code của bạn ra khác thì phải giải thích được bằng quy tắc, hoặc sửa:

| Case | Mức | Kết quả chính |
|---|---|---|
| TC1 | ĐÁNG KỂ | I1, I2, I3 (TB) không có bằng chứng mới. S2 CŨ (vintage Q1/2025), S3 KHÔNG CHẮC (chỉ biết năm 2025), S12 CŨ (Q1/2025). Nếu S2 còn mới: I1, I2 → CAO. S6 (đăng 05/08/2026) CŨ vì trích dẫn được dùng nói về 2024 |
| TC2 | ĐÁNG KỂ | 8/10 nhận định không có bằng chứng mới. S5, S6 precision `year`, CŨ. Bỏ S5 ⇒ I5 mất căn cứ; bỏ S6 ⇒ I6 mất căn cứ; bỏ S1 ⇒ I2 mất căn cứ. Nếu S5 mới: I4 → CAO, I5 → TB; nếu S6 mới: I6 → TB; nếu S2 mới: I1 → CAO |
| TC3 | KHÔNG | Mọi nguồn được trích dẫn đều MỚI (đối chứng: không cảnh báo thừa) |
| TC4 | ĐÁNG KỂ | I2, I3 (TB) không có bằng chứng mới. S10 `icon-era.com` có `date_conflict` (ghi 03/2025, trích dẫn nhắc Q2/2026). S7 cafef CŨ (vintage 2021) |
| TC5 | ĐÁNG KỂ | I5 (TB) không có bằng chứng mới. Bỏ S1 ⇒ I5, I6 TB → THẤP; nếu S1 mới ⇒ I5, I6 → CAO |
| TC6 | VỪA PHẢI | I8 chỉ dựa vào nguồn không rõ ngày (mytour.vn) |

### 4.6 Tích hợp: pipeline, báo cáo Markdown, CLI
- `research/pipeline.py`:
  - `run(...)` thêm tham số `alert_months: Optional[int] = None`. Sau `score_and_finalize_report(...)`, gọi `apply_recency_layer(final_report, ref_date, alert_months)`; thêm step log "Bước 6b/6 · Phân tích độ mới dữ liệu (Change Request A2)" kèm mức ảnh hưởng và số nguồn then chốt cũ.
  - Lưu `plan.keywords` vào `trace["keywords"]`; `trace["version"] = 1`.
- `research/retrieve.py`: trong `retrieve_and_grade_sources`, sau khi fetch, điền `date_method` (`infer_date_method`) cho `Source` trước `grade_source`. `fetch_page_content_and_date` giữ nguyên chữ ký và định dạng cache.
- `research/extract.py`: `extract_claims_from_sources(..., evidence_id_start: int = 1)`; mặc định giữ hành vi cũ, prompt không đổi.
- `render_report_markdown`: giữ nguyên mục 1–6 (chỉ thêm). Mục 2: ô "Nguồn" thêm tuổi (vd "`2024` (chỉ biết năm) · 22–34 tháng"). Mục 5: thêm cột "Cách xác định ngày & tuổi". Mục 3.2 tự hiện các mâu thuẫn cũ ↔ mới từ vòng làm mới (đã nằm trong `conflicts`). Thêm **mục 7** khi `report.recency` có:
  ```
  ## 7. Độ mới của dữ liệu & Ảnh hưởng tới độ tin cậy (Change Request A2)
  > Ngày tham chiếu · Ngưỡng 18 tháng · Mức ảnh hưởng: **…**
  {summary}
  ### 7.1 Nguồn và tuổi dữ liệu
      Nguồn | Hạng | Ngày đăng (cách xác định) | Tuổi | Kỳ số liệu trong trích dẫn | Trạng thái | Then chốt | Hỗ trợ nhận định
  ### 7.2 Ảnh hưởng tới từng nhận định (tính bằng code)
      Nguồn | Nhận định | Hiện tại | Nếu bỏ nguồn này | Nếu nguồn này còn mới
  ### 7.3 Mốc thời gian độ tin cậy sẽ thay đổi
  ### 7.4 Gợi ý làm mới dữ liệu
  ### 7.5 Kết quả vòng làm mới (nếu đã chạy)
  ```
- CLI:
  - `python -m research.cli "<câu hỏi>" [--reference-date YYYY-MM-DD] [--refresh-old] [--out-json …] [--out-md …]`
  - `python -m research.recency <report.json> [--as-of YYYY-MM-DD] [--out-json …] [--out-md …]`: phân tích lại báo cáo đã lưu, 0 lần gọi LLM, in mục 7.
  - `python -m research.refresh <report.json> [--reference-date YYYY-MM-DD] [--out-json …] [--out-md …]`

### 4.7 Vòng làm mới nguồn cũ (`research/refresh.py`)
`refresh_old_sources(report, llm=None, reference_date=None, use_cache=True, max_targets=2, progress_callback=None) -> Report`. `reference_date` mặc định là hôm nay. Dùng LLM riêng `LLMClient(max_calls=6)`, tối đa 4 lần gọi.

0. `baseline = rescore_report_as_of(report, ref)`, để thay đổi do thời gian trôi không bị tính nhầm là do làm mới.
1. **Mục tiêu** = tối đa 2 nguồn đầu của `baseline.recency.key_old_sources`. Không có ⇒ trả báo cáo kèm `refresh.status = "KHÔNG CẦN LÀM MỚI"`, 0 lần gọi LLM.
2. **Truy vấn**: truy vấn tất định (4.5 bước 11) + **1 lần gọi LLM** (`RefreshQueriesLLMOutput`). Đưa cho LLM câu hỏi gốc, tiêu đề/domain/ngày/vintage của mục tiêu, claim + trích dẫn của các bằng chứng mục tiêu mà nhận định đang dùng; yêu cầu tối đa 2 truy vấn tiếng Anh cho mỗi mục tiêu để tìm **cùng chỉ số, cùng phạm vi thị trường**, ở kỳ mới hơn (năm của ref hoặc năm trước). Code: lọc URL, bỏ trùng, bỏ truy vấn không chứa năm lớn hơn năm vintage của mục tiêu, tổng ≤ 6 truy vấn. LLM lỗi ⇒ chỉ dùng truy vấn tất định, ghi vào `note`.
3. **Tìm và tải**: `retrieve_and_grade_sources(queries, keywords=trace["keywords"] hoặc từ tiêu đề mục tiêu, reference_date=ref, max_per_query=5, max_kept_sources=6)`. Code lọc và đưa lý do vào `rejected_new_sources`: URL đã có trong báo cáo; không rõ ngày đăng ("không chứng minh được là mới hơn"); cuối khoảng ngày đăng không mới hơn vintage/ngày của mục tiêu nào; trạng thái nguồn không phải MỚI. Đánh lại mã nguồn mới nối tiếp `S{len(sources)+1}`, … (đổi khóa của các dict text tương ứng). Không còn nguồn nào ⇒ `KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN` (thêm gap "Chưa tìm được dữ liệu mới hơn cho …"), không gọi LLM tiếp. Mọi truy vấn đều trả 0 kết quả ⇒ `LỖI` với note "công cụ tìm kiếm không trả kết quả (có thể bị giới hạn tạm thời)".
4. **Trích và xác minh**: `extract_claims_from_sources(question=report.question, sub_questions=[claim của các bằng chứng mục tiêu, tối đa 8], sources=nguồn mới, …, current_date=ref.isoformat(), evidence_id_start=max E# hiện có + 1)`: ≤ 2 lần gọi LLM, vẫn xác minh nguyên văn `>= 90`.
5. **So sánh** (**1 lần gọi LLM**, `RefreshComparisonLLMOutput`): đưa bằng chứng cũ (E#, S#, ngày, kỳ, trích dẫn, claim) và bằng chứng mới đã xác minh. Quy tắc trong prompt: chỉ ghép khi **cùng chỉ số và cùng phạm vi** (quốc gia/khu vực, nền tảng, phân khúc); XÁC NHẬN = số mới cùng xu hướng và độ lớn; CẬP NHẬT = cùng chỉ số, kỳ mới hơn, giá trị khác đáng kể; MÂU THUẪN = trái chiều; không chắc ⇒ KHÔNG TƯƠNG ĐƯƠNG; giải thích tiếng Việt ≤ 40 từ, nêu rõ kỳ (vd "Q1/2025 vs H1/2026"); không viết URL. Code: bỏ mục có mã không tồn tại, lọc URL trong giải thích; bằng chứng cũ không có mục nào ⇒ `KHÔNG TÌM THẤY DỮ LIỆU MỚI`.
6. **Gộp** (code):
   - Thêm nguồn mới, bằng chứng mới vào báo cáo; giữ nguyên S#/E#/I# cũ.
   - XÁC NHẬN ⇒ gắn E# mới vào mọi nhận định đang dùng E# cũ.
   - CẬP NHẬT / MÂU THUẪN ⇒ thêm `ConflictItem` (topic "Số liệu cũ ↔ mới: …", values `["[E#/S#, kỳ/ngày]: trích ≤ 20 từ", …]`, explanation lấy từ bước 5); đặt `has_conflict=True` cho nhận định dùng E# cũ (quy tắc M2 sẽ hạ xuống THẤP, đúng vì nhận định dựa trên số cũ đã bị số mới thay thế); thêm nhận định mới ở cuối danh sách với `statement` = claim của bằng chứng mới, `type="fact"`, `evidence_ids` = E# mới, để code chấm.
   - KHÔNG TƯƠNG ĐƯƠNG / KHÔNG TÌM THẤY ⇒ không gắn; thêm gap cho mục tiêu chưa có dữ liệu mới.
   - Gọi `finalize_with_recency(...)` với `total_quotes_extracted` và danh sách bị loại đã cộng dồn.
   - `recommendation`: gỡ marker `[Sau vòng làm mới` cũ, nối `" [Sau vòng làm mới dd/mm/yyyy] "` + tóm tắt tất định: nhận định nào được xác nhận, nhận định nào có số mới khác số cũ, nguồn nào chưa tìm được bản mới, và câu "khuyến nghị gốc được viết trước vòng làm mới, cần đọc lại các nhận định có đánh dấu".
   - `confidence_changes`: so từng nhận định với `baseline` (cùng ngày tham chiếu); nhận định mới có `before = "—"`.
   - `trace`: `version` + 1, `parent_run_timestamp` = `run_timestamp` của bản trước, `refresh_timestamp`, cộng thêm log từng bước.
7. Bất kỳ lỗi nào (quota, mạng) ⇒ trả báo cáo cũ không đổi, kèm `refresh.status = "LỖI"` và `note` dễ hiểu. UI hiện thông báo, không crash.

### 4.8 Giao diện Streamlit (`app.py`)
- Báo cáo được nạp (đã lưu hay Live) mà chưa có `recency` ⇒ `apply_recency_layer(report, reference_date=trace.current_date)` trong bộ nhớ. Chỉ tính cho báo cáo đang xem (dùng `st.cache_data` theo `run_timestamp` + ngày), để `AppTest` chạy kịp trong 20 giây.
- **Banner** ngay dưới dòng thông tin báo cáo: `st.warning` (ĐÁNG KỂ) / `st.info` (VỪA PHẢI, NHỎ) / `st.success` (KHÔNG): "Độ mới dữ liệu, mức ảnh hưởng {…}: {summary}".
- **Tab mới** đặt ngay sau tab nhận định: **"3. Độ mới & Ảnh hưởng (A2)"**, đánh số lại các tab sau. Nội dung:
  1. Radio "Tính độ mới theo": "Ngày chạy báo cáo ({trace.current_date})" | "Hôm nay ({date.today()})". Chọn "Hôm nay" ⇒ `rescore_report_as_of` trong bộ nhớ, kèm danh sách thay đổi so với ngày chạy (nguồn đổi nhóm, nhận định đổi mức).
  2. Bảng nguồn (như 7.1) bằng `st.dataframe`.
  3. Mỗi nguồn then chốt cũ là một `st.expander`: summary, bảng "Hiện tại | Nếu bỏ nguồn | Nếu nguồn còn mới", các trích dẫn kèm link tô sáng.
  4. Mốc thời gian (7.3) và truy vấn gợi ý (7.4).
  5. "Thử giả định ngày đăng" (nên có): chọn nguồn + `st.date_input` ⇒ chép báo cáo, đặt `published_date`, `date_method="user_override"` ⇒ `rescore_report_as_of` ⇒ hiện nhận định đổi mức. Ghi rõ "Giả định của người dùng, không lưu vào báo cáo".
  6. Vòng làm mới: báo cáo đã có `refresh` ⇒ hiện kết quả (trạng thái, truy vấn, nguồn mới và nguồn bị loại kèm lý do, bảng so sánh cũ ↔ mới, bảng độ tin cậy trước → sau). Chưa có nhưng `data/cached_runs/` có bản làm mới của đúng báo cáo này (`trace.parent_run_timestamp` khớp `run_timestamp`) ⇒ nút "Xem bản đã làm mới (chạy thật lúc …)". Ngược lại ⇒ nút "Tìm dữ liệu mới hơn cho nguồn cũ (Live)": tốn 1 lượt Live, cần key, chạy trong `st.status`.
- Tab 1: thêm khối "Mức chắc chắn của các nhận định" (3 cột theo `certainty_groups`).
- Thẻ nhận định (tab 2): badge trạng thái độ mới (chỉ khi khác MỚI); dòng nguồn của mỗi trích dẫn hiện `date_display`, cách xác định, tuổi, kỳ số liệu; thêm bộ lọc "Chỉ hiện nhận định dựa trên dữ liệu cũ".
- Tab nguồn: thêm cách xác định ngày, tuổi, trạng thái, cờ "ngày đăng có thể sai".
- Thanh chọn nhanh: thêm nút **"TC7 · Làm mới nguồn cũ (A2)"** mở bản làm mới đã lưu của TC2. Lưu ý: TC7 có cùng câu hỏi với TC2, nên vòng lặp chọn báo cáo phải **khớp theo `stem` trước**, chỉ khớp theo câu hỏi khi không có `stem` nào khớp.
- Chế độ Kết quả đã lưu vẫn chạy **không cần key**. Kiểm tra bằng trình duyệt tích hợp trước CHECKPOINT 2.

### 4.9 Cấu hình (`config/recency_policy.yaml`)
```yaml
# Chính sách độ mới dữ liệu (Mission 3 · Change Request A2). Không đổi các ngưỡng chấm điểm của Mission 2.
alert_months: 18            # "hơn 18 tháng" theo change request (so sánh lớn hơn chặt)
key_source_min_share: 0.25  # nguồn hỗ trợ >= 25% số nhận định (tối thiểu 2) là nguồn then chốt
upcoming_window_months: 12  # chỉ báo mốc thay đổi trong 12 tháng tới
refresh_max_targets: 2
refresh_max_queries: 6
refresh_max_new_sources: 6
```
`load_recency_policy()` có giá trị mặc định nếu file thiếu.

## 5. Phạm vi

### 5.1 Làm (theo thứ tự ưu tiên)
1. Lớp độ mới và ảnh hưởng (4.3–4.6): bắt buộc, trả lời trực tiếp change request.
2. Vòng làm mới nguồn cũ (4.7): biến cảnh báo thành hành động, phục vụ C4.
3. Giao diện (4.8).
4. Bộ kiểm thử và so sánh M2 ↔ M3 (mục 6).

### 5.2 Chủ động không làm (ghi vào `DECISIONS.md`, dùng cho Câu 1)
- **Không đổi ngưỡng độ mới hay quy tắc chấm điểm M2** (vd hạ thẳng mọi nguồn > 18 tháng xuống THẤP): change request hỏi "ảnh hưởng thế nào", nên trả lời bằng phân tích minh bạch; đổi quy tắc sẽ mất khả năng so sánh trước/sau và phá regression.
- **Không để LLM đánh giá "nguồn cũ ảnh hưởng nhiều hay ít"**: ảnh hưởng được tính bằng cách chạy lại quy tắc chấm điểm (phản thực tế).
- **Không tự sửa ngày đăng** khi phát hiện mâu thuẫn ngày, và **không tự thay số cũ bằng số mới** trong câu trả lời: hiện cả hai kèm kỳ và nguồn; nhận định cũ bị đánh dấu mâu thuẫn.
- **Không làm upload CSV/PDF nội bộ, đọc PDF, nguồn dữ liệu trả phí** (ưu tiên số 1 trong Câu 3 của M2): ngoài phạm vi change request, cần xử lý bảo mật dữ liệu; ghi là bước tiếp theo.
- **Không làm hỏi-đáp tiếp tự do (chat follow-up) tổng quát**: chỉ làm vòng làm mới có mục tiêu rõ (nguồn cũ then chốt) vì đo được trước/sau.
- Không thêm database, auth hay framework multi-agent; không đổi search provider giữa chừng (giữ khả năng chạy lại từ cache).

## 6. Bộ kiểm thử Mission 3

### 6.1 Regression: chạy lại các test của Mission 2
- P0: chép `eval/results/*` sang `eval/results/m2/` (snapshot M2, commit) **trước khi chạy bất cứ thứ gì ghi đè**.
- `pytest -q`: 21 test cũ pass, không sửa test cũ.
- `eval/cases.yaml`: thêm `reference_date: "2026-10-15"` cho TC1–TC6, **không đổi assertions cũ**. Chạy `python -m eval.run_eval` cho TC1–TC6 (dùng cache, không `--no-cache`).
- Kỳ vọng: TC2–TC5 trùng M2 100% (nhận định, độ tin cậy, `short_answer` sau khi gỡ marker độ mới, chỉ số tự kiểm). TC1, TC6: giữ % trích dẫn xác minh, 0 nhận định CAO từ nguồn C, 0 URL do LLM viết, kết luận Đạt/Chưa đạt như M2 (TC6 vẫn Chưa đạt là đúng). Lệch ở đâu ghi rõ ở đó, không "chỉnh" cho giống.
- `data/cached_runs/` (dùng cho demo): TC2–TC5 dùng bản chạy lại (trùng M2, có đủ cách xác định ngày); TC1, TC6 dùng bản phân tích lại offline từ JSON M2 (`python -m research.recency`) để demo giữ đúng nội dung đã nộp ở M2. Lý do thêm: test giao diện cũ kiểm báo cáo đầu tiên (TC1) hiển thị `100.0%` trích dẫn xác minh. Ghi nguồn gốc mỗi file trong README.

### 6.2 Unit test mới (yêu cầu ≥ 3; kế hoạch dưới đây 20 test)
| File | Test | Loại | Kiểm |
|---|---|---|---|
| `tests/test_recency.py` | `test_cr_a2_tc2_real_report_flags_key_old_sources` | **Change request** | Trên `eval/results/m2/TC2.json`, ref 2026-10-15: khớp oracle TC2 ở 4.5 (S5, S6 precision `year`, CŨ, then chốt; bỏ S5/S6 ⇒ I5/I6 mất căn cứ; nếu S5 mới ⇒ I4 CAO; mức ĐÁNG KỂ; `short_answer` có marker và ≥ 1 mã nguồn) |
| | `test_cr_a2_synthetic_key_source_older_than_18_months` | Change request | Báo cáo giả: nguồn hạng A 20 tháng hỗ trợ 3/4 nhận định ⇒ then chốt; phản thực tế đúng; câu tóm tắt đúng mẫu |
| | `test_recency_layer_is_idempotent_and_never_changes_confidence` | Regression | Áp 2 lần ⇒ 1 marker; mọi `confidence` giữ nguyên trên cả 6 báo cáo M2 |
| | `test_edge_tc1_year_only_and_old_data_in_fresh_source` | **Edge case** | Oracle TC1: S3 KHÔNG CHẮC (chỉ biết năm); S2 CŨ (Q1/2025) dù đăng 05/2025; S6 CŨ dù đăng 05/08/2026 |
| | `test_edge_date_conflict_icon_era_tc4` | Edge case | TC4-S10 có `date_conflict = True`, có lý do "ngày đăng có thể sai" |
| | `test_edge_unknown_date_key_source_is_uncertain` | Edge case | Nguồn then chốt không rõ ngày ⇒ KHÔNG CHẮC, không bị coi là mới |
| | `test_boundary_exactly_18_months_is_not_older` | Edge case | Ref 2026-10-23: `2025-04-23` không hơn 18 tháng; `2025-04-22` hơn; `2025-04` (month) chỉ "có thể" |
| | `test_detect_data_period_patterns` | Edge case | ≥ 10 câu (dùng trích dẫn thật ở bảng 4.4): "Q1'25", "first quarter of 2025", "H1 2024", "January to August 2024", "in 2024", "tháng 9/2026", "2022–2027" (bỏ), "giai đoạn 2022 – 2025" với ngày đăng 14/05/2024 (bỏ), "since 2020" (bỏ), "by 2030" (bỏ), năm tương lai (bỏ) |
| | `test_tc3_control_has_no_recency_alarm` | Regression | TC3 mức KHÔNG, `short_answer` không có marker |
| | `test_rescore_as_of_later_date_ages_sources` | Edge case | TC2 ở ngày 2026-10-23: S2 chuyển aging → stale, mức các nhận định giữ như cũ |
| `tests/test_regression_m2.py` | `test_m2_reports_rescored_at_run_date_are_identical` | **Regression** | Tham số hóa TC1–TC6 từ `eval/results/m2/`: độ tin cậy từng nhận định và chỉ số tự kiểm trùng 100% |
| | `test_m2_json_loads_with_m3_schema` | Regression | Mọi JSON trong `eval/results/m2/` và `data/cached_runs/` validate được |
| | `test_extract_date_fallback_golden_unchanged` | Regression | Bảng golden đóng băng trước refactor (4.3) |
| | `test_markdown_keeps_m2_sections_and_adds_section_7` | Regression | 6 tiêu đề mục cũ nguyên văn + có mục 7 |
| `tests/test_refresh.py` (LLM giả, patch `retrieve_and_grade_sources`, không mạng) | `test_refresh_confirm_upgrades_confidence_and_keeps_ids` | C4 | Nhận định THẤP chỉ dựa nguồn A năm 2024 + bằng chứng mới hạng B 2026 XÁC NHẬN ⇒ TRUNG BÌNH; S#/E# nối tiếp; `version` = 2; `confidence_changes` đúng |
| | `test_refresh_update_adds_conflict_and_new_insight` | C1 | CẬP NHẬT ⇒ có `ConflictItem`, nhận định cũ THẤP, nhận định mới ở cuối |
| | `test_refresh_no_newer_source_reports_honestly` | Edge case | Nguồn tìm được cũ hơn, không rõ ngày hoặc trùng URL ⇒ `KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN`, không gọi extract/compare, có gap mới |
| | `test_refresh_rejects_invalid_ids_and_llm_urls` | Edge case | Mã không tồn tại bị bỏ, URL trong giải thích bị lọc |
| | `test_refresh_without_targets_makes_no_llm_call` | Edge case | `KHÔNG CẦN LÀM MỚI`, 0 lần gọi LLM |
| `tests/test_app_ui_m3.py` (AppTest, không key) | `test_app_shows_recency_banner_tab_and_section_7` | UI | Có tab "Độ mới", có banner, Markdown có mục 7; vẫn đúng 4 metric |

### 6.3 Eval case mới (ghi vào `eval/cases.yaml` **trước khi chạy**)
| ID | Loại | Câu hỏi | Chế độ | Assertions |
|---|---|---|---|---|
| TC7 | Change request A2 | Câu của TC2 | ref 2026-10-15 (phát lại từ cache) + `refresh_old: true` (làm mới với ref = hôm nay) | `must_have_recency_analysis`, `must_flag_key_old_source`, `must_disclose_recency_in_short_answer`, `no_cao_on_old_only_insights`, `must_report_refresh_outcome` |
| TC8 | Edge case | Câu của TC1 | ref 2026-10-15 | `must_have_recency_analysis`, `must_flag_uncertain_age`, `must_flag_old_data_period`, `no_cao_on_old_only_insights` |
| TC9 | Regression | Câu của TC3 | ref 2026-10-15 | `must_match_m2_baseline: eval/results/m2/TC3.json` + assertions cũ của TC3 + `must_not_alarm_recency` |
| TC10 | Tổng quát hóa (nên có) | Câu mới: "Chi phí cài đặt (CPI) trung bình của game mobile tại Đông Nam Á hiện nay là bao nhiêu?" (dự phòng: "Tỷ lệ giữ chân người chơi D1/D30 của game mobile casual tại Đông Nam Á là bao nhiêu?") | Live, ref hôm nay, `refresh_old: true` | `must_have_recency_analysis`, `recency_note_consistent`, `no_cao_on_old_only_insights`, `must_report_refresh_outcome`. Định tính: không bịa CPI; số liệu > 18 tháng không được trình bày như số hiện tại |

TC7–TC9 dùng lại câu hỏi của M2 là cố ý: đề yêu cầu xử lý yêu cầu mới **trên sản phẩm cũ** và chứng minh bản sau tốt hơn bản trước; cùng câu hỏi, cùng nguồn mới so sánh trực tiếp được với output M2. TC10 chứng minh không hardcode.

Ý nghĩa assertions:
- `must_have_recency_analysis`: `report.recency` có và có mục cho mọi nguồn.
- `must_flag_key_old_source`: ≥ 1 phần tử `key_old_sources` có trạng thái CŨ, mỗi phần tử có ≥ 1 `InsightImpact`.
- `must_disclose_recency_in_short_answer`: mức = ĐÁNG KỂ và `short_answer` chứa `[Độ mới dữ liệu]`.
- `recency_note_consistent`: có marker khi và chỉ khi mức = ĐÁNG KỂ.
- `must_not_alarm_recency`: mức thuộc {KHÔNG, NHỎ} và không có marker.
- `must_flag_uncertain_age`: ≥ 1 nguồn được trích dẫn ở trạng thái KHÔNG CHẮC do precision `year`/`unknown`.
- `must_flag_old_data_period`: ≥ 1 nguồn đăng chưa quá 18 tháng nhưng ở trạng thái CŨ vì kỳ số liệu.
- `no_cao_on_old_only_insights`: không nhận định nào ở trạng thái KHÔNG CÓ BẰNG CHỨNG MỚI có mức CAO.
- `must_match_m2_baseline`: (id, confidence) từng nhận định, chỉ số tự kiểm và `short_answer` (đã gỡ marker) trùng file baseline.
- `must_report_refresh_outcome`: `report.refresh` có, `status` hợp lệ, mỗi mục tiêu có ≥ 1 so sánh hoặc lý do bị loại; `confidence_changes` khớp mức thật sau làm mới.

`eval/run_eval.py`: thêm `--reference-date` (ghi đè); đọc `reference_date`, `refresh_old`, `refresh_reference_date` (mặc định "today") từ case; case có làm mới thì lưu cả `TCx_before_refresh.{json,md}` và `TCx.{json,md}`; in mức ảnh hưởng và trạng thái làm mới; `summary.json` thêm cột `impact_level`, `key_old_sources`, `refresh_status`.

### 6.4 So sánh M2 ↔ M3 (`python -m eval.compare_m2_m3` → `eval/results/m2_vs_m3.{json,md}`)
- **Bảng A, Regression TC1–TC6:** Đạt/Chưa đạt M2 so với M3; % trích dẫn xác minh; số nhận định CAO từ nguồn C; số nhận định; phân bổ CAO/TB/THẤP; "trùng từng nhận định?".
- **Bảng B, Change request** (áp lớp M3 lên chính JSON M2, ref 2026-10-15, 0 lần gọi LLM): mức ảnh hưởng; số nguồn then chốt CŨ/KHÔNG CHẮC; số nhận định không có bằng chứng mới; số nguồn chỉ biết năm nhưng M2 hiển thị như tháng cụ thể; số nguồn mới đăng nhưng trích số liệu cũ; số nguồn có `date_conflict`; "trả lời ngắn có nói về tuổi dữ liệu": M2 (tìm "18 tháng"/"độ mới" trong `short_answer` M2) so với M3.
- **Bảng C, Vòng làm mới (TC7, TC10):** mục tiêu, số truy vấn, nguồn mới giữ/loại, số XÁC NHẬN/CẬP NHẬT/MÂU THUẪN/KHÔNG TƯƠNG ĐƯƠNG/KHÔNG TÌM THẤY, nhận định đổi mức trước → sau.

Mọi con số trong README, TESTING và 3 câu trả lời chỉ được lấy từ file này và `eval/results/`.

### 6.5 `TESTING.md`
Thêm phần **"Mission 3"** lên đầu, giữ nguyên phần Mission 2 bên dưới: lệnh chạy; bảng pytest (cũ/mới); Bảng A, B, C; bảng unit test mới (tên · loại · kiểm gì · kết quả); mỗi eval case mới theo mẫu:

```
### TC_ — <tên ngắn> (<Change request | Edge case | Regression | Tổng quát hóa> · <Đạt | Chưa đạt>)
Câu hỏi: …
Kỳ vọng (ghi trước khi chạy): …
Kết quả thực tế: … (số nguồn, mức ảnh hưởng, nguồn then chốt cũ, trích 1–2 dòng output; link eval/results/…)
So với Mission 2: …
Đạt/Chưa đạt: …
Điều học được: …
```
Case nào chưa đạt ghi chưa đạt, kèm nguyên nhân.

## 7. Kế hoạch & checkpoint (~11 giờ)
- **P0 (0,5h):** đọc `BRIEF_M3.md`, `AGENTS.md`, `README.md`, `TESTING.md`, `DECISIONS.md`. Chạy `pytest -q`, ghi số. Kiểm key (chỉ in có/không). Tóm tắt, điểm mơ hồ, Implementation Plan + Task List P0–P1, rồi dừng chờ tôi duyệt (chưa sửa file nào). Sau khi tôi duyệt: commit tài liệu Mission 3; `git tag mission2-final 58a6fba` (local, chưa push); chép snapshot `eval/results/m2/`; đóng băng golden test cho `_extract_date_fallback` (mục 4.3); rồi vào P1.
- **P1 (3,5h):** 4.2–4.6 và 4.9 (schema, `dates.py`, cách xác định ngày trong retrieve, `recency.py`, tích hợp pipeline, mục 7, CLI `research.recency`); test 6.2 của `test_recency.py` và `test_regression_m2.py`; chạy `python -m research.recency` trên 6 JSON M2 → `eval/results/m3_offline/` (0 lần gọi LLM).
  → **CHECKPOINT 1:** Walkthrough gồm output `pytest`; mục 7 thật của TC1 và TC2 (trích); bảng mức ảnh hưởng 6 case so với bảng tham chiếu ở 4.5 (chỗ nào khác, vì sao); quyết định đã ghi `DECISIONS.md`; vấn đề gặp phải. Dừng chờ duyệt.
- **P2 (3h):** 4.7 vòng làm mới + `test_refresh.py`; CLI `research.refresh`; chạy thật trên báo cáo TC2 (bản phát lại) → lưu `data/cached_runs/tc7_cr_a2_refreshed.{json,md}`; 4.8 giao diện + `test_app_ui_m3.py`; kiểm tra bằng trình duyệt tích hợp.
  - Phát lại TC2: `python -m research.cli "<câu hỏi TC2>" --reference-date 2026-10-15 --out-json eval/results/m3_replay/TC2.json` (phải có `trace.llm_calls_count == 0`), rồi `python -m research.refresh eval/results/m3_replay/TC2.json --reference-date <NGÀY_LÀM_MỚI> …`.
  - Ghi lại NGÀY_LÀM_MỚI (ngày dùng cho `--reference-date` của lần làm mới). P3 dùng lại đúng ngày này để eval TC7 phát lại từ cache và trùng bản demo.
  - Không tìm được dữ liệu mới hơn cũng là kết quả hợp lệ; không chạy lại nhiều lần để chọn kết quả đẹp.
  → **CHECKPOINT 2:** ảnh chụp banner, tab Độ mới, khối làm mới, khối mức chắc chắn ở tab 1; kết quả làm mới thật (trạng thái, nguồn mới, trước → sau); vấn đề gặp phải. Dừng chờ duyệt.
- **P3 (2h):** eval (6.3); chạy TC1–TC10; `compare_m2_m3`; cập nhật `data/cached_runs/` theo 6.1; phần Mission 3 của `TESTING.md`; `DECISIONS.md`.
  - `eval/run_eval.py` bọc `try/except` cho từng case: lỗi (vd hết quota) thì ghi vào summary là chưa đạt kèm lý do rồi chạy tiếp case sau.
  - TC7 đặt `refresh_reference_date` = NGÀY_LÀM_MỚI. **Commit `eval/cases.yaml` trước khi chạy eval**, để lịch sử git chứng minh kỳ vọng có trước kết quả.
  - Khi cập nhật `data/cached_runs/`, giữ tên file cũ (vd `tc1_sea_genres.json`); `tc7_cr_a2_refreshed` lấy từ kết quả TC7 chính thức.
  → **CHECKPOINT 3:** Bảng A, B, C; kết quả từng TC; case chưa đạt; giải thích lệch ở TC1/TC6. Dừng chờ duyệt trước khi viết tài liệu.
- **P4 (1,5h):** `README.md`, `SUBMISSION_M3.md` (3 câu trả lời, kịch bản video, checklist), `DECISIONS.md` (mục 8).
- **P5 (0,5h):** quét secrets (repo + `git log -p`) bằng lệnh chỉ in **số lượng** chuỗi giống key, không bao giờ in chuỗi key: `(git log -p --all | Select-String -Pattern 'AIza[0-9A-Za-z_\-]{30,}','sk-or-v1-[0-9a-f]{20,}','tvly-[0-9A-Za-z\-]{10,}','gsk_[0-9A-Za-z]{20,}').Count` phải bằng 0, và `git ls-files` chỉ có `.env.example`. Hỏi tôi nhánh mà app Streamlit đang deploy và xin phép push. Push `master` và nhánh deploy (theo `SUBMISSION.md` là `main`), push tag `mission2-final`. Chờ Streamlit redeploy, mở link bằng phiên ẩn danh trong trình duyệt tích hợp, kiểm tab mới và TC7 xem được không cần key.
  → **CHECKPOINT CUỐI:** checklist DoD (mục 10) đã tick kèm bằng chứng, và danh sách việc tôi còn phải tự làm.

Commit nhỏ theo từng phần, message tiếng Anh (vd `feat(recency): add data recency impact layer for CR A2`). Không commit file video (`*.mp4` đã ignore).

## 8. Tài liệu nộp

**README.md**
- Ngay sau tên và mô tả: khối **"Mission 3: Cải tiến theo Change Request A2 (Dữ liệu cũ)"** gồm 1 câu tóm tắt; link demo (giữ URL cũ); link video Mission 3 (để "(cập nhật sau khi quay)" cho tôi điền); link tag `mission2-final` để so sánh; 3–5 gạch đầu dòng điều đã thay đổi; bảng trước/sau rút từ Bảng B, C; lệnh mới.
- Mục 4: thêm bước "6b · Độ mới & ảnh hưởng" và "Vòng làm mới" vào sơ đồ Mermaid; tóm tắt quy tắc 4.5.
- Mục 5 (R1–R5): bổ sung bằng chứng Mission 3 cho R3, R4, R5.
- Mục 6: thêm lệnh `research.recency`, `research.refresh`, `eval.compare_m2_m3`.
- Mục 7: thêm TC7–TC10.
- Mục 9 Hạn chế: cập nhật theo thứ tự ưu tiên (độ chính xác ngày đăng và regex kỳ số liệu; vòng làm mới phụ thuộc web mở; paywall vẫn còn, TC6; …).
- Giữ phần 3 câu trả lời của Mission 2 (ghi rõ "Mission 2"), thêm 3 câu Mission 3.

**SUBMISSION_M3.md**
1. Đường dẫn: repo, demo, video Mission 3.
2. Câu 1–3: mỗi câu 5–8 câu, ngôi thứ nhất, dẫn test ID và số thật từ `eval/results/m2_vs_m3.md`, không phóng đại. Ý chính cần có (viết theo kết quả thật; dữ liệu nói khác thì theo dữ liệu):
   - **Câu 1:** ưu tiên (1) lớp độ mới và ảnh hưởng tính bằng code, vì change request hỏi "ảnh hưởng thế nào" và người dùng cần biết kết luận nào còn dùng được; (2) cách xác định ngày và kỳ số liệu, vì phát hiện ngày ước tính từ năm bị hiển thị như tháng cụ thể (TC2) và số liệu Q1/2025 nằm trong nguồn đăng tháng 5/2025 (TC1); (3) vòng làm mới giữ bối cảnh. Chủ động chưa làm: các mục ở 5.2, kèm lý do.
   - **Câu 2:** khác biệt lớn nhất và bằng chứng: Bảng B (M2 so với M3 trên cùng dữ liệu), TC7 (trước → sau làm mới), regression TC2–TC5 trùng 100%, số test mới.
   - **Câu 3:** rủi ro lớn nhất còn lại (gợi ý: độ chính xác ngày đăng và kỳ số liệu trên web mở; dẫn tỷ lệ nguồn chỉ biết năm/không rõ ngày đo được; `ddgs` không trả ngày; regex có thể sót hoặc nhầm) và thứ tự xử lý (thêm nguồn metadata ngày như Tavily `published_date`, `datePublished` của schema.org, HTTP `Last-Modified`, rồi đối chiếu chéo; cho người dùng xác nhận ngày ngay trên UI; dữ liệu trả phí/nội bộ cho câu hỏi kiểu TC6).
3. Kịch bản video ≤ 5 phút (mục tiêu 4:30), mỗi đoạn ghi màn hình cần quay và lời nói:
   - `0:00–0:30` Change request A2; mở TC2 bản M2 (tag `mission2-final` hoặc ảnh chụp): chỉ có nhãn "Cũ", trả lời ngắn không nhắc tuổi dữ liệu.
   - `0:30–1:45` TC2 bản M3: banner, ghi chú trong trả lời ngắn, tab Độ mới (S5/S6 AppsFlyer chỉ biết năm 2024, bảng "nếu bỏ / nếu còn mới"); bấm 1 link trích dẫn tô sáng.
   - `1:45–2:45` TC7 vòng làm mới: truy vấn, nguồn mới, so sánh cũ ↔ mới, bảng trước → sau, mã S#/E# nối tiếp (giữ bối cảnh).
   - `2:45–3:30` Edge case TC1/TC4: kỳ Q1/2025, nguồn chỉ biết năm, nguồn mới trích số cũ, ngày đăng có thể sai; chuyển sang "Hôm nay"; thử giả định ngày.
   - `3:30–4:15` Kiểm thử: `pytest` (cũ + mới), TC2–TC5 trùng M2, Bảng B.
   - `4:15–4:45` Rủi ro còn lại và bước tiếp theo.
4. Checklist việc tôi tự làm.

**DECISIONS.md**: thêm các mục `[M3] …` theo dạng bối cảnh → quyết định → lý do, tối thiểu: ngưỡng 18 tháng là cảnh báo, không đổi quy tắc chấm; xác định nguồn then chốt bằng phản thực tế; kỳ số liệu bằng regex và cách xử lý dự báo; gắn cờ mâu thuẫn ngày thay vì tự sửa; ghi chú trong trả lời ngắn chỉ khi ĐÁNG KỂ; vòng làm mới chỉ gắn bằng chứng khi cùng chỉ số và phạm vi, số mới khác số cũ thì ghi mâu thuẫn; ghim `reference_date` khi so với M2; nguồn gốc các file trong `data/cached_runs/`.

## 9. Thiếu giờ thì cắt theo thứ tự
1. "Thử giả định ngày đăng" trên UI.
2. Mốc thời gian độ tin cậy sẽ thay đổi (`upcoming_changes`).
3. TC10 (câu hỏi mới chạy Live).
4. Khối "Đủ cơ sở / Cần lưu ý / Chưa chắc chắn" ở tab 1.
5. Truy vấn làm mới do LLM sinh (giữ truy vấn tất định).
6. Nút chạy làm mới Live trong UI (giữ CLI và bản làm mới đã lưu xem được trên UI).

**Không bao giờ cắt:** lớp độ mới lõi (cách xác định ngày, tuổi, kỳ số liệu, nguồn then chốt, "nếu bỏ / nếu còn mới", mức ảnh hưởng, ghi chú, mục 7, tab Độ mới); ≥ 1 lần làm mới chạy thật (TC7) được lưu; regression TC1–TC6 và 21 test cũ; test change request/edge case/regression; README, TESTING, 3 câu trả lời.

Chậm hơn kế hoạch quá 1 giờ: báo tôi và đề xuất cắt theo thứ tự trên.

## 10. Tiêu chí hoàn thành (DoD)
- [ ] `pytest`: 21 test cũ pass, không sửa; ≥ 12 test mới pass, trong đó có ít nhất 1 change request, 1 edge case, 1 regression (ghi rõ trong `TESTING.md`).
- [ ] TC1–TC6 chạy lại ở ref 2026-10-15: TC2–TC5 trùng M2; TC1, TC6 giữ bất biến; snapshot M2 ở `eval/results/m2/`.
- [ ] TC7: báo cáo chỉ ra nguồn then chốt hơn 18 tháng, bảng ảnh hưởng từng nhận định, ghi chú trong trả lời ngắn; vòng làm mới chạy thật có trạng thái và trước → sau, đã lưu, xem được trên UI không cần key.
- [ ] TC8: nguồn chỉ biết năm/không rõ ngày ⇒ KHÔNG CHẮC; nguồn mới nhưng số liệu cũ được phát hiện.
- [ ] TC9: TC3 trùng M2 và không bị cảnh báo thừa.
- [ ] 0 nhận định CAO chỉ dựa nguồn C; 0 URL do LLM viết; lớp độ mới không đổi mức nhận định nào (có test).
- [ ] Demo online (link cũ) hiện tab Độ mới và TC7, mở được bằng phiên ẩn danh, không cần key.
- [ ] README có khối Mission 3; `TESTING.md` có phần Mission 3 (Bảng A/B/C, TC7–TC10); `DECISIONS.md` có ≥ 5 mục `[M3]`; `SUBMISSION_M3.md` có 3 câu trả lời và kịch bản video.
- [ ] Không có key trong repo và lịch sử git; tag `mission2-final` đã push.

---

## Phụ lục (dành cho tôi; agent bỏ qua phần này)

Bộ prompt dán cho Antigravity (model Gemini 4 Argon) theo từng phase, kế hoạch tổng một trang, những gì cần soi ở mỗi checkpoint, prompt xử lý sự cố và prompt review chéo cuối nằm ở `PROMPTS_M3.md`.

`AGENTS.md` đã được cập nhật cho Mission 3 ngày 23/10/2026 (trỏ sang file này, hạn 16:00 ngày 24/10/2026, bỏ dòng về các ô `{{...}}` của `BRIEF.md`).
