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
        "Kiểm tra tiền đề (TC5)",
        "Vì sao doanh thu game mobile Đông Nam Á giảm 50% trong năm qua?",
    ),
]


def load_cached_runs() -> dict[str, tuple[Path, Report]]:
    """Load all saved real runs from data/cached_runs/*.json."""
    runs: dict[str, tuple[Path, Report]] = {}
    if not CACHED_RUNS_DIR.exists():
        return runs
    for path in sorted(CACHED_RUNS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rep = Report.model_validate(data)
            ts = rep.trace.get("run_timestamp", "Không rõ thời điểm")
            label = f"{rep.question} (Chạy thật lúc: {ts})"
            runs[label] = (path, rep)
        except Exception:
            continue
    return runs


def main() -> None:
    st.set_page_config(
        page_title="Gamota · Nghiên cứu Thị trường Game có Căn cứ",
        page_icon="🎮",
        layout="wide",
    )

    if "live_runs_used" not in st.session_state:
        st.session_state["live_runs_used"] = 0
    if "question_input" not in st.session_state:
        st.session_state["question_input"] = SAMPLE_QUESTIONS[0][1]
    if "active_report" not in st.session_state:
        st.session_state["active_report"] = None

    max_live_runs = int(os.environ.get("MAX_LIVE_RUNS_PER_SESSION", "5"))

    st.title("🎮 Hệ thống Nghiên cứu Thị trường Game có Căn cứ (Gamota MVP)")
    st.caption(
        "Giả thuyết cốt lõi: Mọi nhận định quan trọng đều truy về trích dẫn nguyên văn (≤ 40 từ, code xác minh RapidFuzz ≥ 90), "
        "gắn với hạng nguồn A/B/C và độ tin cậy tính bằng quy tắc minh bạch (LLM không tự chấm điểm, không tự viết URL)."
    )

    cached_runs = load_cached_runs()
    llm_probe = LLMClient()
    has_key = llm_probe.has_any_api_key()

    with st.sidebar:
        st.header("⚙️ Chế độ vận hành")
        default_mode_idx = 0 if has_key else 1
        mode = st.radio(
            "Chọn chế độ:",
            options=["🔴 Live (Chạy trực tiếp)", "📦 Kết quả đã lưu (Không cần API key)"],
            index=default_mode_idx,
        )
        st.divider()
        st.subheader("Trạng thái cấu hình")
        st.write(f"- **LLM API Key:** `{'ĐÃ CẤU HÌNH' if has_key else 'CHƯA CÓ (Dùng Kết quả đã lưu)'}`")
        st.write(f"- **Model mặc định:** `{llm_probe.provider}/{llm_probe.model}`")
        st.write(
            f"- **Lượt chạy Live trong phiên:** `{st.session_state['live_runs_used']}/{max_live_runs}`"
        )
        st.write(f"- **Số bản chạy thật đã lưu:** `{len(cached_runs)}`")

    st.subheader("1. Chọn câu hỏi mẫu hoặc nhập câu hỏi nghiên cứu")
    cols = st.columns(len(SAMPLE_QUESTIONS))
    for idx, (short_label, q_text) in enumerate(SAMPLE_QUESTIONS):
        if cols[idx].button(short_label, use_container_width=True):
            st.session_state["question_input"] = q_text

    if mode.startswith("📦"):
        if not cached_runs:
            st.info(
                "Hiện chưa có file kết quả chạy thật nào trong `data/cached_runs/`. "
                "Sau khi chạy các câu hỏi mẫu ở P1–P2, kết quả thật sẽ hiển thị tại đây để xem ngay không cần API key."
            )
        else:
            selected_label = st.selectbox(
                "Chọn lần chạy thật đã lưu (`data/cached_runs/*.json`):",
                options=list(cached_runs.keys()),
            )
            if selected_label:
                _path, rep = cached_runs[selected_label]
                st.session_state["active_report"] = rep
    else:
        question_val = st.text_input(
            "Câu hỏi nghiên cứu thị trường game:",
            key="question_input",
            placeholder="Nhập bất kỳ câu hỏi nghiên cứu thị trường game nào...",
        )
        run_btn = st.button("🚀 Phân tích & Xác minh bằng chứng (Live)", type="primary")
        if run_btn:
            if not question_val.strip():
                st.warning("Vui lòng nhập câu hỏi nghiên cứu.")
            elif st.session_state["live_runs_used"] >= max_live_runs:
                st.error(
                    f"Bạn đã dùng hết {max_live_runs} lượt chạy Live trong phiên này để bảo vệ quota miễn phí. "
                    "Vui lòng chuyển sang chế độ **📦 Kết quả đã lưu** ở thanh bên trái."
                )
            elif not has_key:
                st.error(
                    "Chưa cấu hình API Key (`GEMINI_API_KEY` / `GROQ_API_KEY`) trong `.env` hoặc Secrets. "
                    "Vui lòng chuyển sang chế độ **📦 Kết quả đã lưu** ở thanh bên trái để xem kết quả chạy thật."
                )
            else:
                try:
                    with st.status(
                        "Đang chạy pipeline 6 bước (Plan → Retrieve → Grade → Extract → Synthesize → Score)...",
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
                            label=f"Hoàn tất phân tích trong {report.trace.get('duration_seconds', 0)}s!",
                            state="complete",
                            expanded=False,
                        )
                except LLMQuotaOrKeyError as q_err:
                    st.error(
                        f"Lỗi API / Hết hạn mức miễn phí (Quota): {q_err}\n\n"
                        "👉 **Gợi ý:** Hãy chuyển sang chế độ **📦 Kết quả đã lưu** ở thanh bên trái để xem các lần chạy thật đã lưu sẵn."
                    )
                except Exception as exc:
                    st.error(
                        f"Đã xảy ra lỗi khi chạy pipeline: {type(exc).__name__}: {exc}\n\n"
                        "👉 **Gợi ý:** Hãy chuyển sang chế độ **📦 Kết quả đã lưu** để xem các bản chạy thật đã lưu."
                    )

    active_report: Report | None = st.session_state.get("active_report")
    if active_report is not None:
        st.divider()
        md_output = render_report_markdown(active_report)
        json_output = json.dumps(
            active_report.model_dump(), ensure_ascii=False, indent=2
        )

        dl_col1, dl_col2, _ = st.columns([1, 1, 3])
        dl_col1.download_button(
            "⬇️ Tải báo cáo Markdown (.md)",
            data=md_output.encode("utf-8"),
            file_name="gamota_market_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
        dl_col2.download_button(
            "⬇️ Tải dữ liệu JSON (.json)",
            data=json_output.encode("utf-8"),
            file_name="gamota_market_report.json",
            mime="application/json",
            use_container_width=True,
        )

        st.markdown(md_output, unsafe_allow_html=True)

        with st.expander("🔍 Nhật ký Pipeline & Trace chi tiết (Pipeline Audit Log)"):
            st.json(active_report.trace)


if __name__ == "__main__":
    main()
