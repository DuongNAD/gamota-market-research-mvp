"""Streamlit application for Gamota Game Market Research MVP."""

from __future__ import annotations

import html
import json
import os
from pathlib import Path
import streamlit as st

from research.llm import LLMClient, LLMQuotaOrKeyError
from research.pipeline import render_report_markdown, run
from research.schemas import Report

CACHED_RUNS_DIR = Path(__file__).resolve().parent / "data" / "cached_runs"

MODE_CACHED = "Xem báo cáo mẫu đã chạy thật (6 tình huống TC1–TC6)"
MODE_LIVE = "Đặt câu hỏi mới & Chạy trực tiếp (Live)"

PRESET_CASES = [
    {
        "code": "TC1",
        "stem": "tc1_sea_genres",
        "short_title": "TC1 · Thể loại tiềm năng ĐNÁ",
        "group_tag": "Tình huống làm tốt",
        "question": "Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?",
    },
    {
        "code": "TC2",
        "stem": "tc2_casual_monetization",
        "short_title": "TC2 · Kiếm tiền game Casual",
        "group_tag": "Tình huống làm tốt",
        "question": "Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines?",
    },
    {
        "code": "TC3",
        "stem": "tc3_vn_market_size",
        "short_title": "TC3 · Quy mô thị trường VN",
        "group_tag": "Khó · Nguồn mâu thuẫn",
        "question": "Quy mô thị trường game mobile Việt Nam hiện nay là bao nhiêu?",
    },
    {
        "code": "TC4",
        "stem": "tc4_cambodia_mmorpg",
        "short_title": "TC4 · MMORPG Campuchia",
        "group_tag": "Khó · Thiếu dữ liệu",
        "question": "Doanh thu thể loại MMORPG mobile tại Campuchia năm 2025 là bao nhiêu?",
    },
    {
        "code": "TC5",
        "stem": "tc5_sea_drop_50_premise",
        "short_title": "TC5 · ĐNÁ giảm 50%?",
        "group_tag": "Khó · Tiền đề sai",
        "question": "Vì sao doanh thu game mobile Đông Nam Á giảm 50% trong năm qua?",
    },
    {
        "code": "TC6",
        "stem": "tc6_thailand_gacha",
        "short_title": "TC6 · Top 3 Gacha Thái Lan",
        "group_tag": "Chưa đạt · Giới hạn Paywall",
        "question": "Doanh thu tháng trước của 3 game gacha top đầu Thái Lan là bao nhiêu?",
    },
]

CLEAN_LIGHT_CSS = """
<style>
    .stApp {
        background-color: #FFFFFF;
        color: #0F172A;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1260px;
    }
    h1 {
        font-size: 1.65rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.25rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        margin-top: 1.25rem !important;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid #E2E8F0;
    }
    h3 {
        font-size: 1.02rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
        margin-top: 0.9rem !important;
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #475569 !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }
    [data-testid="stMetricDelta"] svg {
        display: none !important;
    }
    [data-testid="stMetricDelta"] > div {
        color: #64748B !important;
        background-color: transparent !important;
        font-size: 0.76rem !important;
        padding: 0 !important;
    }
    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        border-radius: 6px;
        border: 1px solid #CBD5E1;
        background-color: #FFFFFF;
        color: #1E293B;
        font-weight: 500;
        font-size: 0.84rem;
        padding: 0.4rem 0.75rem;
        transition: all 0.15s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: #1D4ED8;
        color: #1D4ED8;
        background-color: #F8FAFC;
    }
    .stButton > button[kind="primary"] {
        background-color: #1D4ED8;
        color: #FFFFFF;
        border-color: #1D4ED8;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1E40AF;
        color: #FFFFFF;
    }
    /* Clean Markdown tables */
    .stMarkdown table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
        margin: 0.6rem 0 1.2rem 0;
    }
    .stMarkdown th {
        background-color: #F8FAFC;
        color: #1E293B;
        font-weight: 600;
        text-align: left;
        padding: 9px 12px;
        border: 1px solid #E2E8F0;
    }
    .stMarkdown td {
        padding: 9px 12px;
        border: 1px solid #E2E8F0;
        vertical-align: top;
        color: #334155;
        line-height: 1.5;
    }
    /* Custom UI boxes and badges */
    .summary-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #1D4ED8;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 14px;
        line-height: 1.6;
        color: #1E293B;
        font-size: 0.94rem;
    }
    .rec-card {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 4px solid #15803D;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 14px;
        line-height: 1.6;
        color: #14532D;
        font-size: 0.94rem;
    }
    .insight-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-cao {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #86EFAC;
    }
    .badge-tb {
        background-color: #DBEAFE;
        color: #1E40AF;
        border: 1px solid #93C5FD;
    }
    .badge-thap {
        background-color: #F1F5F9;
        color: #475569;
        border: 1px solid #CBD5E1;
    }
    .badge-type {
        background-color: #F8FAFC;
        color: #334155;
        border: 1px solid #E2E8F0;
    }
    . badge-tier-a {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .quote-box {
        background-color: #F8FAFC;
        border-left: 3px solid #94A3B8;
        padding: 8px 12px;
        margin-top: 8px;
        font-size: 0.86rem;
        color: #334155;
        border-radius: 0 4px 4px 0;
    }
    .criteria-pill {
        display: inline-block;
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #E2E8F0;
        border-radius: 999px;
        padding: 3px 11px;
        font-size: 0.8rem;
        margin: 0 6px 6px 0;
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


def _conf_badge_html(conf: str) -> str:
    if conf == "CAO":
        cls = "badge badge-cao"
    elif conf == "TRUNG BÌNH":
        cls = "badge badge-tb"
    else:
        cls = "badge badge-thap"
    return f'<span class="{cls}">Độ tin cậy: {html.escape(conf)}</span>'


def _render_insights_interactive(report: Report) -> None:
    """Render filterable, easy-to-scan Insight cards with direct highlight links."""
    source_map = {s.id: s for s in report.sources}
    evidence_map = {e.id: e for e in report.evidences}

    f_col1, f_col2, f_col3 = st.columns([1.2, 1.2, 2])
    conf_filter = f_col1.selectbox(
        "Lọc theo Độ tin cậy:",
        options=["Tất cả", "CAO", "TRUNG BÌNH", "THẤP"],
        index=0,
    )
    type_filter = f_col2.selectbox(
        "Lọc theo Loại nhận định:",
        options=["Tất cả", "Thực chứng (fact)", "Suy luận / Dự báo (inference)"],
        index=0,
    )
    search_kw = f_col3.text_input(
        "Tìm nhanh từ khóa trong nhận định hoặc trích dẫn:",
        placeholder="Nhập từ khóa (ví dụ: Indonesia, IAP, Sensor Tower, 825...)",
    )

    filtered = []
    for ins in report.insights:
        if conf_filter != "Tất cả" and ins.confidence != conf_filter:
            continue
        is_fact = ins.type == "fact" and not ins.is_forecast
        if type_filter == "Thực chứng (fact)" and not is_fact:
            continue
        if type_filter == "Suy luận / Dự báo (inference)" and is_fact:
            continue
        if search_kw.strip():
            kw = search_kw.strip().lower()
            quotes_concat = " ".join(
                evidence_map[eid].quote
                for eid in ins.evidence_ids
                if eid in evidence_map
            ).lower()
            if kw not in ins.statement.lower() and kw not in quotes_concat:
                continue
        filtered.append(ins)

    st.caption(
        f"Đang hiển thị **{len(filtered)} / {len(report.insights)}** nhận định đã xác minh bằng chứng. "
        "Bấm vào đường dẫn màu xanh bên dưới mỗi câu trích dẫn để mở bài gốc và xem đoạn văn được tô sáng tự động."
    )

    for ins in filtered:
        type_str = (
            "Thực chứng (Fact)"
            if ins.type == "fact" and not ins.is_forecast
            else "Suy luận / Dự báo (Inference)"
        )
        badge_html = (
            f'{_conf_badge_html(ins.confidence)}'
            f'<span class="badge badge-type">{type_str}</span>'
        )
        assump_html = ""
        if ins.assumptions:
            joined_assump = html.escape("; ".join(ins.assumptions))
            assump_html = (
                f'<div style="margin-top:6px;font-size:0.84rem;color:#475569;">'
                f"<strong>Giả định đi kèm:</strong> {joined_assump}</div>"
            )

        ev_blocks: list[str] = []
        for eid in ins.evidence_ids:
            ev = evidence_map.get(eid)
            if not ev:
                continue
            src = source_map.get(ev.source_id)
            if src:
                date_disp = src.published_date or "Không rõ ngày"
                link_url = html.escape(ev.highlight_url or src.url)
                dom_disp = html.escape(src.domain)
                q_disp = html.escape(ev.quote)
                ev_blocks.append(
                    f'<div class="quote-box">'
                    f'<div><strong>[{html.escape(eid)}] Nguyên văn:</strong> <em>"{q_disp}"</em> '
                    f'<span style="color:#64748B;font-size:0.78rem;">(Khớp chuỗi: {ev.match_score}%)</span></div>'
                    f'<div style="margin-top:4px;font-size:0.82rem;">'
                    f'Nguồn: <strong>{html.escape(src.id)} ({dom_disp})</strong> · '
                    f'<strong>Hạng {html.escape(src.tier)}</strong> · Ngày: <code>{html.escape(date_disp)}</code> · '
                    f'<a href="{link_url}" target="_blank" rel="noopener noreferrer" style="color:#1D4ED8;font-weight:600;text-decoration:none;">'
                    f'Mở bài báo gốc & tô sáng câu trích dẫn ↗</a>'
                    f"</div></div>"
                )

        ev_html = "".join(ev_blocks)
        card_html = (
            f'<div class="insight-card">'
            f'<div style="margin-bottom:8px;"><strong>{html.escape(ins.id)}</strong> &nbsp; {badge_html} '
            f'<span style="font-size:0.8rem;color:#64748B;">({html.escape(ins.confidence_reason)})</span></div>'
            f'<div style="font-size:0.96rem;color:#0F172A;font-weight:500;line-height:1.55;">{html.escape(ins.statement)}</div>'
            f"{assump_html}"
            f"{ev_html}"
            f"</div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)


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
        st.session_state["question_input"] = PRESET_CASES[0]["question"]
    if "selected_cached_idx" not in st.session_state:
        st.session_state["selected_cached_idx"] = 0
    if "active_report" not in st.session_state:
        st.session_state["active_report"] = (
            cached_runs[0][2] if cached_runs else None
        )

    st.title("Hệ thống Nghiên cứu Thị trường Game có Căn cứ (Gamota MVP)")
    st.caption(
        "Mọi nhận định quan trọng đều truy về trích dẫn nguyên văn (<= 40 từ) được code xác minh (RapidFuzz >= 90) kèm link tô sáng tận nguồn, "
        "xếp hạng nguồn A/B/C và chấm điểm độ tin cậy (CAO / TRUNG BÌNH / THẤP) bằng quy tắc code minh bạch."
    )

    with st.sidebar:
        st.subheader("Chế độ sử dụng")
        default_mode_idx = 0 if cached_runs else (1 if has_key else 0)
        mode = st.radio(
            "Chọn cách thức:",
            options=[MODE_CACHED, MODE_LIVE],
            index=default_mode_idx,
        )
        st.divider()
        st.subheader("Chọn nhanh 6 tình huống (TC1–TC6)")
        st.caption("Bấm vào bất kỳ tình huống nào dưới đây để mở ngay báo cáo tương ứng:")
        for preset in PRESET_CASES:
            if st.button(
                f"{preset['short_title']} ({preset['group_tag']})",
                key=f"sb_{preset['code']}",
                use_container_width=True,
            ):
                st.session_state["question_input"] = preset["question"]
                for c_idx, (_lbl, c_path, c_rep) in enumerate(cached_runs):
                    if (
                        c_path.stem.lower() == preset["stem"]
                        or c_rep.question.strip() == preset["question"].strip()
                    ):
                        st.session_state["selected_cached_idx"] = c_idx
                        st.session_state["active_report"] = c_rep
                        break

        st.divider()
        st.subheader("Trạng thái hệ thống")
        st.write(
            f"- **API Key:** `{'SẴN SÀNG' if has_key else 'CHƯA CẤU HÌNH'}`"
        )
        st.write(f"- **Model:** `{llm_probe.provider}/{llm_probe.model}`")
        st.write(
            f"- **Lượt chạy Live:** `{st.session_state['live_runs_used']}/{max_live_runs}`"
        )
        st.write(f"- **Báo cáo lưu sẵn:** `{len(cached_runs)} tình huống`")

    # Quick 6-case selector bar on main page
    st.markdown("##### 1. Chọn nhanh 6 tình huống kiểm thử (Bấm để xem ngay kết quả)")
    p_cols = st.columns(6)
    for idx, preset in enumerate(PRESET_CASES):
        if p_cols[idx].button(
            preset["short_title"],
            key=f"main_{preset['code']}",
            help=f"{preset['group_tag']}: {preset['question']}",
            use_container_width=True,
        ):
            st.session_state["question_input"] = preset["question"]
            for c_idx, (_lbl, c_path, c_rep) in enumerate(cached_runs):
                if (
                    c_path.stem.lower() == preset["stem"]
                    or c_rep.question.strip() == preset["question"].strip()
                ):
                    st.session_state["selected_cached_idx"] = c_idx
                    st.session_state["active_report"] = c_rep
                    break

    # Input / Selection area
    with st.container():
        c_left, c_right = st.columns([3.2, 1.2])
        with c_left:
            question_val = st.text_input(
                "Câu hỏi nghiên cứu thị trường (Có thể sửa hoặc nhập câu hỏi mới bất kỳ để chạy Live):",
                key="question_input",
                placeholder="Nhập câu hỏi nghiên cứu thị trường game bất kỳ...",
            )
        with c_right:
            st.write("")
            run_btn = st.button(
                "Phân tích câu hỏi này (Chạy Live)",
                type="primary",
                use_container_width=True,
            )

    if mode == MODE_CACHED and cached_runs and not run_btn:
        with st.expander("Chọn từ danh sách file lưu trong data/cached_runs/", expanded=False):
            labels = [item[0] for item in cached_runs]
            safe_idx = min(
                st.session_state.get("selected_cached_idx", 0), len(labels) - 1
            )
            chosen_label = st.selectbox(
                "File báo cáo đã lưu:",
                options=labels,
                index=safe_idx,
            )
            chosen_idx = labels.index(chosen_label)
            if chosen_idx != st.session_state.get("selected_cached_idx", 0):
                st.session_state["selected_cached_idx"] = chosen_idx
                st.session_state["active_report"] = cached_runs[chosen_idx][2]

    if run_btn:
        if not question_val.strip():
            st.warning("Vui lòng nhập câu hỏi nghiên cứu.")
        elif st.session_state["live_runs_used"] >= max_live_runs:
            st.error(
                f"Đã đạt giới hạn {max_live_runs} lượt chạy Live trong phiên này để bảo vệ quota miễn phí. "
                "Bạn vẫn có thể bấm chọn xem toàn bộ 6 báo cáo mẫu (TC1–TC6) ở thanh phía trên."
            )
        elif not has_key:
            st.error(
                "Chưa cấu hình GEMINI_API_KEY trong .env hoặc Secrets của ứng dụng. "
                "Vui lòng bấm chọn 6 báo cáo mẫu (TC1–TC6) ở thanh phía trên để xem kết quả chạy thật."
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
                    "Gợi ý: Bạn có thể bấm vào 6 nút TC1–TC6 ở trên để xem ngay các bản chạy thật đã lưu sẵn."
                )
            except Exception as exc:
                st.error(
                    f"Đã xảy ra lỗi khi gọi API trực tiếp: {type(exc).__name__}: {exc}\n\n"
                    "Gợi ý: Bạn có thể bấm vào 6 nút TC1–TC6 ở trên để xem các bản chạy thật đã lưu."
                )

    active_report: Report | None = st.session_state.get("active_report")
    if active_report is not None:
        st.divider()
        q = active_report.quality
        trace = active_report.trace or {}

        # Header banner for active report
        st.markdown(
            f"**Đang hiển thị báo cáo cho câu hỏi:** {active_report.question}  \n"
            f"<span style='color:#64748B;font-size:0.84rem;'>"
            f"Thời điểm chạy: <code>{trace.get('run_timestamp', 'N/A')}</code> · "
            f"Thời gian xử lý: <code>{trace.get('duration_seconds', 0)}s</code> · "
            f"Model: <code>{trace.get('llm_provider', '')}/{trace.get('llm_model', '')}</code> ({trace.get('llm_calls_count', 0)} LLM calls) · "
            f"Search: <code>{trace.get('search_provider', '')}</code>"
            f"</span>",
            unsafe_allow_html=True,
        )

        # 4 Self-check metric cards
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

        # Structured tabs for effortless navigation
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
            [
                "1. Tóm tắt & Khuyến nghị",
                f"2. Nhận định & Trích dẫn ({len(active_report.insights)})",
                "3. Tiền đề, Mâu thuẫn & Khoảng trống",
                f"4. Nguồn thông tin ({len(active_report.sources)})",
                "5. Nhật ký Pipeline & Tự kiểm",
                "6. Bản đầy đủ (Markdown & Tải file)",
            ]
        )

        with tab1:
            st.markdown("#### Trả lời ngắn")
            st.markdown(
                f'<div class="summary-card">{html.escape(active_report.short_answer)}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### Khuyến nghị hành động (kèm điều kiện áp dụng)")
            st.markdown(
                f'<div class="rec-card">{html.escape(active_report.recommendation)}</div>',
                unsafe_allow_html=True,
            )
            if active_report.decision_criteria:
                st.markdown("#### Tiêu chí ra quyết định đã sử dụng")
                pills = "".join(
                    f'<span class="criteria-pill">{html.escape(c)}</span>'
                    for c in active_report.decision_criteria
                )
                st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)

            if active_report.option_matrix:
                st.markdown("#### Bảng so sánh Phương án × Tiêu chí quyết định")
                matrix_rows = []
                for row in active_report.option_matrix:
                    item = {"Phương án": row.option}
                    for crit in active_report.decision_criteria:
                        item[crit] = row.criteria_assessment.get(crit, "—")
                    item["Đánh giá & Điều kiện phù hợp"] = row.suitability
                    item["Mã bằng chứng"] = ", ".join(row.evidence_ids)
                    matrix_rows.append(item)
                st.dataframe(matrix_rows, use_container_width=True, hide_index=True)

        with tab2:
            _render_insights_interactive(active_report)

        with tab3:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("#### 3.1 Kiểm tra tiền đề trong câu hỏi (Premise Check)")
                if not active_report.premise_checks:
                    st.write("Không phát hiện tiền đề ngầm bất thường.")
                else:
                    for pc in active_report.premise_checks:
                        eids = (
                            f" (Bằng chứng: {', '.join(pc.evidence_ids)})"
                            if pc.evidence_ids
                            else ""
                        )
                        st.markdown(
                            f"- **Tiền đề:** *{pc.premise}*  \n"
                            f"  **Kết luận:** `{pc.status}` — {pc.explanation}{eids}"
                        )

                st.markdown("#### 3.2 Mâu thuẫn số liệu / nhận định giữa các nguồn")
                if not active_report.conflicts:
                    st.write("Không ghi nhận mâu thuẫn trực tiếp giữa các nguồn đã xác minh.")
                else:
                    for cf in active_report.conflicts:
                        vals_str = " vs. ".join(cf.values) if cf.values else ""
                        eids = (
                            f" (Bằng chứng: {', '.join(cf.evidence_ids)})"
                            if cf.evidence_ids
                            else ""
                        )
                        st.markdown(
                            f"- **{cf.topic}**: {vals_str}  \n"
                            f"  *Giải thích khác biệt (định nghĩa / phạm vi / kỳ):* {cf.explanation}{eids}"
                        )

            with col_b:
                st.markdown("#### 4.1 Khoảng trống dữ liệu & Điều chưa chắc chắn")
                for g in active_report.gaps:
                    st.markdown(f"- {g}")

                st.markdown("#### 4.2 Điều gì sẽ làm thay đổi kết luận?")
                for w in active_report.what_would_change:
                    st.markdown(f"- {w}")

                st.markdown("#### 4.3 Bước kiểm chứng tiếp theo (Từ rẻ nhất đến đắt nhất)")
                for idx, nc in enumerate(active_report.next_checks, start=1):
                    st.markdown(f"{idx}. {nc}")

        with tab4:
            tier_filter = st.radio(
                "Lọc theo Hạng nguồn:",
                options=["Tất cả", "Hạng A", "Hạng B", "Hạng C"],
                horizontal=True,
            )
            for s in active_report.sources:
                if tier_filter != "Tất cả" and f"Hạng {s.tier}" != tier_filter:
                    continue
                d_disp = s.published_date or "Không rõ ngày"
                st.markdown(
                    f'<div class="insight-card" style="padding:12px 16px;margin-bottom:8px;">'
                    f'<div><strong>{html.escape(s.id)} · <a href="{html.escape(s.url)}" target="_blank" style="color:#1D4ED8;text-decoration:none;">'
                    f'{html.escape(s.title)} ↗</a></strong></div>'
                    f'<div style="font-size:0.83rem;color:#475569;margin-top:4px;">'
                    f'Domain: <code>{html.escape(s.domain)}</code> · '
                    f'<strong>Hạng {html.escape(s.tier)}</strong> · '
                    f'Ngày đăng: <code>{html.escape(d_disp)}</code> ({html.escape(s.freshness_label)}) · '
                    f'{html.escape(s.tier_reason)}'
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

        with tab5:
            st.markdown("#### Tiến trình thực thi Pipeline 6 bước")
            for log_line in trace.get("step_logs", []):
                st.write(f"- {log_line}")

            st.markdown("#### Câu hỏi phụ & Truy vấn tìm kiếm đã tự động sinh")
            q_col1, q_col2 = st.columns(2)
            with q_col1:
                st.markdown("**Các câu hỏi phụ (Sub-questions):**")
                for sq in trace.get("sub_questions", []):
                    st.write(f"- {sq}")
            with q_col2:
                st.markdown("**Truy vấn tìm kiếm đã chạy:**")
                for qr in trace.get("queries_executed", []):
                    st.write(f"- `{qr}`")

            st.markdown("#### Lý do loại nguồn (`rejected_sources`)")
            if q.rejected_sources:
                st.dataframe(
                    [
                        {"Nguồn / URL": r.item_id, "Lý do loại": r.reason}
                        for r in q.rejected_sources
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.write("Không có nguồn nào bị loại.")

            st.markdown("#### Lý do loại trích dẫn (`rejected_quotes`)")
            if q.rejected_quotes:
                st.dataframe(
                    [
                        {
                            "Mã trích dẫn": r.item_id,
                            "Lý do loại": r.reason,
                            "Nội dung": r.detail,
                        }
                        for r in q.rejected_quotes
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.write("100% trích dẫn đều khớp nguyên văn (0 trích dẫn bị loại).")

        with tab6:
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


if __name__ == "__main__":
    main()
