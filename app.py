"""Streamlit application for Gamota Game Market Research MVP."""

from __future__ import annotations

import json
import os
from pathlib import Path
import streamlit as st

from research.llm import LLMClient, LLMQuotaOrKeyError
from research.pipeline import render_report_markdown, run
from research.schemas import Report

CACHED_RUNS_DIR = Path(__file__).resolve().parent / "data" / "cached_runs"

MODE_CACHED = "Kết quả đã lưu (Chạy thật, không cần key)"
MODE_LIVE = "Chạy trực tiếp (Live qua Pipeline)"

SAMPLE_QUESTIONS = [
    (
        "Cơ hội thể loại (TC1)",
        "Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?",
    ),
    (
        "Mô hình kiếm tiền (TC2)",
        "Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines?",
    ),
    (
        "Quy mô thị trường (TC3)",
        "Quy mô thị trường game mobile Việt Nam hiện nay là bao nhiêu?",
    ),
    (
        "Đối thủ & Doanh thu (TC6)",
        "Doanh thu tháng trước của 3 game gacha top đầu Thái Lan là bao nhiêu?",
    ),
]

CLEAN_LIGHT_CSS = """
<style>
    /* Force clean light background and slate typography */
    .stApp {
        background-color: #FFFFFF;
        color: #0F172A;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1220px;
    }
    h1 {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.4rem !important;
    }
    h2 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        margin-top: 1.6rem !important;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid #E2E8F0;
    }
    h3 {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
        margin-top: 1rem !important;
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 16px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        color: #475569 !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }
    [data-testid="stMetricDelta"] svg {
        display: none !important;
    }
    [data-testid="stMetricDelta"] > div {
        color: #64748B !important;
        background-color: transparent !important;
        font-size: 0.78rem !important;
        padding: 0 !important;
    }
    /* Clean buttons */
    .stButton > button, .stDownloadButton > button {
        border-radius: 6px;
        border: 1px solid #CBD5E1;
        background-color: #FFFFFF;
        color: #1E293B;
        font-weight: 500;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #1D4ED8;
        color: #1D4ED8;
        background-color: #F8FAFC;
    }
    /* Clean Markdown tables */
    .stMarkdown table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        margin: 0.75rem 0 1.25rem 0;
    }
    .stMarkdown th {
        background-color: #F8FAFC;
        color: #1E293B;
        font-weight: 600;
        text-align: left;
        padding: 10px 12px;
        border: 1px solid #E2E8F0;
    }
    .stMarkdown td {
        padding: 10px 12px;
        border: 1px solid #E2E8F0;
        vertical-align: top;
        color: #334155;
        line-height: 1.5;
    }
    .stMarkdown blockquote {
        background-color: #F8FAFC;
        border-left: 3px solid #1D4ED8;
        padding: 8px 14px;
        margin: 0.5rem 0 1rem 0;
        color: #475569;
        font-size: 0.88rem;
    }
</style>
"""


def load_cached_runs() -> list[tuple[str, Path, Report]]:
    """Load all saved real runs from data/cached_runs/*.json."""
    runs: list[tuple[str, Path, Report]] = []
    if not CACHED_RUNS_DIR.exists():
        return runs
    for path in sorted(CACHED_RUNS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rep = Report.model_validate(data)
            ts = rep.trace.get("run_timestamp", "Không rõ thời điểm")
            dur = rep.trace.get("duration_seconds", 0)
            label = f"[{path.stem.upper()}] {rep.question} ({ts} · {dur}s)"
            runs.append((label, path, rep))
        except Exception:
            continue
    return runs


def main() -> None:
    st.set_page_config(
        page_title="Gamota · Nghiên cứu Thị trường Game có Căn cứ",
        layout="wide",
    )
    st.markdown(CLEAN_LIGHT_CSS, unsafe_allow_html=True)

    cached_runs = load_cached_runs()
    llm_probe = LLMClient()
    has_key = llm_probe.has_any_api_key()
    max_live_runs = int(os.environ.get("MAX_LIVE_RUNS_PER_SESSION", "5"))

    if "live_runs_used" not in st.session_state:
        st.session_state["live_runs_used"] = 0
    if "question_input" not in st.session_state:
        st.session_state["question_input"] = SAMPLE_QUESTIONS[0][1]
    if "selected_cached_idx" not in st.session_state:
        st.session_state["selected_cached_idx"] = 0
    if "active_report" not in st.session_state:
        st.session_state["active_report"] = (
            cached_runs[0][2] if cached_runs else None
        )

    st.title("Hệ thống Nghiên cứu Thị trường Game có Căn cứ (Gamota MVP)")
    st.markdown(
        "**Giả thuyết cốt lõi:** Với *bất kỳ* câu hỏi nghiên cứu thị trường game nào, mỗi nhận định quan trọng đều "
        "(a) truy về **trích dẫn nguyên văn ≤ 40 từ đã được code xác minh (`RapidFuzz ≥ 90`)**, "
        "(b) gắn với **hạng tin cậy của nguồn (`A/B/C`)**, và "
        "(c) có **độ tin cậy (`CAO / TRUNG BÌNH / THẤP`) tính bằng quy tắc code minh bạch** — LLM không tự chấm điểm, không tự viết URL. Thiếu dữ liệu thì nói rõ là thiếu."
    )

    with st.sidebar:
        st.subheader("Chế độ vận hành")
        default_mode_idx = 0 if cached_runs else (1 if has_key else 0)
        mode = st.radio(
            "Chọn chế độ:",
            options=[MODE_CACHED, MODE_LIVE],
            index=default_mode_idx,
        )
        st.divider()
        st.subheader("Trạng thái hệ thống")
        st.write(
            f"- **API Key (Free-tier):** `{'SẴN SÀNG' if has_key else 'CHƯA CẤU HÌNH'}`"
        )
        st.write(f"- **Model cấu hình:** `{llm_probe.provider}/{llm_probe.model}`")
        st.write(
            f"- **Lượt chạy Live trong phiên:** `{st.session_state['live_runs_used']}/{max_live_runs}`"
        )
        st.write(f"- **Bản chạy thật đã lưu:** `{len(cached_runs)} báo cáo`")
        st.caption(
            "Chế độ Kết quả đã lưu đọc trực tiếp từ `data/cached_runs/*.json` (các lần chạy thật đã lưu kèm timestamp) để luôn kiểm tra được ngay cả khi hết quota."
        )

    st.markdown("##### Câu hỏi mẫu theo 4 nhóm quyết định")
    cols = st.columns(len(SAMPLE_QUESTIONS))
    for idx, (short_label, q_text) in enumerate(SAMPLE_QUESTIONS):
        if cols[idx].button(short_label, use_container_width=True):
            st.session_state["question_input"] = q_text
            for c_idx, (_lbl, _p, c_rep) in enumerate(cached_runs):
                if c_rep.question.strip() == q_text.strip():
                    st.session_state["selected_cached_idx"] = c_idx
                    st.session_state["active_report"] = c_rep
                    break

    if mode == MODE_CACHED:
        if not cached_runs:
            st.warning(
                "Chưa có file nào trong `data/cached_runs/`. Hãy chuyển sang chế độ Live hoặc chạy CLI để lưu kết quả."
            )
        else:
            labels = [item[0] for item in cached_runs]
            safe_idx = min(
                st.session_state.get("selected_cached_idx", 0), len(labels) - 1
            )
            chosen_label = st.selectbox(
                "Chọn báo cáo chạy thật đã lưu (`data/cached_runs/`):",
                options=labels,
                index=safe_idx,
            )
            chosen_idx = labels.index(chosen_label)
            st.session_state["selected_cached_idx"] = chosen_idx
            st.session_state["active_report"] = cached_runs[chosen_idx][2]
    else:
        question_val = st.text_input(
            "Nhập câu hỏi nghiên cứu thị trường game bất kỳ:",
            key="question_input",
            placeholder="Ví dụ: Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?",
        )
        run_btn = st.button(
            "Chạy Pipeline 6 bước & Xác minh trích dẫn (Live)", type="primary"
        )
        if run_btn:
            if not question_val.strip():
                st.warning("Vui lòng nhập câu hỏi nghiên cứu.")
            elif st.session_state["live_runs_used"] >= max_live_runs:
                st.error(
                    f"Đã đạt giới hạn {max_live_runs} lượt chạy Live trong phiên này để bảo vệ quota miễn phí. "
                    "Vui lòng chuyển sang chế độ Kết quả đã lưu ở thanh bên trái."
                )
            elif not has_key:
                st.error(
                    "Chưa cấu hình `GEMINI_API_KEY` trong `.env` hoặc Secrets của ứng dụng. "
                    "Vui lòng chuyển sang chế độ Kết quả đã lưu ở thanh bên trái để xem kết quả chạy thật."
                )
            else:
                try:
                    with st.status(
                        "Đang thực thi Pipeline 6 bước (Plan → Retrieve → Grade → Extract → Synthesize → Score)...",
                        expanded=True,
                    ) as status_box:

                        def _ui_cb(step_title: str, detail: str) -> None:
                            status_box.write(f"**{step_title}**: {detail}")

                        report = run(
                            question=question_val.strip(),
                            progress_callback=_ui_cb,
                            use_cache=True,
                        )
                        st.session_state["live_runs_used"] += 1
                        st.session_state["active_report"] = report
                        status_box.update(
                            label=f"Hoàn tất phân tích trong {report.trace.get('duration_seconds', 0)}s",
                            state="complete",
                            expanded=False,
                        )
                except LLMQuotaOrKeyError as q_err:
                    st.error(
                        f"Tạm thời chạm giới hạn API miễn phí (Quota): {q_err}\n\n"
                        "Gợi ý: Hãy chuyển sang chế độ Kết quả đã lưu ở thanh bên trái để xem đầy đủ các lần chạy thật đã lưu sẵn."
                    )
                except Exception as exc:
                    st.error(
                        f"Đã xảy ra lỗi khi gọi API trực tiếp: {type(exc).__name__}: {exc}\n\n"
                        "Gợi ý: Hãy chuyển sang chế độ Kết quả đã lưu ở thanh bên trái để xem các bản chạy thật đã lưu."
                    )

    active_report: Report | None = st.session_state.get("active_report")
    if active_report is not None:
        st.divider()
        q = active_report.quality
        trace = active_report.trace or {}

        # Self-check metric cards
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(
            "Trích dẫn xác minh (RapidFuzz ≥ 90)",
            f"{q.verified_quote_rate}%",
            f"{q.verified_quotes_count}/{q.total_quotes_extracted} câu trích gốc",
            delta_color="off",
        )
        m2.metric(
            "Nhận định có ≥ 1 bằng chứng",
            f"{q.insights_with_verified_evidence_rate}%",
            f"{q.total_insights_count} nhận định hợp lệ",
            delta_color="off",
        )
        m3.metric(
            "Nhận định CAO từ nguồn C",
            f"{q.high_confidence_from_tier_c_only_count}",
            "Quy tắc bắt buộc = 0",
            delta_color="off",
        )
        m4.metric(
            "Nguồn giữ lại / bị loại",
            f"{len(active_report.sources)} giữ / {q.rejected_sources_count} loại",
            f"Thời gian: {trace.get('duration_seconds', 0)}s ({trace.get('llm_calls_count', 0)} LLM calls)",
            delta_color="off",
        )

        md_output = render_report_markdown(active_report)
        json_output = json.dumps(
            active_report.model_dump(), ensure_ascii=False, indent=2
        )

        dl_col1, dl_col2, _ = st.columns([1, 1, 2])
        dl_col1.download_button(
            "Tải Báo cáo Markdown (.md)",
            data=md_output.encode("utf-8"),
            file_name="gamota_market_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        dl_col2.download_button(
            "Tải Dữ liệu JSON (.json)",
            data=json_output.encode("utf-8"),
            file_name="gamota_market_report.json",
            mime="application/json",
            use_container_width=True,
        )

        st.markdown(md_output, unsafe_allow_html=True)

        with st.expander(
            "Nhật ký Pipeline (Số nguồn tìm thấy/giữ/loại, câu hỏi con, truy vấn & lý do loại)",
            expanded=False,
        ):
            st.markdown("#### Tiến trình từng bước")
            for log_line in trace.get("step_logs", []):
                st.write(f"- {log_line}")
            st.markdown("#### Truy vấn tìm kiếm đã chạy")
            st.write(trace.get("queries_executed", []))
            st.markdown("#### Lý do loại nguồn (`rejected_sources`)")
            if q.rejected_sources:
                st.table(
                    [
                        {"Nguồn / URL": r.item_id, "Lý do loại": r.reason}
                        for r in q.rejected_sources
                    ]
                )
            else:
                st.write("Không có nguồn nào bị loại.")
            st.markdown("#### Lý do loại trích dẫn (`rejected_quotes`)")
            if q.rejected_quotes:
                st.table(
                    [
                        {
                            "Mã trích dẫn": r.item_id,
                            "Lý do loại": r.reason,
                            "Nội dung": r.detail,
                        }
                        for r in q.rejected_quotes
                    ]
                )
            else:
                st.write("100% trích dẫn đều khớp nguyên văn (0 trích dẫn bị loại).")


if __name__ == "__main__":
    main()
