"""Evaluation runner (`python -m eval.run_eval [--case TC3]`) for Gamota Market Research MVP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

import yaml

from research.pipeline import render_report_markdown, run
from research.schemas import Report

EVAL_DIR = Path(__file__).resolve().parent
CASES_PATH = EVAL_DIR / "cases.yaml"
RESULTS_DIR = EVAL_DIR / "results"


def evaluate_assertions(report: Report, assertions: dict[str, Any]) -> tuple[bool, list[str]]:
    """Evaluate machine-checkable expectations against a real Report run."""
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

        num_mentions = _re.findall(r"\b\d+(?:[.,]\d+)?\s*(?:triệu|tỷ|million|billion|M|B)\b", report.short_answer, _re.IGNORECASE)
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

    if passed:
        reasons.append("Đạt toàn bộ tiêu chí kiểm tự động")
    return passed, reasons


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run Gamota evaluation suite")
    parser.add_argument(
        "--case",
        type=str,
        default="",
        help="Run a specific test case ID (e.g., TC1, TC3). If omitted, runs all cases.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable disk cache for fresh execution",
    )
    args = parser.parse_args()

    data = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8")) or {}
    all_cases: list[dict[str, Any]] = data.get("cases", [])
    if args.case:
        target = args.case.strip().upper()
        all_cases = [c for c in all_cases if str(c.get("id", "")).upper() == target]
        if not all_cases:
            print(f"Không tìm thấy test case có ID '{args.case}' trong {CASES_PATH}.", file=sys.stderr)
            return 1

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, Any]] = []

    for c in all_cases:
        cid = c["id"]
        question = c["question"]
        print(f"\n=== ĐANG CHẠY {cid}: {c['name']} ===")
        print(f"Câu hỏi: {question}")
        t0 = time.perf_counter()
        report = run(question=question, use_cache=not args.no_cache)
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
        print(
            f"[{cid}] Thời gian: {elapsed}s | Nguồn giữ lại: {len(report.sources)} | "
            f"Trích dẫn xác minh: {q.verified_quotes_count}/{q.total_quotes_extracted} ({q.verified_quote_rate}%) | "
            f"Nhận định: {q.total_insights_count} | CAO từ nguồn C: {q.high_confidence_from_tier_c_only_count}"
        )
        print(f"[{cid}] Kết quả: {'ĐẠT' if passed else 'CHƯA ĐẠT'} — {'; '.join(notes)}")

        summary_rows.append(
            {
                "id": cid,
                "name": c["name"],
                "expected_group": c.get("expected_group", ""),
                "question": question,
                "duration_seconds": elapsed,
                "sources_count": len(report.sources),
                "verified_quotes_count": q.verified_quotes_count,
                "total_quotes_extracted": q.total_quotes_extracted,
                "verified_quote_rate": q.verified_quote_rate,
                "insights_count": q.total_insights_count,
                "high_conf_from_tier_c": q.high_confidence_from_tier_c_only_count,
                "passed": passed,
                "notes": notes,
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
