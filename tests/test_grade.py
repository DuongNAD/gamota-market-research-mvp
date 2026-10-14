"""Unit tests for source tier grading and recency calculation in research/grade.py."""

from __future__ import annotations

from datetime import date

from research.grade import compute_freshness, grade_source, grade_source_domain
from research.schemas import Source


def test_grade_source_domain_tiers() -> None:
    tier_a, reason_a, dom_a = grade_source_domain("https://www.sensortower.com/blog/sea-2025")
    assert tier_a == "A"
    assert dom_a == "sensortower.com"
    assert "Sensor Tower" in reason_a

    tier_gov, _, _ = grade_source_domain("https://mic.gov.vn/thong-ke-game")
    assert tier_gov == "A"

    tier_ir, _, _ = grade_source_domain("https://ir.krafton.com/earnings-2025")
    assert tier_ir == "A"

    tier_b, reason_b, dom_b = grade_source_domain("https://www.pocketgamer.biz/news/12345/")
    assert tier_b == "B"
    assert dom_b == "pocketgamer.biz"
    assert "PocketGamer" in reason_b

    tier_c, _, dom_c = grade_source_domain("https://my-unknown-gaming-forum.xyz/thread-1")
    assert tier_c == "C"
    assert dom_c == "my-unknown-gaming-forum.xyz"


def test_compute_freshness_buckets() -> None:
    ref = date(2026, 10, 14)

    code_fresh, _ = compute_freshness("2026-04-01", reference_date=ref)
    assert code_fresh == "fresh"

    code_aging, _ = compute_freshness("2025-05-01", reference_date=ref)
    assert code_aging == "aging"

    code_stale, _ = compute_freshness("2023-01-15", reference_date=ref)
    assert code_stale == "stale"

    code_none, _ = compute_freshness(None, reference_date=ref)
    assert code_none == "stale"


def test_grade_source_model_copy() -> None:
    src = Source(
        id="S1",
        url="https://newzoo.com/resources/blog/global-games-market",
        domain="",
        title="Newzoo Report",
        published_date="2026-02-15",
    )
    graded = grade_source(src, reference_date=date(2026, 10, 14))
    assert graded.tier == "A"
    assert graded.domain == "newzoo.com"
    assert graded.freshness == "fresh"
