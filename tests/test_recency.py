"""Unit tests for the Recency Impact Layer (Mission 3 · Change Request A2) per BRIEF_M3 section 6.2."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

from research.dates import compute_age_metrics, detect_data_period
from research.grade import grade_source
from research.recency import (
    RECENCY_SHORT_MARKER,
    apply_recency_layer,
    rescore_report_as_of,
)
from research.schemas import Evidence, Insight, Report, Source
from research.score import score_and_finalize_report

M2_RESULTS_DIR = Path(__file__).resolve().parent.parent / "eval" / "results" / "m2"


def _load_m2_report(tc_id: str) -> Report:
    path = M2_RESULTS_DIR / f"{tc_id}.json"
    return Report.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_cr_a2_tc2_real_report_flags_key_old_sources() -> None:
    """Change Request A2 oracle test on real Mission 2 TC2 report."""
    raw = _load_m2_report("TC2")
    updated = apply_recency_layer(raw, reference_date=date(2026, 10, 15))
    assert updated.recency is not None
    rec = updated.recency

    assert rec.impact_level == "ĐÁNG KỂ"
    assert RECENCY_SHORT_MARKER in updated.short_answer
    assert re.search(r"\bS\d+\b", updated.short_answer)

    src_map = {s.id: s for s in updated.sources}
    sr_map = {sr.source_id: sr for sr in rec.sources}
    kos_map = {k.source_id: k for k in rec.key_old_sources}

    for sid in ("S5", "S6"):
        assert src_map[sid].date_precision == "year"
        assert sr_map[sid].date_display == "2024 (chỉ biết năm)"
        assert sr_map[sid].status == "CŨ"
        assert sr_map[sid].is_key is True
        assert sid in kos_map

    s5_impacts = {imp.insight_id: imp for imp in kos_map["S5"].impacts}
    assert s5_impacts["I5"].if_source_removed == "MẤT CĂN CỨ"
    assert s5_impacts["I4"].if_source_fresh == "CAO"
    assert s5_impacts["I5"].if_source_fresh == "TRUNG BÌNH"

    s6_impacts = {imp.insight_id: imp for imp in kos_map["S6"].impacts}
    assert s6_impacts["I6"].if_source_removed == "MẤT CĂN CỨ"
    assert s6_impacts["I6"].if_source_fresh == "TRUNG BÌNH"

    s1_impacts = {imp.insight_id: imp for imp in kos_map["S1"].impacts}
    assert s1_impacts["I2"].if_source_removed == "MẤT CĂN CỨ"


def test_cr_a2_synthetic_key_source_older_than_18_months() -> None:
    """Synthetic report: 20-month-old Tier A source supporting 3/4 insights is flagged as key old source."""
    ref = date(2026, 10, 15)
    s1 = grade_source(
        Source(
            id="S1",
            url="https://sensortower.com/blog/2025/02/10/sea-report",
            domain="sensortower.com",
            title="SEA Report Feb 2025",
            published_date="2025-02-10",
            date_method="url_date",
        ),
        reference_date=ref,
    )
    s2 = grade_source(
        Source(
            id="S2",
            url="https://pocketgamer.biz/2026/08/01/sea-update",
            domain="pocketgamer.biz",
            title="SEA Update Aug 2026",
            published_date="2026-08-01",
            date_method="url_date",
        ),
        reference_date=ref,
    )
    evidences = [
        Evidence(id="E1", source_id="S1", quote="Revenue reached 100M USD in SEA region.", claim="Doanh thu 100M", verified=True, match_score=100.0),
        Evidence(id="E2", source_id="S1", quote="Downloads grew 15 percent across Indonesia.", claim="Lượt tải tăng 15%", verified=True, match_score=100.0),
        Evidence(id="E3", source_id="S1", quote="Hybrid casual monetization increased ARPU.", claim="Hybrid tăng ARPU", verified=True, match_score=100.0),
        Evidence(id="E4", source_id="S2", quote="New games launched in August 2026.", claim="Game mới ra mắt", verified=True, match_score=100.0),
    ]
    insights = [
        Insight(id="I1", statement="Doanh thu đạt 100M USD.", type="fact", evidence_ids=["E1"]),
        Insight(id="I2", statement="Lượt tải tại Indonesia tăng 15%.", type="fact", evidence_ids=["E2"]),
        Insight(id="I3", statement="Hybrid casual giúp tăng ARPU.", type="fact", evidence_ids=["E3", "E4"]),
        Insight(id="I4", statement="Nhiều game mới ra mắt tháng 8/2026.", type="fact", evidence_ids=["E4"]),
    ]
    rep = score_and_finalize_report(
        Report(
            question="Test synthetic question?",
            short_answer="Trả lời ngắn gốc.",
            recommendation="Khuyến nghị gốc.",
            sources=[s1, s2],
            evidences=evidences,
            insights=insights,
            trace={"current_date": ref.isoformat()},
        ),
        total_quotes_extracted=4,
    )
    res = apply_recency_layer(rep, reference_date=ref)
    assert res.recency is not None
    assert res.recency.impact_level == "ĐÁNG KỂ"
    assert res.recency.summary.startswith("Mức ảnh hưởng: ĐÁNG KỂ.")

    kos_ids = [k.source_id for k in res.recency.key_old_sources]
    assert "S1" in kos_ids
    kos_s1 = next(k for k in res.recency.key_old_sources if k.source_id == "S1")
    imp_map = {i.insight_id: i for i in kos_s1.impacts}
    assert imp_map["I1"].if_source_removed == "MẤT CĂN CỨ"
    assert imp_map["I2"].if_source_removed == "MẤT CĂN CỨ"


def test_recency_layer_is_idempotent_and_never_changes_confidence() -> None:
    """Applying recency layer twice yields 1 marker and never changes any Insight.confidence across TC1-TC6."""
    ref = date(2026, 10, 15)
    for tc_id in ("TC1", "TC2", "TC3", "TC4", "TC5", "TC6"):
        orig = _load_m2_report(tc_id)
        orig_confs = [(i.id, i.confidence) for i in orig.insights]

        once = apply_recency_layer(orig, reference_date=ref)
        twice = apply_recency_layer(once, reference_date=ref)

        assert [(i.id, i.confidence) for i in once.insights] == orig_confs
        assert [(i.id, i.confidence) for i in twice.insights] == orig_confs
        assert once.short_answer == twice.short_answer
        assert twice.short_answer.count(RECENCY_SHORT_MARKER) <= 1
        for i1, i2 in zip(once.insights, twice.insights):
            assert i1.confidence_reason == i2.confidence_reason


def test_edge_tc1_year_only_and_old_data_in_fresh_source() -> None:
    """Oracle TC1: S3 is KHÔNG CHẮC (year-only 2025); S2 is CŨ (Q1/2025 data); S6 is CŨ (2024 data in Aug 2026 article)."""
    raw = _load_m2_report("TC1")
    updated = apply_recency_layer(raw, reference_date=date(2026, 10, 15))
    assert updated.recency is not None
    sr_map = {sr.source_id: sr for sr in updated.recency.sources}

    assert sr_map["S3"].status == "KHÔNG CHẮC"
    assert "2025 (chỉ biết năm)" in sr_map["S3"].date_display

    assert sr_map["S2"].status == "CŨ"
    assert sr_map["S2"].data_vintage == "Q1/2025"

    assert sr_map["S6"].status == "CŨ"
    assert sr_map["S6"].date_display == "05/08/2026"
    assert any("2024" in r for r in sr_map["S6"].reasons)


def test_edge_date_conflict_icon_era_tc4() -> None:
    """TC4-S10 (icon-era.com) published_date 2025-03 conflicts with Q2 2026 data in quote."""
    raw = _load_m2_report("TC4")
    updated = apply_recency_layer(raw, reference_date=date(2026, 10, 15))
    assert updated.recency is not None
    sr_map = {sr.source_id: sr for sr in updated.recency.sources}

    s10 = sr_map["S10"]
    assert s10.date_conflict is True
    assert any("ngày đăng có thể sai" in r for r in s10.reasons)


def test_edge_unknown_date_key_source_is_uncertain() -> None:
    """A key source with unknown publication date and no quote period is marked KHÔNG CHẮC, never MỚI."""
    ref = date(2026, 10, 15)
    s1 = grade_source(
        Source(
            id="S1",
            url="https://sensortower.com/top-charts",
            domain="sensortower.com",
            title="Sensor Tower Charts",
            published_date=None,
        ),
        reference_date=ref,
    )
    ev = Evidence(
        id="E1",
        source_id="S1",
        quote="Mobile game spending remained strong across Southeast Asia markets.",
        claim="Chi tiêu game mobile duy trì mạnh ở ĐNÁ",
        verified=True,
        match_score=100.0,
    )
    ins = Insight(id="I1", statement="Chi tiêu game mobile ĐNÁ duy trì mạnh.", type="fact", evidence_ids=["E1"])
    rep = score_and_finalize_report(
        Report(
            question="Q?",
            short_answer="A.",
            recommendation="R.",
            sources=[s1],
            evidences=[ev],
            insights=[ins],
            trace={"current_date": ref.isoformat()},
        ),
        total_quotes_extracted=1,
    )
    res = apply_recency_layer(rep, reference_date=ref)
    assert res.recency is not None
    sr_s1 = res.recency.sources[0]
    assert sr_s1.status == "KHÔNG CHẮC"
    assert sr_s1.status != "MỚI"


def test_boundary_exactly_18_months_is_not_older() -> None:
    """Strict > 18 months boundary at ref 2026-10-23: 2025-04-23 is not older; 2025-04-22 is older; 2025-04 is possibly older."""
    ref = date(2026, 10, 23)

    _am, _amin, _amax, _disp, older_exact, possibly_exact = compute_age_metrics(
        "2025-04-23", "day", ref, alert_months=18
    )
    assert older_exact is False
    assert possibly_exact is False

    _am, _amin, _amax, _disp, older_prev, possibly_prev = compute_age_metrics(
        "2025-04-22", "day", ref, alert_months=18
    )
    assert older_prev is True
    assert possibly_prev is True

    _am, _amin, _amax, _disp, older_month, possibly_month = compute_age_metrics(
        "2025-04", "month", ref, alert_months=18
    )
    assert older_month is False
    assert possibly_month is True


def test_detect_data_period_patterns() -> None:
    """Test >= 11 period detection patterns and exclusion rules from BRIEF_M3 section 4.4."""
    ref = date(2026, 10, 15)

    assert detect_data_period("IAP revenue reached $625 million in Q1'25.", ref) == (
        "Q1/2025",
        date(2025, 3, 31),
    )
    assert detect_data_period(
        "In the first quarter of 2025, Southeast Asia ranked second.", ref
    ) == ("Q1/2025", date(2025, 3, 31))
    assert detect_data_period("Downloads grew strongly in H1 2024.", ref) == (
        "H1/2024",
        date(2024, 6, 30),
    )
    assert detect_data_period(
        "From January to August 2024, Indonesia led regional downloads.", ref
    ) == ("08/2024", date(2024, 8, 31))
    assert detect_data_period("Mobile games generated $5.8B in 2024.", ref) == (
        "2024",
        date(2024, 12, 31),
    )
    assert detect_data_period("Doanh thu tháng 9/2026 đạt mức cao nhất.", ref) == (
        "09/2026",
        date(2026, 9, 30),
    )
    # Forecast range ending > ref.year -> dropped completely
    assert detect_data_period("CAGR is projected at 8.5% for 2022–2027.", ref) == (
        "",
        None,
    )
    # Reliable day publication_bound filters out future period relative to publication date
    assert detect_data_period(
        "Tăng trưởng giai đoạn 2022 – 2025 dự kiến đạt 1 tỷ USD.",
        ref,
        publication_bound=date(2024, 5, 14),
    ) == ("", None)
    # Exclusion prefixes: since, by, future year
    assert detect_data_period("The studio has operated since 2020 in Hanoi.", ref) == (
        "",
        None,
    )
    assert detect_data_period("Market will double by 2030.", ref) == ("", None)
    assert detect_data_period("Projected revenue in 2028 will exceed $10B.", ref) == (
        "",
        None,
    )


def test_tc3_control_has_no_recency_alarm() -> None:
    """TC3 control case has impact_level == KHÔNG and no recency marker in short_answer."""
    raw = _load_m2_report("TC3")
    updated = apply_recency_layer(raw, reference_date=date(2026, 10, 15))
    assert updated.recency is not None
    assert updated.recency.impact_level == "KHÔNG"
    assert RECENCY_SHORT_MARKER not in updated.short_answer


def test_rescore_as_of_later_date_ages_sources() -> None:
    """Rescoring TC2 as of 2026-10-23 transitions S2 (2024-10) from aging to stale while keeping insight confidences unchanged."""
    raw = _load_m2_report("TC2")
    at_run = rescore_report_as_of(raw, as_of=date(2026, 10, 15))
    at_later = rescore_report_as_of(raw, as_of=date(2026, 10, 23))

    s2_run = next(s for s in at_run.sources if s.id == "S2")
    s2_later = next(s for s in at_later.sources if s.id == "S2")
    assert s2_run.freshness == "aging"
    assert s2_later.freshness == "stale"

    assert [(i.id, i.confidence) for i in at_run.insights] == [
        (i.id, i.confidence) for i in at_later.insights
    ]
