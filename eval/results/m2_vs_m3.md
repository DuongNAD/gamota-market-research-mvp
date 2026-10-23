# So sánh Định lượng Mission 2 ↔ Mission 3 (Change Request A2)

> File này được sinh tự động bởi `python -m eval.compare_m2_m3` từ dữ liệu thực trong `eval/results/m2/` và `eval/results/`.

## Bảng A — Kiểm thử Hồi quy (Regression `TC1`–`TC6`: M2 so với M3)
| Case | Đạt/Chưa đạt (M2 → M3) | % Trích dẫn xác minh (M2 → M3) | CAO từ nguồn C (M2 → M3) | Số nhận định (M2 → M3) | Phân bổ CAO/TB/THẤP (M2 → M3) | Trùng từng nhận định & trả lời ngắn? |
|---|---|---|---|---|---|---|
| **TC1** | `ĐẠT` → **`ĐẠT`** | `100.0%` (30/30) → `92.6%` (25/27) | `0` → `0` | `8` → `10` | `0/4/4` → `0/6/4` | Khác nguồn phụ khi chạy lại (bản offline trùng 100%) |
| **TC2** | `ĐẠT` → **`ĐẠT`** | `100.0%` (28/28) → `100.0%` (28/28) | `0` → `0` | `10` → `10` | `0/3/7` → `0/3/7` | **Trùng 100%** |
| **TC3** | `ĐẠT` → **`ĐẠT`** | `100.0%` (28/28) → `100.0%` (28/28) | `0` → `0` | `8` → `8` | `3/1/4` → `3/1/4` | **Trùng 100%** |
| **TC4** | `ĐẠT` → **`ĐẠT`** | `100.0%` (29/29) → `100.0%` (29/29) | `0` → `0` | `8` → `8` | `0/2/6` → `0/2/6` | **Trùng 100%** |
| **TC5** | `ĐẠT` → **`ĐẠT`** | `100.0%` (31/31) → `100.0%` (31/31) | `0` → `0` | `9` → `9` | `0/5/4` → `0/5/4` | **Trùng 100%** |
| **TC6** | `CHƯA ĐẠT` → **`CHƯA ĐẠT`** | `100.0%` (20/20) → `100.0%` (20/20) | `0` → `0` | `9` → `8` | `0/2/7` → `0/2/6` | Khác nguồn phụ khi chạy lại (bản offline trùng 100%) |

## Bảng B — Phát hiện của Lớp Độ mới & Ảnh hưởng trên chính dữ liệu Mission 2 (`ref = 2026-10-15`, `0` lần gọi LLM)
| Case | Mức ảnh hưởng (A2) | Nguồn then chốt CŨ / KHÔNG CHẮC | Nhận định thiếu bằng chứng mới | Nguồn chỉ biết năm nhưng M2 hiện như tháng 6 | Nguồn mới đăng nhưng trích số liệu > 18 tháng | Nguồn có `date_conflict` | `short_answer` có nêu tuổi dữ liệu? (M2 → M3) |
|---|---|---|---|---|---|---|---|
| **TC1** | **`ĐÁNG KỂ`** | **3** (S2, S3, S12) | **4/8** (I1, I2, I3, I6) | **3** (S3, S7, S12) | **3** (S2, S6, S12) | 0 | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC2** | **`ĐÁNG KỂ`** | **5** (S1, S5, S2, S3, S6) | **8/10** (I1, I2, I3, I4, I5, I6, I9, I10) | **3** (S5, S6, S10) | **2** (S1, S3) | 0 | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC3** | **`KHÔNG`** | 0 | 0/8 | **1** (S1) | **1** (S10) | 0 | Không → Không (đúng quy tắc) |
| **TC4** | **`ĐÁNG KỂ`** | **6** (S1, S2, S5, S7, S10, S11) | **6/8** (I2, I3, I5, I6, I7, I8) | **3** (S1, S8, S9) | **2** (S2, S11) | **1** (S10) | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC5** | **`ĐÁNG KỂ`** | **1** (S1) | **3/9** (I5, I7, I9) | **3** (S2, S8, S9) | **3** (S1, S7, S12) | 0 | Không → **Có** (`[Độ mới dữ liệu]`) |
| **TC6** | **`VỪA PHẢI`** | 0 | **1/9** (I8) | **1** (S7) | 0 | 0 | Không → Không (đúng quy tắc) |
| **Tổng (TC1–TC6)** | **4 ĐÁNG KỂ · 1 VỪA PHẢI · 1 KHÔNG** | **15 lượt nguồn then chốt** | **22/52 nhận định** | **14/72 nguồn** (tổng nguồn chỉ biết năm/không rõ ngày: **24/72**) | **11 nguồn** | **1 nguồn** | **0/6 → 4/4 case ĐÁNG KỂ** |

## Bảng C — Kết quả Vòng làm mới dữ liệu có mục tiêu (`TC7`, `TC10`)
| Case | Ngày làm mới | Trạng thái | Nguồn mục tiêu | Truy vấn | Nguồn mới (Giữ / Loại) | Bằng chứng mới | Đối chiếu (XÁC NHẬN / CẬP NHẬT / MÂU THUẪN / KHÔNG TĐ / KHÔNG TÌM THẤY) | Cặp bị code hạ nhãn | Nhận định đổi mức (Trước → Sau làm mới) |
|---|---|---|---|---|---|---|---|---|---|
| **TC7** | `2026-10-23` | **`ĐÃ LÀM MỚI`** | `S1, S5` | `6` | `6` giữ (`S13, S14, S15, S16, S17, S18`) / `18` loại | `12` | 2 XN / 0 CN / 0 MT / 5 KTĐ / 0 KTT | **3** (E2→E29 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG); E12→E34 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG); E13→E31,E32,E40 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG)) | I5: THẤP → TRUNG BÌNH |
| **TC10** | `2026-10-23` | **`ĐÃ LÀM MỚI`** | `S1, S10` | `6` | `6` giữ (`S13, S14, S15, S16, S17, S18`) / `17` loại | `15` | 4 XN / 0 CN / 0 MT / 3 KTĐ / 0 KTT | **2** (E2→E23 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG); E16→E23 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG)) | Không đổi mức |

## Bảng D — Trước/sau đợt sửa chốt chặn đối chiếu (`TC7`, `TC10`)
| Case | Nhãn đối chiếu (Trước → Sau sửa) | Cặp bị code hạ nhãn | Số `ConflictItem` (Trước → Sau) | Số nhận định (Trước → Sau) | Thay đổi độ tin cậy (Trước → Sau sửa) |
|---|---|---|---|---|---|
| **TC7** | `2 XN / 3 CN / 0 MT / 2 KTĐ / 0 KTT` → **`2 XN / 0 CN / 0 MT / 5 KTĐ / 0 KTT`** | **3** (`E2→E29 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG); E12→E34 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG); E13→E31,E32,E40 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG)`) | `4` → **`1`** | `13` → **`10`** | `I2: TRUNG BÌNH → THẤP; I5: THẤP → TRUNG BÌNH; I11: — → TRUNG BÌNH; I12: — → THẤP; I13: — → TRUNG BÌNH` → **`I5: THẤP → TRUNG BÌNH`** |
| **TC10** | `4 XN / 2 CN / 0 MT / 1 KTĐ / 0 KTT` → **`4 XN / 0 CN / 0 MT / 3 KTĐ / 0 KTT`** | **2** (`E2→E23 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG); E16→E23 (CẬP NHẬT→KHÔNG TƯƠNG ĐƯƠNG)`) | `2` → **`0`** | `11` → **`9`** | `I4: TRUNG BÌNH → THẤP; I10: — → TRUNG BÌNH; I11: — → TRUNG BÌNH` → **`0 thay đổi (Không đổi mức)`** |
