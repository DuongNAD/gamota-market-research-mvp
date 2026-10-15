# Bản Nộp Bài Hoàn Chỉnh (SUBMISSION.md) — Gamota · Bài test A · Mission 2

Tài liệu này tổng hợp sẵn toàn bộ nội dung để bạn **copy-paste trực tiếp vào Form nộp bài của Gamota** trước hạn **18:22 ngày 15/10/2026**, kèm hướng dẫn 3 bước tự thực hiện cuối cùng (Deploy Streamlit Cloud 1-click, quay video 4:30 và gửi form).

---

## 1. Các đường dẫn nộp bài

- **Link Source Code (GitHub Public):** `https://github.com/DuongNAD/gamota-market-research-mvp`
- **Link Sản phẩm chạy được (Streamlit Cloud):** `https://gamota-market-research-mvp.streamlit.app`
- **Link Video Walkthrough (≤ 5 phút):** `https://youtu.be/WZhY9xlLmMY`

---

## 2. Đoạn "Trình bày bài làm" (Dán vào ô Trình bày bài làm trên Form — 1.163 ký tự, chuẩn khung 600–1.200 ký tự)

```text
Tôi xây dựng Hệ thống Nghiên cứu Thị trường Game có Căn cứ (Gamota MVP) nhằm giải quyết rủi ro lớn nhất khi dùng AI nghiên cứu thị trường: ảo giác số liệu và ngụy tạo nguồn. Thay vì để LLM tự trả lời và tự chấm điểm, sản phẩm chạy pipeline 6 bước (Plan -> Retrieve -> Grade -> Extract & Verify -> Synthesize -> Score), ép mọi nhận định truy về trích dẫn nguyên văn <=40 từ được code xác minh (RapidFuzz >=90) kèm link tô sáng (#:~:text=), xếp hạng nguồn A/B/C và tính độ tin cậy (CAO/TRUNG BÌNH/THẤP) bằng code tất định.
Cách chạy: Mở link Demo Streamlit (chế độ Kết quả đã lưu chạy ngay không cần key với 6 báo cáo thật TC1-TC6) hoặc chạy local: `pip install -r requirements.txt` -> `streamlit run app.py` (`pytest` 21/21 pass, `python -m eval.run_eval`).
Quyết định chính: (1) Cấm LLM viết URL, khóa trần dự báo ở mức TRUNG BÌNH; (2) Tự động hiển thị dải số liệu mâu thuẫn ngay ở tóm tắt (TC3); (3) Bổ sung tách ngày đăng từ URL/tiêu đề và xoay vòng key/model Flash.
Hạn chế: (1) Nguồn mở không lấy được doanh thu tháng trước theo quốc gia sau paywall Sensor Tower/AppMagic (TC6 chưa đạt thật, báo thiếu thay vì bịa số); (2) Chưa đọc file PDF; (3) Chạy Live mất 23-82s.
```

---

## 3. Trả lời 3 câu hỏi bắt buộc (Dán vào Form nếu có ô riêng cho từng câu)

### Câu 1: Phần quan trọng nhất bạn chọn để hiện thực hóa trong MVP là gì? Vì sao nếu phần này hoạt động, bạn tin rằng hướng giải quyết của mình là khả thi?
Tôi chọn hiện thực hóa sâu **lớp kiểm chứng bằng chứng nguyên văn và tính điểm độ tin cậy tất định bằng code** (`Extract & Verify` trong `research/extract.py` kết hợp `Score` trong `research/score.py`). Cụ thể, thay vì để LLM vừa viết báo cáo vừa tự đính kèm link và tự đánh giá mức độ chắc chắn, tôi bắt buộc mọi nhận định phải trỏ về mã `evidence_id` chứa câu trích dẫn nguyên văn `<= 40` từ đạt điểm khớp chuỗi `rapidfuzz.fuzz.partial_ratio >= 90` ngay trên văn bản nguồn đã thu thập. Nếu phần này hoạt động trơn tru, tôi tin hướng giải quyết của mình hoàn toàn khả thi vì nó giải quyết tận gốc rào cản lớn nhất khiến các đội phát hành game không dám dùng AI cho nghiên cứu thị trường: **ảo giác số liệu (hallucination) và ngụy tạo nguồn**. Thực nghiệm trên cả 6 test case (`TC1`–`TC6`) cho thấy hệ thống đã xác minh thành công `166/166` (`100.0%`) câu trích dẫn nguyên văn, tạo link tô sáng trực tiếp `#:~:text=` mở đúng câu gốc trên trình duyệt, giữ số URL do LLM tự viết ở mức `0` và số nhận định `CAO` dựa trên nguồn hạng C ở mức `0`. Đặc biệt, khi đối chiếu trực tiếp với LLM trần ở `TC3` và `TC4` (`eval/results/baseline_raw_llm.json`), lớp kiểm chứng này đã chặn đứng hành vi tự bịa 3 URL cũ ở `TC3` và tự nhân tỷ lệ giả định để bịa ra con số `"3,5 đến 6 triệu USD"` cho MMORPG Campuchia ở `TC4`.

### Câu 2: So với kế hoạch ở Mission 1, bạn đã thay đổi quyết định hoặc thiết kế nào? Điều gì trong quá trình làm khiến bạn thay đổi?
So với ý tưởng ban đầu ở Mission 1 về một hệ thống nghiên cứu thị trường đa tác tử (multi-agent) có cơ sở dữ liệu lưu trữ dài hạn và thu thập đa kênh, tôi đã thực hiện **4 thay đổi thiết kế quan trọng** (ghi nhận chi tiết tại `DECISIONS.md`):
1. **Thu gọn phạm vi sang pipeline tuyến tính 6 bước bằng Python thuần** (không dùng LangChain/CrewAI, không dùng database) để dồn toàn bộ thời gian chứng minh độ tin cậy của từng nhận định.
2. **Bổ sung cơ chế xoay vòng key và tự động chuyển đổi model Flash dự phòng kèm `thinkingBudget=0` trong `research/llm.py`**: Khi chạy thực tế ở P1, model mặc định `gemini-3.8-flash` đôi lúc trả về `HTTP 503 (Service Unavailable)` và `gemini-2.5-flash` bật chế độ suy nghĩ mặc định làm bước tổng hợp mất hơn 35 giây; việc tự động failover và tắt `thinkingBudget` đã kéo thời gian mỗi lệnh gọi LLM xuống ~2,7 giây (tổng thời gian chạy mỗi báo cáo còn `23–82s`).
3. **Mở rộng bộ tách ngày xuất bản dự phòng (`_extract_date_fallback`) và siết quy tắc chấm điểm `CAO` sau vòng chạy kiểm thử đầu tiên (Before → After)**: Ở lượt chạy Before của P3, có tới `3–8/12` bài báo ngành (`Sensor Tower`, `AppsFlyer`) thiếu thẻ HTML meta date nên bị gán nhầm thành nguồn cũ (`stale`), trong khi ở `TC6` một câu thông báo "không có dữ liệu" ghép 1 nguồn A mất ngày và 1 nguồn C mới lại bị chấm nhầm là `CAO`. Tôi đã bổ sung regex tách tháng/quý/năm từ URL slug & tiêu đề (giảm nguồn mất ngày ở `TC3`, `TC5` về `0/12`) và sửa `research/score.py` yêu cầu nguồn hạng A/B phải còn mới (`fresh`) mới được lên `CAO`.
4. **Ép code tự động nối cảnh báo dải số liệu mâu thuẫn vào ngay `short_answer` và escape ký tự `\$` khi xuất bảng**: Sau khi thấy `short_answer` ở lượt chạy Before của `TC3` chỉ nêu một con số `825 triệu USD` dù mục 3.2 có nhiều mốc khác nhau, và thấy ảnh chụp màn hình trình duyệt ở P2 bị lỗi hiển thị phông chữ KaTeX khi một ô bảng có hai dấu `$` (`$625 million`), tôi đã sửa `research/score.py` và `research/pipeline.py` để xử lý triệt để bằng code.

### Câu 3: MVP hiện xử lý chưa tốt nhất ở tình huống nào? Theo bạn nguyên nhân nằm ở đâu và nếu có thêm thời gian bạn sẽ ưu tiên cải thiện điều gì?
MVP hiện xử lý chưa tốt nhất ở **các câu hỏi đòi hỏi số liệu đo lường (telemetry) giao cắt sâu theo `Quốc gia × Thể loại ngách × Tháng gần nhất`**, thể hiện rõ nhất ở **`TC6`** (*"Doanh thu tháng trước của 3 game gacha top đầu Thái Lan là bao nhiêu?"* — kết quả **CHƯA ĐẠT**) và một phần ở **`TC4`** (*"Doanh thu MMORPG mobile tại Campuchia năm 2025"*). Ở `TC6`, dù hệ thống thu thập được 12 nguồn và xác minh `20/20` câu trích dẫn về doanh thu gacha toàn cầu tháng 9/2026 (`Genshin Impact` `50,23 triệu USD`, `Honkai: Star Rail` `35,735 triệu USD` từ `game8.co`) cũng như quy mô thị trường game Thái Lan nói chung (`192 triệu USD` từ `6wresearch.com`), hệ thống vẫn không thể trả lời được con số doanh thu tháng 9/2026 của riêng top 3 game gacha tại Thái Lan. Nguyên nhân gốc rễ nằm ở **giới hạn của nguồn dữ liệu web mở**: các bảng số liệu doanh thu cấp độ từng tựa game theo từng quốc gia và từng tháng không được công bố dưới dạng bài viết HTML công khai mà nằm sau tường phí (paywall) hoặc trang dashboard dựng bằng JavaScript động (SPA) của Sensor Tower, AppMagic và Data.ai. Bên cạnh đó, công cụ trích xuất `trafilatura` hiện chỉ đọc HTML tĩnh và bỏ qua các báo cáo định dạng PDF chuyên sâu (như 3 file PDF báo cáo thị trường Việt Nam của `investgame.net` bị bỏ qua ở `TC3`). Nếu có thêm thời gian, tôi sẽ ưu tiên cải thiện theo thứ tự: **(1)** Tích hợp đầu đọc dữ liệu nội bộ (CSV/Excel export từ tài khoản Sensor Tower/AppMagic của Gamota) và parser PDF (`pypdf`/`pdfplumber`) vào bước `Retrieve` để tận dụng các báo cáo ngành dạng PDF; **(2)** Bổ sung cơ chế truy vấn vòng 2 (iterative search) tự động sinh thêm truy vấn chuyên biệt khi bước `Extract` phát hiện thiếu số liệu cho câu hỏi phụ chính.

---

## 4. Kịch bản quay Video Walkthrough (Mục tiêu 4:30, tối đa 5:00)

- **Công cụ gợi ý:** OBS Studio, Loom hoặc tính năng quay màn hình tích hợp của Windows (`Win + G`).
- **Chuẩn bị trước khi bấm Record:**
  1. Mở sẵn tab 1: Giao diện Streamlit (`http://localhost:8501` hoặc link Streamlit Cloud).
  2. Mở sẵn tab 2: File `README.md` trên GitHub (`https://github.com/DuongNAD/gamota-market-research-mvp`).

| Mốc thời gian | Thao tác trên màn hình | Lời nói (đọc tự nhiên theo ý dưới đây) |
|---|---|---|
| **`0:00 – 0:30`** | Hiển thị tiêu đề trên giao diện Streamlit (`app.py`). | *"Chào anh/chị hội đồng chấm thi Gamota. Khi đội Publishing hoặc BD cần nghiên cứu nhanh một thị trường hay thể loại game mới, thông tin trên mạng thường phân mảnh và mâu thuẫn. Nếu hỏi thẳng các chatbot AI thông thường, chúng rất hay trộn số liệu thật với suy diễn, tự bịa link báo cáo và tự nhận độ tin cậy cao khiến chúng ta không dám dùng để ra quyết định đầu tư."* |
| **`0:30 – 1:00`** | Chuyển sang tab `README.md` mục 4 (Sơ đồ Mermaid Pipeline 6 bước & Bảng quy tắc Độ tin cậy). | *"Vì vậy, trong MVP này, em không làm dàn trải mà chọn chứng minh sâu lớp 'Nhận định có căn cứ' qua pipeline 6 bước. Mọi nhận định bắt buộc phải trỏ về câu trích dẫn nguyên văn tối đa 40 từ, được code kiểm chứng bằng RapidFuzz đạt từ 90 điểm trở lên, gắn với hạng nguồn A/B/C từ file cấu hình, và độ tin cậy CAO, TRUNG BÌNH, THẤP được tính 100% bằng code tất định — LLM tuyệt đối không được tự viết URL và không được tự chấm điểm."* |
| **`1:00 – 2:45`** | Quay lại tab Streamlit:<br>1. Đang ở **TC1** (Thể loại tiềm năng ĐNÁ): trỏ chuột vào 4 ô chỉ số (`100.0%` trích dẫn xác minh, `0` CAO từ nguồn C), cuộn qua Bảng Phương án × Tiêu chí xuống Bảng Nhận định.<br>2. **Bấm vào link `[E2 · S2 (sensortower.com)]` ở dòng `I1`** để mở trang Sensor Tower: trình duyệt tự cuộn và tô sáng câu trích dẫn gốc!<br>3. Quay lại tab Streamlit, bấm nút mẫu **💰 Mô hình kiếm tiền (TC2)** ở phía trên để đổi sang báo cáo TC2. | *"Trên giao diện ứng dụng, chế độ Kết quả đã lưu hoạt động ngay mà không cần API key. Với câu hỏi loại 1 (TC1) về thể loại game tiềm năng tại Đông Nam Á 12 tháng tới, hệ thống xác minh 30/30 câu trích dẫn nguyên văn, lập bảng so sánh 4 thể loại trên 5 tiêu chí, và khóa trần mọi nhận định dự báo ở mức TRUNG BÌNH kèm giả định. Em xin bấm thử vào link bằng chứng E2 của nguồn Hạng A Sensor Tower: trình duyệt mở trực tiếp bài báo gốc và tô sáng đúng câu nguyên văn tiếng Anh đã trích xuất. Khi chuyển sang câu hỏi loại 2 (TC2) về mô hình kiếm tiền game casual tại Indonesia và Philippines, cùng một pipeline tự động đổi bộ tiêu chí sang ARPU, tỷ lệ nhà phát hành dùng IAA (86%) và IAP (29%) mà không hề hardcode."* |
| **`2:45 – 3:45`** | Trên thanh chọn báo cáo của Streamlit, chọn lần lượt **`TC3_VN_MARKET_SIZE`**, **`TC4_CAMBODIA_MMORPG`**, **`TC5_SEA_DROP_50_PREMISE`** và chỉ vào mục `1. Trả lời ngắn` & `3. Mâu thuẫn / Kiểm tra tiền đề`. | *"Ở các tình huống khó: Với TC3 về quy mô game mobile Việt Nam, thay vì chốt bừa một con số, hệ thống trình bày cả mốc 825 triệu USD năm 2025, 500 triệu USD năm 2024 và giải thích sự khác biệt giữa lượt tải nội địa (272 triệu) với sản lượng xuất khẩu toàn cầu của studio Việt (4,9 tỷ lượt tải). Với TC4 về doanh thu MMORPG Campuchia 2025, trong khi LLM trần tự bịa ra con số 3,5 đến 6 triệu USD, hệ thống của em nói rõ nguồn mở không có số liệu này, chỉ cung cấp số liệu proxy 131,44 triệu USD toàn ngành game Campuchia và gợi ý các bước kiểm chứng từ rẻ đến đắt. Với TC5 hỏi vì sao doanh thu Đông Nam Á giảm 50%, bước Premise Check bác bỏ thẳng tiền đề sai này bằng số liệu tăng trưởng thực tế."* |
| **`3:45 – 4:30`** | Chọn **`TC6_THAILAND_GACHA`** trên Streamlit, cuộn qua mục `1`, `3.1`, `4.1`. | *"Về hạn chế và case chưa đạt thật: Ở TC6 hỏi doanh thu tháng trước (tháng 9/2026) của top 3 game gacha tại riêng Thái Lan, nguồn web mở chỉ có số liệu toàn cầu của Genshin Impact (50,23 triệu USD) và Honkai: Star Rail (35,735 triệu USD), còn bảng tách riêng theo quốc gia Thái Lan tháng gần nhất bị khóa sau paywall của Sensor Tower và AppMagic. Hệ thống đã trung thực báo thiếu dữ liệu thay vì lấy số toàn cầu gắn nhầm cho Thái Lan, và đánh dấu TC6 là Chưa đạt. Nếu có thêm thời gian, ưu tiên số 1 của em là cho phép upload file CSV/PDF xuất từ tài khoản Sensor Tower nội bộ của Gamota vào bước Retrieve, tiếp theo là đọc báo cáo PDF trực tuyến và song song hóa bước Extract để giảm thời gian chạy xuống dưới 25 giây. Em xin cảm ơn!"* |

---

## 5. Danh sách 3 việc bạn cần tự làm trước khi bấm Nộp (tổng thời gian ~10 phút)

1. **Deploy lên Streamlit Community Cloud (2 phút):**
   - Mở [https://share.streamlit.io](https://share.streamlit.io) → đăng nhập bằng tài khoản GitHub `DuongNAD`.
   - Bấm **Create app** → Chọn repository `DuongNAD/gamota-market-research-mvp`, branch `main`, Main file path `app.py`, đặt App URL là `gamota-market-research-mvp` → Bấm **Advanced settings...**.
   - Trong ô **Secrets**, dán dòng cấu hình TOML (lấy từ file `.env` trên máy của bạn):
     ```toml
     LLM_PROVIDER = "gemini"
     LLM_MODEL = "gemini-3.8-flash"
     GEMINI_API_KEY = "<dán-1-key-của-bạn-vào-đây>"
     ```
   - Bấm **Deploy!**. Mở thử link trong cửa sổ ẩn danh (Incognito) để xác nhận chế độ **Kết quả đã lưu** hoạt động mượt mà.
2. **Quay Video Walkthrough 4 phút 30 giây (5 phút):**
   - Quay theo đúng bảng kịch bản ở Mục 4 phía trên.
   - Tải lên Loom / YouTube (chế độ *Unlisted / Không công khai*) hoặc Google Drive (bật *Anyone with the link can view*).
3. **Điền Form nộp bài của Gamota (2 phút):**
   - Dán Link Demo, Link GitHub Repo, Link Video và đoạn **Trình bày bài làm** (Mục 2) vào Form.
