"""Evaluation runner (`python -m eval.run_eval [--case TC3] [--reference-date YYYY-MM-DD]`) for Gamota Market Research MVP."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import sys
import time
from typing import Any, Optional

import yaml

from research.grade import parse_published_date
from research.pipeline import render_report_markdown, run
from research.recency import _strip_recency_short_answer, rescore_report_as_of
from research.refresh import refresh_old_sources
from research.schemas import Report

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
CASES_PATH = EVAL_DIR / "cases.yaml"
RESULTS_DIR = EVAL_DIR / "results"


def _parse_date_arg(val: Optional[str]) -> Optional[date]:
    if not val:
        return None
    s = str(val).strip().lower()
    if s == "today":
        return date.today()
    return parse_published_date(s)


def evaluate_assertions(report: Report, assertions: dict[str, Any]) -> tuple[bool, list[str]]:
    """Evaluate machine-checkable expectations (Mission 2 + Mission 3) against a real Report run."""
    reasons: list[str] = []
    passed = True

    min_quotes = assertions.get("min_verified_quotes")
    if min_quotes is not None:
        if report.quality.verified_quotes_count < int(min_quotes):
            passed = False
            reasons.append(
                f"Số trích dẫn xác minh ({report.quality.verified_quotes_count}) < kỳ vọng ({min_quotes})"
            )

    min_rate = assertions.get("min_verified_rate")
    if min_rate is not None:
        if report.quality.verified_quote_rate < float(min_rate):
            passed = False
            reasons.append(
                f"Tỷ lệ xác minh trích dẫn ({report.quality.verified_quote_rate}%) < {min_rate}%"
            )

    if assertions.get("max_forecast_confidence") == "TRUNG BÌNH":
        bad_forecasts = [
            i.id
            for i in report.insights
            if (i.is_forecast or i.type == "inference") and i.confidence == "CAO"
        ]
        if bad_forecasts:
            passed = False
            reasons.append(f"Dự báo/suy luận vượt quá TRUNG BÌNH: {bad_forecasts}")

    if assertions.get("must_have_assumptions_on_forecast"):
        missing_assump = [
            i.id
            for i in report.insights
            if (i.is_forecast or i.type == "inference") and not i.assumptions
        ]
        if missing_assump:
            passed = False
            reasons.append(f"Dự báo/suy luận thiếu giả định: {missing_assump}")

    if assertions.get("must_have_conflicts_or_multiple_figures"):
        if not report.conflicts:
            passed = False
            reasons.append("Chưa ghi nhận các con số/nguồn khác nhau trong mục mâu thuẫn (conflicts)")
        import re as _re

        num_mentions = _re.findall(
            r"\b\d+(?:[.,]\d+)?\s*(?:triệu|tỷ|million|billion|M|B)\b",
            report.short_answer,
            _re.IGNORECASE,
        )
        if len(num_mentions) < 2:
            passed = False
            reasons.append("Câu trả lời ngắn (short_answer) mới nêu 1 con số thay vì nêu dải nhiều con số kèm nguồn")

    if assertions.get("must_have_gaps"):
        if not report.gaps:
            passed = False
            reasons.append("Thiếu mục khoảng trống dữ liệu (gaps)")

    if assertions.get("must_have_next_checks"):
        if not report.next_checks:
            passed = False
            reasons.append("Thiếu đề xuất bước kiểm chứng tiếp theo (next_checks)")

    if assertions.get("must_challenge_premise"):
        challenged = any(
            pc.status in ("BÁC BỎ", "CHƯA ĐỦ BẰNG CHỨNG", "MỘT PHẦN")
            for pc in report.premise_checks
        )
        if not challenged:
            passed = False
            reasons.append("Chưa phản biện/kiểm tra tiền đề sai trong premise_checks")

    if assertions.get("strict_recent_month_data_required"):
        # TC6 requires exact last-month revenue for top 3 Thailand gacha games from open web
        sa_low = (report.short_answer or "").lower()
        admits_missing = any(
            kw in sa_low
            for kw in (
                "không có sẵn",
                "không tìm thấy",
                "chưa có số liệu",
                "chưa có dữ liệu",
                "không thể xác định",
                "không công bố",
            )
        )
        has_high_conf_thailand_gacha = any(
            i.confidence == "CAO"
            and i.type == "fact"
            and ("thái lan" in i.statement.lower() or "thailand" in i.statement.lower())
            and not any(
                m in i.statement.lower()
                for m in ("không có sẵn", "không tìm thấy", "chưa có")
            )
            for i in report.insights
        )
        if admits_missing or not has_high_conf_thailand_gacha:
            passed = False
            reasons.append(
                "CHƯA ĐẠT (Đúng giới hạn nguồn mở): Nguồn web mở không có bảng số liệu doanh thu đúng 'tháng trước' của top 3 game gacha tại riêng Thái Lan (bị khóa sau paywall Sensor Tower/AppMagic); hệ thống đã trung thực báo thiếu dữ liệu thay vì bịa số"
            )

    if report.quality.high_confidence_from_tier_c_only_count > 0:
        passed = False
        reasons.append(
            f"Vi phạm quy tắc: có {report.quality.high_confidence_from_tier_c_only_count} nhận định CAO từ nguồn C"
        )

    # --- Mission 3 Assertions (BRIEF_M3 section 6.3) ---
    if assertions.get("must_have_recency_analysis"):
        if report.recency is None:
            passed = False
            reasons.append("Thiếu report.recency")
        elif len(report.recency.sources) != len(report.sources):
            passed = False
            reasons.append(
                f"Số nguồn trong report.recency ({len(report.recency.sources)}) != số nguồn báo cáo ({len(report.sources)})"
            )

    if assertions.get("must_flag_key_old_source"):
        if report.recency is None or not report.recency.key_old_sources:
            passed = False
            reasons.append("Không phát hiện nguồn then chốt cũ nào trong key_old_sources")
        else:
            sr_map = {sr.source_id: sr for sr in report.recency.sources}
            has_old = any(
                sr_map.get(k.source_id) is not None and sr_map[k.source_id].status == "CŨ"
                for k in report.recency.key_old_sources
            )
            all_have_impacts = all(len(k.impacts) >= 1 for k in report.recency.key_old_sources)
            if not has_old:
                passed = False
                reasons.append("Không có nguồn then chốt nào mang trạng thái CŨ")
            if not all_have_impacts:
                passed = False
                reasons.append("Có phần tử trong key_old_sources thiếu InsightImpact")

    if assertions.get("must_disclose_recency_in_short_answer"):
        if report.recency is None or report.recency.impact_level != "ĐÁNG KỂ":
            passed = False
            reasons.append(
                f"Kỳ vọng mức ảnh hưởng ĐÁNG KỂ nhưng nhận được {report.recency.impact_level if report.recency else None}"
            )
        if "[Độ mới dữ liệu]" not in (report.short_answer or ""):
            passed = False
            reasons.append("short_answer thiếu ghi chú '[Độ mới dữ liệu]'")

    if assertions.get("recency_note_consistent"):
        if report.recency is None:
            passed = False
            reasons.append("Thiếu report.recency để kiểm recency_note_consistent")
        else:
            has_marker = "[Độ mới dữ liệu]" in (report.short_answer or "")
            should_have = report.recency.impact_level == "ĐÁNG KỂ"
            if has_marker != should_have:
                passed = False
                reasons.append(
                    f"Marker '[Độ mới dữ liệu]' ({has_marker}) không nhất quán với impact_level ({report.recency.impact_level})"
                )

    if assertions.get("must_not_alarm_recency"):
        if report.recency is None or report.recency.impact_level not in ("KHÔNG", "NHỎ"):
            passed = False
            reasons.append(
                f"Kỳ vọng mức KHÔNG hoặc NHỎ nhưng nhận được {report.recency.impact_level if report.recency else None}"
            )
        if "[Độ mới dữ liệu]" in (report.short_answer or ""):
            passed = False
            reasons.append("short_answer có marker '[Độ mới dữ liệu]' dù mức ảnh hưởng không ĐÁNG KỂ")

    if assertions.get("must_flag_uncertain_age"):
        if report.recency is None:
            passed = False
            reasons.append("Thiếu report.recency")
        else:
            src_map = {s.id: s for s in report.sources}
            found_uncertain = any(
                bool(sr.supported_insight_ids)
                and sr.status == "KHÔNG CHẮC"
                and src_map.get(sr.source_id) is not None
                and src_map[sr.source_id].date_precision in ("year", "unknown")
                for sr in report.recency.sources
            )
            if not found_uncertain:
                passed = False
                reasons.append(
                    "Không tìm thấy nguồn được trích dẫn nào ở trạng thái KHÔNG CHẮC do precision year/unknown"
                )

    if assertions.get("must_flag_old_data_period"):
        if report.recency is None:
            passed = False
            reasons.append("Thiếu report.recency")
        else:
            found_old_period = any(
                not sr.older_than_alert and sr.status == "CŨ" and bool(sr.data_vintage)
                for sr in report.recency.sources
            )
            if not found_old_period:
                passed = False
                reasons.append(
                    "Không tìm thấy nguồn nào đăng chưa quá 18 tháng nhưng ở trạng thái CŨ vì kỳ số liệu trích dẫn"
                )

    if assertions.get("no_cao_on_old_only_insights"):
        if report.recency is not None:
            ir_map = {ir.insight_id: ir for ir in report.recency.insights}
            violating = [
                ins.id
                for ins in report.insights
                if ins.confidence == "CAO"
                and ir_map.get(ins.id) is not None
                and ir_map[ins.id].status == "KHÔNG CÓ BẰNG CHỨNG MỚI"
            ]
            if violating:
                passed = False
                reasons.append(
                    f"Nhận định KHÔNG CÓ BẰNG CHỨNG MỚI nhưng đạt mức CAO: {violating}"
                )

    baseline_rel = assertions.get("must_match_m2_baseline")
    if baseline_rel:
        b_path = REPO_ROOT / str(baseline_rel)
        if not b_path.exists():
            passed = False
            reasons.append(f"Không tìm thấy file baseline: {baseline_rel}")
        else:
            b_rep = Report.model_validate_json(b_path.read_text(encoding="utf-8"))
            b_conf = [(i.id, i.confidence) for i in b_rep.insights]
            m_conf = [(i.id, i.confidence) for i in report.insights]
            if b_conf != m_conf:
                passed = False
                reasons.append(f"Lệch (id, confidence) so với baseline M2: {m_conf} != {b_conf}")
            if (
                report.quality.verified_quotes_count != b_rep.quality.verified_quotes_count
                or report.quality.verified_quote_rate != b_rep.quality.verified_quote_rate
                or report.quality.high_confidence_from_tier_c_only_count
                != b_rep.quality.high_confidence_from_tier_c_only_count
            ):
                passed = False
                reasons.append("Chỉ số tự kiểm lệch so với baseline M2")
            if _strip_recency_short_answer(report.short_answer) != _strip_recency_short_answer(
                b_rep.short_answer
            ):
                passed = False
                reasons.append("short_answer (sau khi gỡ marker) lệch so với baseline M2")

    if assertions.get("must_report_refresh_outcome"):
        if report.refresh is None:
            passed = False
            reasons.append("Thiếu report.refresh")
        else:
            rf = report.refresh
            valid_statuses = (
                "ĐÃ LÀM MỚI",
                "KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN",
                "KHÔNG CẦN LÀM MỚI",
                "LỖI",
            )
            if rf.status not in valid_statuses:
                passed = False
                reasons.append(f"Trạng thái refresh không hợp lệ: {rf.status}")
            if rf.status in ("ĐÃ LÀM MỚI", "KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN") and rf.target_source_ids:
                ev_to_src = {e.id: e.source_id for e in report.evidences}
                compared_src_ids = {
                    ev_to_src.get(c.old_evidence_id) for c in rf.comparisons
                }
                for tsid in rf.target_source_ids:
                    if tsid not in compared_src_ids and not rf.rejected_new_sources:
                        passed = False
                        reasons.append(
                            f"Nguồn mục tiêu {tsid} không có mục đối chiếu hoặc lý do loại nguồn"
                        )
            # Check confidence_changes match actual post-refresh confidence vs baseline at same reference_date
            ins_conf_map = {i.id: i.confidence for i in report.insights}
            for cc in rf.confidence_changes:
                actual_after = ins_conf_map.get(cc.insight_id)
                if actual_after != cc.after:
                    passed = False
                    reasons.append(
                        f"confidence_changes[{cc.insight_id}].after={cc.after} không khớp mức thật={actual_after}"
                    )

    if passed:
        reasons.append("Đạt toàn bộ tiêu chí kiểm tự động")
    return passed, reasons


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run Gamota evaluation suite (TC1-TC10)")
    parser.add_argument(
        "--case",
        type=str,
        default="",
        help="Run a specific test case ID (e.g., TC1, TC7). If omitted, runs all cases.",
    )
    parser.add_argument(
        "--reference-date",
        type=str,
        default="",
        help="Override reference date YYYY-MM-DD for all executed cases.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable disk cache for fresh execution",
    )
    args = parser.parse_args()

    cli_ref_date = _parse_date_arg(args.reference_date) if args.reference_date else None

    data = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8")) or {}
    all_cases: list[dict[str, Any]] = data.get("cases", [])
    if args.case:
        target = args.case.strip().upper()
        all_cases = [c for c in all_cases if str(c.get("id", "")).upper() == target]
        if not all_cases:
            print(
                f"Không tìm thấy test case có ID '{args.case}' trong {CASES_PATH}.",
                file=sys.stderr,
            )
            return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, Any]] = []

    for c in all_cases:
        cid = c["id"]
        question = c["question"]
        case_ref_date = cli_ref_date or _parse_date_arg(c.get("reference_date")) or date.today()
        do_refresh = bool(c.get("refresh_old", False))
        refresh_ref_date = (
            cli_ref_date
            or _parse_date_arg(c.get("refresh_reference_date", "today"))
            or date.today()
        )

        print(f"\n=== ĐANG CHẠY {cid}: {c['name']} ===")
        print(
            f"Câu hỏi: {question} | ref={case_ref_date.isoformat()}"
            + (f" | refresh_old=True (refresh_ref={refresh_ref_date.isoformat()})" if do_refresh else "")
        )
        t0 = time.perf_counter()
        try:
            if do_refresh:
                before_report = run(
                    question=question,
                    reference_date=case_ref_date,
                    refresh_old=False,
                    use_cache=not args.no_cache,
                )
                before_json = RESULTS_DIR / f"{cid}_before_refresh.json"
                before_md = RESULTS_DIR / f"{cid}_before_refresh.md"
                before_json.write_text(
                    json.dumps(before_report.model_dump(), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                before_md.write_text(
                    render_report_markdown(before_report), encoding="utf-8"
                )
                report = refresh_old_sources(
                    before_report,
                    reference_date=refresh_ref_date,
                    use_cache=not args.no_cache,
                )
            else:
                report = run(
                    question=question,
                    reference_date=case_ref_date,
                    refresh_old=False,
                    use_cache=not args.no_cache,
                )

            elapsed = round(time.perf_counter() - t0, 2)
            passed, notes = evaluate_assertions(report, c.get("assertions", {}) or {})

            json_path = RESULTS_DIR / f"{cid}.json"
            md_path = RESULTS_DIR / f"{cid}.md"
            json_path.write_text(
                json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            md_path.write_text(render_report_markdown(report), encoding="utf-8")

            q = report.quality
            imp_lvl = report.recency.impact_level if report.recency else "N/A"
            kos_ids = (
                [k.source_id for k in report.recency.key_old_sources]
                if report.recency
                else []
            )
            rf_stat = report.refresh.status if report.refresh else "—"

            print(
                f"[{cid}] Thời gian: {elapsed}s | Nguồn giữ lại: {len(report.sources)} | "
                f"Trích dẫn xác minh: {q.verified_quotes_count}/{q.total_quotes_extracted} ({q.verified_quote_rate}%) | "
                f"Nhận định: {q.total_insights_count} | CAO từ nguồn C: {q.high_confidence_from_tier_c_only_count}"
            )
            print(
                f"[{cid}] Độ mới (A2): mức ảnh hưởng={imp_lvl} | Nguồn then chốt cũ={kos_ids} | Trạng thái làm mới={rf_stat}"
            )
            print(
                f"[{cid}] Kết quả: {'ĐẠT' if passed else 'CHƯA ĐẠT'} — {'; '.join(notes)}"
            )

            summary_rows.append(
                {
                    "id": cid,
                    "name": c["name"],
                    "expected_group": c.get("expected_group", ""),
                    "question": question,
                    "reference_date": (
                        refresh_ref_date.isoformat() if do_refresh else case_ref_date.isoformat()
                    ),
                    "duration_seconds": elapsed,
                    "sources_count": len(report.sources),
                    "verified_quotes_count": q.verified_quotes_count,
                    "total_quotes_extracted": q.total_quotes_extracted,
                    "verified_quote_rate": q.verified_quote_rate,
                    "insights_count": q.total_insights_count,
                    "high_conf_from_tier_c": q.high_confidence_from_tier_c_only_count,
                    "impact_level": imp_lvl,
                    "key_old_sources": kos_ids,
                    "refresh_status": rf_stat,
                    "passed": passed,
                    "notes": notes,
                }
            )
        except Exception as exc:
            elapsed = round(time.perf_counter() - t0, 2)
            err_msg = f"Lỗi khi chạy case {cid}: {type(exc).__name__}: {exc}"
            print(f"[{cid}] LỖI: {err_msg}", file=sys.stderr)
            summary_rows.append(
                {
                    "id": cid,
                    "name": c["name"],
                    "expected_group": c.get("expected_group", ""),
                    "question": question,
                    "reference_date": case_ref_date.isoformat(),
                    "duration_seconds": elapsed,
                    "sources_count": 0,
                    "verified_quotes_count": 0,
                    "total_quotes_extracted": 0,
                    "verified_quote_rate": 0.0,
                    "insights_count": 0,
                    "high_conf_from_tier_c": 0,
                    "impact_level": "LỖI",
                    "key_old_sources": [],
                    "refresh_status": "LỖI",
                    "passed": False,
                    "notes": [err_msg],
                }
            )

    if len(summary_rows) > 1:
        summary_path = RESULTS_DIR / "summary.json"
        summary_path.write_text(
            json.dumps(summary_rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
