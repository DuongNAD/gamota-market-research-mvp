"""End-to-end unit test of the 6-step pipeline with deterministic mock LLM & retrieve."""

from __future__ import annotations

from datetime import date
from typing import Type
from unittest.mock import patch

from pydantic import BaseModel

from research.llm import LLMClient
from research.pipeline import render_report_markdown, run
from research.schemas import (
    BatchExtractLLMOutput,
    DraftInsightLLM,
    PlanLLMOutput,
    PremiseCheck,
    RawExtractedClaim,
    Source,
    SynthesisLLMOutput,
)


class DummyLLMClient(LLMClient):
    """Deterministic mock LLMClient for testing full 6-step pipeline mechanics."""

    def __init__(self) -> None:
        super().__init__(use_cache=False)

    def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        step_name: str = "llm_step",
    ):
        self.calls_count += 1
        if response_model is PlanLLMOutput:
            return PlanLLMOutput(
                question_type="option_selection",
                sub_questions=["Thể loại nào tăng trưởng nhanh nhất?"],
                decision_criteria=["Quy mô", "Tăng trưởng"],
                search_queries=["SEA mobile game genre revenue 2026"],
                implicit_premises=["Thị trường ĐNÁ có cơ hội cho thể loại mới"],
                keywords=["RPG", "revenue", "SEA"],
            )
        if response_model is BatchExtractLLMOutput:
            return BatchExtractLLMOutput(
                extracted_claims=[
                    RawExtractedClaim(
                        source_id="S1",
                        quote="Southeast Asia mobile game revenue reached $4.2 billion in 2025, driven primarily by RPG and strategy titles.",
                        claim="Doanh thu game mobile ĐNÁ đạt 4,2 tỷ USD năm 2025 nhờ RPG và chiến thuật.",
                    ),
                    RawExtractedClaim(
                        source_id="S2",
                        quote="Hybrid-casual games grew 28% year-over-year across Indonesia and the Philippines in 2025.",
                        claim="Game hybrid-casual tăng trưởng 28% YoY tại Indonesia và Philippines.",
                    ),
                    RawExtractedClaim(
                        source_id="S1",
                        quote="This quote is completely made up and does not exist in source S1 at all.",
                        claim="Nhận định bịa đặt cần bị code loại bỏ.",
                    ),
                ]
            )
        if response_model is SynthesisLLMOutput:
            return SynthesisLLMOutput(
                short_answer="RPG và Hybrid-casual là hai nhóm dẫn dắt tại Đông Nam Á.",
                recommendation="Nên ưu tiên thử nghiệm Hybrid-casual nếu ngân sách UA vừa phải.",
                insights=[
                    DraftInsightLLM(
                        statement="Doanh thu game mobile ĐNÁ đạt 4,2 tỷ USD, dẫn dắt bởi RPG và Hybrid-casual.",
                        type="fact",
                        evidence_ids=["E1", "E2"],
                    ),
                    DraftInsightLLM(
                        statement="Dự báo Hybrid-casual tiếp tục tăng trưởng trong 12 tháng tới.",
                        type="inference",
                        evidence_ids=["E1", "E2"],
                        assumptions=["Chi phí CPI không tăng đột biến"],
                        is_forecast=True,
                    ),
                ],
                premise_checks=[
                    PremiseCheck(
                        premise="Thị trường ĐNÁ có cơ hội cho thể loại mới",
                        status="XÁC NHẬN",
                        explanation="Dòng hybrid-casual tăng 28% YoY.",
                        evidence_ids=["E2"],
                    )
                ],
                gaps=["Thiếu dữ liệu chi phí CPI chi tiết theo từng quốc gia"],
                what_would_change=["CPI tăng gấp đôi trong quý tới"],
                next_checks=["Kiểm tra top chart AppMagic tại Thái Lan và Indonesia"],
            )
        raise ValueError(f"Unexpected model: {response_model}")


def test_full_pipeline_orchestration_and_markdown_render() -> None:
    fake_sources = [
        Source(
            id="S1",
            url="https://sensortower.com/sea-report-2026",
            domain="sensortower.com",
            title="Sensor Tower SEA 2026",
            published_date="2026-02-01",
            tier="A",
            tier_reason="Tier A data provider",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        ),
        Source(
            id="S2",
            url="https://pocketgamer.biz/sea-hybrid-casual",
            domain="pocketgamer.biz",
            title="PocketGamer Hybrid Casual",
            published_date="2026-03-01",
            tier="B",
            tier_reason="Tier B media",
            freshness="fresh",
            freshness_label="Mới (<=12 tháng)",
        ),
    ]
    fake_texts = {
        "S1": "Southeast Asia mobile game revenue reached $4.2 billion in 2025, driven primarily by RPG and strategy titles.",
        "S2": "Hybrid-casual games grew 28% year-over-year across Indonesia and the Philippines in 2025.",
    }
    fake_stats = {
        "search_provider": "mock",
        "raw_search_results_count": 5,
        "deduped_sources_count": 2,
        "kept_sources_count": 2,
    }

    with patch(
        "research.pipeline.retrieve_and_grade_sources",
        return_value=(fake_sources, fake_texts, fake_texts, [], fake_stats),
    ):
        report = run(
            question="Thể loại game mobile nào có tiềm năng tại Đông Nam Á trong 12 tháng tới?",
            use_cache=False,
            reference_date=date(2026, 10, 14),
            llm_client=DummyLLMClient(),
        )

    assert len(report.evidences) == 2
    assert report.quality.rejected_quotes_count == 1
    assert report.quality.verified_quote_rate == 66.7
    assert len(report.insights) == 2
    # First insight is fact with 2 domains (A + B, fresh) -> CAO
    assert report.insights[0].confidence == "CAO"
    # Second insight is forecast -> capped at TRUNG BÌNH
    assert report.insights[1].confidence == "TRUNG BÌNH"
    assert report.quality.high_confidence_from_tier_c_only_count == 0

    md = render_report_markdown(report)
    assert "## 1. Trả lời ngắn & Khuyến nghị ra quyết định" in md
    assert "## 2. Bảng nhận định có căn cứ" in md
    assert "#:~:text=" in md
    assert "## 6. Tự kiểm chất lượng" in md
