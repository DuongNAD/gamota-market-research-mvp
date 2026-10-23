# Báo cáo Kiểm thử & Đánh giá Chất lượng (TESTING.md)

---

# PHẦN I — MISSION 3: KIỂM THỬ CẢI TIẾN THEO CHANGE REQUEST A2 (DỮ LIỆU CŨ > 18 THÁNG)

> **Change Request A2:** *"Một nguồn quan trọng được phát hành cách đây hơn 18 tháng. Người dùng muốn biết điều đó ảnh hưởng thế nào tới độ tin cậy của kết quả."*

Phần này ghi lại toàn bộ kết quả kiểm thử của **Mission 3** trên ba nhóm bắt buộc:
1. **Kiểm thử hồi quy (Regression)**: 21 test cũ của Mission 2 giữ nguyên 100%, kèm 8 bài kiểm thử hồi quy mới và chạy lại 6 case `TC1`–`TC6` ở `reference_date = 2026-10-15` so với snapshot [`eval/results/m2/`](eval/results/m2/).
2. **Kiểm thử yêu cầu mới (Change Request A2) & Vòng làm mới (C4/C1)**: Phân tích độ mới dữ liệu (`research/dates.py`, `research/recency.py`), kiểm tra phản thực tế (*"Nếu bỏ nguồn này"*, *"Nếu nguồn này còn mới"*), và vòng làm mới có mục tiêu (`research/refresh.py`) trên `TC7` và `TC10`.
3. **Kiểm thử trường hợp biên (Edge Cases)**: Nguồn chỉ biết năm (`precision="year"`), nguồn không rõ ngày (`precision="unknown"`), nguồn mới đăng nhưng trích dẫn kỳ số liệu đã quá 18 tháng (`data_period_end`), nguồn có mâu thuẫn ngày đăng (`date_conflict`), và ranh giới đúng 18 tháng.

---

## M3.1. Lệnh chạy kiểm thử Mission 3

```bash
# 1. Chạy toàn bộ bộ kiểm thử tự động (21 test cũ Mission 2 + 25 test item mới Mission 3 = 46 passed)
.venv\Scripts\python.exe -m pytest -v

# 2. Chạy phân tích độ mới & ảnh hưởng (Change Request A2) offline trên báo cáo JSON sẵn có (0 lần gọi LLM)
.venv\Scripts\python.exe -m research.recency eval/results/m2/TC2.json --as-of 2026-10-15 --out-json eval/results/m3_offline/TC2.json --out-md eval/results/m3_offline/TC2.md

# 3. Chạy vòng làm mới có mục tiêu cho các nguồn then chốt cũ
.venv\Scripts\python.exe -m research.refresh eval/results/m3_replay/TC2.json --reference-date 2026-10-23 --out-json data/cached_runs/tc7_cr_a2_refreshed.json --out-md data/cached_runs/tc7_cr_a2_refreshed.md

# 4. Chạy bộ đánh giá End-to-End 10 test case (TC1–TC10)
.venv\Scripts\python.exe -m eval.run_eval

# 5. Sinh bảng đối chiếu định lượng Mission 2 <-> Mission 3 (eval/results/m2_vs_m3.{json,md})
.venv\Scripts\python.exe -m eval.compare_m2_m3
```

---

## M3.2. Tổng hợp kết quả `pytest` (Mission 2 vs. Mission 3)

Kết quả chạy thực tế `.venv\Scripts\python.exe -m pytest -q`: **`46 passed in 6.38s`**.

| Nhóm file test | Số hàm test | Số test item (`pytest`) | Trạng thái | Ghi chú |
|---|---|---|---|---|
| **Test cũ Mission 2** (`test_grade.py`, `test_verify_quote.py`, `test_score.py`, `test_pipeline_mock.py`, `test_app_ui.py`) | `21` | `21` | **`21 passed`** | Giữ nguyên 100% không sửa bất kỳ dòng nào (`git diff mission2-final` trống). |
| **Test mới Mission 3 — Độ mới & Ảnh hưởng** ([`tests/test_recency.py`](tests/test_recency.py)) | `10` | `10` | **`10 passed`** | Kiểm tra Change Request A2 trên `TC2.json` thật, báo cáo tổng hợp, tính bất biến của `confidence`, và 7 trường hợp biên. |
| **Test mới Mission 3 — Hồi quy M2** ([`tests/test_regression_m2.py`](tests/test_regression_m2.py)) | `4` | `9` | **`9 passed`** | Tham số hóa `TC1`–`TC6` (`6 items`), kiểm tra tương thích ngược schema JSON, golden test `_extract_date_fallback`, và tiêu đề mục 1–7. |
| **Test mới Mission 3 — Vòng làm mới** ([`tests/test_refresh.py`](tests/test_refresh.py)) | `5` | `5` | **`5 passed`** | Kiểm tra nâng mức tin cậy khi `XÁC NHẬN`, gắn `ConflictItem` khi `CẬP NHẬT`, báo trung thực khi không có nguồn mới, lọc mã/URL lậu. |
| **Test mới Mission 3 — Giao diện Streamlit** ([`tests/test_app_ui_m3.py`](tests/test_app_ui_m3.py)) | `1` | `1` | **`1 passed`** | Kiểm tra banner độ mới, tab `"3. Độ mới & Ảnh hưởng (A2)"`, mục 7 Markdown và giữ đúng 4 thẻ `st.metric`. |
| **Tổng cộng** | **`41` hàm** | **`46` items** | **`46 passed`** | **100% pass**, không cần API key khi chạy `pytest`. |

---

## M3.3. Bảng chi tiết 20 hàm Unit & UI Test mới của Mission 3

| STT | File | Tên hàm test | Loại kiểm thử | Nội dung kiểm tra | Kết quả |
|---|---|---|---|---|---|
| 1 | `tests/test_recency.py` | `test_cr_a2_tc2_real_report_flags_key_old_sources` | **Change request** | Trên `eval/results/m2/TC2.json` (`ref = 2026-10-15`): `S5`, `S6` có `date_precision="year"` (`2024 (chỉ biết năm)`), trạng thái `CŨ`, là nguồn then chốt; bỏ `S5`/`S6` làm `I5`/`I6` `MẤT CĂN CỨ`; nếu `S5` còn mới thì `I4` lên `CAO`; mức ảnh hưởng `ĐÁNG KỂ`; `short_answer` có `[Độ mới dữ liệu]`. | **PASS** |
| 2 | `tests/test_recency.py` | `test_cr_a2_synthetic_key_source_older_than_18_months` | **Change request** | Báo cáo giả định có nguồn Hạng A 20 tháng tuổi hỗ trợ 3/4 nhận định: xác định đúng nguồn then chốt, tính đúng bảng phản thực tế (*nếu bỏ / nếu còn mới*) và câu tóm tắt. | **PASS** |
| 3 | `tests/test_recency.py` | `test_recency_layer_is_idempotent_and_never_changes_confidence` | **Regression** | Áp dụng `apply_recency_layer` 2 lần liên tiếp chỉ chèn đúng 1 marker `[Độ mới dữ liệu]` và giữ nguyên 100% điểm `confidence` trên cả 6 báo cáo `TC1`–`TC6` của Mission 2. | **PASS** |
| 4 | `tests/test_recency.py` | `test_edge_tc1_year_only_and_old_data_in_fresh_source` | **Edge case** | Trên `TC1.json`: `S3` chỉ biết năm 2025 → `KHÔNG CHẮC` (`9–21 tháng`); `S2` đăng `05/2025` nhưng trích số liệu `Q1/2025` → `CŨ`; `S6` đăng `05/08/2026` nhưng trích số liệu `2024` → `CŨ`. | **PASS** |
| 5 | `tests/test_recency.py` | `test_edge_date_conflict_icon_era_tc4` | **Edge case** | Trên `TC4.json`: `S10` (`icon-era.com`) có ngày đăng `02/06/2024` nhưng trích dẫn chứa số liệu `Q1/2025` → gắn cờ `date_conflict = True` kèm lý do *"ngày đăng có thể sai"*. | **PASS** |
| 6 | `tests/test_recency.py` | `test_edge_unknown_date_key_source_is_uncertain` | **Edge case** | Nguồn then chốt không rõ ngày đăng (`published_date = None`, `precision = "unknown"`) được gán trạng thái `KHÔNG CHẮC` thay vì coi là mới. | **PASS** |
| 7 | `tests/test_recency.py` | `test_boundary_exactly_18_months_is_not_older` | **Edge case** | Tại `ref = 2026-10-23`: ngày `2025-04-23` (đúng 18 tháng) có `older_than_alert = False`; ngày `2025-04-22` (18 tháng + 1 ngày) có `older_than_alert = True`; tháng `2025-04` (`precision="month"`) chỉ báo *"có thể hơn 18 tháng"*. | **PASS** |
| 8 | `tests/test_recency.py` | `test_detect_data_period_patterns` | **Edge case** | Kiểm tra > 10 mẫu trích dẫn thật: nhận diện đúng `Q1'25`, `first quarter of 2025`, `H1 2024`, `January to August 2024`, `in 2024`, `tháng 9/2026`; bỏ qua dải dự báo `2022–2027`, `giai đoạn 2022 – 2025` (khi bài đăng 2024), `since 2020`, `by 2030`. | **PASS** |
| 9 | `tests/test_recency.py` | `test_tc3_control_has_no_recency_alarm` | **Regression** | Trên `TC3.json` (`ref = 2026-10-15`): toàn bộ nhận định có bằng chứng mới ≤ 18 tháng → `impact_level = "KHÔNG"`, `short_answer` không bị chèn cảnh báo `[Độ mới dữ liệu]`. | **PASS** |
| 10 | `tests/test_recency.py` | `test_rescore_as_of_later_date_ages_sources` | **Edge case** | Chấm lại `TC2` ở ngày `2026-10-23`: nguồn `S2` (`2024-10`) chuyển từ `aging` sang `stale` nhưng điểm `confidence` của các nhận định vẫn giữ nguyên theo quy tắc. | **PASS** |
| 11 | `tests/test_regression_m2.py` | `test_m2_reports_rescored_at_run_date_are_identical` | **Regression** | Tham số hóa `TC1`–`TC6` từ `eval/results/m2/`: chạy lại `score_and_finalize_report` + `apply_recency_layer` tại ngày chạy M2 (`2026-10-15`) cho kết quả `(id, confidence)` và `quality` trùng khớp 100%. | **PASS (6/6)** |
| 12 | `tests/test_regression_m2.py` | `test_m2_json_loads_with_m3_schema` | **Regression** | Mọi file JSON trong `eval/results/m2/` và `data/cached_runs/` đều nạp thành công bằng schema `Report` của Mission 3 (các trường mới đều có giá trị mặc định tương thích ngược). | **PASS** |
| 13 | `tests/test_regression_m2.py` | `test_extract_date_fallback_golden_unchanged` | **Regression** | Đóng băng đầu ra của `_extract_date_fallback` trên 11 mẫu URL/title/text trước và sau khi tách sang `research/dates.py`. | **PASS** |
| 14 | `tests/test_regression_m2.py` | `test_markdown_keeps_m2_sections_and_adds_section_7` | **Regression** | `render_report_markdown` giữ nguyên văn 6 tiêu đề mục 1–6 của Mission 2 và bổ sung mục `## 7. Độ mới của dữ liệu & Ảnh hưởng tới độ tin cậy (Change Request A2)`. | **PASS** |
| 15 | `tests/test_refresh.py` | `test_refresh_confirm_upgrades_confidence_and_keeps_ids` | **Change request (C4)** | Khi nguồn mới Hạng B (2026) `XÁC NHẬN` bằng chứng của nguồn Hạng A năm 2024: nhận định tăng từ `THẤP` lên `TRUNG BÌNH`, mã `S#`/`E#` nối tiếp không đánh số lại, `trace.version = 2`. | **PASS** |
| 16 | `tests/test_refresh.py` | `test_refresh_update_adds_conflict_and_new_insight` | **Change request (C1)** | Khi nguồn mới `CẬP NHẬT` số liệu khác kỳ cũ: thêm `ConflictItem` cũ ↔ mới, đánh dấu `has_conflict=True` hạ nhận định cũ xuống `THẤP`, và thêm nhận định mới ở cuối báo cáo. | **PASS** |
| 17 | `tests/test_refresh.py` | `test_refresh_no_newer_source_reports_honestly` | **Edge case** | Khi các nguồn tìm được đều cũ hơn, không rõ ngày hoặc trùng URL: trả trạng thái `KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN`, không gọi LLM rút trích/so sánh, ghi rõ vào `gaps`. | **PASS** |
| 18 | `tests/test_refresh.py` | `test_refresh_rejects_invalid_ids_and_llm_urls` | **Edge case** | Bỏ qua mã `old_evidence_id` / `new_evidence_ids` không hợp lệ và tự động lọc bỏ mọi URL do LLM viết trong lời giải thích so sánh. | **PASS** |
| 19 | `tests/test_refresh.py` | `test_refresh_without_targets_makes_no_llm_call` | **Edge case** | Báo cáo không có nguồn then chốt cũ trả ngay `KHÔNG CẦN LÀM MỚI` với `0` lần gọi LLM. | **PASS** |
| 20 | `tests/test_app_ui_m3.py` | `test_app_shows_recency_banner_tab_and_section_7` | **UI (AppTest)** | Giao diện Streamlit hiển thị banner độ mới, tab `"3. Độ mới & Ảnh hưởng (A2)"`, mục 7 trong Markdown, và giữ nguyên đúng 1 `st.title` + 4 `st.metric` (`TC1` đạt `100.0%`). | **PASS** |

---

## M3.4. Đối chiếu định lượng Mission 2 ↔ Mission 3 (Bảng A, B, C)

Dữ liệu dưới đây được trích xuất tự động bằng [`eval/compare_m2_m3.py`](eval/compare_m2_m3.py) từ [`eval/results/m2/`](eval/results/m2/) và [`eval/results/`](eval/results/) (lưu tại [`eval/results/m2_vs_m3.md`](eval/results/m2_vs_m3.md) và [`eval/results/m2_vs_m3.json`](eval/results/m2_vs_m3.json)):

### Bảng A — Kiểm thử Hồi quy (`TC1`–`TC6`: Mission 2 so với Mission 3 tại `ref = 2026-10-15`)

| Case | Đạt/Chưa đạt (M2 → M3) | % Trích dẫn xác minh (M2 → M3) | CAO từ nguồn C (M2 → M3) | Số nhận định (M2 → M3) | Phân bổ CAO/TB/THẤP (M2 → M3) | Trùng từng nhận định & trả lời ngắn? |
|---|---|---|---|---|---|---|
| **TC1** | `ĐẠT` → **`ĐẠT`** | `100.0%` (30/30) → `92.6%` (25/27) | `0` → `0` | `8` → `10` | `0/4/4` → `0/6/4` | Khác nguồn phụ khi chạy lại (bản offline trùng 100%) |
| **TC2** | `ĐẠT` → **`ĐẠT`** | `100.0%` (28/28) → `100.0%` (28/28) | `0` → `0` | `10` → `10` | `0/3/7` → `0/3/7` | **Trùng 100%** |
| **TC3** | `ĐẠT` → **`ĐẠT`** | `100.0%` (28/28) → `100.0%` (28/28) | `0` → `0` | `8` → `8` | `3/1/4` → `3/1/4` | **Trùng 100%** |
| **TC4** | `ĐẠT` → **`ĐẠT`** | `100.0%` (29/29) → `100.0%` (29/29) | `0` → `0` | `8` → `8` | `0/2/6` → `0/2/6` | **Trùng 100%** |
| **TC5** | `ĐẠT` → **`ĐẠT`** | `100.0%` (31/31) → `100.0%` (31/31) | `0` → `0` | `9` → `9` | `0/5/4` → `0/5/4` | **Trùng 100%** |
| **TC6** | `CHƯA ĐẠT` → **`CHƯA ĐẠT`** | `100.0%` (20/20) → `100.0%` (20/20) | `0` → `0` | `9` → `8` | `0/2/7` → `0/2/6` | Khác nguồn phụ khi chạy lại (bản offline trùng 100%) |

> **Giải thích nguyên nhân lệch nhẹ ở `TC1` và `TC6` khi chạy lại qua `eval.run_eval`:**
> - Ở Mission 2, `retrieve_and_grade_sources` dùng `as_completed(future_to_cand)` khi tải trang song song bằng `ThreadPoolExecutor`, khiến thứ tự các nguồn đồng hạng cùng điểm `(tier, freshness, -kw_hits)` phụ thuộc vào tốc độ mạng lúc chạy. Trong Mission 3, tôi đã đổi sang duyệt `futures` theo thứ tự tất định. Do đó, `TC2`, `TC3`, `TC4`, `TC5` khớp 100% với cache LLM của Mission 2 (`0` lần gọi LLM mới, trùng 100% từng nhận định, độ tin cậy và `short_answer`). Riêng ở `TC1` và `TC6`, thứ tự tất định chọn 1 nguồn đồng hạng khác với lần chạy ngẫu nhiên `as_completed` của M2 nên tạo tổ hợp lô nguồn mới khi gọi `Extract`/`Synthesize`. Dù vậy, cả `TC1` và `TC6` vẫn giữ nguyên toàn bộ bất biến (`CAO từ nguồn C = 0`, `URL do LLM tự viết = 0`, `TC1` **ĐẠT**, `TC6` **CHƯA ĐẠT** đúng giới hạn paywall). Đồng thời, trên bản phân tích offline từ JSON Mission 2 (`eval/results/m3_offline/TC1.json` và `TC6.json`), cả 6/6 báo cáo đều giữ nguyên 100% nhận định gốc.

### Bảng B — Phát hiện của Lớp Độ mới & Ảnh hưởng trên chính dữ liệu Mission 2 (`ref = 2026-10-15`, `0` lần gọi LLM)

| Case | Mức ảnh hưởng (A2) | Nguồn then chốt CŨ / KHÔNG CHẮC | Nhận định thiếu bằng chứng mới | Nguồn chỉ biết năm nhưng M2 hiện như tháng 6 | Nguồn mới đăng nhưng trích số liệu > 18 tháng | Nguồn có `date_conflict` | `short_answer` có nêu tuổi dữ liệu? (M2 → M3) |
|---|---|---|---|---|---|---|---|
| **TC1** | **`ĐÁNG KỂ`** | **3** (`S2, S3, S12`) | **4/8** (`I1, I2, I3, I6`) | **3** (`S3, S7, S12`) | **3** (`S2, S6, S12`) | `0` | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC2** | **`ĐÁNG KỂ`** | **5** (`S1, S5, S2, S3, S6`) | **8/10** (`I1, I2, I3, I4, I5, I6, I9, I10`) | **3** (`S5, S6, S10`) | **2** (`S1, S3`) | `0` | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC3** | **`KHÔNG`** | `0` | `0/8` | **1** (`S1`) | **1** (`S10`) | `0` | Không → Không (đúng quy tắc) |
| **TC4** | **`ĐÁNG KỂ`** | **6** (`S1, S2, S5, S7, S10, S11`) | **6/8** (`I2, I3, I5, I6, I7, I8`) | **3** (`S1, S8, S9`) | **2** (`S2, S11`) | **1** (`S10`) | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC5** | **`ĐÁNG KỂ`** | **1** (`S1`) | **3/9** (`I5, I7, I9`) | **3** (`S2, S8, S9`) | **3** (`S1, S7, S12`) | `0` | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC6** | **`VỪA PHẢI`** | `0` | **1/9** (`I8`) | **1** (`S7`) | `0` | `0` | Không → Không (đúng quy tắc) |
| **Tổng (`TC1`–`TC6`)** | **4 `ĐÁNG KỂ` · 1 `VỪA PHẢI` · 1 `KHÔNG`** | **15 lượt nguồn then chốt** | **22/52 nhận định** (`42,3%`) | **14/72 nguồn** (tổng nguồn chỉ biết năm/không rõ ngày: **24/72** = `33,3%`) | **11/72 nguồn** (`15,3%`) | **1 nguồn** | **0/6 → 4/4 case `ĐÁNG KỂ`** |

### Bảng C — Kết quả Vòng làm mới dữ liệu có mục tiêu (`TC7`, `TC10`)

| Case | Ngày làm mới | Trạng thái | Nguồn mục tiêu | Truy vấn | Nguồn mới (Giữ / Loại) | Bằng chứng mới | Đối chiếu (`XÁC NHẬN` / `CẬP NHẬT` / `MÂU THUẪN` / `KHÔNG TĐ` / `KHÔNG TÌM THẤY`) | Nhận định đổi mức (Trước → Sau làm mới) |
|---|---|---|---|---|---|---|---|---|
| **TC7** *(Làm mới TC2)* | `2026-10-23` | **`ĐÃ LÀM MỚI`** | `S1, S5` | `6` | `6` giữ (`S13–S18`) / `18` loại | `12` (`E29–E40`) | `2` XN / `3` CN / `0` MT / `2` KTĐ / `0` KTT | `I2`: `TRUNG BÌNH` → `THẤP` *(có số liệu kỳ mới)*; `I5`: `THẤP` → **`TRUNG BÌNH`** *(được xác nhận bởi nguồn 2026)*; thêm `I11` (`TRUNG BÌNH`), `I12` (`THẤP`), `I13` (`TRUNG BÌNH`) |
| **TC10** *(Câu hỏi mới CPI)* | `2026-10-23` | **`ĐÃ LÀM MỚI`** | `S1, S10` | `6` | `6` giữ (`S13–S18`) / `17` loại | `15` (`E23–E37`) | `4` XN / `2` CN / `0` MT / `1` KTĐ / `0` KTT | `I4`: `TRUNG BÌNH` → `THẤP` *(cập nhật tổng lượt tải cả năm 2025 so với Q1/2025)*; thêm `I10` (`TRUNG BÌNH`), `I11` (`TRUNG BÌNH`) |

---

## M3.5. Chi tiết 4 Eval Case mới của Mission 3 (`TC7`–`TC10`)

### TC7 — Change Request A2: Ảnh hưởng nguồn cũ > 18 tháng & Vòng làm mới trên TC2 (`Change request` · `ĐẠT`)
- **Câu hỏi:** Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines?
- **Kỳ vọng (ghi trước khi chạy trong [`eval/cases.yaml`](eval/cases.yaml)):** Phát hiện các nguồn then chốt cũ hơn 18 tháng (`S1`, `S5`, `S2`, `S3`, `S6`), định lượng ảnh hưởng từng nhận định (*"Nếu bỏ nguồn này"*, *"Nếu nguồn này còn mới"*), nối ghi chú `[Độ mới dữ liệu]` vào `short_answer`; sau đó chạy vòng làm mới thực tế (`refresh_old: true`, `refresh_reference_date: 2026-10-23`) để tìm dữ liệu 2025–2026 cho nguồn cũ nhất, đối chiếu với bằng chứng cũ và chấm lại độ tin cậy.
- **Kết quả thực tế:**
  - **Trước làm mới (`eval/results/TC7_before_refresh.json`, `ref = 2026-10-15`):** Mức ảnh hưởng **`ĐÁNG KỂ`**; 8/10 nhận định thiếu bằng chứng mới ≤ 18 tháng; 5 nguồn then chốt cũ (`S1, S5, S2, S3, S6`), trong đó `S5` và `S6` (`appsflyer.com`) chỉ biết năm `2024` (tuổi `22–34 tháng`, trạng thái `CŨ`). Nếu bỏ `S5` thì `I5` mất căn cứ; nếu bỏ `S6` thì `I6` mất căn cứ.
  - **Sau vòng làm mới (`eval/results/TC7.json`, `refresh_ref = 2026-10-23`):** Trạng thái **`ĐÃ LÀM MỚI`** (nhắm vào 2 nguồn then chốt đầu bảng `S1` và `S5`, chạy 6 truy vấn, thu thêm 6 nguồn mới `S13`–`S18` từ 2025–2026, xác minh thêm 12 trích dẫn nguyên văn `E29`–`E40`, nâng tổng số trích dẫn xác minh lên **`40/40 (100.0%)`**).
  - Nhận định **`I5`** (tỷ lệ game di động dùng IAP theo AppsFlyer 2024) được bằng chứng mới năm 2026 xác nhận nên tăng độ tin cậy từ **`THẤP` → `TRUNG BÌNH`**. Nhận định **`I2`** (doanh thu IAP Q1/2025 đạt `625 triệu USD`) được đối chiếu với số liệu mới (`E29`: doanh thu IAP cả năm đạt `5,3 tỷ USD`), nên được gắn `ConflictItem` cũ ↔ mới, hạ `I2` từ `TRUNG BÌNH` → `THẤP` và bổ sung 3 nhận định mới `I11` (`TRUNG BÌNH`), `I12` (`THẤP`), `I13` (`TRUNG BÌNH`).
  - Trích output thực tế từ [`eval/results/TC7.md`](eval/results/TC7.md):
    > **Ghi chú độ mới trong `short_answer`:** *"[Độ mới dữ liệu] 7/13 nhận định chính dựa hoàn toàn vào dữ liệu đã hơn 18 tháng hoặc chưa rõ tuổi (S1, S15, S2; 05/2025, kỳ số liệu Q1/2025); xem mục 7 để biết kết luận nào cần kiểm chứng lại."*
    > **Mục 7.5 (Kết quả vòng làm mới):** *"Trạng thái: `ĐÃ LÀM MỚI` · Ngày tham chiếu làm mới: `2026-10-23` · Nguồn mục tiêu: `S1, S5` · Nguồn mới bổ sung: `S13, S14, S15, S16, S17, S18` · Số lệnh gọi LLM: `3`"*
  - File kết quả: [`eval/results/TC7.md`](eval/results/TC7.md) · [`eval/results/TC7.json`](eval/results/TC7.json) · Bản trước làm mới: [`eval/results/TC7_before_refresh.md`](eval/results/TC7_before_refresh.md)
- **So với Mission 2:** Ở Mission 2, `S5` và `S6` (`appsflyer.com`) bị hiển thị ngày đăng giả tạo là `2024-06` mà không cho biết đó chỉ là năm ước tính (`±6 tháng`), `S1` đăng `05/2025` được gắn nhãn `Mới (<=12 tháng)` dù trích số liệu `Q1/2025` (đã 18,5 tháng), và `short_answer` không hề cảnh báo người đọc rằng 8/10 nhận định dựa trên dữ liệu đã quá 18 tháng. Bản Mission 3 chỉ rõ từng nguồn then chốt cũ, tính bảng phản thực tế và tự động tìm được nguồn 2026 để nâng `I5` từ `THẤP` lên `TRUNG BÌNH` mà vẫn giữ nguyên các mã `S1`–`S12` và `E1`–`E28` cũ.
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Khi có số liệu kỳ mới khác kỳ cũ (`E2` Q1/2025 `625 triệu USD` vs `E29` cả năm `5,3 tỷ USD`), việc không tự ý xóa số cũ mà tạo `ConflictItem` kèm nhận định mới `I11` giúp người làm sản phẩm thấy rõ sự thay đổi theo thời gian và không bị mất ngữ cảnh của báo cáo trước.

---

### TC8 — Edge Case: Nguồn chỉ biết năm & Nguồn mới đăng nhưng trích số liệu cũ trên TC1 (`Edge case` · `ĐẠT`)
- **Câu hỏi:** Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?
- **Kỳ vọng (ghi trước khi chạy trong [`eval/cases.yaml`](eval/cases.yaml)):** Phát hiện nguồn chỉ biết năm 2025 (`S3` `sensortower.com`, `date_precision="year"` → trạng thái `KHÔNG CHẮC`, tuổi `9–21 tháng`) và nguồn mới đăng nhưng trích kỳ số liệu đã quá 18 tháng (`S2` đăng `05/2025` nhưng trích số liệu `Q1/2025`; `S6` đăng `05/08/2026` nhưng trích số liệu năm `2024` → trạng thái `CŨ`); không có nhận định nào chỉ dựa trên dữ liệu cũ đạt mức `CAO`.
- **Kết quả thực tế:**
  - Thu thập **12 nguồn**, xác minh **`25/27 (92.6%)`** trích dẫn nguyên văn, tạo **10 nhận định** (`0 CAO`, `6 TRUNG BÌNH`, `4 THẤP`).
  - Mức ảnh hưởng độ mới: **`ĐÁNG KỂ`**; nguồn then chốt cũ/không chắc: **`S2, S3, S12`**.
  - Cả 4 tiêu chí kiểm tự động (`must_have_recency_analysis`, `must_flag_uncertain_age`, `must_flag_old_data_period`, `no_cao_on_old_only_insights`) đều **ĐẠT**.
  - Trích output thực tế từ [`eval/results/TC8.md`](eval/results/TC8.md) (và [`eval/results/m3_offline/TC1.md`](eval/results/m3_offline/TC1.md)):
    > **S2 (`sensortower.com`, Hạng A):** Ngày đăng `05/2025` (tháng/năm trong URL hoặc tiêu đề), tuổi `~17 tháng`, kỳ số liệu trong trích dẫn `Q1/2025` → Trạng thái **`CŨ`** (*"số liệu trong bài thuộc kỳ Q1/2025 (~18.5 tháng tính từ cuối kỳ)"*).
    > **S3 (`sensortower.com`, Hạng A):** Ngày đăng `2025 (chỉ biết năm)` (chỉ có năm trong URL/tiêu đề — ước tính sai số ±6 tháng), tuổi `9–21 tháng` → Trạng thái **`KHÔNG CHẮC`** (*"chỉ xác định được năm đăng (2025), tuổi thực từ 9 đến 21 tháng"*).
    > **S6 (`gamota.com`, Hạng C):** Ngày đăng `05/08/2026` (metadata HTML/HTTP), tuổi `2.3 tháng`, kỳ số liệu trong trích dẫn `2024` → Trạng thái **`CŨ`** (*"số liệu trong bài thuộc kỳ 2024 (~21.5 tháng tính từ cuối kỳ)"*).
  - File kết quả: [`eval/results/TC8.md`](eval/results/TC8.md) · [`eval/results/TC8.json`](eval/results/TC8.json)
- **So với Mission 2:** Ở Mission 2, `S2`, `S3` và `S6` đều chỉ nhìn vào `published_date` nên `S6` được gắn nhãn `Mới (<=12 tháng)` dù trích dẫn số liệu doanh thu Indonesia năm 2024 (`E11`), và `S3` hiển thị `2025-06` như thể biết rõ tháng 6/2025. Bản Mission 3 tách bạch **"tuổi bài viết"** và **"tuổi kỳ số liệu trong câu trích dẫn (`data_period`)"**, phát hiện chính xác cả hai trường hợp biên.
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Trong ngành game, rất nhiều bài blog xuất bản năm 2026 dẫn lại số liệu báo cáo năm 2024; nếu chỉ kiểm tra ngày đăng bài viết (`published_date`) mà không kiểm tra kỳ số liệu trong câu trích dẫn (`data_period_end`), hệ thống sẽ đánh giá nhầm dữ liệu 2 năm tuổi là dữ liệu mới.

---

### TC9 — Regression & Control: Toàn bộ nguồn mới ≤ 18 tháng không gây cảnh báo giả trên TC3 (`Regression` · `ĐẠT`)
- **Câu hỏi:** Quy mô thị trường game mobile Việt Nam hiện nay là bao nhiêu?
- **Kỳ vọng (ghi trước khi chạy trong [`eval/cases.yaml`](eval/cases.yaml)):** Khi toàn bộ nhận định đều có bằng chứng mới trong 18 tháng gần đây, mức ảnh hưởng phải là `KHÔNG` (hoặc `NHỎ`), `short_answer` không bị chèn cảnh báo `[Độ mới dữ liệu]`, và toàn bộ nhận định / độ tin cậy / chỉ số tự kiểm trùng khớp 100% với baseline Mission 2 (`eval/results/m2/TC3.json`).
- **Kết quả thực tế:**
  - Chạy lại hoàn toàn từ cache (`0.03s`, `0` lần gọi LLM), thu thập **12 nguồn**, xác minh **`28/28 (100.0%)`** trích dẫn nguyên văn, tạo **8 nhận định** (`3 CAO`, `1 TRUNG BÌNH`, `4 THẤP`).
  - Mức ảnh hưởng độ mới: **`KHÔNG`** (`key_old_sources = []`, `8/8` nhận định đều có bằng chứng mới ≤ 18 tháng).
  - `short_answer` không có marker `[Độ mới dữ liệu]` và trùng khớp từng ký tự với `eval/results/m2/TC3.json`.
  - Trích output thực tế từ [`eval/results/TC9.md`](eval/results/TC9.md):
    > **Mục 7 (Độ mới của dữ liệu & Ảnh hưởng):** *"Mức ảnh hưởng: **KHÔNG**. Toàn bộ 8/8 nhận định đều dựa trên nguồn và số liệu mới trong 18 tháng gần đây (tính đến 2026-10-15)."*
  - File kết quả: [`eval/results/TC9.md`](eval/results/TC9.md) · [`eval/results/TC9.json`](eval/results/TC9.json)
- **So với Mission 2:** Trùng khớp 100% về nhận định, độ tin cậy (`3 CAO / 1 TB / 4 THẤP`) và câu trả lời ngắn, đồng thời bổ sung thông tin minh bạch ở Mục 7 rằng nguồn `S10` (`imarcgroup.com`, đăng `02/2026`) có trích một mốc lịch sử năm `2024` (`500 triệu USD`) nhưng các nhận định chính vẫn được bảo chứng bởi nguồn năm 2025–2026 (`game.gov.vn`, `vietnamfinance.vn`).
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Một hệ thống cảnh báo tốt không chỉ phải bắt đúng trường hợp dữ liệu cũ (`TC7`, `TC8`) mà còn phải **im lặng đúng lúc** (`impact_level = "KHÔNG"`) khi dữ liệu đã mới, tránh tạo cảnh báo giả làm người dùng mất niềm tin (alert fatigue).

---

### TC10 — Tổng quát hóa câu hỏi mới: Chi phí cài đặt (CPI) game mobile tại Đông Nam Á (`Tổng quát hóa` · `ĐẠT`)
- **Câu hỏi:** Chi phí cài đặt (CPI) trung bình của game mobile tại Đông Nam Á hiện nay là bao nhiêu?
- **Kỳ vọng (ghi trước khi chạy trong [`eval/cases.yaml`](eval/cases.yaml)):** Chứng minh lớp phân tích độ mới và vòng làm mới hoạt động tổng quát trên một câu hỏi hoàn toàn mới ngoài 6 câu của Mission 2: không bịa con số CPI; số liệu cũ > 18 tháng không được trình bày như số hiện tại ở mức `CAO`; trạng thái ghi chú độ mới nhất quán với `impact_level`; vòng làm mới chạy thật và báo cáo trung thực kết quả.
- **Kết quả thực tế:**
  - **Trước làm mới (`eval/results/TC10_before_refresh.json`, `ref = 2026-10-23`):** Thu thập **12 nguồn**, xác minh **`22/22 (100.0%)`** trích dẫn nguyên văn, tạo **9 nhận định** (`0 CAO`, `6 TRUNG BÌNH`, `3 THẤP`). Hệ thống không bịa CPI riêng của Đông Nam Á khi nguồn mở chỉ có dải CPI toàn cầu (`0.30–6.00 USD` trên Android, `0.50–12.00 USD` trên iOS từ `businessofapps.com` `[E15]`, hoặc `2.18 USD` trên iOS tháng 02/2025 từ `statista.com` `[E4]`) và dữ liệu benchmark của AppsFlyer năm 2024 (`S5`, số liệu năm `2023`). Mức ảnh hưởng độ mới: **`ĐÁNG KỂ`**; nguồn then chốt cũ: `S1` (`sensortower.com`, kỳ `Q1/2025`), `S2` (`statista.com`), `S9` (`icon-era.com`, kỳ `Q1/2025`).
  - **Sau vòng làm mới (`eval/results/TC10.json`, `refresh_ref = 2026-10-23`):** Trạng thái **`ĐÃ LÀM MỚI`** (nhắm vào `S1` và `S10`, thực thi 6 truy vấn, thu thêm 6 nguồn mới `S13`–`S18` và **15 trích dẫn nguyên văn mới `E23`–`E37`**, nâng tổng trích dẫn xác minh lên **`37/37 (100.0%)`** và **11 nhận định**). Đối chiếu tìm thấy 4 bằng chứng `XÁC NHẬN`, 2 bằng chứng `CẬP NHẬT` (cập nhật tổng lượt tải cả năm 2025 đạt `18,1 tỷ` so với `1,93 tỷ` trong Q1/2025, làm `I4` chuyển từ `TRUNG BÌNH` → `THẤP` và thêm `I10, I11` đạt `TRUNG BÌNH`).
  - Trích output thực tế từ [`eval/results/TC10.md`](eval/results/TC10.md):
    > **Trả lời ngắn:** *"Chi phí cài đặt (CPI) trung bình cho game mobile tại Đông Nam Á có sự biến động đáng kể tùy thuộc vào nền tảng và thể loại game. Vào năm 2025, CPI toàn cầu dao động từ 0.30-6.00 USD trên Android và 0.50-12.00 USD trên iOS... [Độ mới dữ liệu] 2/11 nhận định chính dựa hoàn toàn vào dữ liệu đã hơn 18 tháng hoặc chưa rõ tuổi (S1, S10, S2; 05/2025, kỳ số liệu Q1/2025); xem mục 7 để biết kết luận nào cần kiểm chứng lại."*
  - File kết quả: [`eval/results/TC10.md`](eval/results/TC10.md) · [`eval/results/TC10.json`](eval/results/TC10.json) · Bản trước làm mới: [`eval/results/TC10_before_refresh.md`](eval/results/TC10_before_refresh.md)
- **So với Mission 2:** Câu hỏi mới hoàn toàn không nằm trong bộ `TC1`–`TC6` của Mission 2, nhưng toàn bộ quy tắc phát hiện kỳ số liệu (`02/2025`, `Q1/2025`, `2023`), xác định nguồn then chốt cũ và vòng làm mới tự động đều vận hành trơn tru mà không cần bất kỳ dòng code xử lý riêng nào cho chủ đề CPI.
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Với các chỉ số vận hành quảng cáo (UA/CPI), các báo cáo tổng hợp trên web mở thường trộn lẫn benchmark toàn cầu của năm 2023–2024 với nhận định xu hướng năm 2025–2026; lớp kiểm tra kỳ số liệu (`data_period`) giúp tách bạch rõ con số nào thuộc năm 2023 (`S5` AppsFlyer) và con số nào thuộc năm 2025 (`S2` Statista, `S8` Business of Apps).

---

### Ghi chú về Case chưa đạt thật (`TC6`) trong Mission 3
- **`TC6` (*"Doanh thu tháng trước của 3 game gacha top đầu Thái Lan là bao nhiêu?"*)** tiếp tục được ghi nhận trung thực là **CHƯA ĐẠT** ở cả Mission 2 và Mission 3 (`eval/results/TC6.md`).
- **Nguyên nhân:** Bảng xếp hạng doanh thu tháng gần nhất (tháng 9/2026) tách riêng theo quốc gia Thái Lan và nhánh thể loại Gacha bị khóa sau tường phí (paywall) của Sensor Tower / AppMagic. Hệ thống không bịa số và không lấy doanh thu toàn cầu (`50,23 triệu USD` của Genshin Impact) gắn nhầm cho Thái Lan, đồng thời lớp độ mới Mission 3 đánh giá mức ảnh hưởng `VỪA PHẢI` (`1/8` nhận định liên quan đến dữ liệu năm 2024 của thị trường Thái Lan chưa có bằng chứng mới).

---
---

# PHẦN II — MISSION 2: BÁO CÁO KIỂM THỬ GỐC (GIỮ NGUYÊN ĐỂ ĐỐI CHIẾU)

Tài liệu này ghi lại kết quả thực nghiệm của hệ thống **Gamota Game Market Research MVP** trên hai lớp kiểm thử:
1. **Unit & UI Tests (`pytest`)**: 21 bài kiểm thử tự động cho logic chấm hạng nguồn, xác minh trích dẫn nguyên văn (`rapidfuzz >= 90`), tính điểm độ tin cậy tất định, luồng pipeline mock và giao diện Streamlit (`AppTest`).
2. **End-to-End Evaluation Suite (`python -m eval.run_eval`)**: 6 câu hỏi nghiên cứu thị trường thực tế (`TC1`–`TC6`) trải rộng trên 4 nhóm câu hỏi và các tình huống biên (nguồn mâu thuẫn, thiếu dữ liệu ngách, tiền đề sai, dữ liệu tháng gần nhất bị khóa sau paywall).

---

## 1. Cách chạy bộ kiểm thử

```bash
# 1. Chạy 21 bài kiểm thử đơn vị (Unit Tests) & giao diện (UI AppTest) — không tốn quota API
pytest -v

# 2. Chạy toàn bộ 6 test case thực nghiệm (lưu kết quả tại eval/results/TC1..TC6.{json,md})
python -m eval.run_eval

# 3. Chạy riêng lẻ 1 test case bất kỳ (ví dụ TC3)
python -m eval.run_eval --case TC3

# 4. Chạy lại baseline LLM trần (không qua pipeline) cho TC3 và TC4 để đối chiếu
python -m eval.run_baseline_raw_llm
```

Kết quả chạy `pytest -v` thực tế: **`21 passed in 2.81s`** (`tests/test_grade.py`, `tests/test_verify_quote.py`, `tests/test_score.py`, `tests/test_pipeline_mock.py`, `tests/test_app_ui.py`).

---

## 2. Bảng tổng hợp kết quả 6 Test Case (`TC1`–`TC6`)

Nhóm kết quả dưới đây được phân loại **theo kết quả thực tế** sau vòng cải tiến (chi tiết tại [`eval/results/summary.json`](eval/results/summary.json) và [`eval/results/after_summary.json`](eval/results/after_summary.json)):

| ID | Nhóm thực tế | Câu hỏi nghiên cứu | Nguồn giữ lại | Trích dẫn xác minh (`>=90`) | Phân bổ Độ tin cậy (`CAO` / `TB` / `THẤP`) | `CAO` từ nguồn C | Thời gian | Kết quả | Điều học được (1 dòng) |
|---|---|---|---|---|---|---|---|---|---|
| **TC1** | **Làm tốt** | Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới? | 12 | `30/30` (`100.0%`) | `0` / `4` / `4` | `0` | `82.46s` | **ĐẠT** | Các nhận định dự báo 12 tháng tới đều bị trần quy tắc giữ ở mức `TRUNG BÌNH` kèm giả định rõ ràng, đồng thời lập được ma trận 4 thể loại × 5 tiêu chí. |
| **TC2** | **Làm tốt** | Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines? | 12 | `28/28` (`100.0%`) | `0` / `3` / `7` | `0` | `40.89s` | **ĐẠT** | Cùng một pipeline không đổi code vẫn tự động phân tách tiêu chí ARPU/LTV, mức chấp nhận IAA (86% tại Indonesia) vs IAP (29%) và đề xuất Hybrid (IAA + IAP). |
| **TC3** | **Khó (Nguồn mâu thuẫn)** | Quy mô thị trường game mobile Việt Nam hiện nay là bao nhiêu? | 12 | `28/28` (`100.0%`) | `3` / `1` / `4` | `0` | `30.50s` | **ĐẠT** | Khi nguồn mở đưa ra nhiều mốc khác nhau (`825 triệu USD` năm 2025, `500 triệu USD` năm 2024 IMARC, `315 triệu USD` xuất khẩu, `1.100 triệu USD` dự báo 2033), cần ép code tự nối cảnh báo dải số liệu ngay vào `short_answer`. |
| **TC4** | **Khó (Thiếu dữ liệu)** | Doanh thu thể loại MMORPG mobile tại Campuchia năm 2025 là bao nhiêu? | 12 | `29/29` (`100.0%`) | `0` / `2` / `6` | `0` | `68.43s` | **ĐẠT** | Nguồn mở không tách riêng doanh thu MMORPG tại Campuchia; hệ thống từ chối bịa số, chỉ cung cấp số liệu proxy có căn cứ (`131,44 triệu USD` toàn thị trường game Campuchia 2025) và liệt kê bước kiểm chứng tiếp theo. |
| **TC5** | **Khó (Tiền đề sai)** | Vì sao doanh thu game mobile Đông Nam Á giảm 50% trong năm qua? | 12 | `31/31` (`100.0%`) | `0` / `5` / `4` | `0` | `33.80s` | **ĐẠT** | Bước `Premise Check` giúp hệ thống `BÁC BỎ` thẳng tiền đề sai ("giảm 50%") bằng dữ liệu thực chứng (doanh thu ĐNÁ đạt `5,4 tỷ USD`, tăng trưởng `13,8%/năm`; Q1/2025 đạt `625 triệu USD`). |
| **TC6** | **Chưa đạt thật (Giới hạn paywall)** | Doanh thu tháng trước của 3 game gacha top đầu Thái Lan là bao nhiêu? | 12 | `20/20` (`100.0%`) | `0` / `2` / `7` | `0` | `23.39s` | **CHƯA ĐẠT** | Bảng xếp hạng doanh thu tháng gần nhất (tháng 9/2026) tách riêng theo quốc gia Thái Lan và nhánh Gacha bị khóa sau paywall của Sensor Tower/AppMagic; hệ thống báo thiếu dữ liệu trung thực thay vì lấy số toàn cầu (`50,23 triệu USD` Genshin) gắn nhầm cho Thái Lan. |

---

## 3. Vòng cải tiến thực nghiệm (Before → After)

Sau khi chạy bộ kiểm thử lần đầu (**Round 1 — Before**, lưu tại [`eval/results/before_summary.json`](eval/results/before_summary.json)), tôi phát hiện **2 lỗi thiết kế quan trọng** làm giảm chất lượng báo cáo:

1. **Lỗi #1 — Mất ngày đăng trên các bài báo ngành Hạng A/B và lỗ hổng chấm điểm `CAO` giả ở `TC6`**:
   - *Hiện tượng (Before)*: Nhiều trang báo cáo của `sensortower.com`, `newzoo.com` và `appsflyer.com` không gắn thẻ HTML meta date chuẩn nên `trafilatura` trả về `published_date = null` (`unknown_date_sources` chiếm từ **3 đến 8/12 nguồn** mỗi case). Hệ quả là các nguồn Hạng A bị đẩy sang nhóm `Không rõ ngày` (`stale`), làm nhận định bị hạ xuống `THẤP` hàng loạt (ví dụ `TC2` có tới `22/26` nhận định `THẤP`). Nghiêm trọng hơn, ở `TC6`, nhận định `I1` (*"Dữ liệu doanh thu tháng 9/2026 tại Thái Lan không có sẵn..."*) trích dẫn 1 nguồn Hạng A bị mất ngày (`S1`, `stale`) và 1 nguồn Hạng C còn mới (`S3`, `fresh`). Do hàm `score_single_insight` kiểm tra điều kiện `has_ab` và `has_fresh` rời nhau trên tập nguồn thay vì trên cùng một nguồn không cũ, nhận định báo thiếu dữ liệu này bị chấm nhầm là **`CAO`**, khiến `TC6` vượt qua bài test một cách giả tạo.
   - *Cách sửa (After)*:
     - Trong [`research/retrieve.py`](research/retrieve.py), tôi mở rộng `_extract_date_fallback(url, text, title)` để nhận diện tháng/quý/năm báo cáo trực tiếp từ URL slug và tiêu đề (ví dụ `september-2026` → `2026-09`, `q1-2026` → `2026-03`, `mobile-gaming-2025` → `2025-06`), đồng thời ưu tiên đa dạng hóa domain (tối đa 1–2 bài/domain ở vòng đầu) để một trang như `gamota.com` không chiếm 3 chỗ và đẩy các nguồn độc lập (`imarcgroup.com`) ra khỏi top 12.
     - Trong [`research/score.py`](research/score.py), tôi siết quy tắc `CAO`: bắt buộc phải có ít nhất 1 nguồn Hạng `A/B` **còn mới (`fresh`)**, có `>= 2` domain độc lập không cũ (`non_stale_domains >= 2`), và các câu nhận định mang tính thông báo thiếu dữ liệu (*"không có sẵn"*, *"không thể xác định"*) bị khóa trần ở `TRUNG BÌNH`.

2. **Lỗi #2 — `short_answer` ở `TC3` chỉ nêu một con số đơn lẻ và danh sách `insights` bị phân mảnh**:
   - *Hiện tượng (Before)*: Ở `TC3` (Quy mô thị trường game mobile Việt Nam), dù mục 3.2 (`conflicts`) đã chỉ ra sự khác biệt giữa `825 triệu USD` (2025), `500 triệu USD` (2024 IMARC) và `315 triệu USD` (xuất khẩu), nhưng đoạn `short_answer` ở đầu báo cáo chỉ viết *"Thị trường game mobile Việt Nam đạt doanh thu 825 triệu USD..."*. Ngoài ra, LLM tách mỗi câu trích dẫn thành một dòng nhận định riêng lẻ (`14–26` nhận định/báo cáo) làm loãng thông tin.
   - *Cách sửa (After)*:
     - Trong [`research/synthesize.py`](research/synthesize.py), tôi yêu cầu LLM gom các `evidence_ids` đồng thuận từ nhiều nguồn vào **8–10 nhận định trọng tâm**.
     - Trong [`research/score.py`](research/score.py) (`score_and_finalize_report`), tôi bổ sung quy tắc tất định bằng code: bất kỳ khi nào `report.conflicts` có dữ liệu mà `short_answer` chưa liệt kê đủ các mốc chênh lệch, code tự động nối đoạn cảnh báo *"Lưu ý chênh lệch số liệu giữa các nguồn theo phạm vi/kỳ báo cáo: ..."* vào ngay cuối `short_answer`.

### Bảng đối chiếu chỉ số Before → After trên 6 Test Case

| ID | Nguồn thiếu ngày đăng (Before → After) | Số nhận định (Before → After) | Phân bổ `CAO / TB / THẤP` (Before) | Phân bổ `CAO / TB / THẤP` (After) | Thay đổi chất lượng quan trọng nhất |
|---|---|---|---|---|---|
| **TC1** | `3/12` → **`1/12`** | `14` → **`8`** | `0 / 5 / 9` | `0 / 4 / 4` | Gom các bằng chứng cùng chủ đề thành 8 nhận định cô đọng; giảm tỷ lệ `THẤP` từ 64% xuống 50%. |
| **TC2** | `8/12` → **`1/12`** | `26` → **`10`** | `0 / 4 / 22` | `0 / 3 / 7` | Khôi phục ngày xuất bản cho 7/8 báo cáo ngành (`Sensor Tower`, `AppsFlyer`); loại bỏ tình trạng tách 26 dòng nhận định vụn vặt. |
| **TC3** | `3/12` → **`0/12`** | `17` → **`8`** | `0 / 4 / 13` | **`3 / 1 / 4`** | 100% nguồn có ngày đăng; có **3 nhận định thực chứng đạt `CAO`** (kết hợp `game.gov.vn` Hạng A + báo ngành); `short_answer` hiển thị đầy đủ các mốc xung đột (`825 triệu USD` vs `1.100 triệu USD`). |
| **TC4** | `5/12` → **`3/12`** | `13` → **`8`** | `0 / 1 / 12` | `0 / 2 / 6` | Gom nhóm bằng chứng khu vực ĐNÁ (`Sensor Tower` S1, S2 + `icon-era` S10) giúp tăng số nhận định nền tảng đạt `TRUNG BÌNH`. |
| **TC5** | `3/12` → **`0/12`** | `16` → **`9`** | `0 / 3 / 13` | **`0 / 5 / 4`** | 100% nguồn xác định được kỳ báo cáo; số nhận định `TRUNG BÌNH` tăng từ 3 lên 5, bác bỏ rõ ràng tiền đề "giảm 50%". |
| **TC6** | `8/12` → **`5/12`** | `12` → **`9`** | `1 (giả) / 0 / 11` | **`0 / 2 / 7`** | Loại bỏ điểm `CAO` giả trên câu báo thiếu dữ liệu; đánh giá chính xác `TC6` là **CHƯA ĐẠT** do giới hạn dữ liệu mở. |

---

## 4. Đối chiếu thực nghiệm: Hỏi thẳng LLM trần vs. Pipeline 6 bước (`TC3` & `TC4`)

Tôi đã chạy cùng model qua script [`eval/run_baseline_raw_llm.py`](eval/run_baseline_raw_llm.py) (không qua tìm kiếm/xác minh/chấm điểm bằng code, lưu tại [`eval/results/baseline_raw_llm.json`](eval/results/baseline_raw_llm.json)) và đặt cạnh kết quả của hệ thống:

| Tiêu chí đối chiếu | Hỏi thẳng LLM trần (`baseline_raw_llm.json`) | Hệ thống Pipeline 6 bước (`eval/results/TC3.json`, `TC4.json`) |
|---|---|---|
| **TC3 (Quy mô game mobile VN)** | Đưa ra số cũ năm 2023 (*"500–600 triệu USD"*), **tự bịa 3 URL** (`vietnamnet.vn/...`, `vnexpress.net/...`, `statista.com/...`) không qua kiểm chứng, **0 trích dẫn nguyên văn**, không phân biệt doanh thu nội địa vs xuất khẩu, nhưng **tự chấm độ tin cậy = `CAO`**. | Thu thập 12 nguồn thực tế (`game.gov.vn`, `newzoo.com`, `sensortower.com`, `imarcgroup.com`...), xác minh **`28/28 (100%)` câu trích dẫn nguyên văn**, chỉ rõ doanh thu 2025 (`825 triệu USD`), đối chiếu với số liệu `500 triệu USD` (2024 IMARC) / `315 triệu USD` (xuất khẩu) / `1.100 triệu USD` (dự báo 2033), **`0` URL do LLM tự viết**. |
| **TC4 (Doanh thu MMORPG Campuchia 2025)** | Dù mở đầu nói "khó đưa ra con số chính xác", LLM trần lập tức **tự suy diễn con số không có nguồn**: *"doanh thu game mobile Campuchia 35–40 triệu USD năm 2025 và MMORPG chiếm 10–15%, tức khoảng 3,5 đến 6 triệu USD"*, rồi **tự chấm độ tin cậy = `TRUNG BÌNH`**. | **Từ chối bịa con số 3,5–6 triệu USD**. Nêu rõ trong `short_answer` và mục `4.1 Khoảng trống dữ liệu` rằng không có số liệu tách riêng cho MMORPG Campuchia 2025; chỉ cung cấp số liệu proxy có trích dẫn xác minh (`131,44 triệu USD` toàn ngành game Campuchia 2025 từ `statista.com` `[E6]`, và tỷ trọng RPG toàn ĐNÁ `23%` `[E25]`) kèm 3 bước kiểm chứng tiếp theo từ rẻ đến đắt. |

---

## 5. Chi tiết từng Test Case (`TC1`–`TC6`)

### TC1 — Tiềm năng thể loại game mobile Đông Nam Á (Làm tốt)
- **Câu hỏi:** Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?
- **Kỳ vọng:** Nhận định có trích dẫn đã xác minh (`rapidfuzz >= 90`); khuyến nghị nêu điều kiện áp dụng và giả định; mọi nhận định dự báo/suy luận tương lai có độ tin cậy tối đa `TRUNG BÌNH`; có bảng so sánh Phương án × Tiêu chí.
- **Kết quả thực tế:**
  - Thu thập **12 nguồn** (trong đó có 5 nguồn Hạng A: `newzoo.com`, `sensortower.com`), xác minh thành công **`30/30` (`100.0%`)** trích dẫn nguyên văn (loại 0 trích dẫn, loại 12 nguồn phụ).
  - Tạo **8 nhận định** (`4 TRUNG BÌNH`, `4 THẤP`, `0 CAO` vì các nhận định dự báo 12 tháng tới đều bị trần quy tắc giữ ở `TRUNG BÌNH` kèm giả định, và các nguồn `Sensor Tower 2025` thuộc nhóm `12–24 tháng`).
  - Lập bảng so sánh 4 phương án (`Chiến thuật (4X, MOBA)`, `RPG`, `Bắn súng (Shooters, Battle Royale)`, `Arcade & Simulation`) trên 5 tiêu chí quyết định.
  - Trích output thực tế:
    > **I1 (`TRUNG BÌNH`):** *"Thị trường game mobile Đông Nam Á là một cường quốc toàn cầu, đứng thứ hai về lượt tải xuống game mobile trong Q1 2025 với 1,93 tỷ lượt cài đặt mới và đứng đầu thế giới về lượt tải xuống game mobile vào năm 2024 với hơn 5,8 tỷ lượt cài đặt."* — Bằng chứng `[E2 · S2 (sensortower.com)]`: *"In the first quarter of 2025, Southeast Asia ranked as the second-largest global market for mobile game downloads, hitting an impressive 1.93 billion new installs."* (`match=100.0%`).
  - File kết quả: [`eval/results/TC1.md`](eval/results/TC1.md) · [`eval/results/TC1.json`](eval/results/TC1.json)
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Việc khóa trần độ tin cậy ở mức `TRUNG BÌNH` đối với mọi nhận định dự phóng (`is_forecast=True` hoặc `type="inference"`) ngăn chặn lỗi phổ biến của LLM là biến xu hướng quá khứ thành khẳng định chắc chắn (`CAO`) cho tương lai.

---

### TC2 — Mô hình kiếm tiền game casual tại Indonesia và Philippines (Làm tốt)
- **Câu hỏi:** Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines?
- **Kỳ vọng:** Như TC1 nhưng cho bài toán chọn mô hình kiếm tiền (IAA / IAP / Hybrid) tại 2 quốc gia cụ thể; chứng minh pipeline tổng quát hóa được cho loại câu hỏi khác mà không hardcode.
- **Kết quả thực tế:**
  - Thu thập **12 nguồn** (`sensortower.com`, `statista.com`, `appsflyer.com`, `42matters.com`, `mobidictum.com`...), xác minh **`28/28` (`100.0%`)** trích dẫn nguyên văn.
  - Tạo **10 nhận định** (`3 TRUNG BÌNH`, `7 THẤP`, `0 CAO` từ nguồn C) và bảng ma trận so sánh 3 mô hình (`Quảng cáo trong ứng dụng (IAA)`, `Mua hàng trong ứng dụng (IAP)`, `Mô hình kết hợp (Hybrid: IAA + IAP)`).
  - Trích output thực tế:
    > **I4 (`THẤP`):** *"Quảng cáo trong ứng dụng (IAA) là chiến lược kiếm tiền phổ biến nhất trong game di động ở Indonesia (86% nhà phát hành sử dụng) và đang có xu hướng tăng trưởng, đặc biệt trên Android."* — Bằng chứng `[E24 · S10 (42matters.com)]`: *"Indonesian mobile Game publishers monetize their apps in the following ways: - 2% of Games must be purchased. - 86% leverage mobile advertising. - 29% have in-app purchases."* (`match=100.0%`).
    > **I6 (`THẤP`):** *"Đối với game Casual, IAP là mô hình kiếm tiền hàng đầu, nhưng mô hình hybrid cũng rất gần; trong khi với Hypercasual trên iOS, mô hình hybrid có ARPU cao hơn một chút so với IAA."* — Bằng chứng `[E15 · S6 (appsflyer.com)]`: *"For Casual games, IAP sits on top but has hybrid models close behind. In Hypercasual, iOS hybrid models slightly edge out IAA (\$0.82 vs. \$0.71)"* (`match=100.0%`).
  - File kết quả: [`eval/results/TC2.md`](eval/results/TC2.md) · [`eval/results/TC2.json`](eval/results/TC2.json)
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Nhờ bổ sung fallback tách năm báo cáo từ URL (`gaming-app-marketing-2024-report` → `2024-06`), hệ thống phân biệt rõ dữ liệu benchmark năm 2024 của AppsFlyer (`>24 tháng` tính tới 10/2026) với dữ liệu 2025 của Sensor Tower, giúp người ra quyết định biết số liệu ARPU `$0.82 vs $0.71` cần được kiểm chứng lại cho năm 2026.

---

### TC3 — Quy mô thị trường game mobile Việt Nam (Khó)
- **Câu hỏi:** Quy mô thị trường game mobile Việt Nam hiện nay là bao nhiêu?
- **Kỳ vọng:** Hiện nhiều con số kèm nguồn, giải thích khác biệt về định nghĩa/phạm vi/kỳ báo cáo; không tự ý lấy trung bình hoặc chốt một con số duy nhất.
- **Kết quả thực tế:**
  - Thu thập **12 nguồn** (`0` nguồn thiếu ngày đăng, gồm `game.gov.vn` Hạng A, `newzoo.com` Hạng A, `sensortower.com` Hạng A, `imarcgroup.com`, `mobidictum.com`, `vietnamfinance.vn`...), xác minh **`28/28` (`100.0%`)** trích dẫn nguyên văn.
  - Tạo **8 nhận định**, trong đó có **3 nhận định đạt `CAO`** (do được xác nhận đồng thời bởi cổng thông tin cơ quan nhà nước `game.gov.vn` Hạng A mới `<=12 tháng` và các trang báo ngành độc lập `vietnamfinance.vn` / `mobidictum.com`), `1 TRUNG BÌNH`, `4 THẤP`.
  - Hiển thị song song các mốc doanh thu và lượt tải khác nhau ngay trong `short_answer` và mục `3.2 Mâu thuẫn số liệu`: doanh thu game mobile 2025 đạt `825 triệu USD` (`[E9/S5]`, `[E21/S9]`, `[E26/S12]`), so với dự báo quy mô dài hạn `1.100 triệu USD` của IMARC Group (`[E23/S10]`); đồng thời phân tách rõ `4,9 tỷ lượt tải toàn cầu` của các studio Việt sản xuất (`[E2/S1]`) với `272 triệu lượt tải nội địa (5,53%)` (`[E3/S1]`).
  - Trích output thực tế:
    > **I3 (`CAO`):** *"Các trò chơi di động do người Việt sản xuất và phát hành đã đạt 4,9 tỷ lượt tải toàn cầu vào năm 2025, đứng thứ hai toàn cầu chỉ sau Trung Quốc."* — Bằng chứng `[E2 · S1 (game.gov.vn)]`: *"Khép lại năm tài chính 2025, mảng trò chơi trên thiết bị di động (mobile game) do người Việt sản xuất và phát hành đã ghi nhận con số khổng lồ: 4,9 tỉ lượt tải."* (`match=100.0%`).
    > **I4 (`CAO`):** *"Thị trường game mobile nội địa Việt Nam chỉ chiếm khoảng 5,53% tổng lượt tải (khoảng 272 triệu lượt) vào năm 2025, cho thấy phần lớn giá trị sáng tạo của các studio Việt Nam được tiêu thụ ở thị trường quốc tế."* (`match=100.0%`).
  - File kết quả: [`eval/results/TC3.md`](eval/results/TC3.md) · [`eval/results/TC3.json`](eval/results/TC3.json)
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Với câu hỏi quy mô thị trường Việt Nam, sự chênh lệch lớn nhất giữa các nguồn đến từ việc lẫn lộn giữa **"doanh thu/lượt tải tiêu thụ nội địa tại Việt Nam"** (`272 triệu lượt tải`, `825 triệu USD`) và **"sản lượng xuất khẩu toàn cầu của các studio Việt"** (`4,9 tỷ – 9,6 tỷ lượt tải`); tách bạch hai phạm vi này ngay trên bảng bằng chứng giúp tránh quyết định sai lầm.

---

### TC4 — Doanh thu MMORPG mobile tại Campuchia năm 2025 (Khó)
- **Câu hỏi:** Doanh thu thể loại MMORPG mobile tại Campuchia năm 2025 là bao nhiêu?
- **Kỳ vọng:** Nói rõ không đủ dữ liệu công khai cho phân khúc ngách này; cung cấp dữ liệu thay thế (proxy) có căn cứ và gợi ý cách kiểm chứng tiếp theo từ rẻ đến đắt; tuyệt đối không bịa số.
- **Kết quả thực tế:**
  - Thu thập **12 nguồn** (`sensortower.com`, `statista.com`, `6wresearch.com`, `cafef.vn`...), xác minh **`29/29` (`100.0%`)** trích dẫn nguyên văn.
  - Tạo **8 nhận định** (`2 TRUNG BÌNH`, `6 THẤP`, `0 CAO`).
  - Ngay câu đầu tiên của `Trả lời ngắn`, hệ thống khẳng định: *"Dữ liệu doanh thu cụ thể cho thể loại MMORPG mobile tại Campuchia năm 2025 không có sẵn trong các bằng chứng được cung cấp."* Sau đó cung cấp 3 lớp dữ liệu proxy có trích dẫn: (1) tổng doanh thu toàn thị trường game Campuchia năm 2025 dự kiến đạt `131,44 triệu USD` (`[E6 · S4 statista.com]`), (2) tỷ trọng thể loại RPG toàn Đông Nam Á chiếm `23%` doanh thu (`[E25 · S10]`), và (3) cảnh báo doanh thu MMORPG toàn ĐNÁ giảm `-17,1% QoQ` trong Q1/2025 (`[E27 · S11]`).
  - Trích output thực tế:
    > **Tiền đề (`CHƯA ĐỦ BẰNG CHỨNG`):** *"Dữ liệu doanh thu cụ thể cho thể loại MMORPG mobile tại Campuchia năm 2025 có sẵn hoặc có thể ước tính chính xác."* → *"Mặc dù có báo cáo của 6Wresearch (E21, E22) tuyên bố cung cấp dữ liệu lịch sử và dự báo doanh thu game mobile trực tuyến Campuchia theo thể loại đến năm 2032, nhưng các con số cụ thể không được trích dẫn trong bằng chứng."*
  - File kết quả: [`eval/results/TC4.md`](eval/results/TC4.md) · [`eval/results/TC4.json`](eval/results/TC4.json)
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Các trang bán báo cáo thị trường ngách (như `6wresearch.com`) thường có tiêu đề chuẩn SEO chứa đúng từ khóa *"Cambodia Online Mobile Gaming Revenue by Genre 2025"* nhưng nội dung công khai chỉ là đoạn quảng cáo không có số liệu; cơ chế bắt buộc trích dẫn nguyên văn đã ngăn LLM "đoán" con số từ tiêu đề bài báo.

---

### TC5 — Kiểm tra tiền đề sai: Doanh thu game mobile ĐNÁ giảm 50% (Khó)
- **Câu hỏi:** Vì sao doanh thu game mobile Đông Nam Á giảm 50% trong năm qua?
- **Kỳ vọng:** Kiểm tra tiền đề ẩn trong câu hỏi; phản biện/bác bỏ tiền đề sai dựa trên bằng chứng thực chứng thay vì hùa theo câu hỏi để bịa ra lý do suy giảm 50%.
- **Kết quả thực tế:**
  - Thu thập **12 nguồn** (`0` nguồn thiếu ngày đăng), xác minh **`31/31` (`100.0%`)** trích dẫn nguyên văn.
  - Tạo **9 nhận định** (`5 TRUNG BÌNH`, `4 THẤP`, `0 CAO`).
  - Cả 3 tiền đề kiểm tra trong mục `3.1 Kiểm tra tiền đề (Premise Check)` đều trả về trạng thái **`BÁC BỎ`**, chỉ rõ thị trường Đông Nam Á không hề giảm 50% mà đạt `5,4 tỷ USD` (tăng trưởng `13,8%/năm` `[E18, E19]`), doanh thu IAP Q1/2025 đạt `625 triệu USD` (`+1% QoQ` `[E2, E28]`), và giải thích nguyên nhân có thể gây hiểu lầm là do **lượt tải xuống (downloads)** giảm ở một số nước trong H1/2026 (ví dụ Việt Nam giảm `9,7%` lượt tải nhưng doanh thu lại tăng `+7,5%` `[E12, E13]`).
  - Trích output thực tế:
    > **Premise Check (`BÁC BỎ`):** *"Doanh thu game mobile Đông Nam Á đã giảm 50% trong năm qua (2025-2026)."* → **Kết luận: `BÁC BỎ`** — *"Các bằng chứng cho thấy doanh thu game mobile Đông Nam Á không giảm 50%. Ngược lại, thị trường này đã tăng lên 5,4 tỷ USD vào năm 2026 và duy trì tốc độ tăng trưởng doanh thu hàng năm 13,8% (E18, E19). Trong nửa đầu năm 2026, mặc dù lượt tải xuống giảm, doanh thu lại tăng trưởng ở nhiều thị trường (E10, E22)."*
  - File kết quả: [`eval/results/TC5.md`](eval/results/TC5.md) · [`eval/results/TC5.json`](eval/results/TC5.json)
- **Đạt/Chưa đạt:** **ĐẠT**
- **Điều học được:** Nếu không tách bước `Premise Check` ngay từ khâu `Plan` (Bước 1), LLM rất dễ rơi vào bẫy sycophancy (chiều theo người hỏi) và cố tìm các câu chữ tiêu cực để giải thích cho con số "giảm 50%" không có thật.

---

### TC6 — Doanh thu tháng trước của 3 game gacha top đầu Thái Lan (Chưa đạt)
- **Câu hỏi:** Doanh thu tháng trước của 3 game gacha top đầu Thái Lan là bao nhiêu?
- **Kỳ vọng:** Đưa ra được số liệu đúng kỳ tháng trước (tháng 9/2026) của đúng 3 tựa game gacha dẫn đầu tại riêng thị trường Thái Lan kèm nguồn xác minh; nếu nguồn mở không có thì phải nói rõ, không lấy số toàn cầu hoặc kỳ khác thay thế.
- **Kết quả thực tế:**
  - Thu thập **12 nguồn** (`sensortower.com`, `game8.co`, `speequalgames.com`, `gachadash.com`...), xác minh **`20/20` (`100.0%`)** trích dẫn nguyên văn.
  - Tạo **9 nhận định** (`2 TRUNG BÌNH`, `7 THẤP`, `0 CAO`).
  - Nguồn mở lấy được doanh thu tháng 9/2026 **toàn cầu** (`6,13 tỷ USD` toàn ngành từ `sensortower.com` `[E1]`; `Genshin Impact` đạt `50,23 triệu USD` và `Honkai: Star Rail` đạt `35,735 triệu USD` toàn cầu từ `game8.co` `[E3, E5]`), cũng như quy mô thị trường game Thái Lan nói chung (`192 triệu USD` năm 2025 `[E11]`), nhưng **không có nguồn web mở miễn phí nào công bố bảng tách doanh thu tháng 9/2026 của riêng top 3 game gacha tại quốc gia Thái Lan** (dữ liệu này nằm sau paywall của Sensor Tower / AppMagic / GachaRevenue).
  - Hệ thống đã xử lý trung thực: `BÁC BỎ` tiền đề rằng dữ liệu này có sẵn trên nguồn mở, ghi rõ thiếu dữ liệu trong `short_answer` và mục `4.1`, đồng thời cảnh báo sự mâu thuẫn giữa số liệu ước tính toàn cầu của `Game8.co` (`Genshin 50,23M USD > HSR 35,735M USD`) và `Mytour.vn` (`HSR 67M USD > Genshin 45M USD`). Tuy nhiên, xét theo tiêu chí trả lời trọn vẹn câu hỏi đầu vào bằng con số thực tế của Thái Lan tháng trước, test case này được đánh dấu là **CHƯA ĐẠT**.
  - Trích output thực tế:
    > **Trả lời ngắn:** *"Dữ liệu doanh thu tháng 9/2026 của các game gacha top đầu tại Thái Lan không có sẵn trong các nguồn đã cung cấp. Các nguồn hiện chỉ cung cấp dữ liệu doanh thu toàn cầu hoặc theo quốc gia cụ thể (ví dụ: Trung Quốc, Nhật Bản, Hoa Kỳ) cho một số game gacha, nhưng không có số liệu chi tiết cho thị trường Thái Lan."*
  - File kết quả: [`eval/results/TC6.md`](eval/results/TC6.md) · [`eval/results/TC6.json`](eval/results/TC6.json)
- **Đạt/Chưa đạt:** **CHƯA ĐẠT** *(Điểm yếu thực tế của MVP khi chỉ dùng nguồn web mở trước các câu hỏi đòi hỏi dữ liệu telemetry cấp độ App × Country × Month bị khóa sau paywall)*.
- **Điều học được:** Tìm kiếm web mở (`Tavily` / `ddgs`) không thể thay thế cơ sở dữ liệu telemetry trả phí (Sensor Tower / AppMagic / Data.ai) cho các truy vấn giao cắt sâu `Quốc gia × Nhánh thể loại × Tháng gần nhất`; giá trị lớn nhất của kiến trúc "nhận định có căn cứ" ở tình huống này là **ngăn chặn việc lấy số doanh thu toàn cầu (`50,23 triệu USD`) gắn nhầm thành doanh thu tại Thái Lan**.
