"""Unit tests for Mission 3 targeted data refresh loop (BRIEF_M3 6.2)."""

from datetime import date

import research.refresh as refresh_mod
from research.recency import finalize_with_recency, load_recency_policy
from research.refresh import refresh_old_sources
from research.schemas import (
    BatchExtractLLMOutput,
    Evidence,
    Insight,
    RawExtractedClaim,
    RefreshComparisonItemLLM,
    RefreshComparisonLLMOutput,
    RefreshQueriesLLMOutput,
    Report,
    Source,
)


class FakeLLMClient:
    """Fake LLM client that returns scripted responses and counts calls."""

    def __init__(self, responses: list[object]):
        self.responses = list(responses)
        self.calls: list[dict] = []

    @property
    def calls_count(self) -> int:
        return len(self.calls)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model,
        step_name: str = "llm",
        temperature: float = 0.1,
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "model": response_model.__name__,
                "step_name": step_name,
            }
        )
        if not self.responses:
            raise AssertionError(f"Unexpected LLM call for {response_model.__name__} ({step_name})")
        return self.responses.pop(0)


def _make_base_report_with_old_key_source() -> Report:
    """Build a minimal report where I1 (THẤP) depends on old Grade-A source S1 (2024)."""
    policy = load_recency_policy()
    s1 = Source(
        id="S1",
        title="AppsFlyer Gaming Report 2024",
        url="https://www.appsflyer.com/resources/reports/gaming-app-marketing-2024/",
        domain="appsflyer.com",
        published_date="2024-06-15",
        date_method="year_in_text",
        date_precision="year",
        tier="A",
        tier_reason="Nguồn A nhưng năm 2024",
        freshness="stale",
        freshness_label="Cũ (>24 tháng hoặc không rõ ngày)",
    )
    e1 = Evidence(
        id="E1",
        source_id="S1",
        claim="Hybrid monetization tăng trưởng 35% tại Indonesia năm 2024.",
        quote="Hybrid monetization grew 35% in Indonesia in 2024.",
        verified=True,
        match_score=100.0,
    )
    i1 = Insight(
        id="I1",
        statement="Mô hình lai (IAA + IAP) tăng trưởng 35% tại Indonesia.",
        type="fact",
        evidence_ids=["E1"],
    )
    rpt = Report(
        question="Mô hình kiếm tiền nào đang hiệu quả tại Indonesia?",
        run_date="2026-10-15",
        reference_date="2026-10-15",
        short_answer="Mô hình lai đang phát triển tại Indonesia (E1, S1).",
        insights=[i1],
        evidences=[e1],
        sources=[s1],
        recommendation="Thử nghiệm hybrid monetization (I1).",
        trace={"version": 1, "run_timestamp": "2026-10-15T10:00:00"},
    )
    return finalize_with_recency(rpt, total_quotes_extracted=1, reference_date=date(2026, 10, 15))


def test_refresh_confirm_upgrades_confidence_and_keeps_ids(monkeypatch):
    """C4: Nhận định THẤP chỉ dựa nguồn A năm 2024 + bằng chứng mới hạng B 2026 XÁC NHẬN ⇒ TRUNG BÌNH; S#/E# nối tiếp; version=2; confidence_changes đúng."""
    rpt = _make_base_report_with_old_key_source()
    assert rpt.insights[0].confidence == "THẤP"
    assert rpt.trace.get("version") == 1

    raw_text = "In 2026, hybrid monetization continues to grow strongly by 38% across Indonesia casual games."

    def fake_retrieve(queries, keywords, reference_date=None, max_per_query=5, max_kept_sources=6, use_cache=True):
        s_new = Source(
            id="S1",  # retrieve_and_grade_sources numbers from S1 internally; refresh must renumber to S2
            title="SEA Gaming Market Update 2026",
            url="https://newzoo.com/resources/blog/sea-gaming-2026",
            domain="newzoo.com",
            published_date="2026-08-10",
            date_method="meta_tag",
            date_precision="day",
            tier="B",
            tier_reason="Nguồn B năm 2026",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        )
        return [s_new], {"S1": raw_text}, {"S1": raw_text}, [], {"raw_search_results_count": 1}

    monkeypatch.setattr(refresh_mod, "retrieve_and_grade_sources", fake_retrieve)

    fake_llm = FakeLLMClient(
        [
            RefreshQueriesLLMOutput(
                queries=[
                    "Indonesia casual game hybrid monetization 2025 2026",
                    "Indonesia IAA IAP mobile game revenue 2025 2026",
                ]
            ),
            BatchExtractLLMOutput(
                extracted_claims=[
                    RawExtractedClaim(
                        source_id="S2",
                        claim="Năm 2026, mô hình kiếm tiền lai tiếp tục tăng trưởng 38% ở game casual Indonesia.",
                        quote="In 2026, hybrid monetization continues to grow strongly by 38% across Indonesia casual games.",
                    )
                ]
            ),
            RefreshComparisonLLMOutput(
                items=[
                    RefreshComparisonItemLLM(
                        old_evidence_id="E1",
                        new_evidence_ids=["E2"],
                        status="XÁC NHẬN",
                        explanation="Bằng chứng E2 từ S2 (tháng 8/2026) xác nhận xu hướng tăng trưởng của hybrid monetization tại Indonesia so với 2024.",
                    )
                ]
            ),
        ]
    )

    refreshed = refresh_old_sources(rpt, llm=fake_llm, reference_date=date(2026, 10, 23))

    assert refreshed.trace.get("version") == 2
    assert refreshed.refresh is not None
    assert refreshed.refresh.status == "ĐÃ LÀM MỚI"
    # Check sequential S# and E# IDs
    assert [s.id for s in refreshed.sources] == ["S1", "S2"]
    assert [e.id for e in refreshed.evidences] == ["E1", "E2"]
    # Check I1 got E2 attached and upgraded from THẤP -> TRUNG BÌNH (1A old + 1B fresh => 2 independent sources, fresh B => TRUNG BÌNH)
    i1_after = next(i for i in refreshed.insights if i.id == "I1")
    assert "E2" in i1_after.evidence_ids
    assert i1_after.confidence == "TRUNG BÌNH"
    # Check confidence_changes
    assert len(refreshed.refresh.confidence_changes) == 1
    cc = refreshed.refresh.confidence_changes[0]
    assert cc.insight_id == "I1"
    assert cc.before == "THẤP"
    assert cc.after == "TRUNG BÌNH"


def test_refresh_update_adds_conflict_and_new_insight(monkeypatch):
    """C1: CẬP NHẬT ⇒ có ConflictItem, nhận định cũ THẤP, nhận định mới ở cuối."""
    rpt = _make_base_report_with_old_key_source()
    raw_text = "In 2026, hybrid monetization growth in Indonesia slowed to 12% as pure IAA regained share."

    def fake_retrieve(queries, keywords, reference_date=None, max_per_query=5, max_kept_sources=6, use_cache=True):
        s_new = Source(
            id="S1",
            title="Indonesia Mobile Game Report 2026",
            url="https://sensortower.com/blog/indonesia-mobile-games-2026",
            domain="sensortower.com",
            published_date="2026-07-20",
            date_method="meta_tag",
            date_precision="day",
            tier="A",
            tier_reason="Nguồn A năm 2026",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        )
        return [s_new], {"S1": raw_text}, {"S1": raw_text}, [], {"raw_search_results_count": 1}

    monkeypatch.setattr(refresh_mod, "retrieve_and_grade_sources", fake_retrieve)

    fake_llm = FakeLLMClient(
        [
            RefreshQueriesLLMOutput(
                queries=[
                    "Indonesia casual game hybrid monetization 2025 2026",
                    "Indonesia mobile game monetization 2025 2026",
                ]
            ),
            BatchExtractLLMOutput(
                extracted_claims=[
                    RawExtractedClaim(
                        source_id="S2",
                        claim="Năm 2026, tốc độ tăng trưởng hybrid monetization tại Indonesia giảm xuống 12%.",
                        quote="In 2026, hybrid monetization growth in Indonesia slowed to 12% as pure IAA regained share.",
                    )
                ]
            ),
            RefreshComparisonLLMOutput(
                items=[
                    RefreshComparisonItemLLM(
                        old_evidence_id="E1",
                        new_evidence_ids=["E2"],
                        status="CẬP NHẬT",
                        explanation="Số liệu năm 2026 (E2, S2) cập nhật tốc độ tăng trưởng giảm xuống 12% so với mức 35% năm 2024 (E1, S1).",
                    )
                ]
            ),
        ]
    )

    refreshed = refresh_old_sources(rpt, llm=fake_llm, reference_date=date(2026, 10, 23))

    assert refreshed.refresh is not None
    assert refreshed.refresh.status == "ĐÃ LÀM MỚI"
    assert len(refreshed.conflicts) >= 1
    assert any("E1" in c.evidence_ids and "E2" in c.evidence_ids for c in refreshed.conflicts)
    # Old insight remains THẤP, new insight I2 is added at the end
    assert refreshed.insights[0].id == "I1"
    assert refreshed.insights[0].confidence == "THẤP"
    assert refreshed.insights[-1].id == "I2"
    assert "E2" in refreshed.insights[-1].evidence_ids


def test_refresh_no_newer_source_reports_honestly(monkeypatch):
    """Edge case: Nguồn tìm được cũ hơn, không rõ ngày hoặc trùng URL ⇒ KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN, không gọi extract/compare, có gap mới."""
    rpt = _make_base_report_with_old_key_source()

    def fake_retrieve(queries, keywords, reference_date=None, max_per_query=5, max_kept_sources=6, use_cache=True):
        s_dup = Source(
            id="S1",
            title="AppsFlyer Gaming Report 2024 Dup",
            url="https://www.appsflyer.com/resources/reports/gaming-app-marketing-2024",  # trailing slash diff -> same canonical URL
            domain="appsflyer.com",
            published_date="2026-05-01",
            date_method="meta_tag",
            date_precision="day",
            tier="A",
            freshness="fresh",
        )
        s_unknown = Source(
            id="S2",
            title="Unknown Date Blog",
            url="https://example.com/blog-unknown-date",
            domain="example.com",
            published_date=None,
            date_method="unknown",
            date_precision="unknown",
            tier="B",
            freshness="stale",
        )
        s_older = Source(
            id="S3",
            title="Old 2023 Report",
            url="https://newzoo.com/2023-report",
            domain="newzoo.com",
            published_date="2023-11-10",
            date_method="meta_tag",
            date_precision="day",
            tier="B",
            freshness="stale",
        )
        return (
            [s_dup, s_unknown, s_older],
            {"S1": "dup", "S2": "unk", "S3": "old"},
            {"S1": "dup", "S2": "unk", "S3": "old"},
            [],
            {"raw_search_results_count": 3},
        )

    monkeypatch.setattr(refresh_mod, "retrieve_and_grade_sources", fake_retrieve)

    # Only 1 LLM call allowed (query generation); if extract or compare is called, FakeLLMClient will raise AssertionError
    fake_llm = FakeLLMClient(
        [
            RefreshQueriesLLMOutput(
                queries=[
                    "Indonesia casual game hybrid monetization 2025 2026",
                    "Indonesia mobile game monetization 2025 2026",
                ]
            )
        ]
    )

    gaps_before = len(rpt.gaps)
    refreshed = refresh_old_sources(rpt, llm=fake_llm, reference_date=date(2026, 10, 23))

    assert refreshed.refresh is not None
    assert refreshed.refresh.status == "KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN"
    assert len(fake_llm.calls) == 1
    assert len(refreshed.gaps) > gaps_before
    assert len(refreshed.refresh.rejected_new_sources) == 3


def test_refresh_rejects_invalid_ids_and_llm_urls(monkeypatch):
    """Edge case: Mã không tồn tại bị bỏ, URL trong giải thích bị lọc."""
    rpt = _make_base_report_with_old_key_source()
    raw_text = "In 2026, hybrid monetization continues to grow strongly by 38% across Indonesia casual games."

    def fake_retrieve(queries, keywords, reference_date=None, max_per_query=5, max_kept_sources=6, use_cache=True):
        s_new = Source(
            id="S1",
            title="SEA Gaming Market Update 2026",
            url="https://newzoo.com/resources/blog/sea-gaming-2026",
            domain="newzoo.com",
            published_date="2026-08-10",
            date_method="meta_tag",
            date_precision="day",
            tier="B",
            tier_reason="Nguồn B năm 2026",
            freshness="fresh",
        )
        return [s_new], {"S1": raw_text}, {"S1": raw_text}, [], {"raw_search_results_count": 1}

    monkeypatch.setattr(refresh_mod, "retrieve_and_grade_sources", fake_retrieve)

    fake_llm = FakeLLMClient(
        [
            RefreshQueriesLLMOutput(
                queries=[
                    "Indonesia casual game hybrid monetization 2025 2026",
                    "Indonesia mobile game monetization 2025 2026",
                ]
            ),
            BatchExtractLLMOutput(
                extracted_claims=[
                    RawExtractedClaim(
                        source_id="S2",
                        claim="Năm 2026, mô hình kiếm tiền lai tiếp tục tăng trưởng 38% ở game casual Indonesia.",
                        quote="In 2026, hybrid monetization continues to grow strongly by 38% across Indonesia casual games.",
                    )
                ]
            ),
            RefreshComparisonLLMOutput(
                items=[
                    # Invalid old_evidence_id E999 -> must be ignored
                    RefreshComparisonItemLLM(
                        old_evidence_id="E999",
                        new_evidence_ids=["E2"],
                        status="XÁC NHẬN",
                        explanation="Bịa mã E999 tại https://fake.example.com/bad",
                    ),
                    # Valid old_evidence_id E1, mixed valid/invalid new_evidence_ids ["E2", "E888"], and URL in explanation
                    RefreshComparisonItemLLM(
                        old_evidence_id="E1",
                        new_evidence_ids=["E2", "E888"],
                        status="XÁC NHẬN",
                        explanation="Theo https://newzoo.com/resources/blog/sea-gaming-2026 và www.fake.com dữ liệu E2 xác nhận E1.",
                    ),
                ]
            ),
        ]
    )

    refreshed = refresh_old_sources(rpt, llm=fake_llm, reference_date=date(2026, 10, 23))
    assert refreshed.refresh is not None
    assert len(refreshed.refresh.comparisons) == 1
    comp = refreshed.refresh.comparisons[0]
    assert comp.old_evidence_id == "E1"
    assert comp.new_evidence_ids == ["E2"]
    assert "http" not in comp.explanation
    assert "www." not in comp.explanation


def test_refresh_without_targets_makes_no_llm_call():
    """Edge case: KHÔNG CẦN LÀM MỚI, 0 lần gọi LLM."""
    policy = load_recency_policy()
    s1 = Source(
        id="S1",
        title="Fresh 2026 Report",
        url="https://sensortower.com/2026-fresh",
        domain="sensortower.com",
        published_date="2026-09-01",
        date_method="meta_tag",
        date_precision="day",
        tier="A",
        freshness="fresh",
    )
    e1 = Evidence(
        id="E1",
        source_id="S1",
        claim="Fresh data in September 2026.",
        quote="Fresh data in September 2026.",
        verified=True,
        match_score=100.0,
    )
    i1 = Insight(
        id="I1",
        statement="Fresh insight statement.",
        type="fact",
        evidence_ids=["E1"],
    )
    rpt = Report(
        question="Fresh question?",
        run_date="2026-10-15",
        reference_date="2026-10-15",
        short_answer="Fresh short answer (E1, S1).",
        insights=[i1],
        evidences=[e1],
        sources=[s1],
        recommendation="Keep going (I1).",
    )
    rpt = finalize_with_recency(rpt, total_quotes_extracted=1, reference_date=date(2026, 10, 15))

    fake_llm = FakeLLMClient([])
    refreshed = refresh_old_sources(rpt, llm=fake_llm, reference_date=date(2026, 10, 23))

    assert refreshed.refresh is not None
    assert refreshed.refresh.status == "KHÔNG CẦN LÀM MỚI"
    assert refreshed.refresh.llm_calls_count == 0
    assert len(fake_llm.calls) == 0
