# AGENTS.md: quy tắc luôn áp dụng (Gamota · Mission 2)

Đặc tả đầy đủ nằm ở `BRIEF.md`. Đọc toàn bộ trước khi bắt đầu, và đọc lại mục liên quan ở đầu mỗi phase. Nếu có mâu thuẫn, `BRIEF.md` thắng. Nếu còn mơ hồ, hỏi tôi thay vì đoán.

## Cách làm việc
- Làm đúng thứ tự P0 → P5 (BRIEF mục 6). Đầu mỗi phase: Implementation Plan + Task List. Cuối mỗi phase: cập nhật Walkthrough (đã làm, bằng chứng, việc còn lại, rủi ro).
- Tại CHECKPOINT 1, 2, 3: dừng hẳn, chờ tôi trả lời "OK" mới làm tiếp.
- Mục 2 của BRIEF còn ô `{{...}}` chưa điền → hỏi tôi trước khi bắt đầu.
- Hạn của bạn: 16:00 ngày 15/10/2026. Chậm hơn kế hoạch quá 1 giờ → báo tôi và đề xuất phần cắt theo BRIEF mục 5.
- Kiểm tra giao diện bằng trình duyệt tích hợp của Antigravity trước mỗi checkpoint có UI.
- Hỏi tôi trước: lần `git push` đầu tiên, xóa file, cài công cụ toàn cục. Việc cần tài khoản (GitHub, Streamlit Cloud, Gemini, Tavily): hướng dẫn tôi làm, không tự làm.
- Không sửa `BRIEF.md` và `AGENTS.md` trừ khi tôi yêu cầu.

## Không bao giờ vi phạm
1. Không bịa: kết quả test, số liệu, ảnh chụp đều phải từ lần chạy thật. Không hardcode đáp án cho câu hỏi mẫu.
2. Trong sản phẩm, LLM không tự viết URL; mọi nhận định trỏ tới `evidence_id` đã được code xác minh.
3. Không đưa key vào code, log, commit hay chat. Không đọc hay in nội dung `.env`; kiểm tra key chỉ bằng lệnh in có/không.
4. LLM chạy bên trong sản phẩm dùng free tier (mặc định Gemini Flash). Không dùng `gemini-4-argon` hay model trả phí trong code.
5. Trước mỗi `git push`: quét secrets trong repo và lịch sử git.
6. Không mở rộng ngoài R1–R5: không auth, không database, không framework multi-agent.
7. Không che giấu lỗi: case chưa đạt và hạn chế phải ghi rõ trong `TESTING.md` và README.
8. Mỗi quyết định hoặc thay đổi: ghi 1–2 dòng vào `DECISIONS.md`.

## Ngôn ngữ
Giao diện và tài liệu nộp: tiếng Việt có dấu. Code, tên biến, commit message: tiếng Anh.
