# BRIEF — Gamota · Bài test A (Nghiên cứu thị trường game) · Mission 2: Hiện thực hóa

> Bản giao việc cho AI agent. Đọc hết trước khi làm. Hôm nay là 14/10/2026, hạn nộp **18:22 ngày 15/10**. Mọi phần việc của bạn phải xong trước **16:00 ngày 15/10** để tôi còn quay video và nộp form.

## 0. Vai trò & nguyên tắc
- Bạn là kỹ sư AI/full-stack senior. Tôi là người nộp bài và duyệt ở các CHECKPOINT.
- Bạn chạy trong Google Antigravity 2.0. Quy tắc luôn áp dụng nằm ở `AGENTS.md`. Báo cáo qua artifact: Implementation Plan + Task List trước khi code mỗi phase, Walkthrough ở mỗi CHECKPOINT. Dùng trình duyệt tích hợp để kiểm tra giao diện.
- Thứ tự ưu tiên: **chứng minh đúng giả thuyết cốt lõi > chạy được > trung thực về hạn chế > đẹp**. Một MVP nhỏ chứng minh đúng điều quan trọng được chấm cao hơn một sản phẩm nhiều tính năng.
- Tài liệu nộp viết bằng tiếng Việt; code và tên biến bằng tiếng Anh.

## 1. Đề bài (nguồn sự thật)
- Gamota cần một sản phẩm dùng AI để nghiên cứu thị trường game nhanh hơn, có hệ thống hơn, tạo **nhận định dùng được cho việc ra quyết định**. Thông tin trên Internet phân tán, độ tin cậy khác nhau, có thể cũ hoặc mâu thuẫn. Thách thức không phải là tìm thật nhiều, mà là **biến thông tin thành nhận định có căn cứ và kiểm chứng được**.
- Câu hỏi cốt lõi: làm sao để kết quả **vừa đáng tin cậy, vừa thực sự giúp người dùng ra quyết định**?
- Core loop: câu hỏi nghiên cứu → tìm hiểu → dùng nguồn thông tin → nhận định có căn cứ → người dùng kiểm chứng được.
- MVP **bắt buộc** chứng minh:
  - **R1** Xử lý được nhiều hơn một câu hỏi mẫu (ví dụ của đề: "Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?", đây chỉ là một ví dụ).
  - **R2** Kết luận quan trọng có căn cứ.
  - **R3** Không coi mọi nguồn có độ tin cậy ngang nhau.
  - **R4** Thể hiện rõ khi dữ liệu thiếu hoặc không chắc chắn.
  - **R5** Có cách kiểm thử chất lượng.
- Không cần: làm hết những gì đã nghĩ ở Mission 1, sản phẩm production-ready, giao diện đẹp. **Không được** che giấu lỗi hoặc hạn chế.
- Bài nộp: repo GitHub public (có README; không chứa API key, mật khẩu, dữ liệu nhạy cảm) · link chạy thử online (không deploy được thì ghi rõ lý do và hướng dẫn chạy local trong README) · video ≤ 5 phút · ≥ 5 test case · trả lời 3 câu hỏi bắt buộc · đoạn "Trình bày bài làm" (cách chạy, quyết định đã đưa ra, hạn chế đã biết).
- Tự chọn ngôn ngữ, framework, model, nhà cung cấp LLM; ưu tiên free tier.

## 2. Thông tin từ tôi
- Nội dung mục "Bối cảnh" trên trang đề: {{BOI_CANH: dán vào, hoặc ghi "Không có"}}
- Giải pháp tôi đã thiết kế ở Mission 1: {{MISSION_1: phần cốt lõi, kiến trúc, nguồn dữ liệu dự kiến; hoặc "Không có"}}
- Stack/LLM chạy bên trong sản phẩm (không phải model của agent): {{để trống = dùng mặc định ở mục 4.5}}
- Tài khoản đã có: {{vd. "đã có Gemini, chưa có Tavily". Chỉ ghi tên dịch vụ, KHÔNG dán key}}

Nếu Mission 1 chọn phần cốt lõi khác mục 3: giữ phần cốt lõi của Mission 1 nhưng vẫn phải đạt R1–R5. Mọi điểm khác so với Mission 1 đều ghi vào `DECISIONS.md` (dùng để trả lời câu hỏi 2).

## 3. Giả thuyết cốt lõi cần chứng minh
**Lớp "nhận định có căn cứ"**: với *bất kỳ* câu hỏi nghiên cứu thị trường game, mỗi nhận định quan trọng đều (a) truy được về **trích dẫn nguyên văn đã được code xác minh**, (b) gắn với **hạng tin cậy của nguồn**, (c) có **độ tin cậy tính bằng quy tắc minh bạch**, không do LLM tự chấm. Thiếu dữ liệu thì nói là thiếu.

Vì sao đây là phần quan trọng nhất: tìm và tóm tắt thì chatbot nào cũng làm được, nhưng người dùng chỉ dám dùng kết quả để ra quyết định khi **tự kiểm chứng được**. Nếu lớp này chạy tốt trên nhiều loại câu hỏi thì phần còn lại (thêm nguồn dữ liệu, dashboard, theo dõi định kỳ) chỉ là mở rộng.

## 4. Thiết kế MVP mặc định
Được phép đổi nếu có cách tốt hơn, nhưng phải ghi lý do vào `DECISIONS.md`.

### 4.1 Pipeline `run(question) -> Report` (Python thuần, không LangChain/CrewAI)
1. **Plan**: LLM tách câu hỏi thành 3–5 câu hỏi con, tiêu chí quyết định (vd. quy mô, tăng trưởng, mức cạnh tranh, kiếm tiền, chi phí UA), query tìm kiếm (EN + VI, kèm năm gần đây) và **tiền đề ngầm** của câu hỏi cần kiểm tra.
2. **Retrieve**: search mỗi query (top 5) → bỏ trùng → lấy nội dung chính + ngày đăng → giữ ≤ 12 nguồn tốt nhất; mỗi nguồn cắt còn khoảng 6.000 ký tự, ưu tiên đoạn chứa từ khóa.
3. **Grade**: xếp hạng nguồn A/B/C theo `config/source_tiers.yaml` và độ mới theo ngày đăng.
4. **Extract**: LLM rút claim (gom 3–4 nguồn mỗi lần gọi); mỗi claim kèm **trích dẫn nguyên văn ≤ 40 từ, giữ ngôn ngữ gốc, không dịch**. Code xác minh trích dẫn có trong nội dung nguồn (chuẩn hóa khoảng trắng và chữ hoa thường, rapidfuzz `partial_ratio` ≥ 90). Không khớp thì loại và ghi log.
5. **Synthesize**: LLM viết nhận định **chỉ từ evidence đã xác minh**, tham chiếu bằng `evidence_id`; phân loại `fact`/`inference`; nêu mâu thuẫn, khoảng trống, kết quả kiểm tra tiền đề. **LLM không bao giờ tự viết URL**: code gắn URL theo `evidence_id`.
6. **Score**: code tính độ tin cậy (mục 4.2) và các chỉ số tự kiểm (mục 4.3).

- Mọi prompt gửi LLM đều kèm ngày hiện tại (lấy từ hệ thống) để hiểu đúng "12 tháng tới", "năm qua", "tháng trước".
- Giới hạn: ≤ 8 lần gọi LLM và mục tiêu < 90 giây cho mỗi câu hỏi. Cache đĩa theo hash cho search, fetch và LLM để tiết kiệm quota khi dev và test.

### 4.2 Quy tắc chấm (viết bằng code, có unit test)
- **Hạng nguồn**
  - **A**: dữ liệu gốc hoặc nhà cung cấp dữ liệu ngành (báo cáo tài chính/IR của publisher niêm yết, Sensor Tower, Newzoo, số liệu cơ quan nhà nước).
  - **B**: truyền thông và phân tích ngành uy tín (GamesIndustry.biz, PocketGamer.biz, MobileGamer.biz, Naavik, báo lớn như Reuters, Bloomberg, VnExpress).
  - **C** (mặc định): blog, trang SEO, diễn đàn, thông cáo báo chí, domain lạ.
- **Độ mới**: ≤ 12 tháng là mới · 12–24 tháng là cũ dần · > 24 tháng hoặc không rõ ngày là cũ.
- **Độ tin cậy của nhận định**
  - **CAO**: ≥ 2 nguồn khác domain, có ≥ 1 nguồn A/B, không cũ, không mâu thuẫn, loại `fact`.
  - **TRUNG BÌNH**: 1 nguồn A/B; hoặc ≥ 2 nguồn C đồng thuận; hoặc dữ liệu cũ dần. Nhận định `inference` và dự báo **tối đa TRUNG BÌNH**, phải nêu giả định.
  - **THẤP**: chỉ 1 nguồn C, dữ liệu cũ, hoặc mâu thuẫn chưa giải quyết.
  - Không có evidence thì không được là nhận định; chuyển vào "Khoảng trống dữ liệu".
- **Mâu thuẫn số liệu**: hiện đủ các giá trị kèm nguồn và khả năng khác định nghĩa/phạm vi/kỳ; không lấy trung bình ngầm.

### 4.3 Báo cáo đầu ra (tiếng Việt; Markdown + JSON)
1. Trả lời ngắn (2–3 câu) + **khuyến nghị cho quyết định** (nên làm gì, với điều kiện nào), bám theo tiêu chí quyết định ở bước Plan. Câu hỏi dạng chọn phương án thì thêm bảng phương án × tiêu chí.
2. Bảng nhận định: nhận định · loại · độ tin cậy + lý do · nguồn (hạng, ngày, link) · trích dẫn. Link nguồn dùng text fragment `url#:~:text=<đầu câu trích, percent-encode>` để trình duyệt cuộn tới và tô sáng đúng câu.
3. Mâu thuẫn giữa các nguồn · kết quả kiểm tra tiền đề của câu hỏi.
4. Khoảng trống và điều chưa chắc chắn · "Điều gì sẽ làm thay đổi kết luận" · bước kiểm chứng tiếp theo (cách rẻ nhất trước).
5. Danh sách nguồn (hạng, ngày, lý do xếp hạng).
6. **Tự kiểm chất lượng**: % trích dẫn xác minh được · % nhận định có ≥ 1 evidence · số nhận định CAO dựa trên nguồn C (phải bằng 0) · số nguồn bị loại kèm lý do.

Schema (Pydantic; LLM trả JSON theo schema, validate, retry 1 lần):
`Source{id, url, domain, title, published_date?, tier, tier_reason}` · `Evidence{id, source_id, quote, claim, verified, match_score}` · `Insight{id, statement, type, evidence_ids[], confidence, confidence_reason, assumptions[]}` · `Report{question, short_answer, recommendation, insights[], conflicts[], premise_checks[], gaps[], next_checks[], sources[], quality{}, trace{}}`

### 4.4 Giao diện (Streamlit, tối giản)
- Ô nhập câu hỏi + 3–4 nút câu hỏi mẫu **khác loại** (cơ hội thể loại, quy mô thị trường, mô hình kiếm tiền, đối thủ).
- Hai chế độ: **Live** và **Kết quả đã lưu** (`data/cached_runs/*.json`: lần chạy thật, ghi rõ thời điểm chạy). Chế độ này giúp demo luôn chạy được kể cả khi hết quota.
- Hiện tiến trình từng bước khi chạy (`st.status`), báo cáo theo mục 4.3, nhật ký pipeline (số nguồn tìm thấy/giữ/loại và vì sao), nút tải JSON/Markdown.

### 4.5 Stack mặc định
- Python 3.11+, Streamlit, Pydantic, httpx, trafilatura, rapidfuzz, pytest.
- LLM: Gemini Flash qua Google AI Studio (free tier); dự phòng Groq hoặc OpenRouter. Đổi bằng biến môi trường `LLM_PROVIDER`, `LLM_MODEL` trong `research/llm.py`. Không dùng model chỉ có ở paid tier (vd. Gemini 4 Argon) trong code sản phẩm, vì demo công khai sẽ tiêu tiền thật.
- Search: Tavily (free tier, `include_raw_content`); dự phòng thư viện `ddgs` (tên cũ `duckduckgo-search`, không cần key).
- Deploy: Streamlit Community Cloud; key đặt trong mục Secrets của app.

```
app.py
research/   pipeline.py  llm.py  retrieve.py  grade.py  extract.py  synthesize.py  score.py  schemas.py  cli.py
config/source_tiers.yaml
data/cached_runs/
eval/       cases.yaml  run_eval.py  results/
tests/
README.md  TESTING.md  DECISIONS.md  requirements.txt  .env.example  .gitignore
```

## 5. Quy tắc bắt buộc
1. **Trung thực**: "Kết quả thực tế" phải là output chạy thật, lưu ở `eval/results/`. Không bịa, không sửa tay, không hardcode đáp án cho câu hỏi mẫu.
2. **Bảo mật**: key chỉ nằm ở `.env`, `.streamlit/secrets.toml` (cả hai trong `.gitignore`) hoặc Secrets của nền tảng; có `.env.example`. Trước mỗi lần push, quét repo và `git log -p` tìm chuỗi giống key. Lỡ commit key thì dừng lại và báo tôi thu hồi key.
3. **Bản quyền & dung lượng**: không lưu toàn văn bài nguồn vào repo; cached runs và eval results chỉ chứa metadata và trích dẫn ngắn.
4. **Phạm vi**: chỉ làm những gì phục vụ R1–R5. Không auth, không database, không multi-agent framework. Kẹt quá 30 phút ở phần không cốt lõi thì cắt và ghi vào Hạn chế.
5. **Thiếu giờ thì cắt theo thứ tự**: làm đẹp UI → nút tải file → bảng phương án × tiêu chí → Live mode trên bản deploy (giữ Kết quả đã lưu). **Không bao giờ cắt**: trích dẫn + xác minh, hạng nguồn, độ tin cậy + khoảng trống, ≥ 5 test, README, 3 câu trả lời.
6. **`DECISIONS.md`**: ghi liên tục, mỗi quyết định hoặc thay đổi 1–2 dòng theo dạng bối cảnh → quyết định → lý do.
7. **Bản deploy**: giới hạn số lượt chạy Live mỗi phiên để không cạn quota; lỗi API thì hiện thông báo dễ hiểu và gợi ý xem Kết quả đã lưu.
8. **Văn phong tài liệu**: ngôi thứ nhất, cụ thể, dẫn số liệu từ test; không sáo rỗng, không phóng đại.
9. **Không** thêm `BRIEF.md`, `AGENTS.md` vào `.gitignore` (tùy cài đặt, Antigravity có thể không cho agent đọc file bị ignore); hai file này được commit cùng repo. `.env` vẫn gitignore như mục 5.2: tôi tự điền key.

## 6. Kế hoạch & checkpoint (~10 giờ)
- **P0 (0,5h)**: tạo repo public (dùng `gh` nếu có, không thì hướng dẫn tôi), skeleton, `.gitignore`. Liệt kê các key tôi cần tạo kèm link đăng ký để tôi làm song song. Hướng dẫn tôi deploy bản "hello world" lên Streamlit Cloud ngay để loại rủi ro deploy.
- **P1 (3–4h)**: pipeline bước 1–6 chạy được bằng `python -m research.cli "<câu hỏi>"`; unit test cho `score.py` và hàm xác minh trích dẫn.
  → **CHECKPOINT 1**: cập nhật Walkthrough gồm output của 2 câu hỏi khác loại, chỉ số tự kiểm và các vấn đề gặp phải; dừng chờ tôi duyệt.
- **P2 (1,5h)**: giao diện, kiểm tra bằng trình duyệt tích hợp; chạy thật các câu hỏi mẫu và lưu vào `data/cached_runs/`.
- **P3 (2h)**: chạy bộ test (mục 7), ghi kết quả thật. **Vòng cải tiến**: sửa 1–2 lỗi quan trọng nhất lộ ra từ test, chạy lại, ghi before → after vào `TESTING.md` và `DECISIONS.md`. Tùy chọn nếu còn ≥ 1 giờ: chạy TC3, TC4 bằng LLM trần (không qua pipeline) làm baseline để so sánh.
  → **CHECKPOINT 2**: cập nhật Walkthrough với bảng kết quả test; dừng chờ tôi duyệt trước khi viết tài liệu.
- **P4 (1,5h)**: README, `TESTING.md`, 3 câu trả lời, đoạn "Trình bày bài làm", kịch bản video.
- **P5 (0,5h)**: push, mở link demo bằng trình duyệt tích hợp (phiên sạch, không đăng nhập), quét secrets lần cuối. Deploy hỏng quá 1 giờ thì dùng video walkthrough làm link demo, ghi lý do và hướng dẫn chạy local trong README.
  → **CHECKPOINT 3**: Walkthrough gồm checklist mục 9 đã tick kèm bằng chứng, và danh sách việc tôi còn phải tự làm (thêm Secrets, quay video, nộp form).

## 7. Bộ kiểm thử (≥ 5, khuyến nghị 6)
| ID | Nhóm dự kiến | Câu hỏi gợi ý | Kỳ vọng |
|---|---|---|---|
| TC1 | Làm tốt | Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới? | Nhận định có trích dẫn đã xác minh; khuyến nghị nêu giả định; dự báo ≤ TRUNG BÌNH |
| TC2 | Làm tốt (loại câu hỏi khác) | Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines? | Như TC1; cho thấy không hardcode |
| TC3 | Khó: nguồn mâu thuẫn | Quy mô thị trường game mobile Việt Nam hiện nay là bao nhiêu? | Hiện nhiều con số kèm nguồn, giải thích khác biệt định nghĩa/kỳ; không chốt một con số |
| TC4 | Khó: thiếu dữ liệu | Doanh thu thể loại MMORPG mobile tại Campuchia năm 2025 là bao nhiêu? | Nói rõ không đủ dữ liệu; gợi ý dữ liệu thay thế và cách kiểm chứng; không bịa số |
| TC5 | Khó: tiền đề sai | Vì sao doanh thu game mobile Đông Nam Á giảm 50% trong năm qua? | Kiểm tra tiền đề; phản biện nếu không có bằng chứng |
| TC6 | Dễ thất bại | Doanh thu tháng trước của 3 game gacha top đầu Thái Lan là bao nhiêu? | Số liệu đúng kỳ được hỏi, có nguồn; không có thì nói rõ, không lấy số của kỳ khác thay thế |

- `eval/cases.yaml` ghi kỳ vọng **trước khi chạy**, dạng máy kiểm được khi có thể (`min_verified_rate`, `max_confidence`, `must_have_gaps`, `must_challenge_premise`), kèm mô tả định tính. `python -m eval.run_eval [--case TC3]` chạy toàn bộ hoặc một case, lưu output, in chỉ số tự kiểm và thời gian chạy.
- Bắt buộc có ≥ 1 case làm tốt, ≥ 1 case khó hoặc dữ liệu không rõ ràng, ≥ 1 case **chưa đạt thật**. Nếu mọi case đều đạt thì tìm case khó hơn cho đến khi lộ điểm yếu thật. Nhóm trong `TESTING.md` ghi theo kết quả thật, không theo dự kiến.
- Mỗi case trong `TESTING.md` theo đúng thứ tự đề yêu cầu:

```
### TC_ — <tên ngắn> (<Làm tốt | Khó | Chưa đạt>)
Câu hỏi: …
Kỳ vọng: …
Kết quả thực tế: … (số nguồn, % trích dẫn xác minh, độ tin cậy; trích 1–2 dòng output; link eval/results/…)
Đạt/Chưa đạt: …
Điều học được: …
```

## 8. Tài liệu nộp
**README.md** (người chấm đọc đầu tiên), đúng thứ tự:
1. Tên + 1 câu mô tả + link Demo + link Video.
2. Bài toán và người dùng (3–4 dòng).
3. Phần chọn để chứng minh, vì sao, và khác gì so với hỏi thẳng một chatbot có tìm kiếm.
4. Cách hoạt động: sơ đồ pipeline (Mermaid) + quy tắc hạng nguồn và độ tin cậy.
5. Bảng R1–R5 → cách MVP đáp ứng → bằng chứng (màn hình hoặc test ID).
6. Chạy thử: link online (ghi chú: nếu app đang ngủ thì bấm đánh thức và chờ khoảng 1 phút); local: clone → venv → `pip install -r requirements.txt` → copy `.env.example` thành `.env` → `streamlit run app.py`; xem Kết quả đã lưu không cần key; `pytest`; `python -m eval.run_eval`.
7. Kết quả kiểm thử: bảng tóm tắt (ID · nhóm · Đạt/Chưa đạt · 1 dòng điều học được) + link `TESTING.md`.
8. Trả lời 3 câu hỏi bắt buộc.
9. Hạn chế đã biết và hướng cải thiện (theo thứ tự ưu tiên).

**3 câu hỏi bắt buộc**: mỗi câu trả lời 4–8 câu, dẫn test ID và số liệu thật, lấy từ `DECISIONS.md`.
1. Phần quan trọng nhất bạn chọn để hiện thực hóa trong MVP là gì? Vì sao nếu phần này hoạt động, bạn tin rằng hướng giải quyết của mình là khả thi?
2. So với kế hoạch ở Mission 1, bạn đã thay đổi quyết định hoặc thiết kế nào? Điều gì trong quá trình làm khiến bạn thay đổi?
3. MVP hiện xử lý chưa tốt nhất ở tình huống nào? Theo bạn nguyên nhân nằm ở đâu và nếu có thêm thời gian bạn sẽ ưu tiên cải thiện điều gì?

**Trình bày bài làm** (dán vào form, 600–1.200 ký tự): sản phẩm là gì → cách chạy (link + local) → 2–3 quyết định chính → 2–3 hạn chế đã biết.

**Kịch bản video** (≤ 5 phút, mục tiêu 4:30; mỗi đoạn ghi lời nói và màn hình cần quay):
`0:00–0:30` bài toán → `0:30–1:00` phần chọn để chứng minh → `1:00–2:45` demo 2 câu hỏi khác loại, bấm mở 1 trích dẫn để kiểm chứng tận nguồn → `2:45–3:45` tình huống khó (TC3/TC4/TC5) → `3:45–4:30` hạn chế, case chưa đạt, bước tiếp theo.

## 9. Tiêu chí hoàn thành (DoD)
- [ ] Link demo mở được bằng trình duyệt ẩn danh; chế độ Kết quả đã lưu chạy được mà không cần key.
- [ ] ≥ 3 câu hỏi mẫu khác loại đã chạy thật; output có trích dẫn đã xác minh, hạng nguồn, độ tin cậy, khoảng trống.
- [ ] 0 nhận định CAO dựa trên nguồn C; 0 URL do LLM tự sinh.
- [ ] `pytest` pass; `python -m eval.run_eval` chạy được; ≥ 5 test case đúng định dạng, trong đó ≥ 1 case chưa đạt thật.
- [ ] README đủ 9 mục; có 3 câu trả lời, đoạn Trình bày bài làm, kịch bản video.
- [ ] Repo public; không có key hay mật khẩu (kể cả trong lịch sử git); có `.env.example`.

---

## Phụ lục (dành cho tôi; agent bỏ qua phần này)

### A. Lệnh khởi động
Dán vào một hội thoại mới trong Antigravity, model Argon:

> Đọc toàn bộ `BRIEF.md` và `AGENTS.md` ở thư mục gốc. Sau đó:
> 1. Tóm tắt trong 5 dòng: bài toán, giả thuyết cốt lõi, những thứ phải nộp, hạn chót.
> 2. Liệt kê các điểm còn mơ hồ trong BRIEF, hoặc chỗ bạn đề xuất làm khác (kèm lý do).
> 3. Tạo Implementation Plan và Task List cho P0–P1.
>
> Dừng lại chờ tôi duyệt trước khi viết code.

Sau mỗi CHECKPOINT: trả lời "OK, làm tiếp P<n> theo BRIEF.md", hoặc comment góp ý thẳng lên artifact.

### B. Prompt review cuối
Dán vào một hội thoại mới khi agent báo xong. Nên chọn một model khác Argon để review chéo.

> Đóng vai người chấm Gamota khó tính. Đọc `BRIEF.md`, rồi đối chiếu với repo hiện tại:
> 1. Tick từng mục DoD (mục 9) kèm bằng chứng cụ thể: file, lệnh, output.
> 2. Chạy lại `pytest` và một case bằng `python -m eval.run_eval --case <ID>`.
> 3. Quét secrets trong toàn bộ lịch sử git.
> 4. Mở thử mọi link trong README.
> 5. Tìm chỗ tài liệu nói quá so với thực tế: test bị "làm đẹp", tính năng chưa có, số liệu không khớp với `eval/results/`.
> 6. Liệt kê 5 vấn đề dễ bị trừ điểm nhất theo mức độ nghiêm trọng, rồi sửa những gì sửa được trong 30 phút.
