# Gamota · Hệ thống Nghiên cứu Thị trường Game có Căn cứ (MVP)

> **Mô tả 1 câu:** Hệ thống AI nghiên cứu thị trường game biến thông tin phân tán trên Internet thành nhận định ra quyết định có trích dẫn nguyên văn được code xác minh (`rapidfuzz >= 90`), gắn hạng nguồn `A/B/C` và chấm độ tin cậy bằng quy tắc tất định minh bạch.

- **Link Demo Online (Streamlit Cloud):** *(Đang cập nhật sau khi kết nối Streamlit Cloud)*
- **Link Video Walkthrough (≤ 5 phút):** *(Đang cập nhật ở P4–P5)*

---

## Cách chạy nhanh (Local)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Điền GEMINI_API_KEY (và TAVILY_API_KEY tùy chọn) vào file .env
streamlit run app.py
```

- **Chạy qua CLI:** `python -m research.cli "Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?"`
- **Chạy Unit Tests:** `pytest -v`
- **Chạy Bộ Kiểm thử (Eval):** `python -m eval.run_eval`

*(Tài liệu đầy đủ 9 mục theo BRIEF mục 8 sẽ được hoàn thiện sau khi chạy toàn bộ bộ kiểm thử thực tế ở P3–P4).*
