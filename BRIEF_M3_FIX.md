# BRIEF — Gamota · Mission 3 · Đợt sửa trước khi nộp

> Bản giao việc cho AI agent (Google Antigravity, model Gemini 4 Argon). Đọc hết trước khi làm. Hôm nay là tối 23/10/2026.
>
> **Hạn nộp form: 18:00 ngày 24/10/2026** (theo trang nộp bài). Mốc 11:49 ngày 25/10 ghi trong `BRIEF_M3.md` và `SUBMISSION_M3.md` là sai. Phần việc F0–F4 của bạn phải xong trước **10:00 ngày 24/10/2026** để tôi quay lại video và nộp. F5 làm sau khi tôi gửi link video.
>
> Mọi con số ở mục 1 và bảng tham chiếu ở mục 3.7 là kết quả chạy thật trên repo tối 23/10/2026 (phát lại từ cache, chặn mạng, 0 lệnh gọi LLM), không phải ước đoán. Cũng tối 23/10, toàn bộ `eval.run_eval` (TC1–TC10) đã được chạy lại từ cache vào một thư mục nháp ngoài repo với mạng bị chặn: 0 lệnh gọi LLM ở mọi case, 12/12 file báo cáo trùng bản đang lưu (bỏ qua trường thời gian), chỉ khác `TC10.json` ở `refresh.llm_calls_count` (3 → 0, vì bản đang lưu là lần chạy thật).

## 0. Vai trò, thứ tự tài liệu, nguyên tắc

- Bạn là kỹ sư tiếp tục sản phẩm Mission 3 trong repo này. Đây là **đợt sửa ngắn trước khi nộp**, không làm lại. Tôi duyệt ở các CHECKPOINT.
- Thứ tự ưu tiên tài liệu trong đợt này: `BRIEF_M3_FIX.md` (file này) > `BRIEF_M3.md` > `AGENTS.md` > `BRIEF.md`.
  - Thay cho "P0 → P5" và "Hạn của bạn: 16:00 ngày 24/10/2026" trong `AGENTS.md`: đợt này làm F0 → F5 (mục 6), hạn 10:00 ngày 24/10/2026.
  - 8 quy tắc "Không bao giờ vi phạm" trong `AGENTS.md` giữ nguyên tuyệt đối. Vẫn hỏi tôi trước khi push, xóa file, cài công cụ toàn cục.
- Bất biến kỹ thuật ở `BRIEF_M3.md` mục 4.1 giữ nguyên. Thêm 2 bất biến cho đợt này:
  1. **Không đổi prompt của vòng làm mới** (`sys_prompt`/`usr_prompt` trong `_generate_refresh_queries`, `cmp_sys_prompt`/`cmp_usr_prompt` trong `research/refresh.py`). Khóa cache LLM gồm provider, model, tên schema và toàn văn prompt (`research/llm.py:140`). Đổi một ký tự là TC7, TC10 hết phát lại được từ cache.
  2. **Không đổi model chính** (`LLM_PROVIDER=gemini`, `gemini-3.8-flash`). Lý do ở mục 3.6.
- Không chạy lại một case nhiều lần để chọn kết quả đẹp. Mọi số trong tài liệu nộp lấy từ lần chạy của đợt này.
- Thứ tự ưu tiên khi phải đánh đổi: **đúng và trung thực > không regression > tài liệu nộp > đẹp**.
- Python: `.venv\Scripts\python.exe`. Commit nhỏ theo từng phần, message tiếng Anh. Tài liệu tiếng Việt có dấu.

## 1. Vì sao có đợt sửa này (soát trước khi nộp, 23/10)

**Đã kiểm, đang ổn:** repo public; `master` = `main` = `d2c2869`; tag `mission2-final` đã có trên GitHub; `pytest -q` ra 46 passed; 0 chuỗi giống key trong repo và lịch sử git; demo online đã có tab "3. Độ mới & Ảnh hưởng (A2)" và nút TC7, mở không cần key.

**L1. Vòng làm mới ghép nhầm phạm vi và kỳ, rồi gắn nhãn CẬP NHẬT.** Nguồn mới S13 (sensortower.com, "State of Mobile Southeast Asia 2026") nói về **toàn bộ thị trường ứng dụng** Đông Nam Á, không riêng game: trang gốc (bản cache `.cache/retrieve/page_b5d2ad8d7d798c5672d0bed2.json`) nói doanh thu tăng nhờ cả streaming video, dịch vụ tài chính và AI tạo sinh, không chỉ game.
- TC7: `E2` (S1, doanh thu IAP **game** ĐNÁ, Q1/2025, 625 triệu USD) ↔ `E29` (S13, IAP **mọi ứng dụng**, câu trích không nêu kỳ, 5,3 tỷ USD) bị gắn CẬP NHẬT. Hệ quả: thêm một ConflictItem không có thật; `I2` bị hạ TRUNG BÌNH → THẤP; sinh nhận định mới `I11` "Doanh thu IAP ở Đông Nam Á đạt 5,3 tỷ USD" trong báo cáo về game casual.
- TC10: `E2` (S1) và `E16` (S10), cùng là 1,93 tỷ lượt tải **game** Q1/2025, ↔ `E23` (S13, 18,1 tỷ lượt tải **mọi ứng dụng**, năm 2025) bị gắn CẬP NHẬT, kèm giải thích sai "tổng lượt tải game mobile cả năm 2025 là 18,1 tỷ". Hệ quả: `I4` bị hạ TRUNG BÌNH → THẤP.
- TC7 còn 2 cặp CẬP NHẬT không phải cùng một chỉ số: `E12` (IAA +4%, Q2/2024) ↔ `E34` (lời khuyên thiết kế kinh tế game, không có số); `E13` (Q2/2024) ↔ `E31`, `E32`, `E40` (mô tả xu hướng; `E32` nói về mốc 2022 và dự báo 2027).
- Nguyên nhân: `research/refresh.py:589–593` nhận nguyên nhãn LLM, chỉ đổi nhãn khi danh sách bằng chứng mới rỗng. Không có kiểm tra nào bằng code về phạm vi, thị trường, đơn vị hay kỳ.
- S13 vẫn là nguồn hạng A thật, trích dẫn khớp nguyên văn 100%. Lỗi nằm ở bước đối chiếu, không phải ở nguồn hay ở bước xác minh trích dẫn.

**L2. Nhận định mới bị trùng.** Mỗi cặp CẬP NHẬT/MÂU THUẪN sinh một nhận định mới từ bằng chứng mới đầu tiên (`research/refresh.py:669–679`). TC10 có `E2 → E23` và `E16 → E23` nên sinh `I10` và `I11` giống nhau từng chữ.

**L3. Chủ đề mâu thuẫn bị cắt giữa chữ.** `research/refresh.py:656` dùng `oev.claim[:90]`. Trả lời ngắn của TC7 đang hiện "…trong quý 1 năm 2 (" và "…doanh thu từ quản (".

**L4. Không nói rõ bản lưu là bản phát lại.** Khối làm mới của TC7 hiện "0.03s (0 LLM calls)" (`app.py:757–758`, `research/pipeline.py:563–567`) mà không nói đó là bản phát lại từ cache của lần chạy thật. Người chấm có thể nghĩ vòng làm mới không chạy thật.

**L5. Model dự phòng OpenRouter không còn tồn tại.** `DEFAULT_MODELS["openrouter"] = "google/gemini-2.0-flash-exp:free"` (`research/llm.py:28`) không còn trong danh sách `GET https://openrouter.ai/api/v1/models` (kiểm 19:10 ngày 23/10). Khi Gemini hết quota, bước dự phòng qua OpenRouter sẽ lỗi.

**L6. Tài liệu nộp.** (a) Câu 2 trong `SUBMISSION_M3.md`, ý (5) và (6), dùng chính L1, L2 làm bằng chứng "bản mới tốt hơn"; (b) hạn nộp ghi sai (11:49 25/10); (c) link video còn trống ở `README.md:8` và `SUBMISSION_M3.md:12`; (d) video cũ dài 5:09 trong khi tài liệu ghi "≤ 5 phút"; (e) 3 câu trả lời chứa Markdown (link `[...](...)`, backtick, `**`), dán vào ô form sẽ hiện thô; mỗi câu dài 2.200–2.800 ký tự.

## 2. Mục tiêu đợt sửa

**LLM đề xuất nhãn đối chiếu. Code chỉ cho phép dùng số liệu mới để xác nhận, cập nhật hay phản bác số liệu cũ khi hai bên cùng phạm vi, cùng thị trường, cùng đơn vị, và (với CẬP NHẬT, MÂU THUẪN) cùng loại kỳ. Code được hạ nhãn, không được nâng nhãn.** Mọi lần hạ nhãn hiện rõ cho người dùng, kèm nhãn gốc của LLM.

Ánh xạ điểm chấm: **C1** xử lý nguồn mâu thuẫn hoặc không tương đương; **C2** người dùng thấy vì sao một cặp bị loại; **C3** `I2` giữ đúng trạng thái "chưa có bằng chứng mới" thay vì bị coi là đã cập nhật; **C4** vòng làm mới giữ đúng bối cảnh câu hỏi về game.

## 3. Thiết kế chi tiết

### 3.1 Schema (`research/schemas.py`)
```python
class RefreshComparison(BaseModel):
    ...  # giữ nguyên các trường cũ
    llm_status: str = ""                                  # nhãn gốc LLM trả về, trước khi code kiểm tra
    guard_notes: list[str] = Field(default_factory=list)  # lý do code hạ nhãn hoặc ghi chú (tiếng Việt)
```
Có giá trị mặc định nên JSON cũ vẫn đọc được.

### 3.2 Module mới `research/comparability.py` (hàm thuần, không gọi mạng hay LLM)

| Hàm | Đầu vào | Trả về |
|---|---|---|
| `scope_category(quote, title, url)` | trích dẫn, tiêu đề, URL nguồn | `"game"` nếu khớp `GAME_RE`, ngược lại `"không rõ là game"` |
| `region_tags(quote, title)` | trích dẫn, tiêu đề | tập nhãn vùng |
| `unit_kinds(quote)` | trích dẫn | tập đơn vị |
| `has_figure(quote)` | trích dẫn | có chữ số sau khi bỏ các năm `19xx`/`20xx` |
| `period_granularity(label)` | `data_period` | `quý` (`Q1/2025`), `nửa năm` (`H1/2024`), `tháng` (`08/2024`), `năm` (`2025`), `""` (trống), `khác` |
| `check_pair(status, old_ev, old_src, new_ev, new_src, ref)` | một cặp cũ ↔ mới | danh sách lý do (rỗng = đạt) |
| `guard_comparison(cmp, ...)` | một `RefreshComparison` | bản đã kiểm tra |

Từ khóa (giữ như dưới; được thêm từ khóa nếu có lý do, nhưng kết quả bảng 3.7 phải giữ nguyên):
- `GAME_RE` (không phân biệt hoa thường): `\b(games?|gaming|gamers?|gamedev|e-?sports?|hyper-?casual|hybrid-casual|mmorpg|moba|gacha)\b|trò chơi`
- Vùng: `SEA` = `\bSEA\b` (phân biệt hoa thường) hoặc `southeast asia|south-east asia|đông nam á|\basean\b`; `ID` = `indonesia`; `PH` = `philippines`; `TH` = `thailand|thái lan`; `VN` = `vietnam|viet nam|việt nam`; `MY` = `malaysia`; `SG` = `singapore`; `KH` = `cambodia|campuchia`; `GLOBAL` = `\bglobal(ly)?\b|worldwide|toàn cầu`.
- Đơn vị: `usd` = `\$|\bUSD\b|dollars?|triệu USD|tỷ USD`; `downloads` = `download|install|lượt tải|lượt cài`; `percent` = `%|percent`; `users` = `\bplayers?\b|\busers?\b|người chơi|người dùng`.
- Nếu `data_period` của một bằng chứng trống thì tính lại bằng `detect_data_period(quote, ref=ref)` trước khi so.

Quy tắc trong `check_pair`:

| Mã | Áp dụng cho nhãn LLM | Không đạt khi | Lý do ghi vào `guard_notes` (mẫu) |
|---|---|---|---|
| P | XÁC NHẬN, CẬP NHẬT, MÂU THUẪN | `scope_category` hai bên khác nhau | `khác phạm vi (game ↔ không rõ là game)` |
| T | XÁC NHẬN, CẬP NHẬT, MÂU THUẪN | cả hai bên có nhãn vùng và không giao nhau | `khác thị trường (ID ↔ TH)` |
| Đ | CẬP NHẬT, MÂU THUẪN | một bên không có số | `một bên không có số liệu để so` |
| Đ | CẬP NHẬT, MÂU THUẪN; XÁC NHẬN khi cả hai bên có số | không có đơn vị chung | `khác đơn vị (usd ↔ downloads)` |
| K | CẬP NHẬT, MÂU THUẪN | một bên không xác định được kỳ | `không xác định được kỳ số liệu (Q1/2025 ↔ ?)` |
| K | CẬP NHẬT, MÂU THUẪN | khác loại kỳ | `khác loại kỳ (Q1/2025 ↔ 2025)` |
| K | CẬP NHẬT | kỳ mới không muộn hơn kỳ cũ (so `data_period_end`) | `kỳ mới không mới hơn kỳ cũ (Q1/2025 ↔ Q1/2025)` |
| K | MÂU THUẪN | hai nhãn kỳ khác nhau | `khác kỳ (2024 ↔ 2025), không phải mâu thuẫn cùng kỳ` |

Ghi chú không hạ nhãn: XÁC NHẬN mà hai bên đều có kỳ và kỳ mới không muộn hơn kỳ cũ thì giữ XÁC NHẬN, thêm ghi chú `E31: nhắc lại số liệu Q1/2025, không phải dữ liệu mới hơn`.

`guard_comparison`:
- Luôn gán `llm_status` bằng nhãn LLM gốc.
- Chỉ xét XÁC NHẬN, CẬP NHẬT, MÂU THUẪN. KHÔNG TƯƠNG ĐƯƠNG và KHÔNG TÌM THẤY DỮ LIỆU MỚI giữ nguyên.
- Kiểm từng bằng chứng mới. Đạt thì giữ. Không đạt thì ghi `"<id>: <lý do 1>; <lý do 2>"` vào `guard_notes`.
- Còn ít nhất 1 bằng chứng đạt: giữ nhãn, `new_evidence_ids` chỉ còn các id đạt.
- Không còn bằng chứng nào đạt: đổi nhãn thành KHÔNG TƯƠNG ĐƯƠNG. `new_evidence_ids` giữ danh sách LLM đề xuất để người dùng thấy cặp nào đã bị loại (bước 6 không dùng các id này vì nhãn đã là KHÔNG TƯƠNG ĐƯƠNG).
- Bất biến (phải có test): không bao giờ thêm id; không bao giờ đổi qua lại giữa XÁC NHẬN, CẬP NHẬT, MÂU THUẪN; không bao giờ đổi KHÔNG TƯƠNG ĐƯƠNG hay KHÔNG TÌM THẤY DỮ LIỆU MỚI thành nhãn khác.

### 3.3 Tích hợp vào `research/refresh.py`
1. Sau khi dựng xong `comparisons` (vòng lặp ở dòng 601–613), trước bước 6: chạy `guard_comparison` cho từng phần tử. Bằng chứng cũ lấy từ `ev_map`, `src_map`; bằng chứng mới lấy từ `new_ev_map`, `new_src_map`.
2. Bước 6, khử trùng nhận định mới: chỉ tạo nhận định mới khi chưa có nhận định mới nào dùng đúng tập `new_evidence_ids` này, và không có nhận định nào (cũ hay mới) trùng `statement` sau khi chuẩn hóa khoảng trắng và chữ thường. ConflictItem và cờ `has_conflict` vẫn xử lý như cũ.
3. Chủ đề ConflictItem: thay `oev.claim[:90]` bằng `_truncate_words(oev.claim, 16)`.
4. Với mỗi cặp bị code hạ nhãn: thêm 1 dòng vào `gaps` (không trùng): `[Vòng làm mới <ngày>] <E cũ> (<S cũ>): bằng chứng mới <id> chưa so được với số liệu cũ (<lý do rút gọn>); số liệu cũ chưa được cập nhật.`
5. Ghi chú khuyến nghị (`rec_parts`): khi có ít nhất 1 cặp bị hạ, thêm mệnh đề `code hạ <n> cặp đối chiếu xuống KHÔNG TƯƠNG ĐƯƠNG (<các E cũ>) vì khác phạm vi, đơn vị hoặc kỳ`.
6. Không đổi gì khác: cách chọn nguồn mục tiêu, lọc nguồn mới, trích xuất, `finalize_with_recency`, cách tính `confidence_changes`.

### 3.4 Hiển thị (`app.py`, `research/pipeline.py` mục 7.5)
- Bảng đối chiếu có 6 cột: `Bằng chứng cũ` · `Bằng chứng mới` · `Nhãn LLM` · `Kết quả sau kiểm tra code` · `Lý do kiểm tra code` (`—` nếu không có) · `Giải thích của LLM`. Ở dòng bị hạ nhãn, cột giải thích mở đầu bằng `(LLM, đã bị code bác bỏ)` để người đọc không lấy câu sai của LLM làm kết luận.
- Dưới bảng, một dòng chú thích: code chỉ hạ nhãn, không nâng; liệt kê 4 nhóm quy tắc P, T, Đ, K.
- Dòng tiêu đề khối làm mới: nếu `llm_calls_count == 0` và trạng thái khác `KHÔNG CẦN LÀM MỚI` thì thêm `(phát lại từ cache của lần chạy thật, 0 lệnh gọi LLM mới)`. Làm tương tự ở Markdown mục 7.5.
- Không thêm nút, không đổi 7 nút chọn nhanh, không thêm `st.metric` hay `st.title`.

### 3.5 Model dự phòng (`research/llm.py`, `.env.example`)
- Ở nhánh OpenRouter trong `_raw_completion`: `or_model = self.model if self.provider == "openrouter" else _get_secret("OPENROUTER_MODEL", DEFAULT_MODELS["openrouter"])`.
- Đổi `DEFAULT_MODELS["openrouter"]` sang một model **free có hỗ trợ `response_format`** (code gửi `response_format: json_object`) đang có trong danh sách ngày 23/10. Thử lần lượt: `google/gemma-4-31b-it:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `nvidia/nemotron-3.5-super-vl:free`. Với mỗi model, gọi thử **1 lần** qua `_call_openai_compatible` với một prompt JSON nhỏ (vd schema `RefreshQueriesLLMOutput`, câu hỏi giả), không ghi cache, không in key. Chọn model đầu tiên trả JSON hợp lệ. Ghi kết quả thử (model, hợp lệ hay không, thời gian) vào Walkthrough và `DECISIONS.md`.
- Không chọn: `nvidia/nemotron-3-ultra-550b-a55b:free`, `nvidia/nemotron-3.5-lightning:free` (danh sách không ghi hỗ trợ `response_format`); `poolside/laguna-s-2.1:free` (model lập trình, OpenRouter báo gỡ ngày 31/10/2026); `openrouter/free` (tự chọn model ngẫu nhiên, không tái lập được).
- `.env.example`: thêm dòng `OPENROUTER_MODEL=` kèm chú thích; không có giá trị key nào.
- Khóa cache dùng provider và model chính (`gemini`), nên đổi model dự phòng **không** làm trượt cache.

### 3.6 Không đổi model chính (ghi `DECISIONS.md`)
- MiniMax M3.1 Flash (`minimax/minimax-m3.1-flash`) đang **tính phí** trên OpenRouter: 0,15 USD mỗi 1 triệu token đầu vào, 0,60 USD mỗi 1 triệu token đầu ra (API ngày 23/10), không có bản `:free`. Dùng nó vi phạm quy tắc 4 của `AGENTS.md`.
- Kể cả model free (Nemotron, Gemma…): đổi model chính làm trượt toàn bộ cache LLM, mất khả năng phát lại TC1–TC10 và mất phép so hồi quy với Mission 2 (TC2–TC5 trùng 100%). Model free trên OpenRouter còn bị giới hạn số lượt gọi. Vì vậy model free chỉ làm dự phòng (3.5).

### 3.7 Bảng tham chiếu (nguyên mẫu đã chạy thật tối 23/10)
Cách chạy: phát lại `refresh_old_sources(<TCx>_before_refresh.json, reference_date=2026-10-23, use_cache=True)` với mạng và LLM thật bị chặn; áp quy tắc 3.2 lên nhãn LLM rồi để code chạy tiếp như cũ. Trước khi áp quy tắc, bản phát lại **trùng 100%** bản đã lưu (số nhãn từng loại, thay đổi độ tin cậy, trả lời ngắn), 0 lệnh gọi LLM. Nguyên mẫu đã chạy lần hai với đúng đặc tả 3.2 (`SEA` phân biệt hoa thường, tính lại kỳ khi trống, ghi chú "nhắc lại", quy tắc MÂU THUẪN): kết quả không đổi.

**TC7** (`eval/results/TC7_before_refresh.json`, làm mới ngày 2026-10-23):

| Cặp | Nhãn LLM | Sau kiểm tra code | Lý do |
|---|---|---|---|
| E1 → — | KHÔNG TƯƠNG ĐƯƠNG | KHÔNG TƯƠNG ĐƯƠNG | (LLM tự gắn) |
| E3 → E35 | XÁC NHẬN | XÁC NHẬN | — |
| E2 → E29 | CẬP NHẬT | **KHÔNG TƯƠNG ĐƯƠNG** | khác phạm vi (game ↔ không rõ là game); không xác định được kỳ (Q1/2025 ↔ ?) |
| E4 → — | KHÔNG TƯƠNG ĐƯƠNG | KHÔNG TƯƠNG ĐƯƠNG | (LLM tự gắn) |
| E12 → E34 | CẬP NHẬT | **KHÔNG TƯƠNG ĐƯƠNG** | E34 không có số liệu; không xác định được kỳ (Q2/2024 ↔ ?) |
| E13 → E31, E32, E40 | CẬP NHẬT | **KHÔNG TƯƠNG ĐƯƠNG** | E31: không xác định được kỳ; E32: khác loại kỳ (Q2/2024 ↔ 2022); E40: không có số liệu, không xác định được kỳ |
| E11 → E31, E34, E40 | XÁC NHẬN | XÁC NHẬN | — |

Tổng TC7, trước → sau: nhãn `2 XN / 3 CN / 0 MT / 2 KTĐ` → `2 XN / 0 CN / 0 MT / 5 KTĐ` (3 do code hạ). ConflictItem 4 → 1 (chỉ còn "Doanh thu IAP game di động tại Đông Nam Á" có từ Mission 2). Nhận định 13 → 10 (không còn I11–I13). Thay đổi độ tin cậy 5 → 1: chỉ còn `I5: THẤP → TRUNG BÌNH`; `I2` giữ TRUNG BÌNH. Ghi chú độ mới trong trả lời ngắn: "6/10 nhận định chưa có bằng chứng mới trong 18 tháng gần đây (I2, I3, I4, I6, I9, I10); 2 nhận định dựa một phần vào dữ liệu cũ". Trạng thái vẫn `ĐÃ LÀM MỚI` (S1 được xác nhận qua E3, S5 qua E11). Ghi chú khuyến nghị: "đã xác nhận thêm bằng chứng mới cho I1, I5".

**TC10** (`eval/results/TC10_before_refresh.json`, làm mới ngày 2026-10-23):

| Cặp | Nhãn LLM | Sau kiểm tra code | Lý do hoặc ghi chú |
|---|---|---|---|
| E2 → E23 | CẬP NHẬT | **KHÔNG TƯƠNG ĐƯƠNG** | khác phạm vi (game ↔ không rõ là game); khác loại kỳ (Q1/2025 ↔ 2025) |
| E16 → E23 | CẬP NHẬT | **KHÔNG TƯƠNG ĐƯƠNG** | như trên |
| E3 → E31 | XÁC NHẬN | XÁC NHẬN | ghi chú: E31 nhắc lại số liệu Q1/2025 |
| E17 → E31 | XÁC NHẬN | XÁC NHẬN | ghi chú: E31 nhắc lại số liệu Q1/2025 |
| E4 → E34 | XÁC NHẬN | XÁC NHẬN | — |
| E18 → E34 | XÁC NHẬN | XÁC NHẬN | — |
| E19 → — | KHÔNG TƯƠNG ĐƯƠNG | KHÔNG TƯƠNG ĐƯƠNG | (LLM tự gắn) |

Tổng TC10, trước → sau: nhãn `4 XN / 2 CN / 0 MT / 1 KTĐ` → `4 XN / 0 CN / 0 MT / 3 KTĐ` (2 do code hạ). ConflictItem 2 → 0. Nhận định 11 → 9 (không còn I10, I11 trùng nhau). Thay đổi độ tin cậy 3 → 0 (`I4` giữ TRUNG BÌNH). Ghi chú độ mới: "2/9 nhận định chưa có bằng chứng mới (I4, I5); 4 nhận định dựa một phần vào dữ liệu cũ". Trạng thái vẫn `ĐÃ LÀM MỚI`.

Bản cài đặt của bạn phải ra **đúng nhãn cuối, đúng số lượng, đúng thay đổi độ tin cậy** như trên; câu chữ lý do có thể khác. Các dòng `gaps` và mệnh đề khuyến nghị ở 3.3 (mục 4–5) là phần thêm mà nguyên mẫu chưa có. Lệch ở chỗ nào khác: dừng lại, giải thích nguyên nhân ở checkpoint.

## 4. Phạm vi

### 4.1 Làm (theo thứ tự ưu tiên)
1. Chốt chặn đối chiếu (3.1–3.3) và test.
2. Khử trùng nhận định mới, cắt chủ đề theo từ.
3. Chạy lại eval từ cache, cập nhật bản lưu TC7, Bảng C và Bảng D.
4. Hiển thị minh bạch (3.4).
5. Model dự phòng (3.5).
6. Tài liệu nộp, bản văn bản thuần cho form, kịch bản video (mục 7).

### 4.2 Chủ động không làm (ghi `DECISIONS.md`)
- Không sửa prompt đối chiếu để "nhắc LLM cẩn thận hơn": trượt cache, kết quả không tái lập, và LLM vẫn có thể sai. Phải có chốt chặn bằng code.
- Không cho code tự nâng nhãn hay tự gán CẬP NHẬT.
- Không đổi model chính (3.6).
- Không sửa lớp xác định ngày đăng (ví dụ: trang S13 ghi "May 2026" ở dòng tác giả nhưng hệ thống chỉ biết năm 2026). Ghi vào mục Hạn chế và Câu 3.
- Không gọi LLM thật cho TC1–TC10; chỉ phát lại từ cache.
- Không thêm TC10 vào giao diện (giữ 7 nút như cũ).

## 5. Kiểm thử

### 5.1 Regression
- 21 test của Mission 2: không sửa, phải pass.
- 25 test item của Mission 3: phải pass. Ngoại lệ duy nhất được phép sửa là fixture của `tests/test_refresh.py::test_refresh_update_adds_conflict_and_new_insight`: đổi câu trích dẫn mới từ `"In 2026, hybrid monetization growth in Indonesia slowed to 12% ..."` sang `"In 2025, ..."` (cả `raw_text` lẫn `quote`). Lý do: ở ngày tham chiếu 23/10/2026, `detect_data_period` không coi "2026" là kỳ đã kết thúc nên trả rỗng (đã chạy thử), và quy tắc K sẽ hạ nhãn. Với "In 2025", test vẫn kiểm đúng một CẬP NHẬT hợp lệ (2024 → 2025, cùng game, cùng Indonesia, cùng %). Ghi vào `DECISIONS.md`. Không được nới quy tắc để test cũ qua.

### 5.2 Test mới (tối thiểu 8; `tests/test_comparability.py` và bổ sung `tests/test_refresh.py`)

| # | Test | Loại |
|---|---|---|
| 1 | Cặp thật TC7 `E2` ↔ `E29` (trích dẫn, tiêu đề, URL thật của S1, S13): CẬP NHẬT → KHÔNG TƯƠNG ĐƯƠNG; lý do có "khác phạm vi" và "không xác định được kỳ" | Change request |
| 2 | Cặp thật TC10 `E16` ↔ `E23`: → KHÔNG TƯƠNG ĐƯƠNG; lý do có "khác loại kỳ (Q1/2025 ↔ 2025)" | Change request |
| 3 | Cập nhật hợp lệ (cùng game, cùng Indonesia, cùng USD, Q1/2025 → Q1/2026): giữ CẬP NHẬT | Edge case |
| 4 | Một cặp có 2 bằng chứng mới, 1 đạt 1 không: giữ nhãn với id đạt, có ghi chú cho id bị loại | Edge case |
| 5 | Bất biến không nâng nhãn (parametrize): KTĐ, KTT giữ nguyên; XN không thành CN; không thêm id | Regression |
| 6 | MÂU THUẪN khác kỳ (2024 ↔ 2025) → KHÔNG TƯƠNG ĐƯƠNG | Edge case |
| 7 | XÁC NHẬN cùng kỳ Q1/2025: giữ XÁC NHẬN, có ghi chú "nhắc lại" | Edge case |
| 8 | `refresh_old_sources` với 2 cặp CẬP NHẬT hợp lệ cùng trỏ 1 bằng chứng mới: chỉ sinh 1 nhận định mới | Regression (L2) |
| 9 | Chủ đề ConflictItem không bị cắt giữa từ | Regression (L3) |
| 10 | `OPENROUTER_MODEL` ghi đè được model dự phòng; mặc định khác `google/gemini-2.0-flash-exp:free` (giả lập `_call_gemini` lỗi, bắt tên model ở `_call_openai_compatible`, không gọi mạng) | Regression (L5) |

### 5.3 Eval và so sánh
**Chạy phát lại có chặn.** Mọi lần phát lại (`research.refresh`) và chạy eval (`eval.run_eval`) trong đợt này đều chạy qua một script nhỏ đặt ở thư mục tạm **ngoài repo**. Script thêm thư mục repo vào `sys.path`, gán `socket.socket.connect` và `research.llm.LLMClient._raw_completion` thành hàm ném lỗi, đặt `sys.argv`, rồi mới gọi `research.refresh.main()` hoặc `eval.run_eval.main()`. Khi đó trượt cache sẽ thành lỗi rõ ràng thay vì gọi LLM hay mạng thật. Nguyên mẫu tối 23/10 đã chạy đúng cách này. Ngoại lệ duy nhất cần mạng là lần gọi thử model dự phòng ở 3.5.

1. **Trước khi sửa code:** chép sang `eval/results/m3_before_fix/` (giữ nguyên tên): `TC7.*`, `TC7_before_refresh.*`, `TC10.*`, `TC10_before_refresh.*`, `summary.json`, `m2_vs_m3.*`, và `data/cached_runs/tc7_cr_a2_refreshed.*`. Commit riêng: `chore(eval): snapshot M3 results before comparability fix`. Đồng thời chép toàn bộ `eval/results/TC*.json` ra một thư mục tạm **ngoài repo** để so ở bước 3.
2. **Sau khi sửa code:** chạy lại toàn bộ `python -m eval.run_eval` (phát lại từ cache). Cổng kiểm: mọi case có `trace.llm_calls_count == 0`; TC7, TC10 có thêm `refresh.llm_calls_count == 0`. Case nào > 0 (trượt cache): dừng, không giữ output của case đó (`git checkout -- <file>`), báo tôi.
3. Bằng một đoạn Python ngắn, so từng `eval/results/TC*.json` mới với bản ở thư mục tạm, bỏ qua các trường thời gian chạy (`run_timestamp`, `duration_seconds`, `refreshed_at`, `refresh_timestamp`, `parent_run_timestamp`, `step_logs`). Kỳ vọng: TC1–TC6, TC8, TC9 và hai file `*_before_refresh` **trùng hoàn toàn**; chỉ `TC7.json`, `TC10.json` đổi, theo đúng bảng 3.7. Riêng `TC10.json` còn đổi `refresh.llm_calls_count` từ 3 về 0: bản đang lưu là lần chạy thật, bản mới phát lại đúng các lệnh gọi đó từ cache. Đây là khác biệt dự kiến, không phải lỗi. Dán output vào Walkthrough.
4. `eval/compare_m2_m3.py`: Bảng C thêm cột "Cặp bị code hạ nhãn". Thêm **Bảng D — Trước/sau đợt sửa** cho TC7, TC10 (đọc `eval/results/m3_before_fix/` và kết quả hiện tại): số nhãn từng loại, số ConflictItem, số nhận định, danh sách thay đổi độ tin cậy. Chạy `python -m eval.compare_m2_m3`.
5. Chép `eval/results/TC7.json`, `TC7.md` sang `data/cached_runs/tc7_cr_a2_refreshed.json`, `.md` (giữ tên file).
6. Mở giao diện bằng trình duyệt tích hợp của Antigravity: TC7 tab 3 có bảng 6 cột; dòng E2 ↔ E29 hiện KHÔNG TƯƠNG ĐƯƠNG kèm lý do; tiêu đề khối có "phát lại từ cache"; trả lời ngắn TC7 không còn cụm bị cắt; ở TC2, nút "Xem bản đã làm mới" vẫn chạy.

### 5.4 `TESTING.md`
Thêm mục **"Đợt sửa trước khi nộp (23–24/10/2026)"**: lỗi L1–L5 kèm bằng chứng; cách phát hiện (tự soát trước khi nộp); cách sửa; bảng test mới (loại, kết quả); Bảng D; output cổng kiểm 5.3. Cập nhật mục TC7, TC10 theo kết quả mới (Đạt/Chưa đạt, "Điều học được"), cập nhật mọi chỗ ghi số test (46 passed). Ghi rõ: TC7, TC10 sau sửa là phát lại từ cache các câu trả lời LLM của lần chạy thật ngày 23/10 rồi áp chốt chặn bằng code, nên `refresh.llm_calls_count = 0`. Không xóa kết quả cũ: ghi "trước đợt sửa" kèm đường dẫn `eval/results/m3_before_fix/`.

## 6. Kế hoạch và checkpoint (~5,5 giờ)

| Phase | Việc | Giờ gợi ý |
|---|---|---|
| **F0** (0,5h) | Đọc file này, `AGENTS.md`, `research/refresh.py`, `research/schemas.py`, `research/dates.py` (`detect_data_period`), `research/llm.py`, `tests/test_refresh.py`. Chạy `pytest -q` (kỳ vọng 46 passed). Chạy `research.refresh eval/results/TC7_before_refresh.json --reference-date 2026-10-23 --out-json <thư mục tạm ngoài repo>\tc7.json` qua script chặn ở đầu mục 5.3, tương tự với TC10: xác nhận tái tạo bản đã lưu (TC7: 2 XN / 3 CN / 2 KTĐ, 5 thay đổi; TC10: 4 XN / 2 CN / 1 KTĐ, 3 thay đổi; 0 lệnh gọi LLM). Commit `BRIEF_M3_FIX.md` (`docs(m3): add pre-submission fix brief`). Làm 5.3.1. Implementation Plan và Task List, rồi vào F1 luôn. | 19:45–20:15 |
| **F1** (2h) | 3.1–3.3, 3.5; test 5.1–5.2; chạy lại 2 lệnh refresh của F0 và so với bảng 3.7. **→ CHECKPOINT 1:** output `pytest`; bảng nhãn LLM → nhãn cuối của TC7, TC10 so với 3.7; kết quả gọi thử model dự phòng; các mục đã ghi `DECISIONS.md`. Dừng chờ tôi. | 20:15–22:15 |
| **F2** (1h) | 3.4; 5.3.2–5.3.6. **→ CHECKPOINT 2:** output cổng kiểm eval (số lệnh gọi LLM từng case, kết quả so trùng); Bảng C, D; ảnh chụp tab 3 của TC7 (bảng đối chiếu, tiêu đề khối làm mới) và trả lời ngắn TC7. Dừng chờ tôi. | 22:15–23:30 |
| **F3** (1,5h) | Tài liệu nộp (mục 7). **→ CHECKPOINT 3:** toàn văn `SUBMISSION_M3_FORM.txt` kèm số ký tự, kịch bản video, diff tài liệu. Dừng chờ tôi. | sáng 24/10, 07:30–09:00 |
| **F4** (0,5h) | Quét secrets như `BRIEF_M3.md` P5 (lệnh chỉ in số lượng, phải ra 0; `git ls-files` chỉ có `.env.example`). Hỏi tôi rồi mới push `master` và `master:main`. Chờ Streamlit redeploy, mở link bằng phiên ẩn danh trong trình duyệt tích hợp, kiểm lại 5.3.6 trên bản online. **→ CHECKPOINT CUỐI:** DoD (mục 9) kèm bằng chứng. | 09:00–10:00 |
| **F5** (15 phút) | Khi tôi gửi link video: điền vào `README.md`, `SUBMISSION_M3.md`, `SUBMISSION_M3_FORM.txt`; commit; hỏi tôi rồi push. | sau khi tôi quay xong |

Tôi quay video 10:00–12:00 và nộp form trước 15:00 (còn 3 giờ dự phòng). Chậm hơn kế hoạch quá 1 giờ: báo tôi và đề xuất cắt theo mục 8.

## 7. Tài liệu nộp

**`SUBMISSION_M3.md`**
- Mục 1: giữ link repo, tag, demo; link video để "(cập nhật sau khi quay)"; thêm dòng "Hạn nộp: 18:00 ngày 24/10/2026".
- **Câu 1** (≤ 1.800 ký tự khi bỏ Markdown): giữ các ý (1)–(6) hiện có, viết gọn lại; thêm 1 ý: khi tự soát trước khi nộp, tôi phát hiện bước đối chiếu do LLM gắn nhãn ghép nhầm phạm vi, và chọn sửa bằng chốt chặn trong code thay vì sửa prompt (giữ khả năng phát lại; LLM vẫn có thể sai).
- **Câu 2** (≤ 2.000 ký tự): khác biệt lớn nhất là độ tin cậy được tính lại theo tuổi dữ liệu bằng code, và vòng làm mới chỉ dùng số liệu mới khi so được với số cũ. Bằng chứng (chỉ lấy số từ lần chạy của đợt này):
  - Bảng B: 4/6 case ĐÁNG KỂ, 15 lượt nguồn then chốt cũ, 22/52 nhận định thiếu bằng chứng mới, trả lời ngắn có ghi chú tuổi dữ liệu từ 0/6 lên 4/4 case ĐÁNG KỂ.
  - TC2 phản thực tế: bỏ S5 hoặc S6 thì I5, I6 mất căn cứ; nếu S5 còn mới thì I4 từ THẤP lên CAO.
  - TC7 sau sửa: 6 nguồn mới, 12 trích dẫn mới, 40/40 khớp; 2 cặp xác nhận, I5 từ THẤP lên TRUNG BÌNH; code chặn 3 cặp, trong đó 5,3 tỷ USD là IAP của mọi ứng dụng cả năm nên không thay được 625 triệu USD IAP game Q1/2025, và I2 không bị hạ oan.
  - TC10: code chặn 2 cặp (18,1 tỷ lượt tải mọi ứng dụng ↔ 1,93 tỷ lượt tải game Q1/2025); 4 cặp xác nhận; không nhận định nào đổi mức.
  - Hồi quy: TC2–TC5, TC9 trùng 100% với Mission 2; số test pass mới; Bảng D trước/sau đợt sửa.
- **Câu 3** (≤ 1.800 ký tự): rủi ro (1) độ chính xác ngày đăng và kỳ số liệu trên web mở (24/72 nguồn chỉ biết năm hoặc không rõ ngày; ví dụ S13 ghi "May 2026" mà hệ thống chỉ biết năm); (2) chốt chặn đối chiếu dựa trên từ khóa, có thể bỏ sót khác biệt phạm vi tinh vi hoặc chặn nhầm một cập nhật hợp lệ ghi kỳ không chuẩn; (3) dữ liệu sau tường phí (TC6). Thứ tự xử lý: (1) thêm nguồn metadata ngày (Tavily `published_date`, JSON-LD `datePublished`/`dateModified`, HTTP `Last-Modified`, dòng tác giả) rồi đối chiếu chéo; (2) cho chuyên viên xác nhận ngày và phạm vi ngay trên giao diện, lưu vào bộ nhớ đã duyệt; (3) đầu đọc CSV/PDF xuất từ tài khoản Sensor Tower, AppMagic của Gamota.
- **Kịch bản video** ≤ 4:45 (mục tiêu 4:30), tổng lời nói khoảng 650 từ trở xuống, mỗi đoạn ghi màn hình cần quay và lời nói:
  - `0:00–0:25` Change request A2; TC2 bản Mission 2 (file `eval/results/m2/TC2.md` hoặc tag `mission2-final`): S5, S6 hiện `2024-06`, trả lời ngắn không nhắc tuổi dữ liệu.
  - `0:25–1:30` TC2 bản Mission 3: banner, ghi chú trong trả lời ngắn, tab 3 (7.1 cách xác định ngày và kỳ số liệu; 7.2 "nếu bỏ / nếu còn mới"); bấm 1 link trích dẫn tô sáng.
  - `1:30–2:30` TC7 vòng làm mới: truy vấn, nguồn mới S13–S18, mã E29–E40 nối tiếp; bảng đối chiếu có cột "Nhãn LLM" và "Kết quả sau kiểm tra code": dừng ở dòng E2 ↔ E29 và đọc lý do; E11 được xác nhận nên I5 lên TRUNG BÌNH; I2 vẫn "chưa có bằng chứng mới".
  - `2:30–3:15` Trường hợp biên TC1, TC4; chuyển ngày tham chiếu sang "Hôm nay"; thử giả định ngày đăng.
  - `3:15–4:00` Kiểm thử: `pytest` (số mới), Bảng A, B, C, D; nói rõ lỗi tự phát hiện khi soát và các test đã thêm.
  - `4:00–4:30` Rủi ro còn lại và thứ tự xử lý.
- Checklist cho tôi: hạn 18:00 24/10; tải video lên YouTube chế độ Không công khai, mở thử bằng cửa sổ ẩn danh; gửi link cho agent (F5); dán link và 3 câu từ `SUBMISSION_M3_FORM.txt` vào form.

**`SUBMISSION_M3_FORM.txt` (mới):** văn bản thuần để dán vào form. Không Markdown, không backtick, không `**`, không link dạng `[...](...)`; được viết tên file dạng thường (vd research/refresh.py); cần link thì dùng URL đầy đủ trên GitHub. Ba khối "Câu 1.", "Câu 2.", "Câu 3.", nội dung giống `SUBMISSION_M3.md`. Cuối file ghi số ký tự từng câu, đếm bằng code. Cổng kiểm: số lần xuất hiện của `[`, `](`, dấu backtick và `**` trong file đều bằng 0.

**`README.md`:** khối Mission 3 thêm 1 gạch đầu dòng về chốt chặn đối chiếu; bảng trước/sau lấy số mới từ Bảng B, C; mục Hạn chế thêm rủi ro của chốt chặn dựa trên từ khóa; phần 3 câu trả lời Mission 3 đồng bộ với `SUBMISSION_M3.md`; link video giữ "(cập nhật sau khi quay)" tới F5.

**`DECISIONS.md`:** tối thiểu 6 mục `[M3-FIX]`, dạng bối cảnh → quyết định → lý do: code chỉ hạ nhãn; không đổi prompt để còn phát lại cache; hiện nhãn và giải thích gốc của LLM (đánh dấu khi bị bác bỏ); khử trùng nhận định mới; sửa fixture "In 2026" → "In 2025"; model dự phòng và `OPENROUTER_MODEL`; không đổi model chính; snapshot trước sửa.

## 8. Thiếu giờ thì cắt theo thứ tự
1. Ghi chú "nhắc lại số liệu kỳ cũ" cho XÁC NHẬN cùng kỳ.
2. Dòng `gaps` cho từng cặp bị hạ và mệnh đề trong ghi chú khuyến nghị (3.3 mục 4–5).
3. Bảng D tự sinh trong `compare_m2_m3` (thay bằng bảng viết từ output script, vẫn phải là số chạy thật).
4. Cột "Nhãn LLM" tách riêng trên giao diện (gộp vào cột lý do).
5. Model dự phòng (ghi vào mục Hạn chế).

**Không bao giờ cắt:** chốt chặn đối chiếu và test 1, 2, 5; khử trùng nhận định mới; cắt chủ đề theo từ; chạy lại eval từ cache và cập nhật bản lưu TC7; Câu 2, Câu 3 và `SUBMISSION_M3_FORM.txt`; `TESTING.md`, `README.md`, `DECISIONS.md`; quét secrets; kiểm tra demo sau khi push.

## 9. Tiêu chí hoàn thành (DoD)
- [ ] `pytest`: 21 test Mission 2 pass, không sửa; mọi test Mission 3 pass (chỉ sửa đúng fixture ở 5.1); có ≥ 8 test mới.
- [ ] Phát lại TC7, TC10 khớp bảng 3.7 (nhãn cuối, số lượng, thay đổi độ tin cậy); chỗ khác đã giải thích.
- [ ] Chạy lại toàn bộ eval từ cache: mọi case 0 lệnh gọi LLM; TC1–TC6, TC8, TC9 trùng bản trước ngoài trường thời gian; TC2–TC5, TC9 vẫn trùng Mission 2.
- [ ] `data/cached_runs/tc7_cr_a2_refreshed.*` lấy từ TC7 mới; trả lời ngắn TC7 không còn cụm bị cắt; không còn ConflictItem "Số liệu cũ ↔ mới" cho E2 ↔ E29.
- [ ] Giao diện: bảng đối chiếu có nhãn LLM, kết quả sau kiểm tra code, lý do; tiêu đề khối nói rõ phát lại từ cache; đã kiểm bằng trình duyệt tích hợp (có ảnh chụp), cả bản local lẫn bản online sau push.
- [ ] Model dự phòng: `OPENROUTER_MODEL` hoạt động; mặc định là model free có trong danh sách ngày 23/10; kết quả gọi thử đã ghi.
- [ ] Tài liệu: `SUBMISSION_M3.md` (hạn 18:00 24/10, Câu 1–3 mới, kịch bản ≤ 4:45); `SUBMISSION_M3_FORM.txt` (văn bản thuần, có số ký tự, 0 ký tự Markdown); `TESTING.md` (mục đợt sửa, Bảng D); `README.md`; `DECISIONS.md` (≥ 6 mục `[M3-FIX]`).
- [ ] 0 key trong repo và lịch sử git; đã push `master` và `main` sau khi tôi đồng ý; Streamlit online hiện bảng đối chiếu mới khi mở bằng phiên ẩn danh.

---

## Phụ lục (dành cho tôi; agent bỏ qua phần này)

Hai cách dùng: **duyệt từng checkpoint** (mục B–C) hoặc **chạy một mạch** (mục H). Chọn một, không trộn. Mục D dùng được cho cả hai.

### A. Chuẩn bị (5 phút)
1. Hội thoại mới trong Antigravity, model Gemini 4 Argon, mở thư mục repo.
2. Không xóa `.cache/`: cả đợt sửa dựa vào phát lại từ cache.
3. `AGENTS.md` vẫn ghi hạn 16:00 và "BRIEF_M3.md thắng nếu mâu thuẫn". Prompt B đã ghi đè cho đợt này.
4. Nếu để agent chạy qua đêm: cắm sạc, tắt chế độ ngủ.

### B. Prompt khởi động, chạy tới CHECKPOINT 1 (dán nguyên văn)
```text
Bạn thực hiện ĐỢT SỬA TRƯỚC KHI NỘP của Mission 3 trong repo này. Mọi trả lời và artifact (Implementation Plan, Task List, Walkthrough) viết bằng tiếng Việt có dấu.

1) ĐỌC TRƯỚC
BRIEF_M3_FIX.md (toàn bộ, trừ Phụ lục) → AGENTS.md → research/refresh.py, research/schemas.py (RefreshComparison), research/dates.py (detect_data_period), research/llm.py, tests/test_refresh.py. BRIEF_M3.md chỉ để tra bất biến ở mục 4.1. Bỏ qua PROMPTS_M3.md.

2) THỨ TỰ ƯU TIÊN
BRIEF_M3_FIX.md > BRIEF_M3.md > AGENTS.md. Đợt này làm F0 → F5 theo BRIEF_M3_FIX.md mục 6 (thay cho P0–P5), hạn 10:00 ngày 24/10/2026 (thay cho 16:00). 8 quy tắc "Không bao giờ vi phạm" của AGENTS.md giữ nguyên.

3) LUẬT RIÊNG CỦA ĐỢT NÀY
- Không đổi prompt của vòng làm mới, không đổi model chính, không đổi quy tắc chấm điểm Mission 2.
- Không gọi LLM thật cho TC1–TC10: mọi lần chạy phải phát lại từ cache (llm_calls_count == 0). Trượt cache thì dừng và báo tôi.
- Ngoại lệ duy nhất được gọi LLM thật: gọi thử model dự phòng OpenRouter theo mục 3.5 (tối đa 1 lần mỗi model, không ghi cache, không in key).
- Không đọc, không in nội dung .env. Không xóa .cache/. Không xóa file đã có trong repo.
- Mọi con số trong Walkthrough phải kèm output thật (dán nguyên văn các dòng quan trọng).

4) VIỆC NGAY BÂY GIỜ
Làm F0 rồi F1 theo mục 6. Ở F1, kết quả phát lại TC7, TC10 phải khớp bảng tham chiếu mục 3.7; lệch chỗ nào thì giải thích. Dừng ở CHECKPOINT 1, chờ tôi trả lời "OK".
```

### C. Prompt tiếp tục sau mỗi checkpoint
- Sau CHECKPOINT 1: `OK CHECKPOINT 1. Làm F2 theo BRIEF_M3_FIX.md mục 6 và 5.3, dừng ở CHECKPOINT 2.`
- Sau CHECKPOINT 2: `OK CHECKPOINT 2. Làm F3 theo mục 7, dừng ở CHECKPOINT 3.`
- Sau CHECKPOINT 3: `OK CHECKPOINT 3. Làm F4. Tôi đồng ý push đúng 2 lệnh, không --force, chỉ sau khi quét secrets ra 0: git push origin master ; git push origin master:main`
- Khi có link video: `Link video Mission 3: <link>. Làm F5. Tôi đồng ý push đúng 2 lệnh như trên.`

### D. Soi gì ở mỗi checkpoint
**CHECKPOINT 1**
- `pytest`: 21 test cũ không đổi; ≥ 8 test mới; chỉ 1 fixture Mission 3 bị sửa, đúng câu "In 2026" → "In 2025".
- TC7: E2 → E29, E12 → E34, E13 → … thành KHÔNG TƯƠNG ĐƯƠNG; chỉ còn `I5: THẤP → TRUNG BÌNH`. TC10: E2, E16 → E23 thành KHÔNG TƯƠNG ĐƯƠNG; 0 thay đổi độ tin cậy; không còn I10, I11.
- `git diff research/refresh.py`: các dòng prompt (`sys_prompt`, `usr_prompt`, `cmp_sys_prompt`, `cmp_usr_prompt`) không đổi ký tự nào.
- Kết quả gọi thử model dự phòng là output thật (tên model, hợp lệ hay không).

**CHECKPOINT 2**
- Mọi case 0 lệnh gọi LLM; TC1–TC6, TC8, TC9 trùng.
- Ảnh tab 3 của TC7: đọc được lý do ở dòng E2 ↔ E29; cột giải thích của LLM ở dòng đó có "(LLM, đã bị code bác bỏ)".
- Trả lời ngắn TC7 không còn "quý 1 năm 2 (".

**CHECKPOINT 3**
- Đọc to `SUBMISSION_M3_FORM.txt`: mỗi câu dưới giới hạn ký tự; mọi con số có trong `eval/results/m2_vs_m3.md` hoặc `TESTING.md`; không còn câu nào nói TC7 "cập nhật lên 5,3 tỷ USD".
- Kịch bản video ≤ 4:45 và khớp số mới.

### E. Prompt xử lý sự cố
- Trượt cache: `Dừng. Liệt kê case và bước nào gọi LLM (step_name), và bạn đã đổi gì trong prompt hoặc dữ liệu đầu vào. Khôi phục output của case đó từ git. Không chạy lại bằng LLM thật.`
- Lệch bảng 3.7: `Với từng cặp lệch, in: nhãn LLM, data_period hai bên, scope_category, region_tags, unit_kinds và lý do. So với quy tắc 3.2. Sửa code cho đúng quy tắc, không sửa bảng tham chiếu.`
- Test cũ đỏ: `Chỉ ra test nào, assert nào, vì sao. Không sửa test Mission 2. Với test Mission 3, chỉ sửa fixture khi lý do giống mục 5.1 và ghi DECISIONS.md.`

### F. Prompt review chéo cuối (hội thoại mới, nên chọn model khác Argon)
```text
Bạn là người review độc lập, chỉ báo cáo, không sửa file. Đọc BRIEF_M3_FIX.md (trừ Phụ lục), rồi xem git log --oneline -15 và diff từ commit d2c2869 đến HEAD. Báo cáo bằng tiếng Việt, mỗi ý kèm file:dòng:
1. research/comparability.py có đúng 4 nhóm quy tắc P/T/Đ/K như mục 3.2 không? Có đường nào code nâng nhãn hoặc thêm id không?
2. Các prompt của vòng làm mới trong research/refresh.py có bị đổi không?
3. Chạy pytest -q và python -m research.refresh eval/results/TC7_before_refresh.json --reference-date 2026-10-23 --out-json <thư mục tạm ngoài repo>\tc7.json: kết quả có khớp bảng 3.7 không?
4. SUBMISSION_M3_FORM.txt: có con số nào không tìm thấy trong eval/results/ hoặc TESTING.md không? Có câu nào phóng đại không?
5. Diff có chứa key, nội dung .env, hay đường dẫn tới file bí mật nào không?
```

### G. Ghi chú quay video (cho tôi)
- Mục tiêu 4:30, tối đa 4:45. Quay 1080p; phóng to trình duyệt 110–125% để chữ trong bảng đọc được.
- Mở sẵn các tab theo thứ tự kịch bản; tắt thông báo; đánh thức app Streamlit trước khi quay (app đang ngủ thì bấm "Yes, get this app back up!" và chờ khoảng 1 phút).
- Nếu video vượt 5:00, tăng tốc 1,05× bằng ffmpeg (giữ cao độ giọng nói):
  `ffmpeg -i Gamota_Mission3_Demo_v2.mp4 -filter_complex "[0:v]setpts=PTS/1.05[v];[0:a]atempo=1.05[a]" -map "[v]" -map "[a]" Gamota_Mission3_Demo_v2_fast.mp4`
- Tải lên YouTube chế độ Không công khai; mở thử bằng cửa sổ ẩn danh; gửi link cho agent theo dòng cuối của mục C (hoặc prompt F5 ở mục H).

### H. Chạy một mạch: một prompt từ F0 đến F4

Agent tự làm F0 → F4 không dừng chờ duyệt. Mỗi checkpoint được thay bằng một **cổng tự kiểm** có tiêu chí cụ thể. Agent chỉ gọi tôi trong 5 trường hợp ghi trong prompt. Dùng cách này **thay cho** mục B–C.

**Chuẩn bị:**
1. Hội thoại mới trong Antigravity, model Gemini 4 Argon, mở thư mục repo.
2. Nếu bản Antigravity có các cài đặt này: cho phép agent tự chạy lệnh terminal; để agent tự đi tiếp sau khi tạo artifact; thêm vào danh sách lệnh bị chặn: `git push --force`, `git reset --hard`, `git add -A`, `git add .`, `Remove-Item -Recurse`, `rm -rf`. Antigravity vẫn hiện nút duyệt plan thì bấm duyệt.
3. Cắm sạc và tắt chế độ ngủ (Windows: Settings → System → Power → Screen and sleep → Never).
4. Không xóa `.cache/`.

**Prompt (dán nguyên văn):**

```text
Bạn là agent thực hiện TOÀN BỘ đợt sửa trước khi nộp của Mission 3 (F0 → F4 trong BRIEF_M3_FIX.md), chạy một mạch. Mọi trả lời và artifact (Implementation Plan, Task List, Walkthrough) viết bằng tiếng Việt có dấu.

1) ĐỌC TRƯỚC
AGENTS.md → BRIEF_M3_FIX.md (toàn bộ, trừ Phụ lục; mục 6 là thứ tự làm, mục 3.7 là bảng tham chiếu phải khớp) → research/refresh.py, research/schemas.py, research/dates.py (detect_data_period), research/llm.py, research/pipeline.py (mục 7.5), app.py (khối vòng làm mới), eval/run_eval.py, eval/compare_m2_m3.py, tests/test_refresh.py, SUBMISSION_M3.md, TESTING.md. BRIEF_M3.md chỉ để tra bất biến ở mục 4.1. Bỏ qua PROMPTS_M3.md.

2) CHẾ ĐỘ CHẠY MỘT MẠCH (tôi cho phép trước, thay cho các lần hỏi trong AGENTS.md và BRIEF_M3_FIX.md)
- Tôi duyệt trước Implementation Plan của bạn và trả lời trước "OK" cho CHECKPOINT 1, 2, 3 của BRIEF_M3_FIX.md. Tại mỗi checkpoint vẫn cập nhật Walkthrough đầy đủ như mục 6 yêu cầu, chạy CỔNG TỰ KIỂM ở phần 4 dưới đây, đạt thì đi tiếp, không chờ tôi.
- Tôi cho phép trước việc push ở F4, chỉ khi cổng tự kiểm F4 đạt hết. Chỉ được chạy đúng 2 lệnh này (không --force): git push origin master ; git push origin master:main
- Kiểm giờ bằng Get-Date ở mỗi cổng. Quá 02:00 ngày 24/10 mà chưa xong F2, hoặc quá 07:00 ngày 24/10 mà chưa xong F3: tự cắt phần còn lại theo đúng thứ tự BRIEF_M3_FIX.md mục 8, không chờ tôi; ghi phần cắt vào DECISIONS.md và README mục Hạn chế. Không bao giờ cắt phần "Không bao giờ cắt". Hạn cứng: xong F4 trước 10:00 ngày 24/10.
- Chỉ dừng hẳn và gọi tôi khi: (a) cách duy nhất để đi tiếp là vi phạm một bất biến ở BRIEF_M3_FIX.md mục 0, BRIEF_M3.md mục 4.1, hoặc một quy tắc "Không bao giờ vi phạm" trong AGENTS.md; (b) một lần phát lại hay chạy eval bị trượt cache (lỗi do LLM hoặc mạng bị chặn, hoặc llm_calls_count > 0); (c) quét secrets ra số khác 0; (d) cần thao tác bằng tài khoản của tôi (GitHub, Streamlit Cloud, OpenRouter, Google AI Studio); (e) cổng tự kiểm của một phần "Không bao giờ cắt" vẫn đỏ sau 3 lần sửa. Ngoài 5 trường hợp này, tự quyết theo BRIEF_M3_FIX.md và ghi 1–2 dòng vào DECISIONS.md.

3) LUẬT GIỮ NGUYÊN
- Không bịa: mọi con số trong Walkthrough, TESTING.md, README.md, SUBMISSION_M3.md, SUBMISSION_M3_FORM.txt phải có output thật hoặc nằm trong eval/results/. Ở mỗi cổng, dán nguyên văn các dòng output quan trọng.
- Mọi lần phát lại (research.refresh) và chạy eval (eval.run_eval) phải chạy qua script chặn mạng và chặn LLM thật như đầu mục 5.3 của BRIEF_M3_FIX.md. Script đặt ở thư mục tạm ngoài repo ($env:TEMP\gamota_fix). Ngoại lệ duy nhất cần mạng: gọi thử model dự phòng ở mục 3.5 (tối đa 1 lần mỗi model, không ghi cache, không in key).
- Không đổi prompt của vòng làm mới (sys_prompt, usr_prompt, cmp_sys_prompt, cmp_usr_prompt trong research/refresh.py); không đổi model chính; không đổi quy tắc chấm điểm Mission 2; không sửa 21 test của Mission 2; với test Mission 3 chỉ được sửa đúng fixture ở BRIEF_M3_FIX.md mục 5.1.
- Không sửa bảng tham chiếu 3.7 cho khớp code; sửa code cho đúng quy tắc 3.2.
- Không đọc hay in nội dung .env (chỉ kiểm có/không); không in chuỗi key ra bất cứ đâu; không xóa .cache/; không xóa file đã có trong repo; không cài công cụ toàn cục; không dùng model trả phí trong code.
- Không chạy lại một case nhiều lần để chọn kết quả đẹp; không viết code riêng cho câu hỏi mẫu.
- Git: chỉ git add đúng các file bạn tạo hoặc sửa; không bao giờ git add -A hay git add . (PROMPTS_M3.md phải ở ngoài repo). Ở F0, commit BRIEF_M3_FIX.md cùng AGENTS.md. Commit nhỏ theo từng phần, message tiếng Anh.
- Python: .venv\Scripts\python.exe. File nháp và output thử nghiệm để ở $env:TEMP\gamota_fix, không để trong repo.

4) CỔNG TỰ KIỂM (đạt mới sang phase sau; dán output vào Walkthrough)
Sau F0:
- pytest -q ra 46 passed trước khi sửa code.
- Phát lại TC7, TC10 (lệnh ở mục 6, qua script chặn): TC7 = 2 XÁC NHẬN / 3 CẬP NHẬT / 2 KHÔNG TƯƠNG ĐƯƠNG và 5 thay đổi độ tin cậy; TC10 = 4 / 2 / 1 và 3 thay đổi; không lỗi trượt cache.
- eval/results/m3_before_fix/ có đủ file như mục 5.3.1; đã commit snapshot, BRIEF_M3_FIX.md và AGENTS.md.
Sau F1 (CHECKPOINT 1):
- pytest -q pass toàn bộ, tổng ≥ 54 test.
- Lệnh sau ra trống: git diff --stat d2c2869 -- tests/test_grade.py tests/test_verify_quote.py tests/test_score.py tests/test_pipeline_mock.py tests/test_app_ui.py tests/test_recency.py tests/test_regression_m2.py tests/test_app_ui_m3.py research/score.py research/extract.py research/synthesize.py research/grade.py research/retrieve.py research/dates.py research/recency.py config/
- git diff d2c2869 -- research/refresh.py không xóa hay sửa dòng nào thuộc 4 chuỗi prompt (dán phần diff quanh các biến prompt).
- Phát lại TC7, TC10 sau khi sửa (qua script chặn): khớp bảng 3.7 ở nhãn cuối từng cặp, số lượng từng nhãn, danh sách thay đổi độ tin cậy, số ConflictItem, số nhận định; không lỗi trượt cache.
- Có kết quả gọi thử model dự phòng (tên model, JSON hợp lệ hay không, thời gian), hoặc ghi rõ không model nào đạt.
Sau F2 (CHECKPOINT 2):
- eval.run_eval (qua script chặn) chạy xong 10 case, không case nào lỗi; mọi case trace.llm_calls_count == 0; TC7, TC10 có refresh.llm_calls_count == 0.
- Script so sánh ở mục 5.3.3: TC1–TC6, TC8, TC9, TC7_before_refresh, TC10_before_refresh trùng hoàn toàn; TC7, TC10 chỉ đổi theo bảng 3.7 (TC10 đổi thêm refresh.llm_calls_count 3 → 0).
- eval/results/m2_vs_m3.md có Bảng A, B, C, D; Bảng A: TC2–TC5 vẫn "Trùng 100%".
- data/cached_runs/tc7_cr_a2_refreshed.md: số lần xuất hiện "quý 1 năm 2 (" bằng 0; "Số liệu cũ ↔ mới (CẬP NHẬT)" bằng 0.
- Đã kiểm giao diện bằng trình duyệt tích hợp: ảnh chụp tab 3 của TC7 (bảng 6 cột; dòng E2 ↔ E29 có lý do và "(LLM, đã bị code bác bỏ)"; tiêu đề khối có "phát lại từ cache") và ảnh trả lời ngắn TC7.
- pytest -q pass.
Sau F3 (CHECKPOINT 3):
- SUBMISSION_M3_FORM.txt: số lần xuất hiện của "[", "](", dấu backtick và "**" đều bằng 0; Câu 1 ≤ 1800, Câu 2 ≤ 2000, Câu 3 ≤ 1800 ký tự (đếm bằng code, dán kết quả).
- Có bảng "con số → file nguồn" cho mọi con số trong SUBMISSION_M3_FORM.txt và phần Mission 3 của README.md; bỏ mọi câu nói quá dữ liệu (vd "triệt để", "hoàn toàn", "100%" khi dữ liệu không nói vậy).
- Không còn câu nào nói TC7 "cập nhật" doanh thu IAP lên 5,3 tỷ USD, hay TC10 "cập nhật" lượt tải game lên 18,1 tỷ.
- SUBMISSION_M3.md không còn "11:49"; có "18:00 ngày 24/10/2026"; kịch bản video tổng ≤ 4:45.
- DECISIONS.md có ≥ 6 mục [M3-FIX]; TESTING.md có mục "Đợt sửa trước khi nộp".
F4, trước khi push:
- Lệnh này ra 0 (chỉ in số lượng, không in chuỗi key): (git log -p --all | Select-String -Pattern 'AIza[0-9A-Za-z_\-]{30,}','sk-or-v1-[0-9a-f]{20,}','tvly-[0-9A-Za-z\-]{10,}','gsk_[0-9A-Za-z]{20,}').Count
- git ls-files | Select-String '\.env' chỉ có .env.example; pytest -q pass; git status --short chỉ còn dòng ?? PROMPTS_M3.md.
F4, sau khi push:
- git ls-remote origin: refs/heads/master và refs/heads/main cùng trỏ HEAD local.
- Chờ 2–5 phút, mở https://gamota-market-research-mvp.streamlit.app trong phiên ẩn danh của trình duyệt tích hợp (app ngủ thì bấm đánh thức, chờ khoảng 1 phút); bấm TC7 → tab "3. Độ mới & Ảnh hưởng (A2)": thấy bảng đối chiếu 6 cột mới. Chụp ảnh. Sau 15 phút demo vẫn chưa cập nhật thì không thử mãi: ghi vào danh sách việc tôi phải làm (Reboot app trên share.streamlit.io).

5) KẾT THÚC
Walkthrough cuối gồm: checklist DoD ở BRIEF_M3_FIX.md mục 9, mỗi mục tick kèm bằng chứng; bảng 3.7 đặt cạnh kết quả thật; Bảng C, D; danh sách test mới (loại, kết quả); phần đã cắt (nếu có) và lý do; nguyên văn SUBMISSION_M3_FORM.txt để tôi đọc duyệt; kịch bản video; danh sách việc tôi tự làm (quay video theo kịch bản, tải lên YouTube chế độ Không công khai, gửi link để bạn làm F5, dán link và 3 câu vào form trước 18:00 ngày 24/10). Xong F4 thì dừng, không làm thêm.

Bắt đầu ngay: in tóm tắt 5 dòng (lỗi cần sửa, cách sửa, bảng tham chiếu phải khớp, những gì phải cập nhật trong tài liệu nộp, hạn), Implementation Plan + Task List cho toàn bộ F0–F4, rồi làm luôn.
```

**Nếu phiên bị ngắt giữa chừng** (hết lượt dùng model, mất mạng, máy tắt): mở hội thoại mới và dán:

```text
Bạn tiếp tục đợt sửa trước khi nộp của Mission 3 đang chạy dở ở chế độ chạy một mạch. Trả lời bằng tiếng Việt có dấu. Đọc AGENTS.md, BRIEF_M3_FIX.md (trừ Phụ lục), và CHỈ mục H trong Phụ lục của BRIEF_M3_FIX.md: prompt trong mục đó là việc tôi đã giao, áp dụng lại nguyên văn mọi quy tắc và cổng tự kiểm của nó. Chạy: git log --oneline -15, git status --short, .venv\Scripts\python.exe -m pytest -q, Get-Date. Xác định phase và bước đang dở theo BRIEF_M3_FIX.md mục 6, ghi tóm tắt vào Walkthrough, rồi làm tiếp đến hết F4.
```

**Khi có link video (F5):**

```text
Link video Mission 3: <dán link>. Làm F5 theo BRIEF_M3_FIX.md mục 6: thay mọi chỗ "(cập nhật sau khi quay)" bằng link này trong README.md, SUBMISSION_M3.md, SUBMISSION_M3_FORM.txt. Chạy lại cổng "F4, trước khi push" ở mục H. Commit (chỉ git add 3 file đó). Tôi cho phép push đúng 2 lệnh, không --force: git push origin master ; git push origin master:main. Sau khi push, mở README.md trên GitHub và kiểm link video bấm được. Trả lời bằng tiếng Việt có dấu.
```

**Khi agent báo xong, bạn kiểm khoảng 10 phút trước khi quay video:**
1. Đọc Walkthrough cuối: DoD tick đủ kèm bằng chứng; đọc `SUBMISSION_M3_FORM.txt`, tự trình bày lại được.
2. Tự chạy `.venv\Scripts\python.exe -m pytest -q` và `git diff --stat d2c2869 -- tests/test_grade.py tests/test_verify_quote.py tests/test_score.py tests/test_pipeline_mock.py tests/test_app_ui.py` (phải trống).
3. Mở link demo bằng cửa sổ ẩn danh: bấm TC7 → tab "3. Độ mới & Ảnh hưởng (A2)" → xem dòng E2 ↔ E29.
4. Làm các việc agent ghi cho bạn, rồi chạy review chéo ở mục F (hoặc nhờ Claude soát).
5. Quay video theo kịch bản, gửi link bằng prompt F5, dán link và 3 câu vào form.
