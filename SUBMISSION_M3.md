# Hồ sơ Nộp bài — Gamota · Mission 3 (Change Request A2: Độ mới Dữ liệu & Ảnh hưởng Độ tin cậy)

> **Change Request được giao (A2):** *"Một nguồn quan trọng được phát hành cách đây hơn 18 tháng. Người dùng muốn biết điều đó ảnh hưởng thế nào tới độ tin cậy của kết quả."*

---

## 1. Đường dẫn sản phẩm & Mã nguồn

- **Hạn nộp:** `18:00 ngày 24/10/2026`
- **Link Source Code (GitHub Public — nhánh chính có Mission 3):** [https://github.com/DuongNAD/gamota-market-research-mvp](https://github.com/DuongNAD/gamota-market-research-mvp)
- **Link Bản đóng băng Mission 2 (Git Tag `mission2-final` để đối chiếu Trước/Sau):** [https://github.com/DuongNAD/gamota-market-research-mvp/tree/mission2-final](https://github.com/DuongNAD/gamota-market-research-mvp/tree/mission2-final)
- **Link Live Demo (Streamlit Community Cloud — giữ nguyên URL từ Mission 2):** [https://gamota-market-research-mvp.streamlit.app](https://gamota-market-research-mvp.streamlit.app) *(Chế độ mặc định **"Xem báo cáo mẫu đã chạy thật (TC1–TC7)"** mở dùng ngay không cần API key, đã có sẵn Tab **"3. Độ mới & Ảnh hưởng (A2)"** và nút mẫu **"TC7 · Làm mới nguồn cũ (A2)"**)*
- **Link Video Demo Mission 3 (4:22, giọng đọc AI trên ảnh chụp thật từ ứng dụng):** [https://youtu.be/rXCLtsMb9ug](https://youtu.be/rXCLtsMb9ug)

---

## 2. Trả lời 3 câu hỏi bắt buộc của Mission 3

*(Bản văn bản thuần không chứa ký tự Markdown để dán trực tiếp vào biểu mẫu nộp bài nằm tại [`SUBMISSION_M3_FORM.txt`](SUBMISSION_M3_FORM.txt)).*

### Câu 1: Khi nhận yêu cầu thay đổi/mở rộng, bạn đã ưu tiên làm gì và chủ động chưa làm gì? Vì sao?

(1) **Ưu tiên 1:** Xây dựng lớp phân tích độ mới và định lượng ảnh hưởng bằng code tất định ([`research/recency.py`](research/recency.py)). Vì Change Request A2 hỏi nguồn `> 18 tháng` ảnh hưởng thế nào tới độ tin cậy, người dùng cần biết rõ nhận định nào đứng vững hay mất căn cứ qua mô phỏng phản thực tế (*Nếu bỏ nguồn* / *Nếu nguồn còn mới `<= 12 tháng`*).
(2) **Ưu tiên 2:** Minh bạch hóa cách xác định ngày đăng (`date_precision`) và tách kỳ số liệu trong trích dẫn (`data_period` ở [`research/dates.py`](research/dates.py)). Kiểm tra `72` nguồn của 6 báo cáo Mission 2 (Bảng B, [`eval/results/m2_vs_m3.md`](eval/results/m2_vs_m3.md)) cho thấy `14/72` nguồn chỉ biết năm nhưng từng hiện như tháng 6 (như `S5, S6` `appsflyer.com` năm `2024` ở `TC2`), `11/72` nguồn mới đăng nhưng trích số liệu `> 18 tháng` (`S2` đăng `05/2025` trích `Q1/2025`, `S6` đăng `05/08/2026` trích năm `2024` ở `TC1`), và `1/72` nguồn mâu thuẫn ngày đăng với kỳ số liệu (`TC4-S10`).
(3) **Ưu tiên 3:** Thực hiện vòng làm mới có mục tiêu giữ nguyên bối cảnh ([`research/refresh.py`](research/refresh.py), nút `TC7` trên [`app.py`](app.py)), tìm nguồn mới cho tối đa 2 nguồn then chốt cũ nhất, đối chiếu bằng chứng cũ ↔ mới và đánh mã `S#`/`E#` nối tiếp.
(4) **Ưu tiên 4 (tự soát trước khi nộp):** Phát hiện LLM gắn nhãn `CẬP NHẬT` cho cặp lệch phạm vi (như ghép `5,3 tỷ USD` IAP mọi ứng dụng cả năm với `625 triệu USD` IAP game `Q1/2025` ở `TC7`), tôi viết chốt chặn bằng code ([`research/comparability.py`](research/comparability.py)) theo 4 quy tắc *Phạm vi – Thị trường – Đơn vị – Kỳ số liệu*, chỉ hạ nhãn xuống `KHÔNG TƯƠNG ĐƯƠNG` thay vì sửa prompt để giữ khả năng phát lại từ cache (`0` lệnh gọi LLM mới) vì LLM vẫn có thể sai.
(5) **Chủ động chưa làm:** Không đổi quy tắc chấm điểm Mission 2 (giữ hồi quy); không để LLM tự đoán mức ảnh hưởng; không tự sửa `published_date` khi mâu thuẫn ngày; gác lại đầu đọc CSV/PDF nội bộ (`TC6`) và khung chat tự do.

---

### Câu 2: Điểm khác biệt lớn nhất giữa bản mới và bản ở Mission 2 là gì? Bằng chứng nào từ kết quả kiểm thử cho thấy bản mới tốt hơn?

(1) **Khác biệt lớn nhất:** Độ tin cậy được tính lại theo tuổi dữ liệu bằng mô phỏng phản thực tế trên code, và vòng làm mới chỉ dùng số liệu mới khi code kiểm tra tương đương về phạm vi, thị trường, đơn vị và kỳ số liệu với số cũ, trong khi giữ nguyên quy tắc chấm điểm Mission 2.
(2) **Bảng B** ([`eval/results/m2_vs_m3.md`](eval/results/m2_vs_m3.md), chạy trên 6 báo cáo Mission 2 ở ngày `2026-10-15`, `0` lệnh gọi LLM): phát hiện `4/6` case (`TC1, TC2, TC4, TC5`) chịu ảnh hưởng `ĐÁNG KỂ`, `15` lượt nguồn then chốt cũ/không chắc, `22/52` nhận định (`42,3%`) thiếu bằng chứng mới trong 18 tháng; trả lời ngắn có ghi chú tuổi dữ liệu tăng từ `0/6` lên `4/4` case `ĐÁNG KỂ`, không cảnh báo giả ở `TC3, TC9` (`0/8` nhận định thiếu bằng chứng mới).
(3) **TC2 phản thực tế** ([`eval/results/TC2.md`](eval/results/TC2.md)): chỉ rõ `S5, S6` (`appsflyer.com`) chỉ biết năm `2024` (`22–34 tháng`); bỏ `S5` hoặc `S6` thì `I5, I6` rơi vào `MẤT CĂN CỨ`; nếu `S5` còn mới (`<= 12 tháng`) thì `I4` tăng từ `THẤP` lên `CAO`.
(4) **TC7 sau sửa** ([`eval/results/TC7.md`](eval/results/TC7.md), Bảng C & D): thu `6` nguồn mới (`S13–S18`), `12` trích dẫn mới (`E29–E40`), `40/40` trích dẫn khớp (`100.0%`). Có `2` cặp xác nhận: `E3→E35` bổ sung bằng chứng mới cho `I1` (giữ `TRUNG BÌNH`), `E11→E31,E34,E40` nâng `I5` từ `THẤP` lên `TRUNG BÌNH`. Code chặn `3` cặp từ `CẬP NHẬT` xuống `KHÔNG TƯƠNG ĐƯƠNG` (`E2→E29`, `E12→E34`, `E13→E31,E32,E40`), trong đó `5,3 tỷ USD` ở `E29` là IAP mọi ứng dụng cả năm nên không thay được `625 triệu USD` IAP game `Q1/2025` ở `E2`; `I2` không bị hạ oan (giữ `TRUNG BÌNH`), `ConflictItem` giảm `4 → 1`, nhận định `13 → 10`.
(5) **TC10 sau sửa** ([`eval/results/TC10.md`](eval/results/TC10.md), Bảng C & D): thu `6` nguồn mới, `15` trích dẫn mới (`37/37` khớp `100.0%`); code chặn `2` cặp (`E2→E23`, `E16→E23`) do ghép `18,1 tỷ` lượt tải mọi ứng dụng năm `2025` với `1,93 tỷ` lượt tải game `Q1/2025`; giữ `4` cặp xác nhận; không nhận định nào đổi mức (`I4` giữ `TRUNG BÌNH`), `ConflictItem` giảm `2 → 0`, nhận định `11 → 9`.
(6) **Hồi quy** (Bảng A, `pytest`): `TC2–TC5`, `TC9` trùng `100%` với Mission 2; `60/60` test pass (`21` test Mission 2 + `39` test item Mission 3).

---

### Câu 3: Nếu sản phẩm này được đưa vào sử dụng thật, rủi ro lớn nhất còn lại là gì và bạn sẽ xử lý theo thứ tự nào?

(1) **Rủi ro 1 — Độ chính xác ngày đăng và kỳ số liệu trên web mở:** Trên `72` nguồn của 6 báo cáo Mission 2 (Bảng B, [`eval/results/m2_vs_m3.md`](eval/results/m2_vs_m3.md)), có `24/72` nguồn (`33,3%`) chỉ biết năm hoặc không rõ ngày (`14/72` chỉ biết năm), `11/72` nguồn (`15,3%`) mới đăng nhưng trích số liệu `> 18 tháng`, và `1/72` nguồn (`TC4-S10`) mâu thuẫn ngày đăng với kỳ số liệu. Ở `TC7`, trang `S13` (`sensortower.com`) ghi `"May 2026"` ở dòng tác giả nhưng hệ thống chỉ tách được năm `2026` từ URL/tiêu đề nên chỉ biết năm.
(2) **Rủi ro 2 — Giới hạn của chốt chặn từ khóa:** Bộ kiểm tra tương đương ([`research/comparability.py`](research/comparability.py)) và hàm tách kỳ (`detect_data_period`) dựa trên từ khóa và regex, nên có thể bỏ sót khác biệt phạm vi tinh vi ngoài từ điển hoặc chặn nhầm một cập nhật hợp lệ ghi kỳ thời gian phi chuẩn.
(3) **Rủi ro 3 — Dữ liệu sau tường phí (`TC6`):** Doanh thu tháng `9/2026` của top 3 game gacha tại Thái Lan vẫn `CHƯA ĐẠT` vì nguồn web mở không có bảng số liệu cấp `Quốc gia × Thể loại × Tháng` của Sensor Tower hay AppMagic.
(4) **Thứ tự xử lý:**
- **Bước 1:** Thêm nguồn metadata ngày đăng (`published_date` của Tavily API, JSON-LD `datePublished`/`dateModified`, HTTP `Last-Modified`, dòng tác giả) rồi đối chiếu chéo thời điểm xuất hiện con số giữa các domain độc lập.
- **Bước 2:** Cho phép chuyên viên xác nhận hoặc chỉnh trực tiếp ngày đăng, kỳ số liệu và phạm vi ngay trên giao diện rồi lưu vào bộ nhớ đã duyệt.
- **Bước 3:** Bổ sung đầu đọc file CSV/PDF xuất từ tài khoản Sensor Tower, AppMagic của Gamota vào bước thu thập và làm mới.

---

## 3. Kịch bản Video Demo Mission 3 (Mục tiêu `4:30`, tối đa `4:45` — Tổng lời nói ~560 từ)

| Thời lượng | Màn hình cần quay | Lời nói (Voice-over gợi ý) |
|---|---|---|
| **`0:00 – 0:25`**<br>*(Change Request A2 & Bản Mission 2)* | Mở `eval/results/m2/TC2.md` (hoặc tag `mission2-final`): chỉ vào bảng nguồn Mục 5 (`S5, S6` hiện `2024-06`) và `Trả lời ngắn` ở Mục 1. | *"Chào hội đồng chấm thi Gamota. Ở Mission 3, em giải quyết Change Request A2: nguồn quan trọng phát hành hơn 18 tháng ảnh hưởng thế nào tới độ tin cậy kết quả. Nhìn lại báo cáo TC2 ở Mission 2: hai nguồn S5, S6 của AppsFlyer thực chất chỉ có năm 2024 nhưng bị hiển thị như tháng 6/2024, nguồn S1 đăng tháng 5/2025 trích số liệu Q1/2025 đã hơn 18 tháng, và Trả lời ngắn chưa nhắc tuổi dữ liệu."* |
| **`0:25 – 1:30`**<br>*(TC2 bản Mission 3: Banner, Trả lời ngắn, Tab 3 & Link tô sáng)* | Mở ứng dụng Streamlit, chọn **`TC2`**:<br>1. Chỉ vào Banner vàng (`ĐÁNG KỂ`) và ghi chú `[Độ mới dữ liệu]` trong `Trả lời ngắn`.<br>2. Mở **Tab `3. Độ mới & Ảnh hưởng (A2)`**: chỉ vào bảng 7.1 (`S5, S6` ghi `2024 (chỉ biết năm)`, tuổi `22–34 tháng`; `S1` kỳ số liệu `Q1/2025`).<br>3. Mở mục 7.2: chỉ bảng *"Nếu bỏ nguồn này"* / *"Nếu nguồn này còn mới"* và bấm 1 link trích dẫn tô sáng. | *"Trên bản Mission 3, ngay khi mở TC2, hệ thống hiện Banner cảnh báo mức ĐÁNG KỂ và ghi rõ trong Trả lời ngắn rằng 8/10 nhận định chưa có bằng chứng mới trong 18 tháng. Sang Tab 3, bảng 7.1 minh bạch cách xác định ngày đăng và kỳ số liệu: S5 và S6 chỉ biết năm 2024, còn S1 tuy đăng tháng 5/2025 nhưng trích số liệu Q1/2025. Ở mục 7.2, code chạy mô phỏng phản thực tế chỉ rõ: nếu bỏ S5 hoặc S6 thì nhận định I5, I6 mất căn cứ; nếu S5 còn mới trong 12 tháng thì I4 tăng từ THẤP lên CAO. Mọi trích dẫn đều có link mở bài gốc và tô sáng."* |
| **`1:30 – 2:30`**<br>*(TC7 vòng làm mới & Chốt chặn đối chiếu 6 cột)* | Bấm nút **`TC7 · Làm mới nguồn cũ (A2)`**, mở **Tab `3. Độ mới & Ảnh hưởng (A2)`**, cuộn tới mục **7.5**:<br>1. Chỉ tiêu đề khối (`phát lại từ cache`, 6 truy vấn, 6 nguồn mới `S13–S18`, bằng chứng `E29–E40`).<br>2. Dừng ở **bảng đối chiếu 6 cột**, chỉ vào cột `Nhãn LLM`, `Kết quả sau kiểm tra code`, và đọc dòng **`E2 ↔ E29`**.<br>3. Chỉ dòng `E11` (`XÁC NHẬN` → `I5` lên `TRUNG BÌNH`) và `I2` giữ `TRUNG BÌNH`. | *"Tại TC7, vòng làm mới tìm nguồn mới cho S1 và S5, giữ 6 nguồn S13 đến S18 và trích dẫn E29 đến E40 nối tiếp. Điểm quan trọng em phát hiện khi tự soát trước khi nộp là LLM dễ gắn nhầm nhãn CẬP NHẬT cho hai con số khác phạm vi. Vì vậy bảng đối chiếu có cột Nhãn LLM và Kết quả sau kiểm tra code. Ở dòng E2 đối chiếu E29: LLM gắn CẬP NHẬT vì thấy 5,3 tỷ USD so với 625 triệu USD, nhưng code hạ xuống KHÔNG TƯƠNG ĐƯƠNG vì E29 là IAP mọi ứng dụng cả năm và không rõ kỳ, không thể thay cho IAP riêng game Q1/2025 ở E2. Nhờ vậy I2 không bị hạ oan, còn E11 được xác nhận hợp lệ giúp I5 tăng từ THẤP lên TRUNG BÌNH."* |
| **`2:30 – 3:15`**<br>*(Trường hợp biên TC1, TC4, Ngày tham chiếu & Giả định)* | 1. Chọn **`TC1`** → Tab 3: chỉ `S3` (`2025 (chỉ biết năm)` → `KHÔNG CHẮC`) và `S6` (đăng `08/2026`, số liệu `2024` → `CŨ`).<br>2. Chọn **`TC4`** → Tab 3: chỉ `S10` (`ngày đăng có thể sai`).<br>3. Đổi radio sang **"Hôm nay"** và mở **"5. Thử giả định ngày đăng"**. | *"Về trường hợp biên: ở TC1, nguồn S6 đăng tháng 8/2026 nhưng trích số liệu năm 2024 nên vẫn bị gắn CŨ; ở TC4, nguồn S10 ghi ngày đăng Q1/2025 nhưng trích dẫn lại nhắc số liệu Q2/2026 nên bị gắn cờ ngày đăng có thể sai. Chuyên viên cũng có thể đổi ngày tham chiếu sang Hôm nay hoặc thử giả định ngày đăng của từng nguồn ngay trên giao diện."* |
| **`3:15 – 4:00`**<br>*(Kiểm thử: Pytest 60 passed & Bảng A, B, C, D)* | Mở `TESTING.md` và `eval/results/m2_vs_m3.md`: chỉ vào `60 passed` (`21` test Mission 2 + `39` test Mission 3) và 4 bảng **Bảng A, B, C, D**. | *"Về kiểm thử định lượng: toàn bộ 21 test Mission 2 và 39 test Mission 3 đạt 60/60 pass. Bảng A chứng minh TC2 đến TC5 trùng 100% với Mission 2. Bảng B chứng minh trên 6 báo cáo cũ với 0 lệnh gọi LLM, hệ thống phát hiện 22/52 nhận định thiếu bằng chứng mới. Bảng C và D chứng minh chốt chặn đối chiếu chặn đúng 3 cặp lệch phạm vi ở TC7 và 2 cặp ở TC10 mà không cần sửa prompt."* |
| **`4:00 – 4:30`**<br>*(Rủi ro còn lại & Thứ tự xử lý)* | Mở mục **Câu 3** trong `SUBMISSION_M3.md`. | *"Ba rủi ro còn lại là: 24/72 nguồn web mở chỉ biết năm hoặc thiếu ngày (như S13 ghi May 2026 ở dòng tác giả nhưng URL chỉ có năm), chốt chặn từ khóa có thể sót phạm vi tinh vi, và dữ liệu sau tường phí ở TC6. Thứ tự xử lý của em là: bổ sung metadata ngày từ Tavily, JSON-LD và dòng tác giả; cho chuyên viên duyệt ngày và phạm vi ngay trên UI; và thêm đầu đọc CSV/PDF từ Sensor Tower nội bộ. Em xin cảm ơn!"* |

---

## 4. Checklist công việc dành cho người nộp bài (Hạn nộp: `18:00 ngày 24/10/2026`)

- [ ] **1. Kiểm tra bản Live Demo trên Streamlit Cloud:**
  - Mở [https://gamota-market-research-mvp.streamlit.app](https://gamota-market-research-mvp.streamlit.app) bằng cửa sổ ẩn danh (Incognito).
  - Bấm **`TC7 · Làm mới nguồn cũ (A2)`** → mở Tab **`3. Độ mới & Ảnh hưởng (A2)`** → kiểm tra bảng đối chiếu 6 cột có dòng `E2 ↔ E29` hiện `KHÔNG TƯƠNG ĐƯƠNG` kèm lý do và `(LLM, đã bị code bác bỏ)`.
  - *(Nếu Streamlit Cloud chưa tự cập nhật sau 15 phút, đăng nhập [https://share.streamlit.io](https://share.streamlit.io) → bấm **Reboot app**).*
- [ ] **2. Quay Video Demo Mission 3 (`≤ 4:45`, mục tiêu `4:30`):**
  - Quay màn hình 1080p (phóng to trình duyệt 110–125%) theo đúng 6 phân đoạn ở Mục 3.
  - Tải video lên YouTube ở chế độ **Không công khai (Unlisted)**, mở thử bằng cửa sổ ẩn danh để chắc chắn xem được.
- [ ] **3. Gửi link video cho Agent thực hiện F5:**
  - Gửi link video cho Agent để điền vào `README.md`, `SUBMISSION_M3.md`, `SUBMISSION_M3_FORM.txt`, commit và push lên GitHub.
- [ ] **4. Điền Form nộp bài Mission 3 (Trước `18:00 ngày 24/10/2026`):**
  - Dán link GitHub repo, link Streamlit Live Demo, link Video Demo YouTube, và dán nguyên văn 3 câu trả lời từ file văn bản thuần [`SUBMISSION_M3_FORM.txt`](SUBMISSION_M3_FORM.txt) vào biểu mẫu nộp bài.
