"""Streamlit application for Gamota Game Market Research MVP (Mission 2 & Mission 3 · Change Request A2)."""

from __future__ import annotations

from datetime import date
import html
import json
import os
from pathlib import Path
import streamlit as st

from research.grade import parse_published_date
from research.llm import LLMClient, LLMQuotaOrKeyError
from research.pipeline import render_report_markdown, run
from research.recency import apply_recency_layer, rescore_report_as_of
from research.refresh import refresh_old_sources
from research.schemas import Report

CACHED_RUNS_DIR = Path(__file__).resolve().parent / "data" / "cached_runs"

MODE_CACHED = "Xem báo cáo mẫu đã chạy thật (TC1–TC7)"
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
    {
        "code": "TC7",
        "stem": "tc7_cr_a2_refreshed",
        "short_title": "TC7 · Làm mới nguồn cũ (A2)",
        "group_tag": "Mission 3 · Change Request A2",
        "question": "Mô hình kiếm tiền nào đang hiệu quả với game casual tại Indonesia và Philippines?",
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
    .certainty-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 14px;
        height: 100%;
        font-size: 0.88rem;
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
    .badge-recency-old {
        background-color: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    .badge-recency-partial {
        background-color: #FFFBEB;
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


def _find_cached_run_for_preset(
    cached_runs: list[tuple[str, Path, Report]], preset: dict[str, str]
) -> tuple[int, Report] | None:
    """Match preset by file stem FIRST, and fall back to question text ONLY if no stem matches (BRIEF_M3 4.8)."""
    target_stem = preset["stem"].lower().strip()
    for c_idx, (_lbl, c_path, c_rep) in enumerate(cached_runs):
        if c_path.stem.lower() == target_stem:
            return c_idx, c_rep
    target_q = preset["question"].strip()
    for c_idx, (_lbl, _c_path, c_rep) in enumerate(cached_runs):
        if c_rep.question.strip() == target_q:
            return c_idx, c_rep
    return None


@st.cache_data(show_spinner=False)
def _cached_apply_recency(report_json: str, cache_key: str) -> str:
    """Ensure Report has recency layer computed in memory, cached by run_timestamp + reference_date."""
    _ = cache_key
    rep = Report.model_validate_json(report_json)
    if rep.recency is not None:
        return report_json
    ref_str = str((rep.trace or {}).get("current_date") or "").strip()
    ref_dt = parse_published_date(ref_str) if ref_str else None
    enriched = apply_recency_layer(rep, reference_date=ref_dt)
    return enriched.model_dump_json()


def ensure_report_recency(report: Report) -> Report:
    """Return Report with recency layer populated (computed lazily only for the active report)."""
    if report.recency is not None:
        return report
    trace = report.trace or {}
    key = f"{trace.get('run_timestamp', '')}::{trace.get('current_date', '')}::{report.question}"
    enriched_json = _cached_apply_recency(report.model_dump_json(), key)
    return Report.model_validate_json(enriched_json)


def _conf_badge_html(conf: str) -> str:
    if conf == "CAO":
        cls = "badge badge-cao"
    elif conf == "TRUNG BÌNH":
        cls = "badge badge-tb"
    else:
        cls = "badge badge-thap"
    return f'<span class="{cls}">Độ tin cậy: {html.escape(conf)}</span>'


def _recency_badge_html(rec_status: str) -> str:
    """Render recency badge on insight card ONLY when status is not MỚI (BRIEF_M3 4.8)."""
    if rec_status == "KHÔNG CÓ BẰNG CHỨNG MỚI":
        return '<span class="badge badge-recency-old">Độ mới: KHÔNG CÓ BẰNG CHỨNG MỚI (&gt;18 tháng / chưa rõ)</span>'
    if rec_status == "MỘT PHẦN CŨ":
        return '<span class="badge badge-recency-partial">Độ mới: MỘT PHẦN DỰA TRÊN DỮ LIỆU CŨ</span>'
    return ""


def _render_insights_interactive(report: Report) -> None:
    """Render filterable, easy-to-scan Insight cards with direct highlight links and recency metadata."""
    source_map = {s.id: s for s in report.sources}
    evidence_map = {e.id: e for e in report.evidences}
    src_rec_map = (
        {sr.source_id: sr for sr in report.recency.sources}
        if report.recency
        else {}
    )
    ins_rec_map = (
        {ir.insight_id: ir for ir in report.recency.insights}
        if report.recency
        else {}
    )

    f_col1, f_col2, f_col3, f_col4 = st.columns([1.1, 1.2, 1.8, 1.3])
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
    with f_col4:
        st.write("")
        only_old_data = st.checkbox(
            "Chỉ hiện nhận định dựa trên dữ liệu cũ",
            value=False,
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
        ir = ins_rec_map.get(ins.id)
        if only_old_data and (ir is None or ir.status == "MỚI"):
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
        ir = ins_rec_map.get(ins.id)
        rec_badge = _recency_badge_html(ir.status) if ir else ""
        badge_html = (
            f"{_conf_badge_html(ins.confidence)}"
            f'<span class="badge badge-type">{type_str}</span>'
            f"{rec_badge}"
        )
        rec_note_html = ""
        if ir and ir.status != "MỚI" and ir.note:
            rec_note_html = (
                f'<div style="margin-top:5px;font-size:0.82rem;color:#92400E;">'
                f"<strong>Lưu ý tuổi dữ liệu:</strong> {html.escape(ir.note)}</div>"
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
                sr = src_rec_map.get(src.id)
                date_disp = sr.date_display if sr else (src.published_date or "Không rõ ngày")
                method_lbl = sr.date_method_label if sr else (src.date_method or "không rõ")
                age_disp = sr.age_display if sr else src.freshness_label
                period_disp = ev.data_period or (sr.data_vintage if sr and sr.data_vintage else "")
                period_html = (
                    f" · Kỳ số liệu: <code>{html.escape(period_disp)}</code>"
                    if period_disp
                    else ""
                )
                link_url = html.escape(ev.highlight_url or src.url)
                dom_disp = html.escape(src.domain)
                q_disp = html.escape(ev.quote)
                ev_blocks.append(
                    f'<div class="quote-box">'
                    f'<div><strong>[{html.escape(eid)}] Nguyên văn:</strong> <em>"{q_disp}"</em> '
                    f'<span style="color:#64748B;font-size:0.78rem;">(Khớp chuỗi: {ev.match_score}%)</span></div>'
                    f'<div style="margin-top:4px;font-size:0.82rem;">'
                    f"Nguồn: <strong>{html.escape(src.id)} ({dom_disp})</strong> · "
                    f"<strong>Hạng {html.escape(src.tier)}</strong> · "
                    f"Ngày đăng: <code>{html.escape(date_disp)}</code> ({html.escape(method_lbl)}) · "
                    f"Tuổi: <code>{html.escape(age_disp)}</code>{period_html} · "
                    f'<a href="{link_url}" target="_blank" rel="noopener noreferrer" style="color:#1D4ED8;font-weight:600;text-decoration:none;">'
                    f"Mở bài báo gốc & tô sáng câu trích dẫn ↗</a>"
                    f"</div></div>"
                )

        ev_html = "".join(ev_blocks)
        card_html = (
            f'<div class="insight-card">'
            f'<div style="margin-bottom:8px;"><strong>{html.escape(ins.id)}</strong> &nbsp; {badge_html} '
            f'<span style="font-size:0.8rem;color:#64748B;">({html.escape(ins.confidence_reason)})</span></div>'
            f'<div style="font-size:0.96rem;color:#0F172A;font-weight:500;line-height:1.55;">{html.escape(ins.statement)}</div>'
            f"{rec_note_html}"
            f"{assump_html}"
            f"{ev_html}"
            f"</div>"
        )
        st.markdown(card_html, unsafe_allow_html=True)


def _render_recency_tab(
    active_report: Report,
    cached_runs: list[tuple[str, Path, Report]],
    has_key: bool,
    max_live_runs: int,
) -> None:
    """Render Tab 3: Độ mới & Ảnh hưởng (A2) per BRIEF_M3 section 4.8."""
    assert active_report.recency is not None
    trace = active_report.trace or {}
    run_date_str = str(
        trace.get("current_date") or active_report.recency.reference_date
    )
    today_date = date.today()
    today_str = today_date.isoformat()

    st.markdown(
        "#### Phân tích độ mới dữ liệu & Ảnh hưởng tới độ tin cậy (Change Request A2)"
    )

    opt_run = f"Ngày chạy báo cáo ({run_date_str})"
    opt_today = f"Hôm nay ({today_str})"
    calc_mode = st.radio(
        "Tính độ mới theo:",
        options=[opt_run, opt_today],
        index=0,
        horizontal=True,
        key="recency_as_of_mode",
    )

    view_report = active_report
    if calc_mode == opt_today and today_str != active_report.recency.reference_date:
        view_report = rescore_report_as_of(active_report, as_of=today_date)
        # Summarize differences vs run_date
        old_s_map = {s.id: s for s in active_report.sources}
        old_sr_map = {sr.source_id: sr for sr in active_report.recency.sources}
        old_i_map = {i.id: i for i in active_report.insights}

        src_diffs: list[str] = []
        assert view_report.recency is not None
        for n_s in view_report.sources:
            o_s = old_s_map.get(n_s.id)
            if o_s and o_s.freshness != n_s.freshness:
                src_diffs.append(
                    f"Nguồn `{n_s.id}` ({n_s.domain}): nhóm độ mới chấm điểm đổi `{o_s.freshness}` → `{n_s.freshness}`"
                )
        for n_sr in view_report.recency.sources:
            o_sr = old_sr_map.get(n_sr.source_id)
            if o_sr and o_sr.status != n_sr.status:
                src_diffs.append(
                    f"Nguồn `{n_sr.source_id}`: trạng thái cảnh báo 18 tháng đổi `{o_sr.status}` → `{n_sr.status}`"
                )
        ins_diffs: list[str] = []
        for n_i in view_report.insights:
            o_i = old_i_map.get(n_i.id)
            if o_i and o_i.confidence != n_i.confidence:
                ins_diffs.append(
                    f"Nhận định `{n_i.id}`: độ tin cậy đổi `{o_i.confidence}` → `{n_i.confidence}`"
                )

        if src_diffs or ins_diffs:
            st.info(
                "**Thay đổi khi tính lại ở ngày hôm nay so với ngày chạy báo cáo:**\n"
                + "\n".join(f"- {d}" for d in (src_diffs + ins_diffs))
            )
        else:
            st.caption(
                f"Khi tính lại ở ngày hôm nay (`{today_str}`), tuổi nguồn tăng thêm nhưng chưa có nguồn hay nhận định nào vượt ngưỡng đổi mức độ tin cậy so với ngày `{run_date_str}`."
            )

    rec = view_report.recency
    assert rec is not None
    src_map = {s.id: s for s in view_report.sources}
    ev_map = {e.id: e for e in view_report.evidences}

    st.markdown(
        f"**Ngày tham chiếu đang xem:** `{rec.reference_date}` · "
        f"**Ngưỡng cảnh báo:** `> {rec.alert_months} tháng` · "
        f"**Mức ảnh hưởng:** `{rec.impact_level}` — {rec.summary}"
    )

    # 2. Source Recency Table (7.1)
    st.markdown("##### 1. Bảng nguồn thông tin và tuổi dữ liệu (7.1)")
    src_rows = []
    for sr in rec.sources:
        sobj = src_map.get(sr.source_id)
        src_rows.append(
            {
                "Mã": sr.source_id,
                "Domain": sobj.domain if sobj else "",
                "Hạng": f"Hạng {sobj.tier}" if sobj else "",
                "Ngày đăng": sr.date_display,
                "Cách xác định ngày": sr.date_method_label,
                "Tuổi ước tính": sr.age_display,
                "Kỳ số liệu trong trích dẫn": sr.data_vintage or "—",
                "Trạng thái": sr.status,
                "Lý do trạng thái": "; ".join(sr.reasons),
                "Nguồn then chốt": ("Có (" + "; ".join(sr.key_reasons) + ")") if sr.is_key else "Không",
                "Hỗ trợ nhận định": ", ".join(sr.supported_insight_ids) or "—",
                "Cờ ngày đăng": "Có thể sai" if sr.date_conflict else "Bình thường",
            }
        )
    st.dataframe(src_rows, use_container_width=True, hide_index=True)

    # 3. Key Old Sources Expanders (7.2)
    st.markdown(
        "##### 2. Ảnh hưởng của từng nguồn then chốt cũ tới các nhận định — Phân tích phản thực tế bằng code (7.2)"
    )
    if not rec.key_old_sources:
        st.success(
            "Không có nguồn then chốt nào bị cũ (> 18 tháng) hoặc chưa rõ tuổi."
        )
    else:
        for kos in rec.key_old_sources:
            sobj = src_map.get(kos.source_id)
            sr_obj = next(
                (x for x in rec.sources if x.source_id == kos.source_id), None
            )
            exp_title = (
                f"{kos.source_id} ({sobj.domain if sobj else ''}, Hạng {sobj.tier if sobj else ''}) · "
                f"Ngày: {sr_obj.date_display if sr_obj else ''} · "
                f"Trạng thái: {sr_obj.status if sr_obj else ''}"
            )
            with st.expander(exp_title, expanded=True):
                st.markdown(f"**Tóm tắt ảnh hưởng:** {kos.summary}")
                imp_rows = [
                    {
                        "Nhận định": imp.insight_id,
                        "Độ tin cậy hiện tại": imp.current,
                        "Nếu bỏ nguồn này": imp.if_source_removed,
                        "Nếu nguồn này còn mới (≤ 12 tháng)": imp.if_source_fresh,
                    }
                    for imp in kos.impacts
                ]
                st.dataframe(imp_rows, use_container_width=True, hide_index=True)

                # Show verified quotes from this source with highlight links
                src_evs = [
                    ev
                    for ev in view_report.evidences
                    if ev.verified and ev.source_id == kos.source_id
                ]
                if src_evs:
                    st.markdown("**Trích dẫn nguyên văn từ nguồn này:**")
                    for ev in src_evs:
                        hl = html.escape(
                            ev.highlight_url or (sobj.url if sobj else "")
                        )
                        p_tag = (
                            f" · Kỳ số liệu: <code>{html.escape(ev.data_period)}</code>"
                            if ev.data_period
                            else ""
                        )
                        st.markdown(
                            f'<div class="quote-box">'
                            f'<strong>[{html.escape(ev.id)}]</strong> "{html.escape(ev.quote)}"{p_tag} · '
                            f'<a href="{hl}" target="_blank" style="color:#1D4ED8;font-weight:600;text-decoration:none;">'
                            f"Mở bài gốc & tô sáng ↗</a></div>",
                            unsafe_allow_html=True,
                        )

    # 4. Upcoming Milestones (7.3) & Suggested Queries (7.4)
    col_m, col_q = st.columns(2)
    with col_m:
        st.markdown("##### 3. Mốc thời gian độ tin cậy sẽ thay đổi (7.3)")
        if not rec.upcoming_changes:
            st.write(
                "Không có nguồn đang trích dẫn nào chạm ngưỡng giảm độ tin cậy trong 12 tháng tới."
            )
        else:
            for ev_item in rec.upcoming_changes:
                st.markdown(
                    f"- **Từ `{ev_item.date}`** (nguồn `{', '.join(ev_item.source_ids)}` chuyển nhóm độ mới), nếu chưa có dữ liệu mới: "
                    + "; ".join(ev_item.changes)
                )

    with col_q:
        st.markdown("##### 4. Truy vấn gợi ý để tìm bản cập nhật mới hơn (7.4)")
        if not rec.suggested_refresh_queries:
            st.write("Không cần sinh truy vấn làm mới.")
        else:
            for sq in rec.suggested_refresh_queries:
                st.markdown(f"- `{sq}`")

    # 5. User Date Override Simulator ("Thử giả định ngày đăng")
    st.divider()
    with st.expander(
        "5. Thử giả định ngày đăng của một nguồn (What-if Simulator — Giả định của người dùng, không lưu vào báo cáo)",
        expanded=False,
    ):
        st.caption(
            "Giả định của người dùng, không lưu vào báo cáo: chọn một nguồn bất kỳ và thử đặt ngày đăng giả định để xem hệ thống chấm lại độ tin cậy các nhận định như thế nào."
        )
        sim_c1, sim_c2 = st.columns([2, 1.5])
        src_options = [
            f"{s.id} · {s.domain} (hiện tại: {s.published_date or 'Không rõ ngày'})"
            for s in view_report.sources
        ]
        chosen_src_lbl = sim_c1.selectbox(
            "Chọn nguồn muốn giả định ngày đăng:",
            options=src_options,
            key="sim_src_select",
        )
        chosen_sid = chosen_src_lbl.split("·")[0].strip() if chosen_src_lbl else "S1"
        sim_date = sim_c2.date_input(
            "Ngày đăng giả định:",
            value=parse_published_date(rec.reference_date) or date.today(),
            key="sim_date_input",
        )
        # Run simulation on a deep copy
        sim_sources = []
        for s in view_report.sources:
            if s.id == chosen_sid:
                sim_sources.append(
                    s.model_copy(
                        update={
                            "published_date": sim_date.isoformat(),
                            "date_method": "user_override",
                            "date_precision": "day",
                        }
                    )
                )
            else:
                sim_sources.append(s.model_copy(deep=True))
        sim_report = view_report.model_copy(update={"sources": sim_sources})
        ref_dt_sim = parse_published_date(rec.reference_date) or date.today()
        sim_scored = rescore_report_as_of(sim_report, as_of=ref_dt_sim)
        assert sim_scored.recency is not None

        sim_changes = []
        for orig_i, new_i in zip(view_report.insights, sim_scored.insights):
            if orig_i.confidence != new_i.confidence:
                sim_changes.append(
                    {
                        "Nhận định": orig_i.id,
                        "Trước giả định": orig_i.confidence,
                        "Sau giả định": new_i.confidence,
                        "Lý do mới": new_i.confidence_reason,
                    }
                )
        st.markdown(
            f"**Kết quả giả định** (nếu `{chosen_sid}` có ngày đăng `{sim_date.isoformat()}` · `do người dùng nhập giả định`): "
            f"Mức ảnh hưởng toàn báo cáo: `{rec.impact_level}` → **`{sim_scored.recency.impact_level}`**."
        )
        if sim_changes:
            st.dataframe(sim_changes, use_container_width=True, hide_index=True)
        else:
            st.write(
                "Không có nhận định nào đổi mức độ tin cậy với ngày giả định này (lưu ý: nếu trích dẫn trong nguồn vẫn nêu kỳ số liệu cũ > 18 tháng, cảnh báo kỳ số liệu vẫn giữ nguyên)."
            )

    # 6. Targeted Refresh Loop Section (7.5)
    st.divider()
    st.markdown("##### 6. Vòng làm mới dữ liệu có mục tiêu cho nguồn cũ then chốt (7.5)")

    if active_report.refresh is not None:
        rf = active_report.refresh
        st.success(
            f"**Đã thực thi vòng làm mới** · Trạng thái: **`{rf.status}`** · "
            f"Ngày tham chiếu: `{rf.reference_date}` · Thời gian: `{rf.duration_seconds}s` ({rf.llm_calls_count} LLM calls) · "
            f"Nguồn mục tiêu: `{', '.join(rf.target_source_ids) or '—'}` · "
            f"Nguồn mới bổ sung: `{', '.join(rf.new_source_ids) or 'Không có'}`"
        )
        if rf.note:
            st.caption(f"Ghi chú: {rf.note}")

        if rf.queries:
            with st.expander(
                f"Các truy vấn tìm kiếm làm mới đã chạy ({len(rf.queries)})",
                expanded=False,
            ):
                for q_str in rf.queries:
                    st.markdown(f"- `{q_str}`")

        if rf.comparisons:
            st.markdown("**Bảng đối chiếu bằng chứng cũ ↔ bằng chứng mới:**")
            cmp_rows = [
                {
                    "Bằng chứng cũ": c.old_evidence_id,
                    "Bằng chứng mới": ", ".join(c.new_evidence_ids) or "—",
                    "Kết quả đối chiếu": c.status,
                    "Giải thích": c.explanation,
                }
                for c in rf.comparisons
            ]
            st.dataframe(cmp_rows, use_container_width=True, hide_index=True)

        if rf.confidence_changes:
            st.markdown(
                "**Bảng thay đổi độ tin cậy trước → sau làm mới (cùng ngày tham chiếu):**"
            )
            cc_rows = [
                {
                    "Nhận định": cc.insight_id,
                    "Trước làm mới": cc.before,
                    "Sau làm mới": cc.after,
                    "Lý do": cc.reason,
                }
                for cc in rf.confidence_changes
            ]
            st.dataframe(cc_rows, use_container_width=True, hide_index=True)

        if rf.rejected_new_sources:
            with st.expander(
                f"Nguồn ứng viên bị loại trong vòng làm mới ({len(rf.rejected_new_sources)})",
                expanded=False,
            ):
                rej_rows = [
                    {"URL / Nguồn": r.item_id, "Lý do loại": r.reason}
                    for r in rf.rejected_new_sources
                ]
                st.dataframe(rej_rows, use_container_width=True, hide_index=True)
    else:
        # Check if cached_runs has a pre-computed refreshed report for this report
        matching_refreshed: tuple[int, Path, Report] | None = None
        curr_ts = str(trace.get("run_timestamp", "")).strip()
        for c_idx, (_lbl, c_path, c_rep) in enumerate(cached_runs):
            if c_rep.refresh is not None:
                parent_ts = str(
                    (c_rep.trace or {}).get("parent_run_timestamp", "")
                ).strip()
                if (curr_ts and parent_ts == curr_ts) or (
                    c_rep.question.strip() == active_report.question.strip()
                ):
                    matching_refreshed = (c_idx, c_path, c_rep)
                    break

        if matching_refreshed is not None:
            r_idx, _r_path, r_rep = matching_refreshed
            assert r_rep.refresh is not None
            st.info(
                f"Báo cáo này đã có bản chạy vòng làm mới lưu sẵn (`TC7`, chạy thật lúc `{r_rep.refresh.refreshed_at}`, trạng thái `{r_rep.refresh.status}`). "
                "Bạn có thể bấm nút dưới đây để xem ngay mà không tốn API key."
            )
            if st.button(
                f"Xem bản đã làm mới (chạy thật lúc {r_rep.refresh.refreshed_at})",
                type="primary",
                key="btn_open_cached_refresh",
            ):
                st.session_state["selected_cached_idx"] = r_idx
                st.session_state["active_report"] = ensure_report_recency(r_rep)
                st.rerun()

        if st.button(
            "Tìm dữ liệu mới hơn cho nguồn cũ (Live)",
            key="btn_live_refresh",
        ):
            if st.session_state["live_runs_used"] >= max_live_runs:
                st.error(
                    f"Đã đạt giới hạn {max_live_runs} lượt chạy Live trong phiên này."
                )
            elif not has_key:
                st.error(
                    "Chưa cấu hình GEMINI_API_KEY để chạy làm mới trực tiếp. Vui lòng bấm chọn TC7 hoặc nút 'Xem bản đã làm mới' ở trên."
                )
            else:
                with st.status(
                    "Đang chạy vòng làm mới dữ liệu có mục tiêu cho nguồn cũ then chốt...",
                    expanded=True,
                ) as rf_status:

                    def _rf_cb(step_title: str, detail: str) -> None:
                        rf_status.write(f"**{step_title}**: {detail}")

                    refreshed_rep = refresh_old_sources(
                        active_report,
                        reference_date=date.today(),
                        use_cache=True,
                        progress_callback=_rf_cb,
                    )
                    st.session_state["live_runs_used"] += 1
                    st.session_state["active_report"] = refreshed_rep
                    rf_status.update(
                        label=f"Hoàn tất vòng làm mới: {refreshed_rep.refresh.status if refreshed_rep.refresh else ''}",
                        state="complete",
                        expanded=False,
                    )
                    st.rerun()


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
        "xếp hạng nguồn A/B/C, chấm điểm độ tin cậy (CAO / TRUNG BÌNH / THẤP) và phân tích ảnh hưởng của dữ liệu cũ (> 18 tháng · Change Request A2) bằng quy tắc code minh bạch."
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
        st.subheader("Chọn nhanh 7 tình huống (TC1–TC7)")
        st.caption("Bấm vào bất kỳ tình huống nào dưới đây để mở ngay báo cáo tương ứng:")
        for preset in PRESET_CASES:
            if st.button(
                f"{preset['short_title']} ({preset['group_tag']})",
                key=f"sb_{preset['code']}",
                use_container_width=True,
            ):
                st.session_state["question_input"] = preset["question"]
                matched = _find_cached_run_for_preset(cached_runs, preset)
                if matched is not None:
                    st.session_state["selected_cached_idx"] = matched[0]
                    st.session_state["active_report"] = matched[1]

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

    # Quick 7-case selector bar on main page
    st.markdown("##### 1. Chọn nhanh tình huống kiểm thử TC1–TC7 (Bấm để xem ngay kết quả)")
    p_cols = st.columns(len(PRESET_CASES))
    for idx, preset in enumerate(PRESET_CASES):
        if p_cols[idx].button(
            preset["short_title"],
            key=f"main_{preset['code']}",
            help=f"{preset['group_tag']}: {preset['question']}",
            use_container_width=True,
        ):
            st.session_state["question_input"] = preset["question"]
            matched = _find_cached_run_for_preset(cached_runs, preset)
            if matched is not None:
                st.session_state["selected_cached_idx"] = matched[0]
                st.session_state["active_report"] = matched[1]

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
                "Bạn vẫn có thể bấm chọn xem toàn bộ các báo cáo mẫu (TC1–TC7) ở thanh phía trên."
            )
        elif not has_key:
            st.error(
                "Chưa cấu hình GEMINI_API_KEY trong .env hoặc Secrets của ứng dụng. "
                "Vui lòng bấm chọn các báo cáo mẫu (TC1–TC7) ở thanh phía trên để xem kết quả chạy thật."
            )
        else:
            try:
                with st.status(
                    "Đang thực thi Pipeline 6 bước (Plan → Retrieve → Grade → Extract → Synthesize → Score + Recency)...",
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
                    "Gợi ý: Bạn có thể bấm vào các nút TC1–TC7 ở trên để xem ngay các bản chạy thật đã lưu sẵn."
                )
            except Exception as exc:
                st.error(
                    f"Đã xảy ra lỗi khi gọi API trực tiếp: {type(exc).__name__}: {exc}\n\n"
                    "Gợi ý: Bạn có thể bấm vào các nút TC1–TC7 ở trên để xem các bản chạy thật đã lưu."
                )

    raw_active: Report | None = st.session_state.get("active_report")
    if raw_active is not None:
        active_report = ensure_report_recency(raw_active)
        st.session_state["active_report"] = active_report
        assert active_report.recency is not None
        rec = active_report.recency

        st.divider()
        q = active_report.quality
        trace = active_report.trace or {}

        # Header info line for active report
        st.markdown(
            f"**Đang hiển thị báo cáo cho câu hỏi:** {active_report.question}  \n"
            f"<span style='color:#64748B;font-size:0.84rem;'>"
            f"Thời điểm chạy: <code>{trace.get('run_timestamp', 'N/A')}</code> · "
            f"Ngày tham chiếu: <code>{rec.reference_date}</code> · "
            f"Thời gian xử lý: <code>{trace.get('duration_seconds', 0)}s</code> · "
            f"Model: <code>{trace.get('llm_provider', '')}/{trace.get('llm_model', '')}</code> ({trace.get('llm_calls_count', 0)} LLM calls) · "
            f"Search: <code>{trace.get('search_provider', '')}</code>"
            f"</span>",
            unsafe_allow_html=True,
        )

        # Recency impact banner right below report info line (BRIEF_M3 4.8)
        clean_sum = rec.summary
        prefix_to_strip = f"Mức ảnh hưởng: {rec.impact_level}."
        if clean_sum.startswith(prefix_to_strip):
            clean_sum = clean_sum[len(prefix_to_strip) :].strip()
        banner_msg = f"Độ mới dữ liệu, mức ảnh hưởng {rec.impact_level}: {clean_sum}"
        if rec.impact_level == "ĐÁNG KỂ":
            st.warning(banner_msg)
        elif rec.impact_level in ("VỪA PHẢI", "NHỎ"):
            st.info(banner_msg)
        else:
            st.success(banner_msg)

        # 4 Self-check metric cards (keep exact count == 4 per invariant 4.1)
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

        # Structured tabs with Tab 3 = Độ mới & Ảnh hưởng (A2)
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
            [
                "1. Tóm tắt & Khuyến nghị",
                f"2. Nhận định & Trích dẫn ({len(active_report.insights)})",
                "3. Độ mới & Ảnh hưởng (A2)",
                "4. Tiền đề, Mâu thuẫn & Khoảng trống",
                f"5. Nguồn thông tin ({len(active_report.sources)})",
                "6. Nhật ký Pipeline & Tự kiểm",
                "7. Bản đầy đủ (Markdown & Tải file)",
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

            # Certainty groups block (BRIEF_M3 4.8)
            st.markdown("#### Mức chắc chắn của các nhận định (phân nhóm theo độ tin cậy & tuổi dữ liệu)")
            cg = rec.certainty_groups or {}
            ins_by_id = {i.id: i for i in active_report.insights}
            cg_cols = st.columns(3)
            cg_configs = [
                (
                    "Đủ cơ sở",
                    "Đủ cơ sở (dựa trên nguồn mới)",
                    "#166534",
                    "#DCFCE7",
                ),
                (
                    "Cần lưu ý",
                    "Cần lưu ý (một phần cũ / suy luận)",
                    "#92400E",
                    "#FEF3C7",
                ),
                (
                    "Chưa chắc chắn",
                    "Chưa chắc chắn (thiếu bằng chứng mới / mức THẤP)",
                    "#475569",
                    "#F1F5F9",
                ),
            ]
            for col_obj, (g_key, g_label, g_color, g_bg) in zip(cg_cols, cg_configs):
                iids = cg.get(g_key, [])
                items_html = ""
                if not iids:
                    items_html = "<div style='color:#64748B;font-size:0.84rem;'>Không có nhận định nào trong nhóm này.</div>"
                else:
                    for iid in iids:
                        ins_obj = ins_by_id.get(iid)
                        snippet = (
                            (ins_obj.statement[:90] + "...")
                            if ins_obj and len(ins_obj.statement) > 90
                            else (ins_obj.statement if ins_obj else "")
                        )
                        conf_str = ins_obj.confidence if ins_obj else ""
                        items_html += (
                            f"<div style='margin-bottom:6px;font-size:0.84rem;'>"
                            f"<strong>{html.escape(iid)} ({html.escape(conf_str)}):</strong> {html.escape(snippet)}</div>"
                        )
                col_obj.markdown(
                    f'<div class="certainty-box">'
                    f'<div style="background-color:{g_bg};color:{g_color};padding:4px 8px;border-radius:4px;font-weight:600;margin-bottom:8px;">'
                    f"{html.escape(g_label)} ({len(iids)})</div>"
                    f"{items_html}</div>",
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
            _render_recency_tab(
                active_report=active_report,
                cached_runs=cached_runs,
                has_key=has_key,
                max_live_runs=max_live_runs,
            )

        with tab4:
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

        with tab5:
            tier_filter = st.radio(
                "Lọc theo Hạng nguồn:",
                options=["Tất cả", "Hạng A", "Hạng B", "Hạng C"],
                horizontal=True,
            )
            sr_by_id = {sr.source_id: sr for sr in rec.sources}
            for s in active_report.sources:
                if tier_filter != "Tất cả" and f"Hạng {s.tier}" != tier_filter:
                    continue
                sr = sr_by_id.get(s.id)
                d_disp = sr.date_display if sr else (s.published_date or "Không rõ ngày")
                m_lbl = sr.date_method_label if sr else (s.date_method or "không rõ")
                age_lbl = sr.age_display if sr else s.freshness_label
                r_stat = sr.status if sr else "—"
                conflict_flag = ""
                if sr and sr.date_conflict:
                    conflict_flag = (
                        f' · <span style="color:#B91C1C;font-weight:600;">'
                        f"⚠ Ngày đăng có thể sai ({html.escape('; '.join(sr.reasons))})</span>"
                    )
                st.markdown(
                    f'<div class="insight-card" style="padding:12px 16px;margin-bottom:8px;">'
                    f'<div><strong>{html.escape(s.id)} · <a href="{html.escape(s.url)}" target="_blank" style="color:#1D4ED8;text-decoration:none;">'
                    f"{html.escape(s.title)} ↗</a></strong></div>"
                    f'<div style="font-size:0.83rem;color:#475569;margin-top:4px;">'
                    f"Domain: <code>{html.escape(s.domain)}</code> · "
                    f"<strong>Hạng {html.escape(s.tier)}</strong> · "
                    f"Ngày đăng: <code>{html.escape(d_disp)}</code> ({html.escape(m_lbl)}) · "
                    f"Tuổi: <code>{html.escape(age_lbl)}</code> · "
                    f"Trạng thái A2: <strong>{html.escape(r_stat)}</strong>{conflict_flag} · "
                    f"{html.escape(s.tier_reason)}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

        with tab6:
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

        with tab7:
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
