"""Targeted data refresh loop for key old sources (Mission 3 · Change Request A2 · BRIEF_M3 4.7)."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import math
from pathlib import Path
import re
import sys
import time
from typing import Callable, Optional

from research.dates import (
    compute_age_metrics,
    date_range,
    detect_data_period,
    infer_date_method_legacy,
    precision_of,
)
from research.extract import extract_claims_from_sources
from research.grade import parse_published_date
from research.llm import LLMClient
from research.recency import (
    finalize_with_recency,
    load_recency_policy,
    rescore_report_as_of,
)
from research.retrieve import canonicalize_url, retrieve_and_grade_sources
from research.schemas import (
    ConfidenceChange,
    ConflictItem,
    Evidence,
    Insight,
    RefreshComparison,
    RefreshComparisonLLMOutput,
    RefreshQueriesLLMOutput,
    RefreshResult,
    RefreshStatus,
    RejectedItem,
    Report,
    Source,
)
from research.score import strip_llm_urls

ProgressCallback = Callable[[str, str], None]

REFRESH_REC_MARKER = "[Sau vòng làm mới"


def _default_progress(_step: str, _detail: str) -> None:
    pass


def _strip_refresh_recommendation(rec_text: str) -> str:
    if not rec_text:
        return ""
    idx = rec_text.find(REFRESH_REC_MARKER)
    if idx != -1:
        return rec_text[:idx].rstrip()
    return rec_text.strip()


def _max_numeric_id(items: list[str], prefix: str) -> int:
    max_val = 0
    for item_id in items:
        if item_id.startswith(prefix) and item_id[len(prefix) :].isdigit():
            max_val = max(max_val, int(item_id[len(prefix) :]))
    return max_val


def _truncate_words(text: str, max_words: int = 20) -> str:
    words = (text or "").strip().split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "..."


def _target_min_year_and_date(
    target_sources: list[Source],
    target_evidences: list[Evidence],
) -> tuple[int, date]:
    """Determine the minimum year and date that a new source must beat to be considered newer."""
    years: list[int] = []
    end_dates: list[date] = []

    for s in target_sources:
        method = s.date_method or infer_date_method_legacy(s.url, s.title, s.published_date)
        prec = precision_of(method, s.published_date)
        rng = date_range(s.published_date, prec)
        if rng is not None:
            years.append(rng[1].year)
            end_dates.append(rng[1])

    for ev in target_evidences:
        if ev.data_period_end:
            p_dt = parse_published_date(ev.data_period_end)
            if p_dt is not None:
                years.append(p_dt.year)
                end_dates.append(p_dt)

    min_yr = min(years) if years else 2024
    min_dt = min(end_dates) if end_dates else date(2024, 12, 31)
    return min_yr, min_dt


def _generate_refresh_queries(
    baseline: Report,
    target_sources: list[Source],
    target_evidences: list[Evidence],
    llm: LLMClient,
    ref_date: date,
    max_queries: int = 6,
) -> tuple[list[str], str, int]:
    """Combine deterministic suggested queries with 1 LLM call (filtered by year and stripped of URLs)."""
    det_queries = list(
        (baseline.recency.suggested_refresh_queries if baseline.recency else []) or []
    )
    min_yr, _min_dt = _target_min_year_and_date(target_sources, target_evidences)
    urls_removed = 0
    note_parts: list[str] = []

    target_lines: list[str] = []
    for s in target_sources:
        s_evs = [e for e in target_evidences if e.source_id == s.id]
        ev_desc = "; ".join(
            f"[{e.id}] {e.claim} (quote: \"{e.quote}\")" for e in s_evs[:4]
        )
        target_lines.append(
            f"- Source {s.id} ({s.domain}, published={s.published_date or 'unknown'}, title='{s.title}'): {ev_desc}"
        )

    llm_queries: list[str] = []
    try:
        sys_prompt = (
            f"Today's date is {ref_date.isoformat()}. You are a game market research assistant.\n"
            "Generate up to 2 targeted English web search queries per old source listed below to find NEWER data "
            f"(from {ref_date.year} or {ref_date.year - 1}, strictly newer than {min_yr}) covering the EXACT SAME metric and market scope.\n"
            "Do NOT include any URLs (`http://`, `https://`, `www.`). Return concise search queries only."
        )
        usr_prompt = (
            f"Original Research Question: {baseline.question}\n"
            f"Old Key Sources needing newer data:\n" + "\n".join(target_lines)
        )
        q_out = llm.generate_structured(
            system_prompt=sys_prompt,
            user_prompt=usr_prompt,
            response_model=RefreshQueriesLLMOutput,
            step_name="refresh_queries",
        )
        for q_raw in q_out.queries:
            q_clean, n_url = strip_llm_urls(q_raw)
            urls_removed += n_url
            q_clean = q_clean.replace("[link đã lọc]", "").strip()
            # Must contain a year > min_yr
            years_in_q = [int(y) for y in re.findall(r"\b(20[123]\d)\b", q_clean)]
            if q_clean and any(y > min_yr for y in years_in_q):
                llm_queries.append(q_clean)
    except Exception as exc:
        note_parts.append(
            f"Không gọi được LLM sinh truy vấn ({type(exc).__name__}), sử dụng bộ truy vấn tất định."
        )

    # Interleave LLM queries and deterministic queries so both are represented within max_queries
    combined: list[str] = []
    seen: set[str] = set()
    for q in det_queries[:2] + llm_queries + det_queries[2:]:
        q_norm = re.sub(r"\s+", " ", q).strip()
        if not q_norm or q_norm.lower() in seen:
            continue
        years_in_q = [int(y) for y in re.findall(r"\b(20[123]\d)\b", q_norm)]
        if years_in_q and not any(y > min_yr for y in years_in_q):
            continue
        seen.add(q_norm.lower())
        combined.append(q_norm)
        if len(combined) >= max_queries:
            break

    return combined, " ".join(note_parts), urls_removed


def refresh_old_sources(
    report: Report,
    llm: Optional[LLMClient] = None,
    reference_date: Optional[date] = None,
    use_cache: bool = True,
    max_targets: Optional[int] = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> Report:
    """Execute the 7-step targeted refresh loop for key old sources (BRIEF_M3 section 4.7)."""
    t0 = time.perf_counter()
    cb = progress_callback or _default_progress
    ref = reference_date or date.today()
    policy = load_recency_policy()
    alert_months = int(policy.get("alert_months", 18))
    if max_targets is None:
        max_targets = int(policy.get("refresh_max_targets", 2))
    max_queries = int(policy.get("refresh_max_queries", 6))
    max_new_sources = int(policy.get("refresh_max_new_sources", 6))

    llm_client = llm or LLMClient(max_calls=6, use_cache=use_cache)
    calls_before = llm_client.calls_count
    refresh_logs: list[str] = []

    def _rlog(step: str, detail: str) -> None:
        msg = f"[{step}] {detail}"
        refresh_logs.append(msg)
        cb(step, detail)

    # Step 0: Re-score baseline at `ref` so time-elapsed changes are separated from refresh changes
    baseline = rescore_report_as_of(report, as_of=ref, alert_months=alert_months)
    assert baseline.recency is not None

    # Step 1: Identify up to `max_targets` key old sources
    kos_list = baseline.recency.key_old_sources[:max_targets]
    if not kos_list:
        dur = round(time.perf_counter() - t0, 2)
        rf_res = RefreshResult(
            status="KHÔNG CẦN LÀM MỚI",
            refreshed_at=datetime.now().isoformat(timespec="seconds"),
            reference_date=ref.isoformat(),
            target_source_ids=[],
            queries=[],
            new_source_ids=[],
            rejected_new_sources=[],
            comparisons=[],
            confidence_changes=[],
            llm_calls_count=0,
            duration_seconds=dur,
            note="Báo cáo không có nguồn then chốt nào bị cũ hoặc chưa rõ tuổi cần làm mới.",
        )
        return baseline.model_copy(update={"refresh": rf_res})

    target_sids = [k.source_id for k in kos_list]
    src_map = {s.id: s for s in baseline.sources}
    ev_map = {e.id: e for e in baseline.evidences if e.verified}
    target_sources = [src_map[sid] for sid in target_sids if sid in src_map]

    # Collect verified evidences belonging to target sources that are actually cited by insights
    cited_eids_ordered: list[str] = []
    for ins in baseline.insights:
        for eid in ins.evidence_ids:
            ev = ev_map.get(eid)
            if ev and ev.source_id in target_sids and eid not in cited_eids_ordered:
                cited_eids_ordered.append(eid)

    target_evidences = [ev_map[eid] for eid in cited_eids_ordered]

    try:
        # Step 2: Build refresh search queries
        _rlog(
            "Làm mới 1/4 · Sinh truy vấn",
            f"Đang tạo truy vấn tìm dữ liệu mới hơn cho nguồn mục tiêu {', '.join(target_sids)}...",
        )
        queries, q_note, urls_removed_q = _generate_refresh_queries(
            baseline=baseline,
            target_sources=target_sources,
            target_evidences=target_evidences,
            llm=llm_client,
            ref_date=ref,
            max_queries=max_queries,
        )
        notes_accum: list[str] = [q_note] if q_note else []

        # Keywords from trace or target source titles
        keywords: list[str] = list((baseline.trace or {}).get("keywords") or [])
        if not keywords:
            for ts in target_sources:
                keywords.extend(
                    w for w in re.findall(r"[A-Za-zÀ-ỹ0-9]{3,}", ts.title) if len(w) >= 3
                )
            keywords = keywords[:10]

        # Step 3: Retrieve and filter strictly newer sources
        _rlog(
            "Làm mới 2/4 · Tìm & lọc nguồn mới",
            f"Đang chạy {len(queries)} truy vấn và lọc các nguồn có ngày đăng mới hơn...",
        )
        (
            cand_sources,
            cand_trunc_texts,
            cand_full_texts,
            retr_rejected,
            retr_stats,
        ) = retrieve_and_grade_sources(
            queries=queries,
            keywords=keywords,
            reference_date=ref,
            max_per_query=5,
            max_kept_sources=max_new_sources,
            use_cache=use_cache,
        )

        if int(retr_stats.get("raw_search_results_count", 0)) == 0 and not cand_sources:
            dur = round(time.perf_counter() - t0, 2)
            rf_err = RefreshResult(
                status="LỖI",
                refreshed_at=datetime.now().isoformat(timespec="seconds"),
                reference_date=ref.isoformat(),
                target_source_ids=target_sids,
                queries=queries,
                new_source_ids=[],
                rejected_new_sources=retr_rejected,
                comparisons=[],
                confidence_changes=[],
                llm_calls_count=llm_client.calls_count - calls_before,
                duration_seconds=dur,
                note="công cụ tìm kiếm không trả kết quả (có thể bị giới hạn tạm thời)",
            )
            return baseline.model_copy(update={"refresh": rf_err})

        existing_urls = {canonicalize_url(s.url) for s in baseline.sources}
        _min_yr, min_target_end = _target_min_year_and_date(
            target_sources, target_evidences
        )

        rejected_new: list[RejectedItem] = list(retr_rejected)
        kept_new_sources: list[Source] = []
        new_trunc_texts: dict[str, str] = {}
        new_full_texts: dict[str, str] = {}
        next_src_num = _max_numeric_id([s.id for s in baseline.sources], "S") + 1

        for cs in cand_sources:
            c_url = canonicalize_url(cs.url)
            if c_url in existing_urls:
                rejected_new.append(
                    RejectedItem(
                        item_id=cs.url[:80],
                        reason="Trùng URL đã có trong báo cáo gốc",
                    )
                )
                continue

            method = cs.date_method or infer_date_method_legacy(
                cs.url, cs.title, cs.published_date
            )
            prec = precision_of(method, cs.published_date)
            if not cs.published_date or prec == "unknown":
                rejected_new.append(
                    RejectedItem(
                        item_id=cs.url[:80],
                        reason="Không rõ ngày đăng (không chứng minh được là mới hơn)",
                    )
                )
                continue

            rng = date_range(cs.published_date, prec)
            if rng is None or rng[1] <= min_target_end:
                rejected_new.append(
                    RejectedItem(
                        item_id=cs.url[:80],
                        reason=f"Ngày đăng ({cs.published_date}) không mới hơn kỳ/ngày của nguồn mục tiêu ({min_target_end.isoformat()})",
                    )
                )
                continue

            _am, _amin, _amax, _adisp, older_alert, possibly_alert = compute_age_metrics(
                cs.published_date, prec, ref, alert_months
            )
            if older_alert or possibly_alert:
                rejected_new.append(
                    RejectedItem(
                        item_id=cs.url[:80],
                        reason=f"Nguồn ({cs.published_date}) vẫn có thể quá {alert_months} tháng tính đến {ref.isoformat()}",
                    )
                )
                continue

            new_sid = f"S{next_src_num}"
            next_src_num += 1
            existing_urls.add(c_url)
            renamed_src = cs.model_copy(
                update={
                    "id": new_sid,
                    "date_method": method,
                    "date_precision": prec,
                }
            )
            kept_new_sources.append(renamed_src)
            new_trunc_texts[new_sid] = cand_trunc_texts.get(cs.id, "")
            new_full_texts[new_sid] = cand_full_texts.get(cs.id, "")

        if not kept_new_sources:
            gap_msg = (
                f"[Vòng làm mới {ref.isoformat()}] Chưa tìm được dữ liệu mới hơn trên nguồn mở cho "
                f"{', '.join(f'{s.id} ({s.domain})' for s in target_sources)}."
            )
            new_gaps = list(baseline.gaps)
            if gap_msg not in new_gaps:
                new_gaps.append(gap_msg)
            no_find_cmps = [
                RefreshComparison(
                    old_evidence_id=ev.id,
                    new_evidence_ids=[],
                    status="KHÔNG TÌM THẤY DỮ LIỆU MỚI",
                    explanation="Các nguồn tìm được không rõ ngày đăng, trùng URL hoặc không mới hơn nguồn gốc.",
                )
                for ev in target_evidences
            ]
            notes_accum.append(
                "Không có nguồn mới nào vượt qua bộ lọc ngày đăng nghiêm ngặt (phải có ngày đăng rõ ràng và mới hơn nguồn cũ)."
            )
            dur = round(time.perf_counter() - t0, 2)
            rf_none = RefreshResult(
                status="KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN",
                refreshed_at=datetime.now().isoformat(timespec="seconds"),
                reference_date=ref.isoformat(),
                target_source_ids=target_sids,
                queries=queries,
                new_source_ids=[],
                rejected_new_sources=rejected_new,
                comparisons=no_find_cmps,
                confidence_changes=[],
                llm_calls_count=llm_client.calls_count - calls_before,
                duration_seconds=dur,
                note=" ".join(notes_accum),
            )
            new_trace = dict(baseline.trace or {})
            new_trace["version"] = int(new_trace.get("version", 1)) + 1
            new_trace["parent_run_timestamp"] = str(
                (report.trace or {}).get("run_timestamp", "")
            )
            new_trace["refresh_timestamp"] = rf_none.refreshed_at
            new_trace["step_logs"] = list(new_trace.get("step_logs", [])) + refresh_logs
            return baseline.model_copy(
                update={"gaps": new_gaps, "refresh": rf_none, "trace": new_trace}
            )

        # Step 4: Extract & verify quotes from new sources (<= 2 LLM calls)
        _rlog(
            "Làm mới 3/4 · Trích xuất & xác minh trích dẫn mới",
            f"Đang rút trích và kiểm chứng RapidFuzz >= 90 từ {len(kept_new_sources)} nguồn mới...",
        )
        next_ev_num = _max_numeric_id([e.id for e in baseline.evidences], "E") + 1
        sub_qs = [e.claim for e in target_evidences[:8]] or [baseline.question]
        (
            new_evidences,
            new_rejected_quotes,
            new_total_extracted,
        ) = extract_claims_from_sources(
            question=baseline.question,
            sub_questions=sub_qs,
            sources=kept_new_sources,
            source_texts=new_trunc_texts,
            full_source_texts=new_full_texts,
            llm=llm_client,
            current_date=ref.isoformat(),
            batch_size=max(4, math.ceil(len(kept_new_sources) / 2)),
            evidence_id_start=next_ev_num,
        )

        # Populate data_period on new_evidences
        new_src_map = {s.id: s for s in kept_new_sources}
        enriched_new_evs: list[Evidence] = []
        for nev in new_evidences:
            ns = new_src_map.get(nev.source_id)
            pub_b = (
                parse_published_date(ns.published_date)
                if (ns and ns.date_precision == "day")
                else None
            )
            plbl, pend = detect_data_period(nev.quote, ref=ref, publication_bound=pub_b)
            enriched_new_evs.append(
                nev.model_copy(
                    update={
                        "data_period": plbl,
                        "data_period_end": pend.isoformat() if pend else None,
                    }
                )
            )
        new_evidences = enriched_new_evs

        if not new_evidences:
            gap_msg = (
                f"[Vòng làm mới {ref.isoformat()}] Đã tải {len(kept_new_sources)} nguồn mới nhưng không trích xuất được trích dẫn nguyên văn nào khớp >= 90 cho "
                f"{', '.join(target_sids)}."
            )
            new_gaps = list(baseline.gaps)
            if gap_msg not in new_gaps:
                new_gaps.append(gap_msg)
            no_ev_cmps = [
                RefreshComparison(
                    old_evidence_id=ev.id,
                    new_evidence_ids=[],
                    status="KHÔNG TÌM THẤY DỮ LIỆU MỚI",
                    explanation="Không có trích dẫn nguyên văn đạt ngưỡng xác minh từ nguồn mới.",
                )
                for ev in target_evidences
            ]
            dur = round(time.perf_counter() - t0, 2)
            rf_no_ev = RefreshResult(
                status="KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN",
                refreshed_at=datetime.now().isoformat(timespec="seconds"),
                reference_date=ref.isoformat(),
                target_source_ids=target_sids,
                queries=queries,
                new_source_ids=[s.id for s in kept_new_sources],
                rejected_new_sources=rejected_new,
                comparisons=no_ev_cmps,
                confidence_changes=[],
                llm_calls_count=llm_client.calls_count - calls_before,
                duration_seconds=dur,
                note=" ".join(notes_accum + ["Không có trích dẫn mới vượt ngưỡng xác minh."]),
            )
            new_trace = dict(baseline.trace or {})
            new_trace["version"] = int(new_trace.get("version", 1)) + 1
            new_trace["parent_run_timestamp"] = str(
                (report.trace or {}).get("run_timestamp", "")
            )
            new_trace["refresh_timestamp"] = rf_no_ev.refreshed_at
            new_trace["step_logs"] = list(new_trace.get("step_logs", [])) + refresh_logs
            return baseline.model_copy(
                update={"gaps": new_gaps, "refresh": rf_no_ev, "trace": new_trace}
            )

        # Step 5: Compare old target evidences vs new verified evidences (1 LLM call)
        _rlog(
            "Làm mới 4/4 · Đối chiếu bằng chứng cũ ↔ mới & Chấm lại độ tin cậy",
            f"Đang so sánh {len(target_evidences)} bằng chứng cũ với {len(new_evidences)} bằng chứng mới...",
        )
        old_lines: list[str] = []
        for oev in target_evidences:
            osrc = src_map.get(oev.source_id)
            o_date = osrc.published_date if osrc else "unknown"
            o_dom = osrc.domain if osrc else "unknown"
            old_lines.append(
                f"- [{oev.id}] (Source {oev.source_id} {o_dom}, published={o_date}, period={oev.data_period or 'unspecified'})\n"
                f"  Claim: {oev.claim}\n"
                f"  Quote: \"{oev.quote}\""
            )

        new_lines: list[str] = []
        for nev in new_evidences:
            nsrc = new_src_map.get(nev.source_id)
            n_date = nsrc.published_date if nsrc else "unknown"
            n_dom = nsrc.domain if nsrc else "unknown"
            new_lines.append(
                f"- [{nev.id}] (Source {nev.source_id} {n_dom}, published={n_date}, period={nev.data_period or 'unspecified'})\n"
                f"  Claim: {nev.claim}\n"
                f"  Quote: \"{nev.quote}\""
            )

        cmp_sys_prompt = (
            f"Today's date is {ref.isoformat()}. You are a strict evidence comparison auditor.\n"
            "Compare each OLD evidence item against the NEW verified evidence items.\n"
            "STRICT RULES:\n"
            "1. Only match a new evidence ID to an old evidence ID if they address the SAME metric/topic AND the SAME market scope (country/region, platform, genre/segment).\n"
            "2. Choose `status` strictly:\n"
            "   - `XÁC NHẬN`: New evidence covers the same metric/scope in a newer period and confirms the same trend or magnitude.\n"
            "   - `CẬP NHẬT`: New evidence covers the same metric/scope in a newer period with a significantly updated/different figure.\n"
            "   - `MÂU THUẪN`: New evidence directly contradicts the old evidence's direction or conclusion.\n"
            "   - `KHÔNG TƯƠNG ĐƯƠNG`: New evidence is about a different metric, different country/region, or different segment.\n"
            "3. `explanation` must be in Vietnamese, <= 40 words, explicitly stating the old vs. new period/date (e.g., 'Q1/2025 vs H1/2026').\n"
            "4. NEVER write any URL (`http://`, `https://`, `www.`) in `explanation`."
        )
        cmp_usr_prompt = (
            f"Research Question: {baseline.question}\n\n"
            "OLD EVIDENCES TO CHECK:\n"
            + "\n".join(old_lines)
            + "\n\nNEW VERIFIED EVIDENCES:\n"
            + "\n".join(new_lines)
        )

        cmp_llm_out = llm_client.generate_structured(
            system_prompt=cmp_sys_prompt,
            user_prompt=cmp_usr_prompt,
            response_model=RefreshComparisonLLMOutput,
            step_name="refresh_compare",
        )

        valid_old_eids = {e.id for e in target_evidences}
        valid_new_eids = {e.id for e in new_evidences}
        new_ev_map = {e.id: e for e in new_evidences}
        urls_removed_cmp = 0

        comparisons_by_old: dict[str, RefreshComparison] = {}
        for item in cmp_llm_out.items:
            oeid = (item.old_evidence_id or "").strip()
            if oeid not in valid_old_eids or oeid in comparisons_by_old:
                continue
            filtered_neids = [
                neid.strip()
                for neid in item.new_evidence_ids
                if neid.strip() in valid_new_eids
            ]
            expl_clean, n_u = strip_llm_urls(item.explanation)
            urls_removed_cmp += n_u
            st_val = item.status
            if st_val in ("XÁC NHẬN", "CẬP NHẬT", "MÂU THUẪN") and not filtered_neids:
                st_val_final = "KHÔNG TÌM THẤY DỮ LIỆU MỚI"
            else:
                st_val_final = st_val
            comparisons_by_old[oeid] = RefreshComparison(
                old_evidence_id=oeid,
                new_evidence_ids=filtered_neids,
                status=st_val_final,
                explanation=expl_clean,
            )

        comparisons: list[RefreshComparison] = []
        for oev in target_evidences:
            if oev.id in comparisons_by_old:
                comparisons.append(comparisons_by_old[oev.id])
            else:
                comparisons.append(
                    RefreshComparison(
                        old_evidence_id=oev.id,
                        new_evidence_ids=[],
                        status="KHÔNG TÌM THẤY DỮ LIỆU MỚI",
                        explanation="Không tìm thấy trích dẫn mới nào đề cập cùng chỉ số và phạm vi thị trường.",
                    )
                )

        # Step 6: Merge sources, evidences, conflicts, and insights
        merged_sources = list(baseline.sources) + kept_new_sources
        merged_evidences = list(baseline.evidences) + new_evidences
        merged_conflicts = list(baseline.conflicts)
        merged_insights = [ins.model_copy(deep=True) for ins in baseline.insights]
        merged_gaps = list(baseline.gaps)

        confirmed_iids: list[str] = []
        updated_or_conflicted_iids: list[str] = []
        refreshed_target_sids: set[str] = set()
        next_ins_num = _max_numeric_id([i.id for i in merged_insights], "I") + 1

        for cmp in comparisons:
            oev = ev_map[cmp.old_evidence_id]
            osrc = src_map.get(oev.source_id)
            if cmp.status == "XÁC NHẬN" and cmp.new_evidence_ids:
                refreshed_target_sids.add(oev.source_id)
                for ins in merged_insights:
                    if cmp.old_evidence_id in ins.evidence_ids:
                        for neid in cmp.new_evidence_ids:
                            if neid not in ins.evidence_ids:
                                ins.evidence_ids.append(neid)
                        if ins.id not in confirmed_iids:
                            confirmed_iids.append(ins.id)

            elif cmp.status in ("CẬP NHẬT", "MÂU THUẪN") and cmp.new_evidence_ids:
                refreshed_target_sids.add(oev.source_id)
                old_p = oev.data_period or (osrc.published_date if osrc else "cũ")
                vals = [
                    f"[{oev.id}/{oev.source_id}, {old_p}]: \"{_truncate_words(oev.quote, 20)}\""
                ]
                for neid in cmp.new_evidence_ids:
                    nev = new_ev_map[neid]
                    nsrc = new_src_map.get(nev.source_id)
                    new_p = nev.data_period or (nsrc.published_date if nsrc else "mới")
                    vals.append(
                        f"[{nev.id}/{nev.source_id}, {new_p}]: \"{_truncate_words(nev.quote, 20)}\""
                    )

                merged_conflicts.append(
                    ConflictItem(
                        topic=f"Số liệu cũ ↔ mới ({cmp.status}): {oev.claim[:90]}",
                        values=vals,
                        explanation=cmp.explanation,
                        evidence_ids=[cmp.old_evidence_id] + list(cmp.new_evidence_ids),
                    )
                )

                for ins in merged_insights:
                    if cmp.old_evidence_id in ins.evidence_ids:
                        ins.has_conflict = True
                        if ins.id not in updated_or_conflicted_iids:
                            updated_or_conflicted_iids.append(ins.id)

                first_new_ev = new_ev_map[cmp.new_evidence_ids[0]]
                new_iid = f"I{next_ins_num}"
                next_ins_num += 1
                merged_insights.append(
                    Insight(
                        id=new_iid,
                        statement=first_new_ev.claim,
                        type="fact",
                        evidence_ids=list(cmp.new_evidence_ids),
                    )
                )

        unrefreshed_sids = [
            sid for sid in target_sids if sid not in refreshed_target_sids
        ]
        for sid in unrefreshed_sids:
            s_obj = src_map.get(sid)
            dom_s = s_obj.domain if s_obj else sid
            g_str = f"[Vòng làm mới {ref.isoformat()}] Chưa tìm được số liệu mới tương đương cùng phạm vi cho nguồn {sid} ({dom_s})."
            if g_str not in merged_gaps:
                merged_gaps.append(g_str)

        any_matched = bool(refreshed_target_sids)
        final_status: RefreshStatus = (
            "ĐÃ LÀM MỚI" if any_matched else "KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN"
        )

        # Finalize report and compute recency
        combined_total_quotes = (
            baseline.quality.total_quotes_extracted + new_total_extracted
        )
        combined_rej_sources = list(baseline.quality.rejected_sources) + rejected_new
        combined_rej_quotes = (
            list(baseline.quality.rejected_quotes) + new_rejected_quotes
        )
        urls_floor = (
            baseline.quality.llm_invented_urls_removed_count
            + urls_removed_q
            + urls_removed_cmp
        )

        draft_merged = baseline.model_copy(
            update={
                "sources": merged_sources,
                "evidences": merged_evidences,
                "conflicts": merged_conflicts,
                "insights": merged_insights,
                "gaps": merged_gaps,
            }
        )
        finalized = finalize_with_recency(
            report=draft_merged,
            reference_date=ref,
            total_quotes_extracted=combined_total_quotes,
            rejected_sources=combined_rej_sources,
            rejected_quotes=combined_rej_quotes,
            urls_removed_floor=urls_floor,
            alert_months=alert_months,
        )

        # Compute confidence_changes vs baseline (at the same `ref` date)
        base_ins_map = {ins.id: ins for ins in baseline.insights}
        conf_changes: list[ConfidenceChange] = []
        for ins in finalized.insights:
            old_ins = base_ins_map.get(ins.id)
            if old_ins is None:
                conf_changes.append(
                    ConfidenceChange(
                        insight_id=ins.id,
                        before="—",
                        after=ins.confidence,
                        reason=f"Nhận định mới bổ sung từ nguồn làm mới ({', '.join(ins.evidence_ids)})",
                    )
                )
            elif old_ins.confidence != ins.confidence:
                conf_changes.append(
                    ConfidenceChange(
                        insight_id=ins.id,
                        before=old_ins.confidence,
                        after=ins.confidence,
                        reason=ins.confidence_reason,
                    )
                )

        # Idempotent recommendation note
        base_rec = _strip_refresh_recommendation(finalized.recommendation)
        rec_parts: list[str] = []
        if confirmed_iids:
            rec_parts.append(f"đã xác nhận thêm bằng chứng mới cho {', '.join(confirmed_iids)}")
        if updated_or_conflicted_iids:
            rec_parts.append(
                f"phát hiện số liệu mới thay đổi/mâu thuẫn tại {', '.join(updated_or_conflicted_iids)}"
            )
        if unrefreshed_sids:
            rec_parts.append(
                f"chưa tìm được bản mới tương đương cho nguồn {', '.join(unrefreshed_sids)}"
            )
        summary_clause = "; ".join(rec_parts) if rec_parts else "đã kiểm tra độ mới các nguồn then chốt"
        new_rec = (
            f"{base_rec} [Sau vòng làm mới {ref.strftime('%d/%m/%Y')}] "
            f"Kết quả làm mới: {summary_clause}; "
            "khuyến nghị gốc được viết trước vòng làm mới, cần đọc lại các nhận định có đánh dấu."
        )

        dur = round(time.perf_counter() - t0, 2)
        rf_result = RefreshResult(
            status=final_status,
            refreshed_at=datetime.now().isoformat(timespec="seconds"),
            reference_date=ref.isoformat(),
            target_source_ids=target_sids,
            queries=queries,
            new_source_ids=[s.id for s in kept_new_sources],
            rejected_new_sources=rejected_new,
            comparisons=comparisons,
            confidence_changes=conf_changes,
            llm_calls_count=llm_client.calls_count - calls_before,
            duration_seconds=dur,
            note=" ".join(notes_accum).strip(),
        )

        new_trace = dict(finalized.trace or {})
        new_trace["version"] = int(new_trace.get("version", 1)) + 1
        new_trace["parent_run_timestamp"] = str(
            (report.trace or {}).get("run_timestamp", "")
        )
        new_trace["refresh_timestamp"] = rf_result.refreshed_at
        new_trace["step_logs"] = list(new_trace.get("step_logs", [])) + refresh_logs

        return finalized.model_copy(
            update={
                "recommendation": new_rec,
                "refresh": rf_result,
                "trace": new_trace,
            }
        )

    except Exception as exc:
        dur = round(time.perf_counter() - t0, 2)
        rf_fail = RefreshResult(
            status="LỖI",
            refreshed_at=datetime.now().isoformat(timespec="seconds"),
            reference_date=ref.isoformat(),
            target_source_ids=target_sids,
            queries=[],
            new_source_ids=[],
            rejected_new_sources=[],
            comparisons=[],
            confidence_changes=[],
            llm_calls_count=llm_client.calls_count - calls_before,
            duration_seconds=dur,
            note=f"Lỗi khi thực hiện vòng làm mới ({type(exc).__name__}: {exc}). Giữ nguyên báo cáo gốc.",
        )
        return baseline.model_copy(update={"refresh": rf_fail})


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Run targeted data refresh loop on a saved Report JSON (BRIEF_M3 4.7)."
    )
    parser.add_argument("report_json", type=str, help="Path to input Report JSON")
    parser.add_argument(
        "--reference-date",
        type=str,
        default="",
        help="Reference date YYYY-MM-DD for refresh (defaults to today)",
    )
    parser.add_argument("--out-json", type=str, default="", help="Output JSON path")
    parser.add_argument("--out-md", type=str, default="", help="Output Markdown path")
    parser.add_argument("--no-cache", action="store_true", help="Disable disk cache")
    args = parser.parse_args()

    in_path = Path(args.report_json)
    report = Report.model_validate(json.loads(in_path.read_text(encoding="utf-8")))

    ref_date = None
    if args.reference_date:
        ref_date = parse_published_date(args.reference_date)
        if ref_date is None:
            raise ValueError(f"Invalid --reference-date: {args.reference_date}")

    def _cli_cb(step: str, detail: str) -> None:
        print(f">> {step}: {detail}", file=sys.stderr, flush=True)

    refreshed = refresh_old_sources(
        report=report,
        reference_date=ref_date,
        use_cache=not args.no_cache,
        progress_callback=_cli_cb,
    )

    from research.pipeline import render_report_markdown

    full_md = render_report_markdown(refreshed)
    sec7_idx = full_md.find("## 7. Độ mới của dữ liệu")
    if sec7_idx != -1:
        print(full_md[sec7_idx:])
    else:
        print(full_md)

    if args.out_json:
        out_j = Path(args.out_json)
        out_j.parent.mkdir(parents=True, exist_ok=True)
        out_j.write_text(
            json.dumps(refreshed.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.out_md:
        out_m = Path(args.out_md)
        out_m.parent.mkdir(parents=True, exist_ok=True)
        out_m.write_text(full_md, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
