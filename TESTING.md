# Báo cáo Kiểm thử & Đánh giá Chất lượng (TESTING.md)

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
- **Điều học được:** Việc khóa trần độ tin cậy ở mức `TRUNG BÌNH` đối với mọi nhận định dự phóng (`is_forecast=True` hoặc `type="inference"`) ngăn chặn triệt để lỗi phổ biến của LLM là biến xu hướng quá khứ thành khẳng định chắc chắn (`CAO`) cho tương lai.

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
