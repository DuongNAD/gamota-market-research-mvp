"""Main 6-step market research pipeline (`run(question) -> Report`) and Vietnamese Markdown renderer."""

from __future__ import annotations

from datetime import date, datetime
import time
from typing import Callable, Optional

from research.dates import DATE_METHOD_LABELS, format_date_display
from research.extract import extract_claims_from_sources
from research.llm import LLMClient
from research.recency import apply_recency_layer
from research.retrieve import retrieve_and_grade_sources
from research.schemas import (
    Insight,
    PipelineTrace,
    Report,
)
from research.score import score_and_finalize_report
from research.synthesize import plan_research, synthesize_report

ProgressCallback = Callable[[str, str], None]


def _default_progress(_step: str, _detail: str) -> None:
    pass


def run(
    question: str,
    progress_callback: Optional[ProgressCallback] = None,
    use_cache: bool = True,
    reference_date: Optional[date] = None,
    refresh_old: bool = False,
    llm_client: Optional[LLMClient] = None,
    alert_months: Optional[int] = None,
) -> Report:
    """Execute the 6-step market research pipeline: Plan -> Retrieve -> Grade -> Extract -> Synthesize -> Score."""
    t0 = time.perf_counter()
    cb = progress_callback or _default_progress
    ref_date = reference_date or date.today()
    current_date_str = ref_date.isoformat()
    llm = llm_client or LLMClient(max_calls=8, use_cache=use_cache)
    step_logs: list[str] = []

    def _log(step_title: str, detail: str) -> None:
        msg = f"[{step_title}] {detail}"
        step_logs.append(msg)
        cb(step_title, detail)

    # --- STEP 1: PLAN ---
    _log(
        "Bước 1/6 · Lập kế hoạch (Plan)",
        "Phân tách câu hỏi con, tiêu chí ra quyết định, truy vấn tìm kiếm EN/VI và tiền đề ngầm...",
    )
    plan = plan_research(question=question, llm=llm, current_date=current_date_str)
    _log(
        "Bước 1/6 · Hoàn tất Plan",
        f"Đã tạo {len(plan.sub_questions)} câu hỏi con, {len(plan.decision_criteria)} tiêu chí quyết định, "
        f"{len(plan.search_queries)} truy vấn tìm kiếm và {len(plan.implicit_premises)} tiền đề cần kiểm chứng.",
    )

    # --- STEP 2 & 3: RETRIEVE & GRADE ---
    _log(
        "Bước 2–3/6 · Thu thập & Xếp hạng nguồn (Retrieve & Grade)",
        f"Đang tìm kiếm {len(plan.search_queries)} truy vấn (top 5/truy vấn), khử trùng lặp, trích xuất nội dung và chấm hạng A/B/C...",
    )
    (
        kept_sources,
        truncated_texts,
        full_texts,
        rejected_sources,
        retrieve_stats,
    ) = retrieve_and_grade_sources(
        queries=plan.search_queries,
        keywords=plan.keywords,
        reference_date=ref_date,
        max_per_query=5,
        max_kept_sources=12,
        max_chars_per_source=6000,
        use_cache=use_cache,
    )
    tier_counts = {
        t: sum(1 for s in kept_sources if s.tier == t) for t in ("A", "B", "C")
    }
    _log(
        "Bước 2–3/6 · Hoàn tất Retrieve & Grade",
        f"Tìm thấy {retrieve_stats['raw_search_results_count']} kết quả thô -> {retrieve_stats['deduped_sources_count']} URL duy nhất "
        f"-> Giữ {len(kept_sources)} nguồn tốt nhất (Hạng A: {tier_counts['A']}, Hạng B: {tier_counts['B']}, Hạng C: {tier_counts['C']}); "
        f"Loại {len(rejected_sources)} nguồn.",
    )

    # --- STEP 4: EXTRACT & VERIFY ---
    _log(
        "Bước 4/6 · Rút trích & Xác minh trích dẫn (Extract & Verify)",
        f"Đang rút trích claim kèm trích dẫn nguyên văn <= 40 từ từ {len(kept_sources)} nguồn (gom 4 nguồn/lần gọi LLM) và kiểm tra bằng RapidFuzz >= 90...",
    )
    (
        verified_evidences,
        rejected_quotes,
        total_quotes_extracted,
    ) = extract_claims_from_sources(
        question=question,
        sub_questions=plan.sub_questions,
        sources=kept_sources,
        source_texts=truncated_texts,
        full_source_texts=full_texts,
        llm=llm,
        current_date=current_date_str,
        batch_size=4,
    )
    _log(
        "Bước 4/6 · Hoàn tất Extract & Verify",
        f"Xác minh thành công {len(verified_evidences)}/{total_quotes_extracted} trích dẫn nguyên văn "
        f"(Loại {len(rejected_quotes)} trích dẫn không đạt chuẩn).",
    )

    # --- STEP 5: SYNTHESIZE ---
    _log(
        "Bước 5/6 · Tổng hợp nhận định (Synthesize)",
        f"Đang tổng hợp nhận định, kiểm tra tiền đề, phát hiện mâu thuẫn và khoảng trống dữ liệu từ {len(verified_evidences)} bằng chứng đã xác minh...",
    )
    synthesis = synthesize_report(
        question=question,
        plan=plan,
        sources=kept_sources,
        verified_evidences=verified_evidences,
        llm=llm,
        current_date=current_date_str,
    )
    _log(
        "Bước 5/6 · Hoàn tất Synthesize",
        f"Đã tổng hợp {len(synthesis.insights)} nhận định dự thảo, {len(synthesis.conflicts)} điểm mâu thuẫn, "
        f"{len(synthesis.premise_checks)} kiểm tra tiền đề và {len(synthesis.gaps)} khoảng trống dữ liệu.",
    )

    # --- STEP 6: SCORE & SELF-CHECK ---
    _log(
        "Bước 6/6 · Chấm điểm độ tin cậy & Tự kiểm (Score & Self-Check)",
        "Áp dụng quy tắc chấm điểm CAO/TRUNG BÌNH/THẤP, gắn link Text Fragment và tính chỉ số tự kiểm...",
    )
    draft_insights = [
        Insight(
            id=f"I{idx + 1}",
            statement=di.statement,
            type=di.type,
            evidence_ids=di.evidence_ids,
            assumptions=di.assumptions,
            is_forecast=di.is_forecast,
            has_conflict=di.has_conflict,
        )
        for idx, di in enumerate(synthesis.insights)
    ]

    duration_sec = round(time.perf_counter() - t0, 2)
    trace_obj = PipelineTrace(
        run_timestamp=datetime.now().isoformat(timespec="seconds"),
        current_date=current_date_str,
        duration_seconds=duration_sec,
        llm_provider=llm.provider,
        llm_model=llm.model,
        llm_calls_count=llm.calls_count,
        search_provider=str(retrieve_stats.get("search_provider", "unknown")),
        queries_executed=plan.search_queries,
        sub_questions=plan.sub_questions,
        decision_criteria=plan.decision_criteria,
        implicit_premises=plan.implicit_premises,
        raw_search_results_count=int(retrieve_stats.get("raw_search_results_count", 0)),
        deduped_sources_count=int(retrieve_stats.get("deduped_sources_count", 0)),
        kept_sources_count=len(kept_sources),
        step_logs=step_logs,
        keywords=plan.keywords,
        version=1,
    )

    raw_report = Report(
        question=question,
        short_answer=synthesis.short_answer,
        recommendation=synthesis.recommendation,
        decision_criteria=plan.decision_criteria,
        option_matrix=synthesis.option_matrix,
        insights=draft_insights,
        conflicts=synthesis.conflicts,
        premise_checks=synthesis.premise_checks,
        gaps=synthesis.gaps,
        what_would_change=synthesis.what_would_change,
        next_checks=synthesis.next_checks,
        sources=kept_sources,
        evidences=verified_evidences,
        trace=trace_obj.model_dump(),
    )

    final_report = score_and_finalize_report(
        report=raw_report,
        total_quotes_extracted=total_quotes_extracted,
        rejected_sources=rejected_sources,
        rejected_quotes=rejected_quotes,
    )

    final_report = apply_recency_layer(
        report=final_report,
        reference_date=ref_date,
        alert_months=alert_months,
    )
    if final_report.recency is not None:
        _log(
            "Bước 6b/6 · Phân tích độ mới dữ liệu (Change Request A2)",
            f"Mức ảnh hưởng: {final_report.recency.impact_level} | "
            f"Số nguồn then chốt cũ (> {final_report.recency.alert_months} tháng hoặc chưa rõ tuổi): "
            f"{len(final_report.recency.key_old_sources)}.",
        )

    duration_sec = round(time.perf_counter() - t0, 2)
    _log(
        "Bước 6/6 · Hoàn tất",
        f"Hoàn thành trong {duration_sec}s với {llm.calls_count} lần gọi LLM. "
        f"Tỷ lệ trích dẫn xác minh: {final_report.quality.verified_quote_rate}% | "
        f"Số nhận định CAO từ nguồn C: {final_report.quality.high_confidence_from_tier_c_only_count}.",
    )
    final_report.trace["step_logs"] = step_logs
    final_report.trace["duration_seconds"] = duration_sec
    if refresh_old:
        from research.refresh import refresh_old_sources

        final_report = refresh_old_sources(
            report=final_report,
            reference_date=ref_date,
            use_cache=use_cache,
            progress_callback=progress_callback,
        )
    return final_report


def _esc_md(text: str, is_table: bool = True) -> str:
    s = (text or "").replace("$", r"\$")
    if is_table:
        s = s.replace("|", "/").replace("\n", " ")
    return s


def render_report_markdown(report: Report) -> str:
    """Render Report into a structured 6-part (plus Section 7 Recency Impact) Vietnamese Markdown document."""
    source_map = {s.id: s for s in report.sources}
    evidence_map = {e.id: e for e in report.evidences}
    src_rec_map = (
        {sr.source_id: sr for sr in report.recency.sources}
        if report.recency is not None
        else {}
    )

    lines: list[str] = []
    lines.append(f"# Báo cáo Nghiên cứu Thị trường Game")
    lines.append(f"**Câu hỏi nghiên cứu:** {_esc_md(report.question, False)}\n")
    trace = report.trace or {}
    if trace:
        lines.append(
            f"> **Thời điểm chạy:** `{trace.get('run_timestamp', '')}` · "
            f"**Thời gian xử lý:** `{trace.get('duration_seconds', 0)}s` · "
            f"**Model:** `{trace.get('llm_provider', '')}/{trace.get('llm_model', '')}` ({trace.get('llm_calls_count', 0)} lệnh gọi LLM) · "
            f"**Search:** `{trace.get('search_provider', '')}`\n"
        )

    # --- SECTION 1 ---
    lines.append("## 1. Trả lời ngắn & Khuyến nghị ra quyết định")
    lines.append(f"### Trả lời ngắn\n{_esc_md(report.short_answer, False)}\n")
    lines.append(f"### Khuyến nghị hành động (kèm điều kiện áp dụng)\n{_esc_md(report.recommendation, False)}\n")

    if report.decision_criteria:
        crit_str = " · ".join(f"`{c}`" for c in report.decision_criteria)
        lines.append(f"**Tiêu chí ra quyết định đã dùng:** {crit_str}\n")

    if report.option_matrix:
        lines.append("### Bảng so sánh Phương án × Tiêu chí quyết định")
        all_crit: list[str] = list(report.decision_criteria)
        for row in report.option_matrix:
            for k in row.criteria_assessment.keys():
                if k not in all_crit:
                    all_crit.append(k)
        header = "| Phương án | " + " | ".join(all_crit) + " | Đánh giá & Điều kiện phù hợp | Bằng chứng |"
        sep = "|---|" + "|".join(["---"] * len(all_crit)) + "|---|---|"
        lines.append(header)
        lines.append(sep)
        for row in report.option_matrix:
            cells = [
                _esc_md(row.criteria_assessment.get(c, "—") or "—")
                for c in all_crit
            ]
            eids_str = ", ".join(f"`{eid}`" for eid in row.evidence_ids) if row.evidence_ids else "—"
            suit_clean = _esc_md(row.suitability or "—")
            opt_clean = _esc_md(row.option)
            lines.append(f"| **{opt_clean}** | " + " | ".join(cells) + f" | {suit_clean} | {eids_str} |")
        lines.append("")

    # --- SECTION 2 ---
    lines.append("## 2. Bảng nhận định có căn cứ (Verified Insights)")
    if not report.insights:
        lines.append(
            "*Không có nhận định nào đủ bằng chứng nguyên văn đã xác minh. Xem mục 4 (Khoảng trống dữ liệu) bên dưới.*\n"
        )
    else:
        lines.append(
            "| ID | Nhận định & Giả định | Loại | Độ tin cậy & Lý do | Nguồn (Hạng, Ngày, Link tô sáng) | Trích dẫn nguyên văn (<=40 từ) |"
        )
        lines.append("|---|---|---|---|---|---|")
        for ins in report.insights:
            type_label = (
                "Thực chứng (`fact`)"
                if ins.type == "fact" and not ins.is_forecast
                else "Suy luận / Dự báo (`inference`)"
            )
            stmt_cell = _esc_md(ins.statement)
            if ins.assumptions:
                assump_str = _esc_md("; ".join(ins.assumptions))
                stmt_cell += f"<br>*(Giả định: {assump_str})*"

            conf_cell = f"**{ins.confidence}**<br><small>{_esc_md(ins.confidence_reason)}</small>"

            src_links: list[str] = []
            quotes_cells: list[str] = []
            for eid in ins.evidence_ids:
                ev = evidence_map.get(eid)
                if not ev:
                    continue
                src = source_map.get(ev.source_id)
                if src:
                    sr_info = src_rec_map.get(src.id)
                    if sr_info:
                        date_part = f"`{sr_info.date_display}` · {sr_info.age_display}"
                        if ev.data_period:
                            date_part += f" (số liệu `{ev.data_period}`)"
                    else:
                        date_disp = src.published_date or "Không rõ ngày"
                        date_part = f"`{date_disp}`"
                    link_url = ev.highlight_url or src.url
                    src_links.append(
                        f"[{eid} · {src.id} ({src.domain})]({link_url}) "
                        f"— **Hạng {src.tier}**, {date_part}"
                    )
                q_clean = _esc_md(ev.quote)
                quotes_cells.append(f"**[{eid}]** *\"{q_clean}\"* (`match={ev.match_score}%`)")

            src_cell = "<br>".join(src_links) if src_links else "—"
            quote_cell = "<br>".join(quotes_cells) if quotes_cells else "—"
            lines.append(
                f"| **{ins.id}** | {stmt_cell} | {type_label} | {conf_cell} | {src_cell} | {quote_cell} |"
            )
        lines.append("")

    # --- SECTION 3 ---
    lines.append("## 3. Mâu thuẫn giữa các nguồn & Kiểm tra tiền đề câu hỏi")
    lines.append("### 3.1 Kiểm tra tiền đề (Premise Check)")
    if not report.premise_checks:
        lines.append("- Không phát hiện tiền đề ngầm bất thường.")
    else:
        for pc in report.premise_checks:
            eids = f" (Bằng chứng: {', '.join(pc.evidence_ids)})" if pc.evidence_ids else ""
            lines.append(f"- **Tiền đề:** *{_esc_md(pc.premise, False)}* → **Kết luận: `{pc.status}`** — {_esc_md(pc.explanation, False)}{eids}")
    lines.append("")

    lines.append("### 3.2 Mâu thuẫn số liệu / nhận định giữa các nguồn")
    if not report.conflicts:
        lines.append("- Không ghi nhận mâu thuẫn trực tiếp giữa các nguồn đã xác minh.")
    else:
        for cf in report.conflicts:
            vals_str = " vs. ".join(_esc_md(v, False) for v in cf.values) if cf.values else ""
            eids = f" (Bằng chứng: {', '.join(cf.evidence_ids)})" if cf.evidence_ids else ""
            lines.append(f"- **{_esc_md(cf.topic, False)}**: {vals_str}")
            lines.append(f"  - *Giải thích khác biệt (định nghĩa / phạm vi / kỳ):* {_esc_md(cf.explanation, False)}{eids}")
    lines.append("")

    # --- SECTION 4 ---
    lines.append("## 4. Khoảng trống dữ liệu, Điều kiện đảo chiều & Bước kiểm chứng tiếp theo")
    lines.append("### 4.1 Khoảng trống dữ liệu & Điều chưa chắc chắn")
    if not report.gaps:
        lines.append("- Chưa ghi nhận khoảng trống dữ liệu trọng yếu.")
    else:
        for g in report.gaps:
            lines.append(f"- {_esc_md(g, False)}")
    lines.append("")

    lines.append("### 4.2 Điều gì sẽ làm thay đổi kết luận?")
    if not report.what_would_change:
        lines.append("- Có thêm dữ liệu sơ cấp (Hạng A) cập nhật quý gần nhất ngược với xu hướng hiện tại.")
    else:
        for w in report.what_would_change:
            lines.append(f"- {_esc_md(w, False)}")
    lines.append("")

    lines.append("### 4.3 Bước kiểm chứng tiếp theo (ưu tiên cách rẻ nhất trước)")
    if not report.next_checks:
        lines.append("1. Kiểm tra bảng xếp hạng doanh thu/lượt tải công khai trên AppMagic / Sensor Tower.")
    else:
        for idx, nc in enumerate(report.next_checks, start=1):
            lines.append(f"{idx}. {_esc_md(nc, False)}")
    lines.append("")

    # --- SECTION 5 ---
    lines.append("## 5. Danh sách nguồn thông tin (Source Grading)")
    if not report.sources:
        lines.append("*Không có nguồn nào được giữ lại.*\n")
    else:
        lines.append(
            "| Mã nguồn | Tiêu đề & Link gốc | Domain | Hạng | Ngày đăng & Độ mới | Cách xác định ngày & tuổi | Lý do xếp hạng |"
        )
        lines.append("|---|---|---|---|---|---|---|")
        for s in report.sources:
            t_clean = _esc_md(s.title)
            sr_info = src_rec_map.get(s.id)
            d_disp = sr_info.date_display if sr_info else format_date_display(s.published_date, s.date_precision)
            method_lbl = (
                sr_info.date_method_label
                if sr_info
                else DATE_METHOD_LABELS.get(s.date_method or "unknown", "không xác định được")
            )
            age_str = sr_info.age_display if sr_info else "không rõ"
            r_clean = _esc_md(s.tier_reason)
            lines.append(
                f"| **{s.id}** | [{t_clean}]({s.url}) | `{s.domain}` | **Hạng {s.tier}** | "
                f"`{d_disp}` ({s.freshness_label}) | {_esc_md(method_lbl)} · `{age_str}` | {r_clean} |"
            )
        lines.append("")

    # --- SECTION 6 ---
    q = report.quality
    lines.append("## 6. Tự kiểm chất lượng (Self-Check Quality Metrics)")
    lines.append(
        f"- **Tỷ lệ trích dẫn xác minh được (`rapidfuzz >= 90`):** `{q.verified_quote_rate}%` "
        f"({q.verified_quotes_count}/{q.total_quotes_extracted} trích dẫn)"
    )
    lines.append(
        f"- **Tỷ lệ nhận định có ≥ 1 bằng chứng đã xác minh:** `{q.insights_with_verified_evidence_rate}%` "
        f"({q.total_insights_count} nhận định hợp lệ)"
    )
    lines.append(
        f"- **Số nhận định CAO chỉ dựa trên nguồn hạng C (bắt buộc = 0):** `{q.high_confidence_from_tier_c_only_count}`"
    )
    lines.append(
        f"- **Số URL do LLM tự viết bị phát hiện và lọc bỏ:** `{q.llm_invented_urls_removed_count}`"
    )
    lines.append(f"- **Số nguồn bị loại:** `{q.rejected_sources_count}` · **Số trích dẫn bị loại:** `{q.rejected_quotes_count}`")

    if q.rejected_quotes:
        lines.append("\n<details><summary>Chi tiết các trích dẫn bị loại (không khớp nguyên văn hoặc > 40 từ)</summary>\n")
        for rq in q.rejected_quotes:
            lines.append(f"- `{rq.item_id}`: {rq.reason} — *\"{rq.detail}\"*")
        lines.append("\n</details>")

    if q.rejected_sources:
        lines.append("\n<details><summary>Chi tiết các nguồn bị loại</summary>\n")
        for rs in q.rejected_sources:
            lines.append(f"- `{rs.item_id}`: {rs.reason}")
        lines.append("\n</details>")

    # --- SECTION 7 (Mission 3 · Change Request A2) ---
    if report.recency is not None:
        rec = report.recency
        lines.append("")
        lines.append(
            "## 7. Độ mới của dữ liệu & Ảnh hưởng tới độ tin cậy (Change Request A2)"
        )
        lines.append(
            f"> **Ngày tham chiếu:** `{rec.reference_date}` · "
            f"**Ngưỡng cảnh báo:** `> {rec.alert_months} tháng` · "
            f"**Mức ảnh hưởng:** **{rec.impact_level}**\n"
        )
        lines.append(f"{_esc_md(rec.summary, False)}\n")

        lines.append("### 7.1 Nguồn và tuổi dữ liệu")
        lines.append(
            "| Nguồn | Hạng | Ngày đăng (cách xác định) | Tuổi | Kỳ số liệu trong trích dẫn | Trạng thái | Then chốt | Hỗ trợ nhận định |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for sr in rec.sources:
            s_obj = source_map.get(sr.source_id)
            dom_str = s_obj.domain if s_obj else ""
            tier_str = f"Hạng {s_obj.tier}" if s_obj else "—"
            conflict_flag = " ⚠️ *(ngày đăng có thể sai)*" if sr.date_conflict else ""
            date_cell = f"`{sr.date_display}` ({_esc_md(sr.date_method_label)}){conflict_flag}"
            vint_cell = f"`{sr.data_vintage}`" if sr.data_vintage else "—"
            reasons_str = _esc_md("; ".join(sr.reasons)) if sr.reasons else ""
            st_cell = f"**{sr.status}**" + (f"<br><small>{reasons_str}</small>" if reasons_str else "")
            key_cell = (
                f"**Có**<br><small>{_esc_md('; '.join(sr.key_reasons))}</small>"
                if sr.is_key
                else "Không"
            )
            supp_cell = ", ".join(f"`{iid}`" for iid in sr.supported_insight_ids) if sr.supported_insight_ids else "—"
            lines.append(
                f"| **{sr.source_id}** (`{dom_str}`) | {tier_str} | {date_cell} | `{sr.age_display}` | "
                f"{vint_cell} | {st_cell} | {key_cell} | {supp_cell} |"
            )
        lines.append("")

        lines.append("### 7.2 Ảnh hưởng tới từng nhận định (tính bằng code)")
        if not rec.key_old_sources:
            lines.append(
                "- Không có nguồn then chốt nào vượt ngưỡng 18 tháng hoặc chưa rõ tuổi gây ảnh hưởng tới các nhận định.\n"
            )
        else:
            for kos in rec.key_old_sources:
                lines.append(f"- **{_esc_md(kos.summary, False)}**")
            lines.append("")
            lines.append(
                "| Nguồn | Nhận định | Độ tin cậy hiện tại | Nếu bỏ nguồn này | Nếu nguồn này còn mới (≤ 12 tháng) |"
            )
            lines.append("|---|---|---|---|---|")
            for kos in rec.key_old_sources:
                s_obj = source_map.get(kos.source_id)
                sr_obj = src_rec_map.get(kos.source_id)
                src_label = (
                    f"**{kos.source_id}** (`{s_obj.domain}`, `{sr_obj.date_display}`)"
                    if s_obj and sr_obj
                    else f"**{kos.source_id}**"
                )
                for imp in kos.impacts:
                    rem_cell = (
                        f"**{imp.if_source_removed}**"
                        if imp.if_source_removed != imp.current
                        else imp.if_source_removed
                    )
                    fresh_cell = (
                        f"**{imp.if_source_fresh}**"
                        if imp.if_source_fresh != imp.current
                        else imp.if_source_fresh
                    )
                    lines.append(
                        f"| {src_label} | **{imp.insight_id}** | `{imp.current}` | {rem_cell} | {fresh_cell} |"
                    )
            lines.append("")

        lines.append("### 7.3 Mốc thời gian độ tin cậy sẽ thay đổi")
        if not rec.upcoming_changes:
            lines.append(
                "- Trong 12 tháng tới không có nguồn dẫn chứng nào chuyển nhóm độ mới làm thay đổi điểm độ tin cậy.\n"
            )
        else:
            for ev_item in rec.upcoming_changes:
                sids_str = ", ".join(ev_item.source_ids)
                chg_str = "; ".join(ev_item.changes)
                lines.append(
                    f"- **Từ `{ev_item.date}`** (nguồn `{sids_str}` chuyển nhóm độ mới), nếu chưa có dữ liệu mới: {_esc_md(chg_str, False)}"
                )
            lines.append("")

        lines.append("### 7.4 Gợi ý làm mới dữ liệu")
        if not rec.suggested_refresh_queries:
            lines.append("- Báo cáo không cần truy vấn làm mới bổ sung.\n")
        else:
            lines.append(
                "Các truy vấn tìm kiếm tự động sinh để tìm bản báo cáo/số liệu mới hơn cho các nguồn then chốt cũ:"
            )
            for q_str in rec.suggested_refresh_queries:
                lines.append(f"- `{q_str}`")
            lines.append("")

        lines.append("### 7.5 Kết quả vòng làm mới (nếu đã chạy)")
        if report.refresh is None:
            lines.append(
                "- *Chưa chạy vòng làm mới trên báo cáo này. Có thể chạy qua CLI `python -m research.refresh <report.json>` hoặc bấm nút trên giao diện Streamlit.*"
            )
        else:
            rf = report.refresh
            lines.append(
                f"- **Trạng thái:** `{rf.status}` · **Ngày tham chiếu làm mới:** `{rf.reference_date}` · "
                f"**Nguồn mục tiêu:** `{', '.join(rf.target_source_ids) or '—'}` · "
                f"**Nguồn mới bổ sung:** `{', '.join(rf.new_source_ids) or '0'}` · "
                f"**Số lệnh gọi LLM:** `{rf.llm_calls_count}` ({rf.duration_seconds}s)"
            )
            if rf.note:
                lines.append(f"- **Ghi chú:** {_esc_md(rf.note, False)}")
            if rf.comparisons:
                lines.append("\n| Bằng chứng cũ | Bằng chứng mới | Kết quả đối chiếu | Giải thích (kỳ cũ vs kỳ mới) |")
                lines.append("|---|---|---|---|")
                for cmp in rf.comparisons:
                    new_eids = ", ".join(f"`{e}`" for e in cmp.new_evidence_ids) if cmp.new_evidence_ids else "—"
                    lines.append(
                        f"| `{cmp.old_evidence_id}` | {new_eids} | **{cmp.status}** | {_esc_md(cmp.explanation)} |"
                    )
            if rf.confidence_changes:
                lines.append("\n| Nhận định | Trước làm mới | Sau làm mới | Lý do thay đổi |")
                lines.append("|---|---|---|---|")
                for cc in rf.confidence_changes:
                    lines.append(
                        f"| **{cc.insight_id}** | `{cc.before}` | **{cc.after}** | {_esc_md(cc.reason)} |"
                    )

    return "\n".join(lines)
