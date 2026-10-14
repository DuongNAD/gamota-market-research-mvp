"""Step 1 (Plan) and Step 5 (Synthesize) LLM prompts and structured synthesis logic."""

from __future__ import annotations

from research.llm import LLMClient
from research.schemas import (
    Evidence,
    PlanLLMOutput,
    PremiseCheck,
    Source,
    SynthesisLLMOutput,
)


def plan_research(
    question: str,
    llm: LLMClient,
    current_date: str,
) -> PlanLLMOutput:
    """Step 1: Decompose research question into sub-questions, decision criteria, search queries, and implicit premises."""
    system_prompt = (
        f"Today's system date is {current_date}. You are a senior game market research strategist at Gamota.\n"
        "Analyze the user's game market research question and produce a structured research plan:\n"
        "1. `question_type`: Choose 'option_selection' if the question asks which genre/model/market/option has potential or works best; "
        "'market_sizing' if asking for market size/revenue; 'premise_check' if the question contains a strong claim (e.g. 'Why did X drop 50%?'); "
        "'competitor_or_metric' if asking for specific rankings/monthly numbers.\n"
        "2. `sub_questions`: 3 to 5 specific sub-questions in Vietnamese.\n"
        "3. `decision_criteria`: 3 to 5 concrete criteria in Vietnamese to evaluate the answer for business decision-making "
        "(e.g., 'Quy mô & tốc độ tăng trưởng', 'Mức độ cạnh tranh & rào cản gia nhập', 'Hiệu quả kiếm tiền (ARPU/IAP/IAA)', 'Chi phí UA & giữ chân người chơi').\n"
        "4. `search_queries`: 4 to 5 targeted web search queries (include at least 3 English queries using industry terms like Sensor Tower, Newzoo, Data.ai, mobile game revenue, SEA, Vietnam, and 1-2 Vietnamese/regional queries if relevant, anchored to recent years based on today's date).\n"
        "5. `implicit_premises`: 1 to 3 explicit or implicit assumptions embedded in the question that MUST be verified against data "
        "(especially if the question assumes a dramatic rise/drop or assumes data exists for a niche segment).\n"
        "6. `keywords`: 5 to 10 important keywords (EN + VI) to prioritize paragraphs when reading long articles."
    )

    user_prompt = f"User Research Question: {question}"
    return llm.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=PlanLLMOutput,
        step_name="plan_research",
    )


def synthesize_report(
    question: str,
    plan: PlanLLMOutput,
    sources: list[Source],
    verified_evidences: list[Evidence],
    llm: LLMClient,
    current_date: str,
) -> SynthesisLLMOutput:
    """Step 5: Synthesize insights, conflicts, premise checks, and gaps strictly from verified Evidence IDs."""
    if not verified_evidences:
        return SynthesisLLMOutput(
            short_answer=(
                "Hiện không tìm thấy trích dẫn nguyên văn nào đủ độ tin cậy từ các nguồn mở để trả lời trực tiếp câu hỏi này."
            ),
            recommendation=(
                "Chưa nên ra quyết định đầu tư dựa trên giả định chưa kiểm chứng. "
                "Cần thực hiện các bước kiểm chứng tiếp theo từ nguồn dữ liệu trả phí (Sensor Tower / AppMagic) hoặc khảo sát trực tiếp."
            ),
            option_matrix=[],
            insights=[],
            conflicts=[],
            premise_checks=[
                PremiseCheck(
                    premise=p,
                    status="CHƯA ĐỦ BẰNG CHỨNG",
                    explanation="Không thu thập được trích dẫn xác minh từ các nguồn mở.",
                    evidence_ids=[],
                )
                for p in plan.implicit_premises
            ],
            gaps=[
                f"Không có trích dẫn nguyên văn nào vượt qua ngưỡng xác minh (rapidfuzz >= 90) cho câu hỏi: '{question}'."
            ],
            what_would_change=[
                "Có báo cáo đo lường trực tiếp từ Sensor Tower, Data.ai, Newzoo hoặc báo cáo tài chính của nhà phát hành liên quan."
            ],
            next_checks=[
                "Tra cứu nhanh trên bản miễn phí của AppMagic / Sensor Tower Top Charts theo quốc gia và thể loại.",
                "Kiểm tra báo cáo ngành công khai gần nhất của Newzoo, Niko Partners hoặc Bộ TT&TT.",
            ],
        )

    source_map = {s.id: s for s in sources}
    evidence_lines: list[str] = []
    for ev in verified_evidences:
        src = source_map.get(ev.source_id)
        src_info = (
            f"SOURCE_ID={src.id} | DOMAIN={src.domain} | TIER={src.tier} | "
            f"DATE={src.published_date or 'unknown'} ({src.freshness_label})"
            if src
            else f"SOURCE_ID={ev.source_id}"
        )
        evidence_lines.append(
            f"- [{ev.id}] ({src_info})\n"
            f"  Claim (VI): {ev.claim}\n"
            f"  Verbatim Quote: \"{ev.quote}\""
        )

    evidences_block = "\n".join(evidence_lines)

    system_prompt = (
        f"Today's system date is {current_date}. You are a rigorous game market research analyst at Gamota.\n"
        "You must synthesize a decision-ready market research report in VIETNAMESE (tiếng Việt có dấu) "
        "based ONLY on the verified evidences (`[E1]`, `[E2]`, ...) provided below.\n\n"
        "STRICT NON-NEGOTIABLE RULES:\n"
        "1. DO NOT invent any facts, numbers, or URLs. NEVER write `http://`, `https://`, or `www.` anywhere in your response.\n"
        "2. Every `insight` MUST reference one or more valid `evidence_ids` (e.g. `[\"E1\", \"E3\"]`).\n"
        "3. Classify each insight `type` accurately:\n"
        "   - `'fact'`: Direct empirical data or historical/current fact explicitly stated in the evidence.\n"
        "   - `'inference'`: Synthesis across sources, strategic interpretation, or future projection/forecast.\n"
        "   - Set `is_forecast = true` whenever the insight predicts future performance (e.g., next 12 months).\n"
        "   - For any `'inference'` or forecast, you MUST provide 1-2 explicit `assumptions` in Vietnamese.\n"
        "4. Handle CONFLICTS honestly (`conflicts`): If different sources report different market sizes, growth rates, or claims, "
        "list ALL values with their `[E#/S#]` IDs and explain likely differences in definition (mobile vs all platforms, gross vs net, local vs foreign publishers), geographic scope, or time period. DO NOT silently average conflicting numbers.\n"
        "5. Handle DATA GAPS honestly (`gaps`): If the user asks for a very specific metric/country/time period (e.g., Cambodia MMORPG 2025 revenue, or exact last-month revenue of top 3 Thailand gacha games) and the verified evidence does NOT contain that exact figure/period, state clearly in `short_answer` and `gaps` that the exact data is unavailable in public sources. Do NOT pass off older or regional data as the exact number requested.\n"
        "6. Check every premise in `implicit_premises` (`premise_checks`): If a question contains a false or unsubstantiated premise (e.g., 'Why did SEA mobile game revenue drop 50% last year?'), challenge/refute it (`BÁC BỎ` or `CHƯA ĐỦ BẰNG CHỨNG`) using the verified evidence.\n"
        "7. If the question asks to compare or choose options (e.g., game genres, monetization models), populate `option_matrix` evaluating 3-4 candidate options across the `decision_criteria`.\n"
        "8. Order `next_checks` from the cheapest/fastest verification action to the most expensive."
    )

    user_prompt = (
        f"Research Question: {question}\n"
        f"Question Type: {plan.question_type}\n"
        f"Sub-questions: {', '.join(plan.sub_questions)}\n"
        f"Decision Criteria: {', '.join(plan.decision_criteria)}\n"
        f"Premises to Check: {', '.join(plan.implicit_premises)}\n\n"
        f"VERIFIED EVIDENCES (ONLY USE THESE):\n{evidences_block}"
    )

    return llm.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=SynthesisLLMOutput,
        step_name="synthesize_report",
    )
