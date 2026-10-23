"""Recency Impact Layer (Mission 3 · Change Request A2): deterministic source age, quote vintage, counterfactual scoring, and CLI."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from functools import lru_cache
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Optional

import yaml

from research.dates import (
    DATE_METHOD_LABELS,
    add_months,
    compute_age_metrics,
    date_range,
    detect_data_period,
    extract_all_data_periods,
    format_date_display,
    infer_date_method_legacy,
    precision_of,
)
from research.grade import compute_freshness, parse_published_date
from research.schemas import (
    ConfidenceLevel,
    CounterfactualLevel,
    Evidence,
    ImpactLevel,
    InsightImpact,
    InsightRecency,
    InsightRecencyStatus,
    KeySourceImpact,
    RecencyImpact,
    RecencyStatus,
    RejectedItem,
    Report,
    Source,
    SourceRecency,
    ThresholdEvent,
)
from research.score import score_and_finalize_report, score_single_insight

POLICY_PATH = Path(__file__).resolve().parent.parent / "config" / "recency_policy.yaml"

RECENCY_SHORT_MARKER = "[Độ mới dữ liệu]"
RECENCY_REASON_MARKER = " · Độ mới:"

DEFAULT_POLICY: dict[str, Any] = {
    "alert_months": 18,
    "key_source_min_share": 0.25,
    "upcoming_window_months": 12,
    "refresh_max_targets": 2,
    "refresh_max_queries": 6,
    "refresh_max_new_sources": 6,
}


@lru_cache(maxsize=1)
def load_recency_policy(policy_path: Optional[Path] = None) -> dict[str, Any]:
    """Load recency policy from config/recency_policy.yaml with safe defaults."""
    path = policy_path or POLICY_PATH
    policy = dict(DEFAULT_POLICY)
    if path.exists():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                policy.update(loaded)
        except Exception:
            pass
    return policy


def _strip_recency_short_answer(short_answer: str) -> str:
    if not short_answer:
        return ""
    idx = short_answer.find(RECENCY_SHORT_MARKER)
    if idx != -1:
        return short_answer[:idx].rstrip()
    return short_answer.strip()


def _strip_recency_confidence_reason(reason: str) -> str:
    if not reason:
        return ""
    idx = reason.find(RECENCY_REASON_MARKER)
    if idx != -1:
        return reason[:idx].rstrip()
    return reason.strip()


def _conf_rank(level: str) -> int:
    return {"CAO": 3, "TRUNG BÌNH": 2, "THẤP": 1, "MẤT CĂN CỨ": 0}.get(level, 0)


def _status_severity(st: RecencyStatus) -> int:
    return {"MỚI": 0, "KHÔNG CHẮC": 1, "CŨ": 2}.get(st, 1)


def _period_age_approx_months(period_end: date, ref: date) -> int:
    return max(0, round((ref - period_end).days / 30.4375))


def _enrich_sources_and_evidences(
    report: Report, reference_date: date, alert_months: int
) -> tuple[
    list[Source],
    list[Evidence],
    dict[str, tuple[str, Optional[date]]],
    dict[str, bool],
]:
    """Populate date_method, date_precision, age_months*, and evidence data_period* on copies of sources/evidences."""
    updated_sources: list[Source] = []
    source_bounds: dict[str, Optional[date]] = {}
    source_ranges: dict[str, Optional[tuple[date, date]]] = {}

    for s in report.sources:
        method = (
            s.date_method
            if (s.date_method and s.date_method.strip())
            else infer_date_method_legacy(s.url, s.title, s.published_date)
        )
        prec = precision_of(method, s.published_date)
        age_m, age_min, age_max, _age_disp, _older, _possibly = compute_age_metrics(
            s.published_date, prec, reference_date, alert_months
        )
        new_s = s.model_copy(
            update={
                "date_method": method,
                "date_precision": prec,
                "age_months": age_m,
                "age_months_min": age_min,
                "age_months_max": age_max,
            }
        )
        updated_sources.append(new_s)
        source_bounds[s.id] = (
            parse_published_date(s.published_date) if prec == "day" else None
        )
        source_ranges[s.id] = date_range(s.published_date, prec)

    updated_evidences: list[Evidence] = []
    source_periods: dict[str, list[tuple[str, date]]] = {s.id: [] for s in updated_sources}
    source_conflicts: dict[str, bool] = {s.id: False for s in updated_sources}
    src_map = {s.id: s for s in updated_sources}

    for ev in report.evidences:
        pub_bound = source_bounds.get(ev.source_id)
        p_lbl, p_end = detect_data_period(
            ev.quote, ref=reference_date, publication_bound=pub_bound
        )
        new_ev = ev.model_copy(
            update={
                "data_period": p_lbl,
                "data_period_end": p_end.isoformat() if p_end else None,
            }
        )
        updated_evidences.append(new_ev)
        if ev.verified and p_lbl and p_end is not None and ev.source_id in source_periods:
            source_periods[ev.source_id].append((p_lbl, p_end))

        # Check date_conflict: precision != 'day' and quote mentions a period starting AFTER range_end
        s_obj = src_map.get(ev.source_id)
        s_rng = source_ranges.get(ev.source_id)
        if (
            ev.verified
            and s_obj is not None
            and s_obj.date_precision not in ("day", "unknown")
            and s_rng is not None
        ):
            _r_start, r_end = s_rng
            all_p = extract_all_data_periods(
                ev.quote, ref=reference_date, publication_bound=None
            )
            for _lbl, p_start, _p_end in all_p:
                if p_start > r_end:
                    source_conflicts[ev.source_id] = True
                    break

    source_vintages: dict[str, tuple[str, Optional[date]]] = {}
    for s in updated_sources:
        plist = source_periods.get(s.id, [])
        if plist:
            # Sort by end_date ascending -> take last
            plist_sorted = sorted(plist, key=lambda x: x[1])
            source_vintages[s.id] = plist_sorted[-1]
        else:
            source_vintages[s.id] = ("", None)

    return updated_sources, updated_evidences, source_vintages, source_conflicts


def _evaluate_evidence_status(
    src: Source,
    date_disp: str,
    age_disp: str,
    older_than_alert: bool,
    possibly_older_than_alert: bool,
    period_label: str,
    period_end: Optional[date],
    date_conflict: bool,
    reference_date: date,
    alert_months: int,
    conflict_period: str = "",
) -> tuple[RecencyStatus, list[str]]:
    """Evaluate (RecencyStatus, reasons) for a single evidence (or un-cited source) per 4.5 step 2."""
    reasons: list[str] = []
    has_p = bool(period_label and period_end is not None)
    p_is_old = bool(
        has_p and period_end is not None and add_months(period_end, alert_months) < reference_date
    )

    if date_conflict:
        c_lbl = conflict_period or period_label or "mới hơn"
        reasons.append(
            f"ngày đăng có thể sai (ghi {date_disp} nhưng trích dẫn nhắc số liệu {c_lbl})"
        )

    # Rule 2.1: p exists and add_months(p_end, alert) < ref => CŨ
    if has_p and p_is_old and period_end is not None:
        p_months = _period_age_approx_months(period_end, reference_date)
        reasons.insert(0, f"kỳ số liệu {period_label}, ~{p_months} tháng")
        if older_than_alert:
            reasons.append(f"đăng {date_disp}, {age_disp}")
        return "CŨ", reasons

    # Rule 2.2: source older_than_alert
    if older_than_alert:
        if has_p and not p_is_old:
            if not any("ngày đăng có thể sai" in r for r in reasons):
                reasons.insert(
                    0,
                    f"ngày đăng có thể sai (ghi {date_disp} nhưng trích dẫn nhắc kỳ {period_label})",
                )
            return "KHÔNG CHẮC", reasons
        reasons.insert(0, f"đăng {date_disp}, {age_disp}")
        return "CŨ", reasons

    # Rule 2.3: source possibly_older_than_alert or unknown date
    if possibly_older_than_alert or src.date_precision == "unknown":
        if has_p and not p_is_old:
            reasons.insert(
                0,
                f"kỳ số liệu {period_label} gần đây cho thấy nguồn không quá cũ (đăng {date_disp})",
            )
            return "MỚI", reasons
        if src.date_precision == "unknown" or not src.published_date:
            reasons.insert(0, "không rõ ngày đăng")
        elif src.date_precision == "year":
            yr_str = date_disp.split()[0]
            reasons.insert(0, f"chỉ biết năm {yr_str} → {age_disp}")
        else:
            reasons.insert(0, f"đăng {date_disp} ({age_disp}, có thể hơn {alert_months} tháng)")
        return "KHÔNG CHẮC", reasons

    # Rule 2.4: Otherwise => MỚI
    if has_p:
        reasons.append(f"đăng {date_disp} ({age_disp}), kỳ số liệu {period_label}")
    else:
        reasons.append(f"đăng {date_disp} ({age_disp})")
    return "MỚI", reasons


def _simulate_thresholds(
    report: Report,
    sources: list[Source],
    evidences: list[Evidence],
    cited_source_ids: set[str],
    reference_date: date,
    window_months: int = 12,
) -> list[ThresholdEvent]:
    """Compute up to 3 upcoming freshness bucket transitions within `window_months` (step 10)."""
    horizon = add_months(reference_date, window_months)
    date_to_sids: dict[date, list[str]] = {}

    for s in sources:
        if s.id not in cited_source_ids or not s.published_date:
            continue
        parsed = parse_published_date(s.published_date)
        if parsed is None:
            continue
        transitions: list[date] = []
        if s.freshness == "fresh":
            transitions.append(parsed + timedelta(days=367))
            transitions.append(parsed + timedelta(days=732))
        elif s.freshness == "aging":
            transitions.append(parsed + timedelta(days=732))

        for t_date in transitions:
            if reference_date < t_date <= horizon:
                date_to_sids.setdefault(t_date, []).append(s.id)

    if not date_to_sids:
        return []

    evidence_map = {e.id: e for e in evidences if e.verified}
    events: list[ThresholdEvent] = []
    running_confs: dict[str, str] = {ins.id: ins.confidence for ins in report.insights}

    for t_date in sorted(date_to_sids.keys()):
        sids = sorted(date_to_sids[t_date], key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
        future_smap: dict[str, Source] = {}
        for s in sources:
            f_code, f_lbl = compute_freshness(s.published_date, reference_date=t_date)
            future_smap[s.id] = s.model_copy(
                update={"freshness": f_code, "freshness_label": f_lbl}
            )

        changes: list[str] = []
        for ins in report.insights:
            fut_scored = score_single_insight(ins, evidence_map, future_smap)
            prev_c = running_confs.get(ins.id, ins.confidence)
            if fut_scored.confidence != prev_c:
                changes.append(f"{ins.id}: {prev_c} → {fut_scored.confidence}")
                running_confs[ins.id] = fut_scored.confidence

        if changes:
            events.append(
                ThresholdEvent(
                    date=t_date.isoformat(),
                    source_ids=sids,
                    changes=changes,
                )
            )
        if len(events) >= 3:
            break

    # If no transition within 12m caused an immediate confidence drop, still record earliest transition up to 3
    if not events:
        for t_date in sorted(date_to_sids.keys())[:3]:
            sids = sorted(
                date_to_sids[t_date], key=lambda x: int(x[1:]) if x[1:].isdigit() else 999
            )
            events.append(
                ThresholdEvent(
                    date=t_date.isoformat(),
                    source_ids=sids,
                    changes=["Chưa làm đổi mức độ tin cậy của nhận định (chuyển nhóm độ mới nguồn)"],
                )
            )

    return events


def _build_suggested_queries(
    key_old_sources: list[KeySourceImpact],
    source_map: dict[str, Source],
    reference_date: date,
) -> list[str]:
    """Generate deterministic refresh queries from key old sources (step 11)."""
    ref_yr = str(reference_date.year)
    prev_yr = str(reference_date.year - 1)
    queries: list[str] = []
    seen: set[str] = set()

    def _add(q: str) -> None:
        q_clean = re.sub(r"\s+", " ", q).strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            queries.append(q_clean)

    for kos in key_old_sources:
        src = source_map.get(kos.source_id)
        if not src:
            continue
        base_title = re.sub(r"\s*[\|\-–—]\s*[^|\-–—]+$", "", src.title or "").strip()
        if not base_title:
            base_title = src.title or src.domain

        if re.search(r"\b20[12]\d\b", base_title):
            title_ref = re.sub(r"\b20[12]\d\b", ref_yr, base_title)
            title_prev = re.sub(r"\b20[12]\d\b", prev_yr, base_title)
        else:
            title_ref = f"{base_title} {ref_yr}"
            title_prev = f"{base_title} {prev_yr}"

        _add(f"{title_ref} site:{src.domain}")
        _add(title_ref)
        if title_prev != title_ref:
            _add(f"{title_prev} site:{src.domain}")

    return queries[:6]


def analyze_recency(
    report: Report, reference_date: date, alert_months: int = 18
) -> RecencyImpact:
    """Run deterministic 12-step recency and counterfactual impact analysis (BRIEF_M3 4.5)."""
    policy = load_recency_policy()
    min_share = float(policy.get("key_source_min_share", 0.25))
    window_months = int(policy.get("upcoming_window_months", 12))

    sources, evidences, source_vintages, source_conflicts = _enrich_sources_and_evidences(
        report, reference_date, alert_months
    )
    source_map = {s.id: s for s in sources}
    evidence_map = {e.id: e for e in evidences if e.verified}

    # Map which insights cite which evidences and sources
    source_to_insights: dict[str, list[str]] = {s.id: [] for s in sources}
    source_cited_evidences: dict[str, list[Evidence]] = {s.id: [] for s in sources}
    for ins in report.insights:
        for eid in ins.evidence_ids:
            ev = evidence_map.get(eid)
            if not ev:
                continue
            sid = ev.source_id
            if sid in source_to_insights and ins.id not in source_to_insights[sid]:
                source_to_insights[sid].append(ins.id)
            if sid in source_cited_evidences and all(
                x.id != ev.id for x in source_cited_evidences[sid]
            ):
                source_cited_evidences[sid].append(ev)

    # Evaluate each evidence's recency status
    ev_status_map: dict[str, tuple[RecencyStatus, list[str]]] = {}
    src_metrics_cache: dict[str, tuple[str, str, str, bool, bool]] = {}

    for s in sources:
        prec = s.date_precision
        date_disp = format_date_display(s.published_date, prec)
        method_lbl = DATE_METHOD_LABELS.get(s.date_method, "không xác định được")
        _am, _amin, _amax, age_disp, older, possibly = compute_age_metrics(
            s.published_date, prec, reference_date, alert_months
        )
        src_metrics_cache[s.id] = (date_disp, method_lbl, age_disp, older, possibly)

    for ev in evidences:
        if not ev.verified:
            continue
        s = source_map.get(ev.source_id)
        if not s:
            continue
        date_disp, _mlbl, age_disp, older, possibly = src_metrics_cache[s.id]
        v_lbl, v_end = source_vintages.get(s.id, ("", None))
        p_lbl = ev.data_period or v_lbl
        p_end = (
            date.fromisoformat(ev.data_period_end)
            if ev.data_period_end
            else v_end
        )
        st_code, st_reasons = _evaluate_evidence_status(
            src=s,
            date_disp=date_disp,
            age_disp=age_disp,
            older_than_alert=older,
            possibly_older_than_alert=possibly,
            period_label=p_lbl,
            period_end=p_end,
            date_conflict=source_conflicts.get(s.id, False),
            reference_date=reference_date,
            alert_months=alert_months,
            conflict_period=v_lbl,
        )
        ev_status_map[ev.id] = (st_code, st_reasons)

    # Step 3 & Step 5 & Step 6: Build SourceRecency and counterfactuals
    num_insights = len(report.insights)
    min_supported_for_key = max(2, math.ceil(min_share * num_insights)) if num_insights > 0 else 2

    # Identify unique Tier A/B sources for CAO/TRUNG BÌNH insights (condition 6b)
    sole_ab_sources: dict[str, list[str]] = {s.id: [] for s in sources}
    for ins in report.insights:
        if ins.confidence not in ("CAO", "TRUNG BÌNH"):
            continue
        ab_sids = sorted(
            {
                evidence_map[eid].source_id
                for eid in ins.evidence_ids
                if eid in evidence_map
                and evidence_map[eid].source_id in source_map
                and source_map[evidence_map[eid].source_id].tier in ("A", "B")
            }
        )
        if len(ab_sids) == 1:
            sole_ab_sources[ab_sids[0]].append(ins.id)

    source_recencies: list[SourceRecency] = []
    source_impacts_map: dict[str, list[InsightImpact]] = {}
    ins_map = {ins.id: ins for ins in report.insights}

    for s in sources:
        date_disp, method_lbl, age_disp, older, possibly = src_metrics_cache[s.id]
        v_lbl, v_end = source_vintages.get(s.id, ("", None))
        d_conflict = source_conflicts.get(s.id, False)
        cited_evs = source_cited_evidences.get(s.id, [])
        supported_iids = source_to_insights.get(s.id, [])

        if cited_evs:
            # Worst status among cited evidences: CŨ > KHÔNG CHẮC > MỚI
            worst_status: RecencyStatus = "MỚI"
            combined_reasons: list[str] = []
            for cev in cited_evs:
                est, ereasons = ev_status_map.get(cev.id, ("KHÔNG CHẮC", []))
                if _status_severity(est) > _status_severity(worst_status):
                    worst_status = est
                for r in ereasons:
                    if r not in combined_reasons:
                        combined_reasons.append(r)
            s_status = worst_status
            s_reasons = combined_reasons
        else:
            s_status, s_reasons = _evaluate_evidence_status(
                src=s,
                date_disp=date_disp,
                age_disp=age_disp,
                older_than_alert=older,
                possibly_older_than_alert=possibly,
                period_label=v_lbl,
                period_end=v_end,
                date_conflict=d_conflict,
                reference_date=reference_date,
                alert_months=alert_months,
                conflict_period=v_lbl,
            )

        # Step 5: Counterfactuals for each insight citing s
        impacts: list[InsightImpact] = []
        fresh_smap = dict(source_map)
        fresh_smap[s.id] = s.model_copy(
            update={"freshness": "fresh", "freshness_label": "Mới (<=12 tháng)"}
        )

        dropped_high_med: list[str] = []
        upgraded_if_fresh: list[str] = []

        for iid in supported_iids:
            ins = ins_map[iid]
            rem_eids = [
                eid
                for eid in ins.evidence_ids
                if eid in evidence_map and evidence_map[eid].source_id != s.id
            ]
            if not rem_eids:
                if_removed: CounterfactualLevel = "MẤT CĂN CỨ"
            else:
                rescored_rem = score_single_insight(
                    ins.model_copy(update={"evidence_ids": rem_eids}),
                    evidence_map,
                    source_map,
                )
                if_removed = rescored_rem.confidence

            rescored_fresh = score_single_insight(ins, evidence_map, fresh_smap)
            if_fresh: ConfidenceLevel = rescored_fresh.confidence

            impacts.append(
                InsightImpact(
                    insight_id=iid,
                    current=ins.confidence,
                    if_source_removed=if_removed,
                    if_source_fresh=if_fresh,
                )
            )

            if ins.confidence in ("CAO", "TRUNG BÌNH") and _conf_rank(if_removed) < _conf_rank(
                ins.confidence
            ):
                dropped_high_med.append(f"{iid} ({ins.confidence} → {if_removed})")

            if _conf_rank(if_fresh) > _conf_rank(ins.confidence):
                upgraded_if_fresh.append(f"{iid} ({ins.confidence} → {if_fresh})")

        source_impacts_map[s.id] = impacts

        # Step 6: Key source conditions (only for cited sources)
        key_reasons: list[str] = []
        if supported_iids:
            if dropped_high_med:
                key_reasons.append(
                    f"bỏ nguồn làm giảm/mất căn cứ nhận định {', '.join(dropped_high_med)}"
                )
            if sole_ab_sources.get(s.id):
                key_reasons.append(
                    f"nguồn hạng {s.tier} duy nhất của nhận định {', '.join(sole_ab_sources[s.id])}"
                )
            if len(supported_iids) >= min_supported_for_key:
                key_reasons.append(
                    f"hỗ trợ {len(supported_iids)}/{num_insights} nhận định ({', '.join(supported_iids)})"
                )
            if upgraded_if_fresh:
                key_reasons.append(
                    f"nếu còn mới sẽ nâng mức {', '.join(upgraded_if_fresh)}"
                )

        source_recencies.append(
            SourceRecency(
                source_id=s.id,
                status=s_status,
                reasons=s_reasons,
                date_display=date_disp,
                date_method_label=method_lbl,
                age_display=age_disp,
                older_than_alert=older,
                possibly_older_than_alert=possibly,
                data_vintage=v_lbl,
                date_conflict=d_conflict,
                supported_insight_ids=supported_iids,
                is_key=bool(key_reasons),
                key_reasons=key_reasons,
            )
        )

    src_rec_map = {sr.source_id: sr for sr in source_recencies}

    # Step 4: InsightRecency
    insight_recencies: list[InsightRecency] = []
    for ins in report.insights:
        ev_statuses: list[RecencyStatus] = []
        non_recent_sids: list[str] = []
        note_parts: list[str] = []

        for eid in ins.evidence_ids:
            ev = evidence_map.get(eid)
            if not ev:
                continue
            est, _er = ev_status_map.get(ev.id, ("KHÔNG CHẮC", []))
            ev_statuses.append(est)
            if est != "MỚI":
                if ev.source_id not in non_recent_sids:
                    non_recent_sids.append(ev.source_id)
                    sr = src_rec_map.get(ev.source_id)
                    if sr:
                        v_part = f", kỳ {ev.data_period or sr.data_vintage}" if (ev.data_period or sr.data_vintage) else ""
                        note_parts.append(f"{ev.source_id} {sr.date_display}{v_part}")

        if ev_statuses and all(st == "MỚI" for st in ev_statuses):
            i_status: InsightRecencyStatus = "MỚI"
        elif any(st == "MỚI" for st in ev_statuses):
            i_status = "MỘT PHẦN CŨ"
        else:
            i_status = "KHÔNG CÓ BẰNG CHỨNG MỚI"

        insight_recencies.append(
            InsightRecency(
                insight_id=ins.id,
                status=i_status,
                non_recent_source_ids=non_recent_sids,
                note="; ".join(note_parts),
            )
        )

    # Step 7: Build and sort key_old_sources
    key_old_candidates: list[SourceRecency] = [
        sr for sr in source_recencies if sr.is_key and sr.status in ("CŨ", "KHÔNG CHẮC")
    ]

    def _kos_sort_key(sr: SourceRecency) -> tuple[int, int, int, int]:
        imps = source_impacts_map.get(sr.source_id, [])
        # Count affected CAO/TRUNG BÌNH insights (dropped when removed OR any insight upgraded to CAO/TB when fresh)
        affected_cnt = sum(
            1
            for imp in imps
            if (
                imp.current in ("CAO", "TRUNG BÌNH")
                and _conf_rank(imp.if_source_removed) < _conf_rank(imp.current)
            )
            or _conf_rank(imp.if_source_fresh) > _conf_rank(imp.current)
        )
        tier_rank = {"A": 0, "B": 1, "C": 2}.get(source_map[sr.source_id].tier, 2)
        s_num = int(sr.source_id[1:]) if sr.source_id[1:].isdigit() else 999
        return (-affected_cnt, -len(sr.supported_insight_ids), tier_rank, s_num)

    key_old_candidates.sort(key=_kos_sort_key)

    key_old_sources: list[KeySourceImpact] = []
    for sr in key_old_candidates:
        s = source_map[sr.source_id]
        imps = source_impacts_map.get(sr.source_id, [])

        rem_changes: list[str] = []
        fresh_changes: list[str] = []
        for imp in imps:
            if imp.if_source_removed == "MẤT CĂN CỨ":
                rem_changes.append(f"{imp.insight_id} mất căn cứ (không còn nguồn nào khác)")
            elif imp.if_source_removed != imp.current:
                rem_changes.append(
                    f"{imp.insight_id} giảm {imp.current} → {imp.if_source_removed}"
                )
            if imp.if_source_fresh != imp.current:
                fresh_changes.append(
                    f"{imp.insight_id} tăng {imp.current} → {imp.if_source_fresh}"
                )

        rem_str = "; ".join(rem_changes) if rem_changes else "không nhận định nào bị tụt mức"
        fresh_str = (
            "; ".join(fresh_changes)
            if fresh_changes
            else "độ tin cậy giữ nguyên"
        )
        vint_str = (
            f"; kỳ số liệu mới nhất trong trích dẫn: {sr.data_vintage}"
            if sr.data_vintage
            else ""
        )
        kos_summary = (
            f"{s.id} ({s.domain}, hạng {s.tier}; đăng {sr.date_display} — {sr.date_method_label}; "
            f"tuổi ước tính {sr.age_display}{vint_str}) là căn cứ của "
            f"{len(sr.supported_insight_ids)}/{num_insights} nhận định ({', '.join(sr.supported_insight_ids)}). "
            f"Nếu bỏ nguồn này: {rem_str}. "
            f"Nếu có bản cập nhật mới (≤ 12 tháng): {fresh_str}."
        )
        key_old_sources.append(
            KeySourceImpact(
                source_id=s.id,
                impacts=imps,
                summary=kos_summary,
            )
        )

    # Step 8: Overall report impact_level
    ins_rec_map = {ir.insight_id: ir for ir in insight_recencies}
    has_high_med_without_fresh = any(
        ins.confidence in ("CAO", "TRUNG BÌNH")
        and ins_rec_map[ins.id].status == "KHÔNG CÓ BẰNG CHỨNG MỚI"
        for ins in report.insights
    )
    has_old_source_dropping_high_med = any(
        sr.status == "CŨ"
        and any(
            imp.current in ("CAO", "TRUNG BÌNH")
            and _conf_rank(imp.if_source_removed) < _conf_rank(imp.current)
            for imp in source_impacts_map.get(sr.source_id, [])
        )
        for sr in source_recencies
    )
    has_low_without_fresh = any(
        ins.confidence == "THẤP"
        and ins_rec_map[ins.id].status == "KHÔNG CÓ BẰNG CHỨNG MỚI"
        for ins in report.insights
    )
    part_old_count = sum(1 for ir in insight_recencies if ir.status == "MỘT PHẦN CŨ")
    has_25pct_part_old = (
        num_insights > 0 and (part_old_count / num_insights) >= 0.25
    )
    has_any_cited_non_fresh = any(
        bool(sr.supported_insight_ids) and sr.status in ("CŨ", "KHÔNG CHẮC")
        for sr in source_recencies
    )

    if has_high_med_without_fresh or has_old_source_dropping_high_med:
        impact_level: ImpactLevel = "ĐÁNG KỂ"
    elif has_low_without_fresh or has_25pct_part_old:
        impact_level = "VỪA PHẢI"
    elif has_any_cited_non_fresh:
        impact_level = "NHỎ"
    else:
        impact_level = "KHÔNG"

    # Step 9: Deterministic Vietnamese summary (<= 60 words)
    no_fresh_iids = [
        ir.insight_id
        for ir in insight_recencies
        if ir.status == "KHÔNG CÓ BẰNG CHỨNG MỚI"
    ]
    if impact_level == "KHÔNG":
        summary = (
            f"Mức ảnh hưởng: KHÔNG. Toàn bộ {num_insights}/{num_insights} nhận định đều dựa trên "
            f"nguồn và số liệu mới trong {alert_months} tháng gần đây (tính đến {reference_date.isoformat()})."
        )
    else:
        no_fresh_str = (
            f"{len(no_fresh_iids)}/{num_insights} nhận định chưa có bằng chứng mới trong {alert_months} tháng gần đây ({', '.join(no_fresh_iids)})"
            if no_fresh_iids
            else f"0/{num_insights} nhận định thiếu hoàn toàn bằng chứng mới"
        )
        part_str = (
            f"; {part_old_count} nhận định dựa một phần vào dữ liệu cũ"
            if part_old_count > 0
            else ""
        )
        if key_old_sources:
            top_kos_id = key_old_sources[0].source_id
            top_sr = src_rec_map[top_kos_id]
            top_s = source_map[top_kos_id]
            v_note = f", số liệu {top_sr.data_vintage}" if top_sr.data_vintage else ""
            extra_kos = (
                f" (cùng {', '.join(k.source_id for k in key_old_sources[1:3])})"
                if len(key_old_sources) > 1
                else ""
            )
            top_src_str = (
                f" Nguồn cũ then chốt: {top_s.id}{extra_kos} ({top_s.domain}, {top_sr.date_display}, "
                f"{top_sr.age_display}{v_note})."
            )
        else:
            non_fresh_cited = [
                sr for sr in source_recencies if sr.supported_insight_ids and sr.status != "MỚI"
            ]
            if non_fresh_cited:
                nf = non_fresh_cited[0]
                nf_s = source_map[nf.source_id]
                top_src_str = f" Nguồn cần lưu ý: {nf_s.id} ({nf_s.domain}, {nf.date_display})."
            else:
                top_src_str = ""
        summary = f"Mức ảnh hưởng: {impact_level}. {no_fresh_str}{part_str}.{top_src_str} Chi tiết ở mục 7."

    # Step 10: Upcoming threshold events
    cited_sids = {sr.source_id for sr in source_recencies if sr.supported_insight_ids}
    upcoming_changes = _simulate_thresholds(
        report=report,
        sources=sources,
        evidences=evidences,
        cited_source_ids=cited_sids,
        reference_date=reference_date,
        window_months=window_months,
    )

    # Step 11: Suggested refresh queries
    suggested_queries = _build_suggested_queries(
        key_old_sources=key_old_sources,
        source_map=source_map,
        reference_date=reference_date,
    )

    # Step 12: Certainty groups ("Đủ cơ sở" | "Cần lưu ý" | "Chưa chắc chắn")
    certainty_groups: dict[str, list[str]] = {
        "Đủ cơ sở": [],
        "Cần lưu ý": [],
        "Chưa chắc chắn": [],
    }
    for ins in report.insights:
        ir = ins_rec_map[ins.id]
        if ins.confidence == "CAO" or (
            ins.confidence == "TRUNG BÌNH"
            and ins.type == "fact"
            and not ins.is_forecast
            and not ins.has_conflict
            and ir.status == "MỚI"
        ):
            certainty_groups["Đủ cơ sở"].append(ins.id)
        elif ins.confidence == "THẤP" or ir.status == "KHÔNG CÓ BẰNG CHỨNG MỚI":
            certainty_groups["Chưa chắc chắn"].append(ins.id)
        else:
            certainty_groups["Cần lưu ý"].append(ins.id)

    return RecencyImpact(
        reference_date=reference_date.isoformat(),
        alert_months=alert_months,
        impact_level=impact_level,
        summary=summary,
        sources=source_recencies,
        key_old_sources=key_old_sources,
        insights=insight_recencies,
        upcoming_changes=upcoming_changes,
        suggested_refresh_queries=suggested_queries,
        certainty_groups=certainty_groups,
    )


def apply_recency_layer(
    report: Report,
    reference_date: Optional[date] = None,
    alert_months: Optional[int] = None,
) -> Report:
    """Enrich sources/evidences, attach `recency`, and idempotently append recency notes (never mutates confidence)."""
    if reference_date is None:
        cur_str = str((report.trace or {}).get("current_date") or "").strip()
        parsed_ref = parse_published_date(cur_str)
        reference_date = parsed_ref or date.today()

    if alert_months is None:
        alert_months = int(load_recency_policy().get("alert_months", 18))

    sources, evidences, _vintages, _conflicts = _enrich_sources_and_evidences(
        report, reference_date, alert_months
    )
    temp_report = report.model_copy(update={"sources": sources, "evidences": evidences})
    recency = analyze_recency(temp_report, reference_date=reference_date, alert_months=alert_months)

    # Idempotently update short_answer (only append marker when impact_level == 'ĐÁNG KỂ')
    base_short = _strip_recency_short_answer(report.short_answer)
    if recency.impact_level == "ĐÁNG KỂ":
        new_short = f"{base_short} {RECENCY_SHORT_MARKER} {recency.summary}"
    else:
        new_short = base_short

    # Idempotently update confidence_reason on non-MỚI insights (never touch confidence)
    ins_rec_map = {ir.insight_id: ir for ir in recency.insights}
    updated_insights = []
    for ins in report.insights:
        base_reason = _strip_recency_confidence_reason(ins.confidence_reason)
        ir = ins_rec_map.get(ins.id)
        if ir and ir.status != "MỚI":
            detail_part = f" ({ir.note})" if ir.note else ""
            new_reason = f"{base_reason}{RECENCY_REASON_MARKER} {ir.status}{detail_part}"
        else:
            new_reason = base_reason
        updated_insights.append(ins.model_copy(update={"confidence_reason": new_reason}))

    return temp_report.model_copy(
        update={
            "short_answer": new_short,
            "insights": updated_insights,
            "recency": recency,
        }
    )


def finalize_with_recency(
    report: Report,
    reference_date: date,
    total_quotes_extracted: int,
    rejected_sources: Iterable[RejectedItem] = (),
    rejected_quotes: Iterable[RejectedItem] = (),
    urls_removed_floor: int = 0,
    alert_months: Optional[int] = None,
) -> Report:
    """Common finalization path: strip recency markers -> score_and_finalize_report -> apply_recency_layer."""
    clean_short = _strip_recency_short_answer(report.short_answer)
    clean_insights = [
        ins.model_copy(
            update={"confidence_reason": _strip_recency_confidence_reason(ins.confidence_reason)}
        )
        for ins in report.insights
    ]
    cleaned_report = report.model_copy(
        update={"short_answer": clean_short, "insights": clean_insights}
    )
    scored = score_and_finalize_report(
        report=cleaned_report,
        total_quotes_extracted=total_quotes_extracted,
        rejected_sources=rejected_sources,
        rejected_quotes=rejected_quotes,
    )
    if urls_removed_floor > scored.quality.llm_invented_urls_removed_count:
        scored = scored.model_copy(
            update={
                "quality": scored.quality.model_copy(
                    update={"llm_invented_urls_removed_count": urls_removed_floor}
                )
            }
        )
    return apply_recency_layer(scored, reference_date=reference_date, alert_months=alert_months)


def rescore_report_as_of(
    report: Report, as_of: date, alert_months: Optional[int] = None
) -> Report:
    """Recompute source freshness buckets as of `as_of`, re-score insights deterministically, and apply recency layer."""
    regraded_sources: list[Source] = []
    for s in report.sources:
        f_code, f_lbl = compute_freshness(s.published_date, reference_date=as_of)
        regraded_sources.append(
            s.model_copy(update={"freshness": f_code, "freshness_label": f_lbl})
        )

    base_report = report.model_copy(update={"sources": regraded_sources})
    finalized = finalize_with_recency(
        report=base_report,
        reference_date=as_of,
        total_quotes_extracted=report.quality.total_quotes_extracted,
        rejected_sources=report.quality.rejected_sources,
        rejected_quotes=report.quality.rejected_quotes,
        urls_removed_floor=report.quality.llm_invented_urls_removed_count,
        alert_months=alert_months,
    )
    new_trace = dict(finalized.trace or {})
    new_trace["rescored_as_of"] = as_of.isoformat()
    return finalized.model_copy(update={"trace": new_trace})


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Analyze data recency and counterfactual confidence impact on a saved Report JSON (0 LLM calls)."
    )
    parser.add_argument("report_json", type=str, help="Path to saved report JSON")
    parser.add_argument(
        "--as-of",
        type=str,
        default="",
        help="Reference date YYYY-MM-DD (if different from report's current_date, runs rescore_report_as_of)",
    )
    parser.add_argument("--out-json", type=str, default="", help="Output JSON path")
    parser.add_argument("--out-md", type=str, default="", help="Output Markdown path")
    args = parser.parse_args()

    in_path = Path(args.report_json)
    raw_data = json.loads(in_path.read_text(encoding="utf-8"))
    report = Report.model_validate(raw_data)

    report_date_str = str((report.trace or {}).get("current_date") or "").strip()
    report_date = parse_published_date(report_date_str)

    if args.as_of:
        as_of_date = parse_published_date(args.as_of)
        if as_of_date is None:
            raise ValueError(f"Invalid --as-of date: {args.as_of}")
        if report_date is not None and as_of_date != report_date:
            updated = rescore_report_as_of(report, as_of=as_of_date)
        else:
            updated = apply_recency_layer(report, reference_date=as_of_date)
    else:
        updated = apply_recency_layer(report, reference_date=report_date)

    from research.pipeline import render_report_markdown

    full_md = render_report_markdown(updated)
    sec7_idx = full_md.find("## 7. Độ mới của dữ liệu")
    if sec7_idx != -1:
        print(full_md[sec7_idx:])
    else:
        print(full_md)

    if args.out_json:
        out_j = Path(args.out_json)
        out_j.parent.mkdir(parents=True, exist_ok=True)
        out_j.write_text(
            json.dumps(updated.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    if args.out_md:
        out_m = Path(args.out_md)
        out_m.parent.mkdir(parents=True, exist_ok=True)
        out_m.write_text(full_md, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
