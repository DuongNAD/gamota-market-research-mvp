# Báo cáo Kiểm thử Chất lượng (TESTING.md)

Tài liệu này ghi nhận kết quả chạy thực tế từ bộ kiểm thử `eval/cases.yaml` (`python -m eval.run_eval`) và quá trình cải tiến (before → after) trong Phase 3.

## 1. Kiểm thử đơn vị (Unit Tests — `pytest`)
- `tests/test_grade.py`: Kiểm thử phân hạng nguồn `A/B/C` theo `config/source_tiers.yaml` và độ mới (`<=12m`, `12-24m`, `>24m`).
- `tests/test_verify_quote.py`: Kiểm thử xác minh trích dẫn nguyên văn `<= 40` từ bằng `rapidfuzz.fuzz.partial_ratio >= 90` và tạo URL Text Fragment `#:~:text=...`.
- `tests/test_score.py`: Kiểm thử quy tắc chấm độ tin cậy `CAO / TRUNG BÌNH / THẤP`, đảm bảo `0` nhận định `CAO` từ nguồn `C` và lọc bỏ URL do LLM tự sinh.

## 2. Kết quả chạy bộ 6 Test Cases thực tế (`eval/run_eval.py`)
*(Kết quả chạy thật của TC1–TC6 sẽ được ghi tự động từ `eval/results/` trong Phase 3).*
