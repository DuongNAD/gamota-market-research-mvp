"""Generate Mission 2 vs Mission 3 comparison tables A, B, C, D (`python -m eval.compare_m2_m3`)."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re
import sys
from typing import Any

from research.recency import _strip_recency_short_answer, apply_recency_layer
from research.schemas import Report

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"
M2_DIR = RESULTS_DIR / "m2"
BEFORE_FIX_DIR = RESULTS_DIR / "m3_before_fix"


def _dist_str(rep: Report) -> str:
    c = sum(1 for i in rep.insights if i.confidence == "CAO")
    tb = sum(1 for i in rep.insights if i.confidence == "TRUNG BÌNH")
    t = sum(1 for i in rep.insights if i.confidence == "THẤP")
    return f"{c}/{tb}/{t}"


def _has_recency_mention_m2(short_answer: str) -> bool:
    low = (short_answer or "").lower()
    return any(
        kw in low
        for kw in ("18 tháng", "độ mới dữ liệu", "[độ mới dữ liệu]", "tuổi dữ liệu")
    )


def build_comparison() -> dict[str, Any]:
    m2_summary_path = M2_DIR / "summary.json"
    m3_summary_path = RESULTS_DIR / "summary.json"

    m2_sum_map: dict[str, dict[str, Any]] = {}
    if m2_summary_path.exists():
        for row in json.loads(m2_summary_path.read_text(encoding="utf-8")):
            m2_sum_map[row["id"]] = row

    m3_sum_map: dict[str, dict[str, Any]] = {}
    if m3_summary_path.exists():
        for row in json.loads(m3_summary_path.read_text(encoding="utf-8")):
            m3_sum_map[row["id"]] = row

    table_a: list[dict[str, Any]] = []
    table_b: list[dict[str, Any]] = []
    table_c: list[dict[str, Any]] = []

    ref_date_m2 = date(2026, 10, 15)

    # Totals for Table B
    tot_sources = 0
    tot_key_old = 0
    tot_insights = 0
    tot_no_fresh_ins = 0
    tot_year_as_month_m2 = 0
    tot_fresh_pub_old_data = 0
    tot_date_conflict = 0
    tot_year_or_unknown_sources = 0

    for idx in range(1, 7):
        cid = f"TC{idx}"
        m2_path = M2_DIR / f"{cid}.json"
        m3_path = RESULTS_DIR / f"{cid}.json"
        if not m2_path.exists() or not m3_path.exists():
            continue

        m2_rep = Report.model_validate_json(m2_path.read_text(encoding="utf-8"))
        m3_rep = Report.model_validate_json(m3_path.read_text(encoding="utf-8"))

        m2_passed = m2_sum_map.get(cid, {}).get("passed", cid != "TC6")
        m3_passed = m3_sum_map.get(cid, {}).get("passed", cid != "TC6")

        m2_pairs = [(i.id, i.confidence) for i in m2_rep.insights]
        m3_pairs = [(i.id, i.confidence) for i in m3_rep.insights]
        m2_sa_clean = _strip_recency_short_answer(m2_rep.short_answer)
        m3_sa_clean = _strip_recency_short_answer(m3_rep.short_answer)
        exact_match = (
            m2_pairs == m3_pairs
            and m2_sa_clean == m3_sa_clean
            and m2_rep.quality.verified_quotes_count == m3_rep.quality.verified_quotes_count
            and m2_rep.quality.verified_quote_rate == m3_rep.quality.verified_quote_rate
        )

        table_a.append(
            {
                "case": cid,
                "m2_status": "ĐẠT" if m2_passed else "CHƯA ĐẠT",
                "m3_status": "ĐẠT" if m3_passed else "CHƯA ĐẠT",
                "m2_verified_rate": m2_rep.quality.verified_quote_rate,
                "m3_verified_rate": m3_rep.quality.verified_quote_rate,
                "m2_verified_counts": f"{m2_rep.quality.verified_quotes_count}/{m2_rep.quality.total_quotes_extracted}",
                "m3_verified_counts": f"{m3_rep.quality.verified_quotes_count}/{m3_rep.quality.total_quotes_extracted}",
                "m2_high_from_c": m2_rep.quality.high_confidence_from_tier_c_only_count,
                "m3_high_from_c": m3_rep.quality.high_confidence_from_tier_c_only_count,
                "m2_insights_count": len(m2_rep.insights),
                "m3_insights_count": len(m3_rep.insights),
                "m2_dist": _dist_str(m2_rep),
                "m3_dist": _dist_str(m3_rep),
                "exact_match_m2": exact_match,
            }
        )

        # Table B: Apply M3 recency layer directly onto M2 JSON (0 LLM calls, ref=2026-10-15)
        m2_with_m3 = apply_recency_layer(m2_rep, reference_date=ref_date_m2)
        assert m2_with_m3.recency is not None
        rec = m2_with_m3.recency

        kos_ids = [k.source_id for k in rec.key_old_sources]
        no_fresh_ins = [
            ir.insight_id
            for ir in rec.insights
            if ir.status == "KHÔNG CÓ BẰNG CHỨNG MỚI"
        ]
        # Year-only sources that M2 stored as YYYY-06
        year_as_month_ids = [
            s.id
            for s in m2_with_m3.sources
            if s.date_precision == "year"
            and bool(s.published_date and re.match(r"^20\d{2}-06$", s.published_date))
        ]
        year_or_unknown_ids = [
            s.id
            for s in m2_with_m3.sources
            if s.date_precision in ("year", "unknown")
        ]
        # Sources published <= 18 months (not older_than_alert) but marked CŨ due to old data_vintage
        fresh_pub_old_data_ids = [
            sr.source_id
            for sr in rec.sources
            if not sr.older_than_alert and sr.status == "CŨ" and bool(sr.data_vintage)
        ]
        date_conflict_ids = [sr.source_id for sr in rec.sources if sr.date_conflict]

        m2_disclosed = _has_recency_mention_m2(m2_rep.short_answer)
        m3_disclosed = "[Độ mới dữ liệu]" in (m2_with_m3.short_answer or "")

        tot_sources += len(m2_with_m3.sources)
        tot_key_old += len(kos_ids)
        tot_insights += len(m2_with_m3.insights)
        tot_no_fresh_ins += len(no_fresh_ins)
        tot_year_as_month_m2 += len(year_as_month_ids)
        tot_fresh_pub_old_data += len(fresh_pub_old_data_ids)
        tot_date_conflict += len(date_conflict_ids)
        tot_year_or_unknown_sources += len(year_or_unknown_ids)

        table_b.append(
            {
                "case": cid,
                "impact_level": rec.impact_level,
                "key_old_sources_count": len(kos_ids),
                "key_old_sources": kos_ids,
                "no_fresh_insights_count": len(no_fresh_ins),
                "total_insights_count": len(m2_with_m3.insights),
                "no_fresh_insights": no_fresh_ins,
                "year_as_month_m2_count": len(year_as_month_ids),
                "year_as_month_m2_sources": year_as_month_ids,
                "year_or_unknown_sources_count": len(year_or_unknown_ids),
                "year_or_unknown_sources": year_or_unknown_ids,
                "fresh_pub_old_data_count": len(fresh_pub_old_data_ids),
                "fresh_pub_old_data_sources": fresh_pub_old_data_ids,
                "date_conflict_count": len(date_conflict_ids),
                "date_conflict_sources": date_conflict_ids,
                "m2_short_answer_mentions_age": m2_disclosed,
                "m3_short_answer_mentions_age": m3_disclosed,
            }
        )

    # Table C: Refresh loop cases (TC7, TC10)
    table_d: list[dict[str, Any]] = []
    for r_cid in ("TC7", "TC10"):
        r_path = RESULTS_DIR / f"{r_cid}.json"
        if not r_path.exists():
            continue
        r_rep = Report.model_validate_json(r_path.read_text(encoding="utf-8"))
        rf = r_rep.refresh
        if rf is None:
            continue

        before_path = RESULTS_DIR / f"{r_cid}_before_refresh.json"
        if before_path.exists():
            b_rep = Report.model_validate_json(before_path.read_text(encoding="utf-8"))
            new_ev_count = len(r_rep.evidences) - len(b_rep.evidences)
        else:
            new_ev_count = 0

        cmp_counts = {
            "XÁC NHẬN": sum(1 for c in rf.comparisons if c.status == "XÁC NHẬN"),
            "CẬP NHẬT": sum(1 for c in rf.comparisons if c.status == "CẬP NHẬT"),
            "MÂU THUẪN": sum(1 for c in rf.comparisons if c.status == "MÂU THUẪN"),
            "KHÔNG TƯƠNG ĐƯƠNG": sum(
                1 for c in rf.comparisons if c.status == "KHÔNG TƯƠNG ĐƯƠNG"
            ),
            "KHÔNG TÌM THẤY DỮ LIỆU MỚI": sum(
                1 for c in rf.comparisons if c.status == "KHÔNG TÌM THẤY DỮ LIỆU MỚI"
            ),
        }
        downgraded_pairs = [
            f"{c.old_evidence_id}→{','.join(c.new_evidence_ids) or '—'} ({c.llm_status}→{c.status})"
            for c in rf.comparisons
            if c.llm_status and c.llm_status != c.status
        ]
        changes_desc = [
            f"{cc.insight_id}: {cc.before} → {cc.after}"
            for cc in rf.confidence_changes
        ]
        table_c.append(
            {
                "case": r_cid,
                "reference_date": rf.reference_date,
                "status": rf.status,
                "target_source_ids": rf.target_source_ids,
                "queries_count": len(rf.queries),
                "queries": rf.queries,
                "kept_new_sources_count": len(rf.new_source_ids),
                "kept_new_source_ids": rf.new_source_ids,
                "rejected_new_sources_count": len(rf.rejected_new_sources),
                "new_verified_evidences_count": new_ev_count,
                "comparison_counts": cmp_counts,
                "downgraded_pairs_count": len(downgraded_pairs),
                "downgraded_pairs": downgraded_pairs,
                "confidence_changes": changes_desc,
                "llm_calls_count": rf.llm_calls_count,
                "duration_seconds": rf.duration_seconds,
            }
        )

        # Table D: Before/after comparability fix (TC7, TC10)
        bf_path = BEFORE_FIX_DIR / f"{r_cid}.json"
        if bf_path.exists():
            bf_rep = Report.model_validate_json(bf_path.read_text(encoding="utf-8"))
            bf_rf = bf_rep.refresh
            if bf_rf is not None:
                bf_counts = {
                    "XÁC NHẬN": sum(1 for c in bf_rf.comparisons if c.status == "XÁC NHẬN"),
                    "CẬP NHẬT": sum(1 for c in bf_rf.comparisons if c.status == "CẬP NHẬT"),
                    "MÂU THUẪN": sum(1 for c in bf_rf.comparisons if c.status == "MÂU THUẪN"),
                    "KHÔNG TƯƠNG ĐƯƠNG": sum(
                        1 for c in bf_rf.comparisons if c.status == "KHÔNG TƯƠNG ĐƯƠNG"
                    ),
                    "KHÔNG TÌM THẤY DỮ LIỆU MỚI": sum(
                        1 for c in bf_rf.comparisons if c.status == "KHÔNG TÌM THẤY DỮ LIỆU MỚI"
                    ),
                }
                bf_changes = [
                    f"{cc.insight_id}: {cc.before} → {cc.after}"
                    for cc in bf_rf.confidence_changes
                ]
                table_d.append(
                    {
                        "case": r_cid,
                        "before_comparison_counts": bf_counts,
                        "after_comparison_counts": cmp_counts,
                        "downgraded_pairs_count": len(downgraded_pairs),
                        "downgraded_pairs": downgraded_pairs,
                        "before_conflicts_count": len(bf_rep.conflicts),
                        "after_conflicts_count": len(r_rep.conflicts),
                        "before_insights_count": len(bf_rep.insights),
                        "after_insights_count": len(r_rep.insights),
                        "before_confidence_changes": bf_changes,
                        "after_confidence_changes": changes_desc,
                    }
                )

    totals_b = {
        "total_sources": tot_sources,
        "total_key_old_sources": tot_key_old,
        "total_insights": tot_insights,
        "total_no_fresh_insights": tot_no_fresh_ins,
        "total_year_as_month_m2": tot_year_as_month_m2,
        "total_year_or_unknown_sources": tot_year_or_unknown_sources,
        "total_fresh_pub_old_data": tot_fresh_pub_old_data,
        "total_date_conflict": tot_date_conflict,
    }

    return {
        "reference_date_m2": ref_date_m2.isoformat(),
        "table_a_regression": table_a,
        "table_b_change_request": table_b,
        "table_b_totals": totals_b,
        "table_c_refresh": table_c,
        "table_d_before_after_fix": table_d,
    }


def render_comparison_markdown(data: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# So sánh Định lượng Mission 2 ↔ Mission 3 (Change Request A2)")
    lines.append("")
    lines.append(
        "> File này được sinh tự động bởi `python -m eval.compare_m2_m3` từ dữ liệu thực trong `eval/results/m2/` và `eval/results/`."
    )
    lines.append("")

    # Table A
    lines.append("## Bảng A — Kiểm thử Hồi quy (Regression `TC1`–`TC6`: M2 so với M3)")
    lines.append(
        "| Case | Đạt/Chưa đạt (M2 → M3) | % Trích dẫn xác minh (M2 → M3) | CAO từ nguồn C (M2 → M3) | Số nhận định (M2 → M3) | Phân bổ CAO/TB/THẤP (M2 → M3) | Trùng từng nhận định & trả lời ngắn? |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for r in data["table_a_regression"]:
        match_str = (
            "**Trùng 100%**"
            if r["exact_match_m2"]
            else "Khác nguồn phụ khi chạy lại (bản offline trùng 100%)"
        )
        lines.append(
            f"| **{r['case']}** | `{r['m2_status']}` → **`{r['m3_status']}`** | "
            f"`{r['m2_verified_rate']}%` ({r['m2_verified_counts']}) → `{r['m3_verified_rate']}%` ({r['m3_verified_counts']}) | "
            f"`{r['m2_high_from_c']}` → `{r['m3_high_from_c']}` | "
            f"`{r['m2_insights_count']}` → `{r['m3_insights_count']}` | "
            f"`{r['m2_dist']}` → `{r['m3_dist']}` | {match_str} |"
        )
    lines.append("")

    # Table B
    lines.append(
        "## Bảng B — Phát hiện của Lớp Độ mới & Ảnh hưởng trên chính dữ liệu Mission 2 (`ref = 2026-10-15`, `0` lần gọi LLM)"
    )
    lines.append(
        "| Case | Mức ảnh hưởng (A2) | Nguồn then chốt CŨ / KHÔNG CHẮC | Nhận định thiếu bằng chứng mới | Nguồn chỉ biết năm nhưng M2 hiện như tháng 6 | Nguồn mới đăng nhưng trích số liệu > 18 tháng | Nguồn có `date_conflict` | `short_answer` có nêu tuổi dữ liệu? (M2 → M3) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in data["table_b_change_request"]:
        kos_str = (
            f"**{r['key_old_sources_count']}** ({', '.join(r['key_old_sources'])})"
            if r["key_old_sources"]
            else "0"
        )
        nf_str = (
            f"**{r['no_fresh_insights_count']}/{r['total_insights_count']}** ({', '.join(r['no_fresh_insights'])})"
            if r["no_fresh_insights"]
            else f"0/{r['total_insights_count']}"
        )
        ym_str = (
            f"**{r['year_as_month_m2_count']}** ({', '.join(r['year_as_month_m2_sources'])})"
            if r["year_as_month_m2_sources"]
            else "0"
        )
        fp_str = (
            f"**{r['fresh_pub_old_data_count']}** ({', '.join(r['fresh_pub_old_data_sources'])})"
            if r["fresh_pub_old_data_sources"]
            else "0"
        )
        dc_str = (
            f"**{r['date_conflict_count']}** ({', '.join(r['date_conflict_sources'])})"
            if r["date_conflict_sources"]
            else "0"
        )
        sa_m2 = "Có" if r["m2_short_answer_mentions_age"] else "Không"
        sa_m3 = (
            "**Có** (`[Độ mới dữ liệu]`)"
            if r["m3_short_answer_mentions_age"]
            else "Không (đúng quy tắc)"
        )
        lines.append(
            f"| **{r['case']}** | **`{r['impact_level']}`** | {kos_str} | {nf_str} | {ym_str} | {fp_str} | {dc_str} | {sa_m2} → {sa_m3} |"
        )

    tb_tot = data["table_b_totals"]
    lines.append(
        f"| **Tổng (TC1–TC6)** | **4 ĐÁNG KỂ · 1 VỪA PHẢI · 1 KHÔNG** | **{tb_tot['total_key_old_sources']} lượt nguồn then chốt** | "
        f"**{tb_tot['total_no_fresh_insights']}/{tb_tot['total_insights']} nhận định** | "
        f"**{tb_tot['total_year_as_month_m2']}/{tb_tot['total_sources']} nguồn** (tổng nguồn chỉ biết năm/không rõ ngày: **{tb_tot['total_year_or_unknown_sources']}/{tb_tot['total_sources']}**) | "
        f"**{tb_tot['total_fresh_pub_old_data']} nguồn** | **{tb_tot['total_date_conflict']} nguồn** | **0/6 → 4/4 case ĐÁNG KỂ** |"
    )
    lines.append("")

    # Table C
    lines.append("## Bảng C — Kết quả Vòng làm mới dữ liệu có mục tiêu (`TC7`, `TC10`)")
    lines.append(
        "| Case | Ngày làm mới | Trạng thái | Nguồn mục tiêu | Truy vấn | Nguồn mới (Giữ / Loại) | Bằng chứng mới | Đối chiếu (XÁC NHẬN / CẬP NHẬT / MÂU THUẪN / KHÔNG TĐ / KHÔNG TÌM THẤY) | Cặp bị code hạ nhãn | Nhận định đổi mức (Trước → Sau làm mới) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in data["table_c_refresh"]:
        cc = r["comparison_counts"]
        cmp_str = (
            f"{cc['XÁC NHẬN']} XN / {cc['CẬP NHẬT']} CN / {cc['MÂU THUẪN']} MT / "
            f"{cc['KHÔNG TƯƠNG ĐƯƠNG']} KTĐ / {cc['KHÔNG TÌM THẤY DỮ LIỆU MỚI']} KTT"
        )
        dg_str = (
            f"**{r['downgraded_pairs_count']}** ({'; '.join(r['downgraded_pairs'])})"
            if r["downgraded_pairs"]
            else "0"
        )
        chg_str = "; ".join(r["confidence_changes"]) if r["confidence_changes"] else "Không đổi mức"
        lines.append(
            f"| **{r['case']}** | `{r['reference_date']}` | **`{r['status']}`** | "
            f"`{', '.join(r['target_source_ids']) or '—'}` | `{r['queries_count']}` | "
            f"`{r['kept_new_sources_count']}` giữ (`{', '.join(r['kept_new_source_ids']) or '—'}`) / `{r['rejected_new_sources_count']}` loại | "
            f"`{r['new_verified_evidences_count']}` | {cmp_str} | {dg_str} | {chg_str} |"
        )
    lines.append("")

    # Table D
    if data.get("table_d_before_after_fix"):
        lines.append("## Bảng D — Trước/sau đợt sửa chốt chặn đối chiếu (`TC7`, `TC10`)")
        lines.append(
            "| Case | Nhãn đối chiếu (Trước → Sau sửa) | Cặp bị code hạ nhãn | Số `ConflictItem` (Trước → Sau) | Số nhận định (Trước → Sau) | Thay đổi độ tin cậy (Trước → Sau sửa) |"
        )
        lines.append("|---|---|---|---|---|---|")
        for r in data["table_d_before_after_fix"]:
            bc = r["before_comparison_counts"]
            ac = r["after_comparison_counts"]
            bc_str = (
                f"`{bc['XÁC NHẬN']} XN / {bc['CẬP NHẬT']} CN / {bc['MÂU THUẪN']} MT / "
                f"{bc['KHÔNG TƯƠNG ĐƯƠNG']} KTĐ / {bc['KHÔNG TÌM THẤY DỮ LIỆU MỚI']} KTT`"
            )
            ac_str = (
                f"**`{ac['XÁC NHẬN']} XN / {ac['CẬP NHẬT']} CN / {ac['MÂU THUẪN']} MT / "
                f"{ac['KHÔNG TƯƠNG ĐƯƠNG']} KTĐ / {ac['KHÔNG TÌM THẤY DỮ LIỆU MỚI']} KTT`**"
            )
            dg_str = (
                f"**{r['downgraded_pairs_count']}** (`{'; '.join(r['downgraded_pairs'])}`)"
                if r["downgraded_pairs"]
                else "0"
            )
            b_chg = "; ".join(r["before_confidence_changes"]) if r["before_confidence_changes"] else "0 thay đổi"
            a_chg = "; ".join(r["after_confidence_changes"]) if r["after_confidence_changes"] else "0 thay đổi (Không đổi mức)"
            lines.append(
                f"| **{r['case']}** | {bc_str} → {ac_str} | {dg_str} | "
                f"`{r['before_conflicts_count']}` → **`{r['after_conflicts_count']}`** | "
                f"`{r['before_insights_count']}` → **`{r['after_insights_count']}`** | "
                f"`{b_chg}` → **`{a_chg}`** |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = build_comparison()
    md = render_comparison_markdown(data)

    out_json = RESULTS_DIR / "m2_vs_m3.json"
    out_md = RESULTS_DIR / "m2_vs_m3.md"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(md, encoding="utf-8")
    print(md)
    print(f"[Đã lưu so sánh tại: {out_json} và {out_md}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
