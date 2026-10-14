"""Unit tests for deterministic confidence scoring and quality metrics in research/score.py."""

from __future__ import annotations

from research.schemas import ConflictItem, Evidence, Insight, Report, Source
from research.score import (
    score_and_finalize_report,
    score_single_insight,
    strip_llm_urls,
)


def _make_sources() -> dict[str, Source]:
    return {
        "S1": Source(
            id="S1",
            url="https://sensortower.com/report-2026",
            domain="sensortower.com",
            title="Sensor Tower SEA 2026",
            published_date="2026-03-10",
            tier="A",
            tier_reason="Tier A data provider",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        ),
        "S2": Source(
            id="S2",
            url="https://pocketgamer.biz/news/sea-rpg",
            domain="pocketgamer.biz",
            title="PocketGamer SEA RPG",
            published_date="2026-01-20",
            tier="B",
            tier_reason="Tier B media",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        ),
        "S3": Source(
            id="S3",
            url="https://randomgameblog.net/post1",
            domain="randomgameblog.net",
            title="Blog 1",
            published_date="2026-02-01",
            tier="C",
            tier_reason="Tier C default",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        ),
        "S4": Source(
            id="S4",
            url="https://anotherseoblog.org/post2",
            domain="anotherseoblog.org",
            title="Blog 2",
            published_date="2026-02-15",
            tier="C",
            tier_reason="Tier C default",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        ),
        "S5": Source(
            id="S5",
            url="https://newzoo.com/old-report-2022",
            domain="newzoo.com",
            title="Newzoo 2022",
            published_date="2022-05-01",
            tier="A",
            tier_reason="Tier A data provider",
            freshness="stale",
            freshness_label="Cũ (>24 tháng hoặc không rõ ngày)",
        ),
        "S6": Source(
            id="S6",
            url="https://gamesindustry.biz/report-2025",
            domain="gamesindustry.biz",
            title="GI 2025",
            published_date="2025-02-01",
            tier="B",
            tier_reason="Tier B media",
            freshness="aging",
            freshness_label="Cũ dần (12-24 tháng)",
        ),
    }


def _make_evidences() -> dict[str, Evidence]:
    return {
        f"E{i}": Evidence(
            id=f"E{i}",
            source_id=f"S{i}",
            quote=f"Verbatim quote from source {i} with sufficient length.",
            claim=f"Claim {i}",
            verified=True,
            match_score=100.0,
        )
        for i in range(1, 7)
    }


def test_high_confidence_fact_with_two_domains_and_tier_a() -> None:
    sources = _make_sources()
    evidences = _make_evidences()
    ins = Insight(
        id="I1",
        statement="Doanh thu RPG tại Đông Nam Á dẫn đầu bảng xếp hạng năm qua.",
        type="fact",
        evidence_ids=["E1", "E2"],
    )
    scored = score_single_insight(ins, evidences, sources)
    assert scored.confidence == "CAO"


def test_inference_or_forecast_capped_at_trung_binh_even_with_tier_a_b() -> None:
    sources = _make_sources()
    evidences = _make_evidences()
    ins = Insight(
        id="I2",
        statement="Dự báo dòng game Hybrid-casual sẽ tăng trưởng mạnh trong 12 tháng tới.",
        type="inference",
        evidence_ids=["E1", "E2"],
        is_forecast=True,
    )
    scored = score_single_insight(ins, evidences, sources)
    assert scored.confidence == "TRUNG BÌNH"
    assert len(scored.assumptions) >= 1


def test_tier_c_sources_never_reach_high_confidence() -> None:
    sources = _make_sources()
    evidences = _make_evidences()
    # Two distinct Tier C domains agreeing -> TRUNG BÌNH (never CAO)
    ins_two_c = Insight(
        id="I3",
        statement="Hai nguồn blog đều ghi nhận lượng tải tăng.",
        type="fact",
        evidence_ids=["E3", "E4"],
    )
    scored_two_c = score_single_insight(ins_two_c, evidences, sources)
    assert scored_two_c.confidence == "TRUNG BÌNH"

    # Single Tier C source -> THẤP
    ins_one_c = Insight(
        id="I4",
        statement="Một nguồn blog đơn lẻ nhận định.",
        type="fact",
        evidence_ids=["E3"],
    )
    scored_one_c = score_single_insight(ins_one_c, evidences, sources)
    assert scored_one_c.confidence == "THẤP"


def test_single_tier_a_or_aging_data_gets_trung_binh() -> None:
    sources = _make_sources()
    evidences = _make_evidences()

    ins_single_a = Insight(
        id="I5",
        statement="Số liệu từ 1 nguồn hạng A duy nhất.",
        type="fact",
        evidence_ids=["E1"],
    )
    assert score_single_insight(ins_single_a, evidences, sources).confidence == "TRUNG BÌNH"

    ins_aging = Insight(
        id="I6",
        statement="Số liệu từ nguồn hạng B nhưng đã 18 tháng trước.",
        type="fact",
        evidence_ids=["E6"],
    )
    assert score_single_insight(ins_aging, evidences, sources).confidence == "TRUNG BÌNH"


def test_stale_or_conflicting_insight_gets_thap() -> None:
    sources = _make_sources()
    evidences = _make_evidences()

    ins_stale = Insight(
        id="I7",
        statement="Số liệu cũ từ năm 2022.",
        type="fact",
        evidence_ids=["E5"],
    )
    assert score_single_insight(ins_stale, evidences, sources).confidence == "THẤP"

    ins_conflict = Insight(
        id="I8",
        statement="Số liệu quy mô thị trường đang mâu thuẫn giữa các bên.",
        type="fact",
        evidence_ids=["E1", "E2"],
        has_conflict=True,
    )
    assert score_single_insight(ins_conflict, evidences, sources).confidence == "THẤP"


def test_finalize_report_moves_unverified_insights_to_gaps_and_strips_urls() -> None:
    sources = list(_make_sources().values())
    evidences = list(_make_evidences().values())

    raw_report = Report(
        question="Test question?",
        short_answer="Trả lời ngắn có link lậu https://fake-llm-url.com/abc cần xóa.",
        recommendation="Khuyến nghị hành động.",
        insights=[
            Insight(
                id="I1",
                statement="Nhận định có căn cứ hợp lệ từ www.unverified.com.",
                type="fact",
                evidence_ids=["E3", "E4"],
            ),
            Insight(
                id="I2",
                statement="Nhận định không có evidence hợp lệ phải chuyển sang khoảng trống.",
                type="fact",
                evidence_ids=["E999"],
            ),
        ],
        conflicts=[
            ConflictItem(
                topic="Quy mô",
                values=["$1B", "$2B"],
                explanation="Khác phạm vi tính toán",
                evidence_ids=["E1", "E2"],
            )
        ],
        sources=sources,
        evidences=evidences,
    )

    finalized = score_and_finalize_report(raw_report, total_quotes_extracted=8)
    assert len(finalized.insights) == 1
    assert finalized.insights[0].confidence == "TRUNG BÌNH"
    assert any("Nhận định không có evidence hợp lệ" in g for g in finalized.gaps)
    assert "https://fake-llm-url.com" not in finalized.short_answer
    assert "www.unverified.com" not in finalized.insights[0].statement
    assert finalized.quality.llm_invented_urls_removed_count == 2
    assert finalized.quality.high_confidence_from_tier_c_only_count == 0
    assert finalized.quality.insights_with_verified_evidence_rate == 100.0


def test_strip_llm_urls() -> None:
    cleaned, count = strip_llm_urls("Xem tại https://example.com/test và www.test.org ngay.")
    assert count == 2
    assert "https://" not in cleaned
    assert "www." not in cleaned


def test_stale_tier_a_plus_fresh_tier_c_or_missing_data_does_not_reach_cao() -> None:
    sources = _make_sources()
    evidences = _make_evidences()
    # S5 is Tier A stale; S3 is Tier C fresh -> only 1 non-stale domain (Tier C) -> THẤP (not CAO)
    ins_mixed = Insight(
        id="I9",
        statement="Số liệu kết hợp nguồn A cũ và nguồn C mới.",
        type="fact",
        evidence_ids=["E5", "E3"],
    )
    assert score_single_insight(ins_mixed, evidences, sources).confidence == "THẤP"

    # Negative statement saying data is unavailable -> capped at TRUNG BÌNH even with S1+S2
    ins_missing = Insight(
        id="I10",
        statement="Dữ liệu doanh thu tháng 9/2026 tại Thái Lan không có sẵn trong các nguồn mở.",
        type="fact",
        evidence_ids=["E1", "E2"],
    )
    assert score_single_insight(ins_missing, evidences, sources).confidence == "TRUNG BÌNH"

