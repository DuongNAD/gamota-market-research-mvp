# PROMPTS_M3 — Bộ prompt Mission 3 cho Antigravity (Gemini 4 Argon)

> File dành cho tôi (người nộp bài), không phải cho agent. Mỗi khối `text` bên dưới là một prompt: copy nguyên văn, dán vào hội thoại Antigravity. Đặc tả đầy đủ nằm ở `BRIEF_M3.md`; file này chỉ điều phối thứ tự làm việc và những gì tôi cần soi ở mỗi điểm dừng.
>
> Hai cách dùng: **(A) chạy một mạch bằng 1 prompt**, xem mục 0; **(B) duyệt từng chặng**, xem mục 3–8. Chọn một trong hai, không trộn.

## 0. Cách A — một prompt chạy từ đầu đến cuối

Agent tự làm P0 → P5 không dừng chờ duyệt. Các checkpoint vẫn có, nhưng việc chờ tôi được thay bằng **cổng tự kiểm** có tiêu chí cụ thể. Agent chỉ gọi tôi trong 4 trường hợp ghi trong prompt. Tổng thời lượng dự kiến như mục 1 (~11 giờ máy chạy nếu không gặp sự cố), không còn thời gian chờ duyệt.

**Chuẩn bị:**
1. Hội thoại mới trong Antigravity, model **Gemini 4 Argon**, mở thư mục repo.
2. Nếu bản Antigravity của bạn có các cài đặt này: cho phép agent tự chạy lệnh terminal; để agent tự đi tiếp sau khi tạo artifact; nếu có danh sách lệnh bị chặn, thêm `git push --force`, `git reset --hard`, `Remove-Item -Recurse`, `rm -rf`. Antigravity vẫn hiện nút duyệt plan thì bấm duyệt.
3. Cắm sạc và tắt chế độ ngủ của máy (Windows: Settings → System → Power → Screen and sleep → Never), vì phiên chạy nhiều giờ.
4. Không xóa `.cache/`.

**Prompt (dán nguyên văn):**

```text
Bạn là agent thực hiện TOÀN BỘ Mission 3 trong repo này, từ P0 đến P5, chạy một mạch. Mọi trả lời và artifact (Implementation Plan, Task List, Walkthrough) viết bằng tiếng Việt có dấu.

1) ĐỌC TRƯỚC
AGENTS.md → BRIEF_M3.md (toàn bộ; đây là đặc tả và kế hoạch, mục 7 là thứ tự làm) → README.md, TESTING.md, DECISIONS.md. BRIEF.md chỉ để tra cứu quy tắc Mission 2. Bỏ qua PROMPTS_M3.md.

2) CHẾ ĐỘ CHẠY MỘT MẠCH (tôi cho phép trước, thay cho các lần hỏi trong AGENTS.md)
- Tôi duyệt trước Implementation Plan của bạn và trả lời trước "OK" cho CHECKPOINT 1, 2, 3. Tại mỗi checkpoint: vẫn cập nhật Walkthrough đầy đủ như BRIEF_M3.md mục 7 yêu cầu, chạy CỔNG TỰ KIỂM ở phần 4, đạt thì đi tiếp, không chờ tôi.
- Tôi cho phép trước việc push ở P5, chỉ khi cổng tự kiểm P5 đạt hết. Chỉ được chạy đúng 3 lệnh này (không --force): git push origin master ; git push origin master:main ; git push origin mission2-final
- Kiểm giờ bằng Get-Date ở mỗi cổng. Quá 09:00 ngày 24/10 mà chưa xong P2, hoặc quá 12:00 ngày 24/10 mà chưa xong P3: tự cắt phần còn lại theo đúng thứ tự BRIEF_M3.md mục 9, không chờ tôi; ghi phần cắt vào DECISIONS.md và README mục Hạn chế. Không bao giờ cắt phần "Không bao giờ cắt". Hạn cứng: xong P5 trước 16:00 ngày 24/10.
- Chỉ dừng hẳn và gọi tôi khi: (a) cách duy nhất để đi tiếp là vi phạm một bất biến ở BRIEF_M3.md mục 4.1 hoặc một quy tắc "Không bao giờ vi phạm" trong AGENTS.md; (b) quét secrets ra số khác 0; (c) cần thao tác bằng tài khoản của tôi (GitHub, Streamlit Cloud, Google AI Studio); (d) cổng tự kiểm của một phần "Không bao giờ cắt" vẫn đỏ sau 3 lần sửa. Ngoài 4 trường hợp này, tự quyết theo BRIEF_M3.md và ghi 1–2 dòng vào DECISIONS.md.

3) LUẬT GIỮ NGUYÊN
- Không bịa: mọi con số trong Walkthrough, TESTING.md, README.md, SUBMISSION_M3.md phải có output thật hoặc nằm trong eval/results/. Ở mỗi cổng, dán nguyên văn các dòng output quan trọng.
- Không sửa 21 test cũ; không đổi prompt Plan/Extract/Synthesize; không đổi quy tắc chấm điểm; giữ nguyên tiêu đề mục 1–6 của báo cáo; không thêm st.metric hay st.title (BRIEF_M3.md mục 4.1).
- Không đọc hay in nội dung .env (chỉ kiểm có/không); không in chuỗi key ra bất cứ đâu; không xóa .cache/; không xóa file đã có trong repo; không cài công cụ toàn cục; không dùng model trả phí trong code sản phẩm.
- Không chạy lại một case nhiều lần để chọn kết quả đẹp; không viết code riêng cho câu hỏi mẫu. Case chưa đạt ghi chưa đạt, kèm nguyên nhân.
- Python: .venv\Scripts\python.exe. Commit nhỏ theo từng phần, message tiếng Anh.

4) CỔNG TỰ KIỂM (đạt mới sang phase sau; dán output vào Walkthrough)
Sau P0:
- pytest -q ra 21 passed trước khi sửa code; tag mission2-final trỏ 58a6fba; eval/results/m2/ có đủ file của TC1–TC6; golden test của _extract_date_fallback pass.
Sau P1 (CHECKPOINT 1):
- pytest -q pass toàn bộ.
- Lệnh sau ra trống: git diff --stat mission2-final -- tests/test_grade.py tests/test_verify_quote.py tests/test_score.py tests/test_pipeline_mock.py tests/test_app_ui.py research/synthesize.py research/score.py
- git diff mission2-final -- research/extract.py chỉ thêm tham số evidence_id_start, prompt không đổi.
- .venv\Scripts\python.exe -m research.recency eval\results\m2\TC2.json --as-of 2026-10-15: mức ĐÁNG KỂ; S5, S6 có date_precision "year" (hiển thị "2024 (chỉ biết năm)"), trạng thái CŨ; bỏ S5 thì I5 MẤT CĂN CỨ, bỏ S6 thì I6 MẤT CĂN CỨ.
- Cùng lệnh với TC3.json: mức KHÔNG, short_answer không có "[Độ mới dữ liệu]".
- Bảng mức ảnh hưởng 6 case khớp bảng tham chiếu ở BRIEF_M3.md mục 4.5, hoặc giải thích bằng quy tắc cho từng chỗ khác.
- Đọc lại mục 7 của TC2 như một người dùng không biết code; câu nào khó hiểu thì viết lại template cho dễ hiểu.
Sau P2 (CHECKPOINT 2):
- pytest -q pass, gồm test giao diện cũ (đúng 4 metric, TC1 hiện 100.0%).
- Bản phát lại TC2 có trace.llm_calls_count == 0; data/cached_runs/tc7_cr_a2_refreshed.json tồn tại, refresh.status hợp lệ; ghi rõ NGÀY_LÀM_MỚI.
- Đã kiểm giao diện bằng trình duyệt tích hợp, có đủ 4 ảnh chụp như BRIEF_M3.md mục 7 (CHECKPOINT 2).
Sau P3 (CHECKPOINT 3):
- git log cho thấy commit eval/cases.yaml nằm trước commit kết quả eval.
- eval/results/m2_vs_m3.md có Bảng A, B, C; TC2–TC5 trùng M2; TC6 vẫn Chưa đạt (khác thì giải thích).
- pytest -q pass sau khi cập nhật data/cached_runs/.
Sau P4:
- Có bảng "con số → file nguồn" cho mọi con số trong README.md, TESTING.md, SUBMISSION_M3.md; bỏ mọi câu nói quá dữ liệu (vd "triệt để", "hoàn toàn", "100%" khi dữ liệu không nói vậy).
P5, trước khi push:
- Lệnh này ra 0 (chỉ in số lượng, không in chuỗi key): (git log -p --all | Select-String -Pattern 'AIza[0-9A-Za-z_\-]{30,}','sk-or-v1-[0-9a-f]{20,}','tvly-[0-9A-Za-z\-]{10,}','gsk_[0-9A-Za-z]{20,}').Count
- git ls-files | Select-String '\.env' chỉ có .env.example; pytest -q pass.
P5, sau khi push:
- Chờ 2–5 phút, mở https://gamota-market-research-mvp.streamlit.app trong phiên ẩn danh của trình duyệt tích hợp (app ngủ thì bấm đánh thức, chờ khoảng 1 phút); chụp TC2 với tab "Độ mới & Ảnh hưởng" và TC7. Sau 10 phút demo vẫn chưa cập nhật thì không thử mãi: ghi vào danh sách việc tôi phải làm (kiểm nhánh deploy trên share.streamlit.io).

5) KẾT THÚC
Walkthrough cuối gồm: checklist DoD ở BRIEF_M3.md mục 10, mỗi mục tick kèm bằng chứng; Bảng A, B, C; danh sách test mới; case chưa đạt; phần đã cắt (nếu có) và lý do; nguyên văn 3 câu trả lời trong SUBMISSION_M3.md để tôi đọc duyệt; danh sách việc tôi tự làm (quay video theo kịch bản, gửi link video để cập nhật README, điền form trước 11:49 ngày 25/10). Xong P5 thì dừng, không làm thêm.

Bắt đầu ngay: in tóm tắt 5 dòng (change request, cách chứng minh bản mới tốt hơn, 3 loại test bắt buộc, những thứ phải nộp, hạn), Implementation Plan + Task List cho toàn bộ P0–P5, rồi làm luôn.
```

**Nếu phiên bị ngắt giữa chừng** (hết lượt dùng model, mất mạng, máy tắt): mở hội thoại mới và dán:

```text
Bạn tiếp tục Mission 3 đang chạy dở ở chế độ chạy một mạch. Trả lời bằng tiếng Việt có dấu. Đọc AGENTS.md, BRIEF_M3.md, và CHỈ mục 0 của PROMPTS_M3.md: prompt trong mục đó là việc tôi đã giao, áp dụng lại nguyên văn mọi quy tắc và cổng tự kiểm của nó (bỏ qua phần còn lại của PROMPTS_M3.md). Chạy: git log --oneline -20, git status --short, .venv\Scripts\python.exe -m pytest -q, Get-Date. Xác định phase và bước đang dở theo BRIEF_M3.md mục 7, ghi tóm tắt vào Walkthrough, rồi làm tiếp đến hết P5.
```

**Khi agent báo xong, bạn kiểm khoảng 10 phút trước khi quay video:**
1. Đọc Walkthrough cuối: DoD tick đủ kèm bằng chứng; đọc 3 câu trả lời, tự trình bày lại được.
2. Tự chạy `.venv\Scripts\python.exe -m pytest -q` và `git diff --stat mission2-final -- tests/test_grade.py tests/test_verify_quote.py tests/test_score.py tests/test_pipeline_mock.py tests/test_app_ui.py` (phải trống).
3. Mở link demo bằng cửa sổ ẩn danh: TC2 → tab "Độ mới & Ảnh hưởng"; bấm TC7.
4. Làm các việc agent ghi cho bạn (vd kiểm nhánh deploy), rồi chạy review chéo ở mục 10 (hoặc nhờ Claude).
5. Quay video, gửi link bằng prompt ở cuối mục 8, điền form.

## 1. Kế hoạch tổng (1 trang)

| Phase | Thời lượng | Mục tiêu xong lúc | Đầu ra chính | Điểm dừng |
|---|---|---|---|---|
| P0 | 0,5h | 23/10 ~13:30 | Tóm tắt, điểm mơ hồ, Implementation Plan + Task List. Sau khi duyệt: commit tài liệu, tag `mission2-final`, snapshot `eval/results/m2/`, golden test ngày đăng | Duyệt plan |
| P1 | 3,5h | 23/10 ~17:30 | `research/dates.py`, `research/recency.py`, mục 7 trong báo cáo, CLI `research.recency`, test change request / edge case / regression | **CHECKPOINT 1** |
| P2 | 3h | 23/10 ~21:00 | `research/refresh.py`, 1 lần làm mới chạy thật trên TC2, tab "Độ mới & Ảnh hưởng" trên giao diện | **CHECKPOINT 2** |
| P3 | 2h | 24/10 ~10:30 | Eval TC1–TC10, `eval/results/m2_vs_m3.md`, phần Mission 3 trong `TESTING.md` | **CHECKPOINT 3** |
| P4 | 1,5h | 24/10 ~12:00 | `README.md`, `SUBMISSION_M3.md` (3 câu trả lời + kịch bản video) | Bước xin phép push |
| P5 | 0,5h | 24/10 ~13:00 | Quét secrets, push, kiểm demo online | **CHECKPOINT CUỐI** |
| Tôi | | 24/10 tối → 25/10 ~11:00 | Quay video ≤ 5 phút, điền form | Hạn nộp 11:49 25/10 |

Hạn của agent: 16:00 ngày 24/10 (còn khoảng 3 giờ dự phòng). Agent chậm hơn kế hoạch quá 1 giờ: dùng prompt S3 ở mục 9.

## 2. Chuẩn bị (5 phút, trước prompt đầu tiên)
1. Mở thư mục `C:\Users\Admin\Desktop\Gamota_Mission2` trong Antigravity, tạo **hội thoại mới**, chọn model **Gemini 4 Argon**. Nếu có lựa chọn chế độ, chọn chế độ lập kế hoạch (Planning) để agent tạo Implementation Plan / Task List trước khi làm.
2. Nếu Antigravity có cài đặt duyệt lệnh terminal, để chế độ hỏi trước với lệnh nguy hiểm (`git push`, xóa file).
3. Không xóa `.cache/` (cho phép chạy lại Mission 2 từ cache để so sánh). Không mở `.env` trong cửa sổ có agent.
4. Quy tắc "không dùng `gemini-4-argon`" trong `AGENTS.md` chỉ áp cho LLM **chạy bên trong sản phẩm** (code), không áp cho agent đang code.
5. Làm các phase trong **cùng một hội thoại** để agent giữ bối cảnh. Hội thoại quá dài, agent bắt đầu quên quy tắc: mở hội thoại mới bằng prompt S9 ở mục 9.

## 3. Prompt P0 — khởi động (chỉ đọc, chưa sửa gì)

```text
Bạn là agent thực hiện Mission 3 trong repo này. Mọi trả lời và artifact (Implementation Plan, Task List, Walkthrough) viết bằng tiếng Việt có dấu.

ĐỌC THEO THỨ TỰ: AGENTS.md → BRIEF_M3.md (toàn bộ) → README.md, TESTING.md, DECISIONS.md. BRIEF.md chỉ để tra cứu quy tắc Mission 2. Bỏ qua PROMPTS_M3.md (file dành cho tôi).

QUY TẮC CHO CẢ PHIÊN LÀM VIỆC:
- Chỉ làm phase tôi giao; tới điểm dừng thì dừng hẳn, chờ tôi trả lời.
- Mọi kết quả (test, số liệu, ảnh chụp) phải từ lần chạy thật. Trong Walkthrough, dán nguyên văn các dòng output quan trọng (vd dòng cuối của pytest), không thay output bằng lời kể.
- Bất biến ở BRIEF_M3.md mục 4.1 là luật: không sửa 21 test cũ, không đổi prompt Plan/Extract/Synthesize, không đổi quy tắc chấm điểm, không đổi tiêu đề mục 1–6 của báo cáo, không thêm st.metric hay st.title. Sắp phải vi phạm thì dừng và hỏi tôi.
- Không đọc hay in nội dung .env (chỉ kiểm có/không), không xóa .cache/, không git push khi chưa hỏi tôi.
- Python: .venv\Scripts\python.exe

VIỆC P0 (chỉ đọc, chưa tạo hay sửa file nào trong repo):
1. Tóm tắt trong 5 dòng: change request A2; cách bạn sẽ chứng minh bản mới tốt hơn; 3 loại test bắt buộc; những thứ phải nộp; hạn của bạn.
2. Liệt kê tối đa 5 điểm còn mơ hồ hoặc chỗ bạn đề xuất làm khác, kèm lý do.
3. Chạy và dán kết quả:
   git status --short
   git log --oneline -3
   .venv\Scripts\python.exe -m pytest -q          (kỳ vọng: 21 passed)
   .venv\Scripts\python.exe -c "from dotenv import dotenv_values as d; v=d('.env'); print({k: bool((v.get(k) or '').strip()) for k in ['GEMINI_API_KEY','GEMINI_API_KEYS','OPENROUTER_API_KEY','TAVILY_API_KEY']})"
4. Tạo Implementation Plan và Task List cho P0–P1 theo BRIEF_M3.md mục 7.

Dừng lại chờ tôi duyệt.
```

**Soi trước khi duyệt:**
- Tóm tắt có nói đúng ý "không đổi quy tắc chấm điểm; lớp độ mới là hậu xử lý; độ tin cậy chỉ đổi khi vòng làm mới thêm bằng chứng" không.
- `pytest` ra `21 passed`; lệnh kiểm key chỉ in True/False.
- Task List P1 theo đúng thứ tự ở prompt mục 4. Có góp ý thì comment thẳng lên artifact.

## 4. Prompt P0 + P1 — thực thi tới CHECKPOINT 1

```text
Duyệt plan. Làm phần thực thi của P0, rồi làm P1 theo BRIEF_M3.md, dừng ở CHECKPOINT 1.

P0:
1. Commit các tài liệu tôi đã thêm/sửa: BRIEF_M3.md, AGENTS.md, PROMPTS_M3.md. Message: docs: add Mission 3 brief and update agent rules
2. git tag mission2-final 58a6fba   (chưa push)
3. Chép các file trong eval/results/ (không gồm thư mục con) sang eval/results/m2/. Commit: test: snapshot Mission 2 eval results as regression baseline
4. Trước khi động vào research/retrieve.py: chạy _extract_date_fallback hiện tại trên ≥ 12 mẫu (BRIEF_M3 mục 4.3), đóng băng kết quả vào tests/test_regression_m2.py::test_extract_date_fallback_golden_unchanged, chạy cho pass.

P1 — làm đúng thứ tự, xong mỗi bước chạy pytest -q:
1. Schema (mục 4.2); mọi trường mới có giá trị mặc định.
2. research/dates.py (mục 4.3, 4.4) + test_detect_data_period_patterns, test_boundary_exactly_18_months_is_not_older.
3. research/retrieve.py: _extract_date_fallback thành wrapper; điền date_method trong retrieve_and_grade_sources. Golden test phải vẫn pass.
4. config/recency_policy.yaml + research/recency.py (mục 4.5) + các test của tests/test_recency.py (mục 6.2).
5. Tích hợp research/pipeline.py, render_report_markdown (mục 7 + cột mới), tham số evidence_id_start trong research/extract.py (mục 4.6).
6. CLI python -m research.recency và cờ --reference-date của research/cli.py (cờ --refresh-old để sang P2).
7. tests/test_regression_m2.py (đủ 4 test ở mục 6.2).
8. Chạy python -m research.recency cho 6 file eval/results/m2/TC*.json với --as-of 2026-10-15, lưu JSON + MD vào eval/results/m3_offline/.
9. Ghi các mục [M3] vào DECISIONS.md. Commit theo từng phần, message tiếng Anh.

WALKTHROUGH CHECKPOINT 1 PHẢI CÓ (dán output thật):
- Dòng cuối của: .venv\Scripts\python.exe -m pytest -q
- Output của lệnh sau (phải trống):
  git diff --stat mission2-final -- tests/test_grade.py tests/test_verify_quote.py tests/test_score.py tests/test_pipeline_mock.py tests/test_app_ui.py research/synthesize.py research/score.py
- Output của: git diff mission2-final -- research/extract.py   (chỉ được thêm evidence_id_start)
- Bảng mức ảnh hưởng của 6 case, đặt cạnh bảng tham chiếu ở BRIEF_M3.md mục 4.5; case nào khác thì giải thích bằng quy tắc.
- Trích mục 7 của TC2 và TC1 trong eval/results/m3_offline/.
- Quyết định đã ghi DECISIONS.md, vấn đề gặp phải, việc còn lại.

Dừng ở CHECKPOINT 1.
```

**Soi ở CHECKPOINT 1** (tự chạy trong terminal cho chắc):
- `.venv\Scripts\python.exe -m pytest -q`: toàn bộ pass.
- `.venv\Scripts\python.exe -m research.recency eval\results\m2\TC2.json --as-of 2026-10-15`: mục 7 có S5, S6 hiện "2024 (chỉ biết năm)"; bỏ S5/S6 thì I5/I6 "MẤT CĂN CỨ"; mức "ĐÁNG KỂ".
- Cùng lệnh với `TC3.json`: mức "KHÔNG", trả lời ngắn không có `[Độ mới dữ liệu]`.
- Đọc mục 7 như một người dùng không biết code: có hiểu "nguồn nào cũ, ảnh hưởng tới nhận định nào, ra sao" không. Không hiểu thì yêu cầu sửa câu chữ trước khi sang P2.

## 5. Prompt P2 — vòng làm mới + giao diện, tới CHECKPOINT 2

```text
OK CHECKPOINT 1. Làm P2 theo BRIEF_M3.md (mục 4.7, 4.8 và các test tương ứng ở 6.2), dừng ở CHECKPOINT 2.

1. research/refresh.py + tests/test_refresh.py (LLM giả, patch retrieve_and_grade_sources, không gọi mạng) + CLI python -m research.refresh + cờ --refresh-old trong research/cli.py.
2. Chạy thật. Ghi lại ngày dùng cho --reference-date của lần làm mới, gọi là NGÀY_LÀM_MỚI (P3 sẽ dùng lại đúng ngày này để eval phát lại từ cache):
   a. Phát lại TC2 từ cache:
      .venv\Scripts\python.exe -m research.cli "Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines?" --reference-date 2026-10-15 --out-json eval\results\m3_replay\TC2.json --out-md eval\results\m3_replay\TC2.md
      Xác nhận trace.llm_calls_count == 0.
   b. Làm mới:
      .venv\Scripts\python.exe -m research.refresh eval\results\m3_replay\TC2.json --reference-date NGÀY_LÀM_MỚI --out-json data\cached_runs\tc7_cr_a2_refreshed.json --out-md data\cached_runs\tc7_cr_a2_refreshed.md
   c. Không tìm được dữ liệu mới hơn cũng là kết quả hợp lệ: ghi đúng như vậy. Không chạy lại nhiều lần để chọn kết quả đẹp.
3. Giao diện (mục 4.8) + tests/test_app_ui_m3.py. Nút TC7 phải khớp báo cáo theo stem trước, rồi mới tới câu hỏi.
4. Chạy .venv\Scripts\python.exe -m streamlit run app.py --server.headless true, kiểm bằng trình duyệt tích hợp, chụp 4 ảnh:
   (a) TC2: banner + tab "Độ mới & Ảnh hưởng", mở 1 nguồn then chốt;
   (b) TC2: chọn "Hôm nay" và danh sách thay đổi;
   (c) TC7: khối kết quả làm mới;
   (d) tab 1: khối "Mức chắc chắn của các nhận định".
   Xác nhận xem báo cáo đã lưu không gọi LLM và không tốn lượt Live.
5. pytest -q toàn bộ. Commit.

WALKTHROUGH CHECKPOINT 2: 4 ảnh chụp; kết quả làm mới thật (trạng thái tổng, truy vấn, nguồn mới được giữ và bị loại kèm lý do, bảng so sánh cũ ↔ mới, bảng độ tin cậy trước → sau, số lần gọi LLM); NGÀY_LÀM_MỚI; dòng cuối pytest; vấn đề gặp phải.

Dừng ở CHECKPOINT 2.
```

**Soi ở CHECKPOINT 2:**
- Tự chạy `.venv\Scripts\python.exe -m streamlit run app.py`; bấm TC2 → tab "Độ mới & Ảnh hưởng"; bấm TC7.
- Người dùng có hiểu vì sao một nhận định đổi mức sau vòng làm mới không (mỗi thay đổi phải có lý do và mã E#/S#).
- TC1 vẫn hiện `100.0%` ở thẻ "Trích dẫn xác minh"; vẫn đúng 4 thẻ chỉ số.

## 6. Prompt P3 — eval và so sánh, tới CHECKPOINT 3

```text
OK CHECKPOINT 2. Làm P3 theo BRIEF_M3.md mục 6.1, 6.3, 6.4, 6.5, dừng ở CHECKPOINT 3.

1. Sửa eval/run_eval.py theo mục 6.3. Bọc try/except cho từng case: lỗi (vd hết quota) thì ghi vào summary là chưa đạt kèm lý do rồi chạy tiếp case sau; không bịa kết quả.
2. Cập nhật eval/cases.yaml: thêm reference_date: "2026-10-15" cho TC1–TC6 (không đổi assertions cũ); thêm TC7–TC10 với kỳ vọng định tính + assertions; TC7 đặt refresh_reference_date bằng NGÀY_LÀM_MỚI ở P2.
   Commit eval/cases.yaml TRƯỚC khi chạy (message: test: add Mission 3 eval cases before running) để lịch sử git chứng minh kỳ vọng có trước kết quả.
3. Chạy .venv\Scripts\python.exe -m eval.run_eval (TC1–TC10, dùng cache). TC10 gọi LLM thật; hết quota thì chờ rồi chạy lại riêng TC10, hoặc ghi là chưa chạy được.
4. Viết và chạy python -m eval.compare_m2_m3 → eval/results/m2_vs_m3.json và .md.
5. Cập nhật data/cached_runs/ theo mục 6.1, giữ tên file cũ (vd tc1_sea_genres.json): TC2–TC5 lấy từ eval/results/; TC1, TC6 lấy từ eval/results/m3_offline/; tc7_cr_a2_refreshed lấy từ kết quả TC7 chính thức. Chạy lại pytest -q.
6. Thêm phần "Mission 3" vào đầu TESTING.md (mục 6.5); cập nhật DECISIONS.md. Commit.

WALKTHROUGH CHECKPOINT 3: dán Bảng A, B, C từ eval/results/m2_vs_m3.md; dòng "Kết quả: ĐẠT/CHƯA ĐẠT" của run_eval cho từng case; case chưa đạt và nguyên nhân; giải thích chỗ TC1/TC6 lệch so với M2; dòng cuối pytest.

Dừng ở CHECKPOINT 3, chờ tôi duyệt trước khi viết tài liệu.
```

**Soi ở CHECKPOINT 3:**
- Mở `eval/results/m2_vs_m3.md`: TC2–TC5 ở cột "trùng từng nhận định" phải là có; TC6 vẫn "Chưa đạt"; số trong Walkthrough khớp file.
- `git log --oneline`: commit `eval/cases.yaml` nằm **trước** commit có kết quả eval.
- Bảng B nói được điều Mission 2 không nói (vd số nguồn chỉ biết năm nhưng M2 hiển thị như tháng cụ thể, số nhận định không có bằng chứng mới).

## 7. Prompt P4 — tài liệu nộp, tới bước xin phép push

```text
OK CHECKPOINT 3. Làm P4 theo BRIEF_M3.md mục 8, rồi phần đầu của P5:

P4:
1. README.md: khối "Mission 3" ở đầu và các mục cần cập nhật theo mục 8; link video để "(cập nhật sau khi quay)".
2. SUBMISSION_M3.md: đường dẫn; 3 câu trả lời (mỗi câu 5–8 câu, ngôi thứ nhất, dẫn test ID và số liệu từ eval/results/m2_vs_m3.md); kịch bản video ≤ 5 phút (màn hình + lời nói cho từng đoạn); checklist việc tôi tự làm.
3. DECISIONS.md có đủ ≥ 5 mục [M3].
4. Tự kiểm: mọi con số trong README, TESTING.md, SUBMISSION_M3.md đều có trong eval/results/; bỏ mọi câu nói quá kết quả (vd "triệt để", "hoàn toàn", "100%" khi dữ liệu không nói vậy).
5. pytest -q, commit.

P5 (phần đầu):
6. Quét secrets, dán output. Lệnh đầu chỉ in SỐ LƯỢNG chuỗi giống key (phải là 0); nếu khác 0 thì dừng, báo tôi số lượng và commit liên quan, tuyệt đối không in chuỗi key ra:
   (git log -p --all | Select-String -Pattern 'AIza[0-9A-Za-z_\-]{30,}','sk-or-v1-[0-9a-f]{20,}','tvly-[0-9A-Za-z\-]{10,}','gsk_[0-9A-Za-z]{20,}').Count
   git ls-files | Select-String '\.env'          (chỉ được thấy .env.example)
7. Liệt kê chính xác các lệnh push sẽ chạy (nhánh master, nhánh mà app Streamlit đang deploy, tag mission2-final).

Trong Walkthrough: dán nguyên văn 3 câu trả lời và bảng "con số → file nguồn". Dừng chờ tôi cho phép push.
```

**Soi trước khi cho push:**
- Đọc 3 câu trả lời: tự trình bày lại được không; có số nào không tìm thấy trong `eval/results/` không.
- Vào https://share.streamlit.io → app `gamota-market-research-mvp` → Settings: xem app đang deploy từ nhánh nào (theo `SUBMISSION.md` là `main`).

## 8. Prompt P5 — push và kiểm demo, tới CHECKPOINT CUỐI

Thay `<NHÁNH_DEPLOY>` bằng nhánh vừa xem (thường là `main`):

```text
Được phép push. App Streamlit deploy từ nhánh <NHÁNH_DEPLOY>.
1. Chạy:
   git push origin master
   git push origin master:<NHÁNH_DEPLOY>     (bỏ qua nếu NHÁNH_DEPLOY là master)
   git push origin mission2-final
2. Chờ Streamlit Cloud tự redeploy (2–5 phút). Mở https://gamota-market-research-mvp.streamlit.app trong phiên ẩn danh của trình duyệt tích hợp (app đang ngủ thì bấm đánh thức, chờ ~1 phút). Chụp: TC2 với tab "Độ mới & Ảnh hưởng"; TC7 với khối kết quả làm mới.
3. Hoàn tất Walkthrough CHECKPOINT CUỐI: checklist DoD ở BRIEF_M3.md mục 10, mỗi mục tick kèm bằng chứng (file, lệnh, output, ảnh); danh sách việc tôi còn phải tự làm.
```

**Sau khi quay và upload video** (YouTube để Unlisted), dán:

```text
Link video Mission 3: <LINK>. Cập nhật link này vào README.md và SUBMISSION_M3.md, commit "docs: add Mission 3 video link", quét secrets như P5, rồi push lên đúng các nhánh đã push trước đó (đã được phép).
```

**Điền form trước 11:00 ngày 25/10:** GitHub repo (giữ link cũ), link demo (giữ link cũ), link video, 3 câu trả lời copy từ `SUBMISSION_M3.md`.

## 9. Prompt xử lý sự cố (dán khi gặp)

**S1 — Agent sửa test cũ, đổi prompt LLM hoặc quy tắc chấm điểm:**
```text
Dừng lại. Thay đổi ở <TÊN FILE> vi phạm BRIEF_M3.md mục 4.1. Giải thích vì sao bạn cần sửa, đề xuất cách đạt cùng mục tiêu mà không đụng file đó, và chờ tôi duyệt trước khi hoàn tác hay sửa tiếp.
```

**S2 — Báo kết quả mà không kèm output:**
```text
Với mỗi con số bạn vừa báo, dán lệnh đã chạy và vài dòng output nguyên văn. Con số nào không có output thật thì xóa khỏi Walkthrough.
```

**S3 — Chậm hơn kế hoạch quá 1 giờ:**
```text
Bạn đang chậm so với kế hoạch. Liệt kê việc còn lại kèm thời gian ước tính, đề xuất cắt theo đúng thứ tự ở BRIEF_M3.md mục 9 (không cắt phần "Không bao giờ cắt"), và ghi phần bị cắt vào README mục Hạn chế. Chờ tôi chọn.
```

**S4 — Hết quota Gemini (HTTP 429) hoặc lỗi mạng khi chạy Live:**
```text
Không đổi sang model trả phí và không bịa kết quả. Tạm dừng các lệnh gọi LLM, làm trước những việc không cần LLM (code, test, tài liệu). Thử lại sau 15–30 phút; nếu vẫn lỗi thì ghi rõ case nào chưa chạy được và vì sao trong TESTING.md.
```

**S5 — TC1/TC6 lệch M2, hoặc vòng làm mới ra kết quả "xấu":**
```text
Đây là kết quả thật. Không chạy lại để chọn kết quả đẹp và không chỉnh code riêng cho câu hỏi này. Ghi đúng kết quả, nguyên nhân và điều học được vào TESTING.md.
```

**S6 — Agent muốn làm thêm tính năng ngoài brief:**
```text
Không làm tính năng này trong Mission 3. Ghi ý tưởng vào README mục "Hạn chế đã biết và hướng cải thiện", rồi quay lại task hiện tại.
```

**S7 — Test giao diện (AppTest) chậm hoặc timeout:**
```text
Chỉ tính phân tích độ mới cho báo cáo đang xem và cache bằng st.cache_data theo run_timestamp + ngày (BRIEF_M3.md mục 4.8); không tính trước cho mọi báo cáo khi mở app. Chạy lại pytest -q.
```

**S8 — Agent làm luôn sang phase sau mà không dừng ở checkpoint:**
```text
Dừng ngay. Theo AGENTS.md, tại mỗi CHECKPOINT phải dừng hẳn chờ tôi. Liệt kê những gì bạn đã làm sau điểm dừng (file, commit) để tôi quyết định giữ hay bỏ.
```

**S9 — Mở hội thoại mới để tiếp tục (hội thoại cũ quá dài hoặc agent quên quy tắc):**
```text
Bạn tiếp tục Mission 3 đang làm dở trong repo này. Trả lời bằng tiếng Việt có dấu. Đọc AGENTS.md và BRIEF_M3.md (bỏ qua PROMPTS_M3.md), rồi chạy: git log --oneline -15, git status --short, .venv\Scripts\python.exe -m pytest -q. Tóm tắt: đã xong phase nào, đang dở bước nào (theo BRIEF_M3.md mục 7), việc còn lại. Không làm gì thêm, chờ tôi giao việc.
```

## 10. Prompt review chéo cuối (hội thoại mới, nên chọn model khác Argon)

```text
Đóng vai người chấm Gamota khó tính cho Mission 3. Đọc BRIEF_M3.md (mục 1 là đề), rồi đối chiếu với repo hiện tại:
1. Change request A2 đã được trả lời chưa: chạy .venv\Scripts\python.exe -m streamlit run app.py, mở TC2 và TC7 (chế độ Kết quả đã lưu). Người dùng có hiểu nguồn nào hơn 18 tháng, ảnh hưởng tới nhận định nào, ra sao không.
2. Chạy .venv\Scripts\python.exe -m pytest -q và .venv\Scripts\python.exe -m eval.run_eval --case TC9. Kiểm 21 test cũ không bị sửa: git diff --stat mission2-final -- tests/test_grade.py tests/test_verify_quote.py tests/test_score.py tests/test_pipeline_mock.py tests/test_app_ui.py
3. Tick từng mục DoD (BRIEF_M3.md mục 10) kèm bằng chứng cụ thể: file, lệnh, output.
4. Tìm chỗ tài liệu (README.md, TESTING.md, SUBMISSION_M3.md) nói quá so với eval/results/m2_vs_m3.md và eval/results/.
5. Quét secrets trong toàn bộ lịch sử git; mở thử mọi link trong README.
6. Liệt kê 5 vấn đề dễ bị trừ điểm nhất theo mức độ nghiêm trọng, rồi sửa những gì sửa được trong 30 phút (không push khi chưa hỏi tôi).
```
