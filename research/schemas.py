"""Pydantic schemas for the Gamota Game Market Research pipeline."""

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


SourceTier = Literal["A", "B", "C"]
FreshnessCode = Literal["fresh", "aging", "stale"]
InsightType = Literal["fact", "inference"]
ConfidenceLevel = Literal["CAO", "TRUNG BÌNH", "THẤP"]
PremiseStatus = Literal["XÁC NHẬN", "BÁC BỎ", "MỘT PHẦN", "CHƯA ĐỦ BẰNG CHỨNG"]
DatePrecision = Literal["day", "month", "quarter", "year", "unknown"]
RecencyStatus = Literal["MỚI", "KHÔNG CHẮC", "CŨ"]
InsightRecencyStatus = Literal["MỚI", "MỘT PHẦN CŨ", "KHÔNG CÓ BẰNG CHỨNG MỚI"]
ImpactLevel = Literal["KHÔNG", "NHỎ", "VỪA PHẢI", "ĐÁNG KỂ"]
CounterfactualLevel = Literal["CAO", "TRUNG BÌNH", "THẤP", "MẤT CĂN CỨ"]
RefreshStatus = Literal[
    "ĐÃ LÀM MỚI", "KHÔNG TÌM THẤY DỮ LIỆU MỚI HƠN", "KHÔNG CẦN LÀM MỚI", "LỖI"
]
ComparisonStatus = Literal[
    "XÁC NHẬN",
    "CẬP NHẬT",
    "MÂU THUẪN",
    "KHÔNG TƯƠNG ĐƯƠNG",
    "KHÔNG TÌM THẤY DỮ LIỆU MỚI",
]


class Source(BaseModel):
    """Information source retrieved from the web and graded by code rules."""

    id: str = Field(..., description="Unique source identifier, e.g., S1, S2")
    url: str = Field(..., description="Canonical URL of the source")
    domain: str = Field(..., description="Normalized domain name, e.g., sensortower.com")
    title: str = Field(..., description="Page or article title")
    published_date: Optional[str] = Field(
        default=None, description="ISO date YYYY-MM-DD or YYYY-MM if detected"
    )
    tier: SourceTier = Field(default="C", description="Reliability tier A, B, or C")
    tier_reason: str = Field(
        default="", description="Rule-based explanation for the assigned tier"
    )
    freshness: FreshnessCode = Field(
        default="stale",
        description="Recency bucket: fresh (<=12m), aging (12-24m), stale (>24m or unknown)",
    )
    freshness_label: str = Field(
        default="Cũ (>24 tháng hoặc không rõ ngày)",
        description="Vietnamese human-readable recency label",
    )
    date_method: str = ""
    date_precision: DatePrecision = "unknown"
    age_months: Optional[float] = None
    age_months_min: Optional[float] = None
    age_months_max: Optional[float] = None


class Evidence(BaseModel):
    """Extracted claim with a verbatim quote verified against the raw source text."""

    id: str = Field(..., description="Unique evidence identifier, e.g., E1, E2")
    source_id: str = Field(..., description="Reference to Source.id")
    quote: str = Field(
        ...,
        description="Verbatim quote from source (<= 40 words, original language, untranslated)",
    )
    claim: str = Field(
        ..., description="Vietnamese summary of the specific claim supported by the quote"
    )
    verified: bool = Field(
        default=False,
        description="True if verified by code against source text (rapidfuzz >= 90)",
    )
    match_score: float = Field(
        default=0.0, description="Fuzzy partial match score (0-100) computed by code"
    )
    highlight_url: str = Field(
        default="",
        description="Code-generated URL with #:~:text=... fragment for browser highlighting",
    )
    data_period: str = ""
    data_period_end: Optional[str] = None


class Insight(BaseModel):
    """Market research insight grounded in verified evidence IDs and scored by code."""

    id: str = Field(..., description="Unique insight identifier, e.g., I1, I2")
    statement: str = Field(
        ..., description="Vietnamese insight statement (no LLM-invented URLs allowed)"
    )
    type: InsightType = Field(
        ..., description="'fact' for direct empirical findings, 'inference' for synthesis/forecasts"
    )
    evidence_ids: list[str] = Field(
        default_factory=list, description="List of verified Evidence.id supporting this insight"
    )
    confidence: ConfidenceLevel = Field(
        default="THẤP", description="Code-computed confidence level: CAO, TRUNG BÌNH, or THẤP"
    )
    confidence_reason: str = Field(
        default="", description="Transparent rule-based explanation for the confidence score"
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions required (mandatory for inference/forecasts)",
    )
    is_forecast: bool = Field(
        default=False,
        description="True if the insight projects future market behavior/numbers",
    )
    has_conflict: bool = Field(
        default=False,
        description="True if underlying sources present conflicting figures or conclusions",
    )


class ConflictItem(BaseModel):
    """Explicit disagreement or discrepancy in figures/claims across sources."""

    topic: str = Field(..., description="Metric or topic where sources disagree")
    values: list[str] = Field(
        default_factory=list,
        description="Distinct figures/claims with source references (e.g. '[E1/S1]: $1.2B vs [E3/S2]: $850M')",
    )
    explanation: str = Field(
        ...,
        description="Analysis of why figures differ (scope, definition, time period, methodology)",
    )
    evidence_ids: list[str] = Field(
        default_factory=list, description="Evidence IDs involved in this conflict"
    )


class PremiseCheck(BaseModel):
    """Verification of an explicit or implicit premise inside the user's question."""

    premise: str = Field(..., description="The implicit or explicit premise in the question")
    status: PremiseStatus = Field(
        ..., description="XÁC NHẬN, BÁC BỎ, MỘT PHẦN, or CHƯA ĐỦ BẰNG CHỨNG"
    )
    explanation: str = Field(
        ..., description="Evidence-backed explanation of why the premise holds or fails"
    )
    evidence_ids: list[str] = Field(
        default_factory=list, description="Supporting or refuting Evidence IDs"
    )


class OptionComparisonRow(BaseModel):
    """Row in the Option x Decision Criteria table for decision/selection questions."""

    option: str = Field(..., description="Option name (e.g., game genre, monetization model)")
    criteria_assessment: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from criterion name to concise assessment with [E#] references",
    )
    suitability: str = Field(
        default="", description="Overall suitability / condition for choosing this option"
    )
    evidence_ids: list[str] = Field(default_factory=list)


class RejectedItem(BaseModel):
    """Record of a rejected source or unverified quote for audit transparency."""

    item_id: str
    reason: str
    detail: str = ""


class QualityMetrics(BaseModel):
    """Self-check quality metrics computed strictly by code (BRIEF section 4.3 item 6)."""

    total_quotes_extracted: int = 0
    verified_quotes_count: int = 0
    verified_quote_rate: float = Field(
        default=0.0, description="Percentage (0-100) of extracted quotes verified >= 90"
    )
    total_insights_count: int = 0
    insights_with_verified_evidence_rate: float = Field(
        default=100.0, description="Percentage (0-100) of insights with >= 1 verified evidence"
    )
    high_confidence_from_tier_c_only_count: int = Field(
        default=0, description="Must always be 0 per rule 4.3"
    )
    llm_invented_urls_removed_count: int = Field(
        default=0, description="Number of raw URLs stripped from LLM text"
    )
    rejected_sources_count: int = 0
    rejected_quotes_count: int = 0
    rejected_sources: list[RejectedItem] = Field(default_factory=list)
    rejected_quotes: list[RejectedItem] = Field(default_factory=list)


class PipelineTrace(BaseModel):
    """Execution metadata and pipeline audit log."""

    run_timestamp: str = ""
    current_date: str = ""
    duration_seconds: float = 0.0
    llm_provider: str = ""
    llm_model: str = ""
    llm_calls_count: int = 0
    search_provider: str = ""
    queries_executed: list[str] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)
    decision_criteria: list[str] = Field(default_factory=list)
    implicit_premises: list[str] = Field(default_factory=list)
    raw_search_results_count: int = 0
    deduped_sources_count: int = 0
    kept_sources_count: int = 0
    step_logs: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    version: int = 1
    parent_run_timestamp: str = ""


class SourceRecency(BaseModel):
    source_id: str
    status: RecencyStatus = "KHÔNG CHẮC"
    reasons: list[str] = Field(default_factory=list)
    date_display: str = "Không rõ ngày"
    date_method_label: str = "không xác định được"
    age_display: str = "không rõ"
    older_than_alert: bool = False
    possibly_older_than_alert: bool = True
    data_vintage: str = ""
    date_conflict: bool = False
    supported_insight_ids: list[str] = Field(default_factory=list)
    is_key: bool = False
    key_reasons: list[str] = Field(default_factory=list)


class InsightImpact(BaseModel):
    insight_id: str
    current: ConfidenceLevel
    if_source_removed: CounterfactualLevel
    if_source_fresh: ConfidenceLevel


class KeySourceImpact(BaseModel):
    source_id: str
    impacts: list[InsightImpact] = Field(default_factory=list)
    summary: str = ""


class InsightRecency(BaseModel):
    insight_id: str
    status: InsightRecencyStatus = "MỚI"
    non_recent_source_ids: list[str] = Field(default_factory=list)
    note: str = ""


class ThresholdEvent(BaseModel):
    date: str
    source_ids: list[str] = Field(default_factory=list)
    changes: list[str] = Field(default_factory=list)


class RecencyImpact(BaseModel):
    reference_date: str
    alert_months: int = 18
    impact_level: ImpactLevel = "KHÔNG"
    summary: str = ""
    sources: list[SourceRecency] = Field(default_factory=list)
    key_old_sources: list[KeySourceImpact] = Field(default_factory=list)
    insights: list[InsightRecency] = Field(default_factory=list)
    upcoming_changes: list[ThresholdEvent] = Field(default_factory=list)
    suggested_refresh_queries: list[str] = Field(default_factory=list)
    certainty_groups: dict[str, list[str]] = Field(default_factory=dict)


class RefreshComparison(BaseModel):
    old_evidence_id: str
    new_evidence_ids: list[str] = Field(default_factory=list)
    status: ComparisonStatus = "KHÔNG TÌM THẤY DỮ LIỆU MỚI"
    explanation: str = ""


class ConfidenceChange(BaseModel):
    insight_id: str
    before: str
    after: str
    reason: str = ""


class RefreshResult(BaseModel):
    status: RefreshStatus
    refreshed_at: str = ""
    reference_date: str = ""
    target_source_ids: list[str] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)
    new_source_ids: list[str] = Field(default_factory=list)
    rejected_new_sources: list[RejectedItem] = Field(default_factory=list)
    comparisons: list[RefreshComparison] = Field(default_factory=list)
    confidence_changes: list[ConfidenceChange] = Field(default_factory=list)
    llm_calls_count: int = 0
    duration_seconds: float = 0.0
    note: str = ""


class Report(BaseModel):
    """Complete market research output schema (BRIEF section 4.3)."""

    question: str
    short_answer: str
    recommendation: str
    decision_criteria: list[str] = Field(default_factory=list)
    option_matrix: list[OptionComparisonRow] = Field(default_factory=list)
    insights: list[Insight] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)
    premise_checks: list[PremiseCheck] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    what_would_change: list[str] = Field(default_factory=list)
    next_checks: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    evidences: list[Evidence] = Field(default_factory=list)
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    trace: dict[str, Any] = Field(default_factory=dict)
    recency: Optional[RecencyImpact] = None
    refresh: Optional[RefreshResult] = None


# --- Intermediate Schemas for LLM Structured Output ---


class PlanLLMOutput(BaseModel):
    """Schema returned by the Plan step (Step 1)."""

    question_type: Literal[
        "option_selection", "market_sizing", "premise_check", "competitor_or_metric", "general"
    ] = "general"
    sub_questions: list[str] = Field(
        ..., description="3-5 specific sub-questions to investigate"
    )
    decision_criteria: list[str] = Field(
        ...,
        description="3-5 concrete criteria for decision making (e.g., Quy mô, Tăng trưởng, Cạnh tranh, Kiếm tiền, Chi phí UA)",
    )
    search_queries: list[str] = Field(
        ...,
        description="4-6 search queries (mix of English and Vietnamese with recent years)",
    )
    implicit_premises: list[str] = Field(
        ...,
        description="1-3 implicit or explicit premises in the user's question that must be fact-checked",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Important domain keywords to prioritize when truncating source text",
    )


class RawExtractedClaim(BaseModel):
    """Single claim + verbatim quote extracted by LLM from a source."""

    source_id: str = Field(..., description="Exact Source ID, e.g., S1")
    quote: str = Field(
        ...,
        description="Exact verbatim substring from the source text, <= 40 words, original language",
    )
    claim: str = Field(
        ..., description="Vietnamese summary of the specific claim or metric in the quote"
    )


class BatchExtractLLMOutput(BaseModel):
    """Schema returned by the Extract step (Step 4)."""

    extracted_claims: list[RawExtractedClaim] = Field(default_factory=list)


class DraftInsightLLM(BaseModel):
    """Insight drafted by LLM in Step 5 before code scoring in Step 6."""

    statement: str = Field(
        ...,
        description="Clear Vietnamese insight statement for decision makers. Do NOT include any URLs.",
    )
    type: InsightType = Field(
        ..., description="'fact' for direct empirical data, 'inference' for synthesis/forecasts"
    )
    evidence_ids: list[str] = Field(
        ..., description="Non-empty list of verified Evidence IDs (e.g. ['E1', 'E3'])"
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Explicit assumptions if type is 'inference' or forecast",
    )
    is_forecast: bool = Field(
        default=False, description="True if predicting future trends/numbers"
    )
    has_conflict: bool = Field(
        default=False, description="True if evidence sources disagree on this point"
    )


class SynthesisLLMOutput(BaseModel):
    """Schema returned by the Synthesize step (Step 5)."""

    short_answer: str = Field(
        ..., description="Direct 2-3 sentence Vietnamese answer to the research question"
    )
    recommendation: str = Field(
        ...,
        description="Actionable recommendation in Vietnamese (what to do, under what conditions), aligned with decision_criteria",
    )
    option_matrix: list[OptionComparisonRow] = Field(
        default_factory=list,
        description="Populated if the question asks to choose/compare options (genres, models, markets)",
    )
    insights: list[DraftInsightLLM] = Field(
        default_factory=list,
        description="Key market insights, each referencing verified evidence_ids",
    )
    conflicts: list[ConflictItem] = Field(
        default_factory=list,
        description="Discrepancies in numbers or claims across sources, with scope/period explanation",
    )
    premise_checks: list[PremiseCheck] = Field(
        default_factory=list,
        description="Verification results for each premise identified in the Plan step",
    )
    gaps: list[str] = Field(
        default_factory=list,
        description="Explicit data gaps and uncertainties that could not be verified from available sources",
    )
    what_would_change: list[str] = Field(
        default_factory=list,
        description="Specific conditions or new data that would change the recommendation",
    )
    next_checks: list[str] = Field(
        default_factory=list,
        description="Ordered list of next verification steps, from cheapest/fastest to most expensive",
    )


class RefreshQueriesLLMOutput(BaseModel):
    queries: list[str] = Field(default_factory=list)


class RefreshComparisonItemLLM(BaseModel):
    old_evidence_id: str
    new_evidence_ids: list[str] = Field(default_factory=list)
    status: Literal["XÁC NHẬN", "CẬP NHẬT", "MÂU THUẪN", "KHÔNG TƯƠNG ĐƯƠNG"]
    explanation: str


class RefreshComparisonLLMOutput(BaseModel):
    items: list[RefreshComparisonItemLLM] = Field(default_factory=list)
