"""Step 4: Claim extraction and verbatim quote verification with RapidFuzz."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import quote as url_quote

from rapidfuzz import fuzz

from research.llm import LLMClient
from research.schemas import (
    BatchExtractLLMOutput,
    Evidence,
    RejectedItem,
    Source,
)

QUOTE_TRANSLATION_TABLE = str.maketrans(
    {
        "“": '"',
        "”": '"',
        "„": '"',
        "‟": '"',
        "«": '"',
        "»": '"',
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "–": "-",
        "—": "-",
        "−": "-",
        "\u00a0": " ",
        "\u200b": "",
    }
)


def normalize_for_match(text: str) -> str:
    """Normalize Unicode, curly quotes/dashes, case, and whitespace for quote verification."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFKC", text)
    norm = norm.translate(QUOTE_TRANSLATION_TABLE)
    norm = norm.lower()
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm


def count_words(text: str) -> int:
    """Count whitespace-delimited words in text."""
    if not text or not text.strip():
        return 0
    return len(text.strip().split())


def verify_quote(
    quote: str,
    source_text: str,
    threshold: float = 90.0,
    max_words: int = 40,
    min_chars: int = 12,
) -> tuple[bool, float, str]:
    """Verify that `quote` is a verbatim substring (or >= 90 fuzzy partial match) of `source_text`.

    Rules (BRIEF section 4.1 step 4):
    - Quote must be <= 40 words.
    - Normalized whitespace, punctuation, and lowercase.
    - rapidfuzz.fuzz.partial_ratio >= 90.0.
    """
    if not quote or not quote.strip():
        return False, 0.0, "Trích dẫn rỗng"
    if not source_text or not source_text.strip():
        return False, 0.0, "Nội dung nguồn rỗng"

    word_cnt = count_words(quote)
    if word_cnt > max_words:
        return (
            False,
            0.0,
            f"Trích dẫn vượt quá giới hạn {max_words} từ ({word_cnt} từ)",
        )

    norm_quote = normalize_for_match(quote).strip("\"' .,;:!?")
    norm_source = normalize_for_match(source_text)

    if len(norm_quote) < min_chars:
        return (
            False,
            0.0,
            f"Trích dẫn quá ngắn ({len(norm_quote)} ký tự < {min_chars})",
        )

    if norm_quote in norm_source:
        return True, 100.0, ""

    score = float(fuzz.partial_ratio(norm_quote, norm_source))
    score_rounded = round(score, 1)
    if score >= threshold:
        return True, score_rounded, ""
    return (
        False,
        score_rounded,
        f"Không khớp nguyên văn với nguồn (rapidfuzz partial_ratio = {score_rounded} < {threshold})",
    )


def build_text_fragment_url(base_url: str, quote: str, max_snippet_words: int = 10) -> str:
    """Build a browser Text Fragment URL (`url#:~:text=<percent-encoded start of quote>`).

    Per W3C Text Fragments spec, commas and dashes are percent-encoded via safe=''.
    """
    clean_url = (base_url or "").split("#")[0].strip()
    if not clean_url:
        return ""
    cleaned_quote = re.sub(r"^[\s\"'“”‘’\.…]+|[\s\"'“”‘’\.…]+$", "", quote or "")
    words = cleaned_quote.split()
    if not words:
        return clean_url
    snippet = " ".join(words[:max_snippet_words])
    encoded = url_quote(snippet, safe="")
    return f"{clean_url}#:~:text={encoded}"


def _trim_quote_to_max_words(quote: str, max_words: int = 40) -> str:
    """If LLM returned slightly more than max_words, trim to max_words at word boundary."""
    words = (quote or "").strip().split()
    if len(words) <= max_words:
        return (quote or "").strip()
    return " ".join(words[:max_words])


def extract_claims_from_sources(
    question: str,
    sub_questions: list[str],
    sources: list[Source],
    source_texts: dict[str, str],
    full_source_texts: dict[str, str],
    llm: LLMClient,
    current_date: str,
    batch_size: int = 4,
    evidence_id_start: int = 1,
) -> tuple[list[Evidence], list[RejectedItem], int]:
    """Batch sources (3-4 per LLM call), extract verbatim quotes + claims, and verify with code.

    Returns:
        (verified_evidences, rejected_quotes, total_extracted_count)
    """
    verified_evidences: list[Evidence] = []
    rejected_quotes: list[RejectedItem] = []
    total_extracted = 0
    evidence_counter = evidence_id_start

    # Filter sources that actually have text
    valid_sources = [s for s in sources if (source_texts.get(s.id) or "").strip()]
    if not valid_sources:
        return [], [], 0

    for i in range(0, len(valid_sources), batch_size):
        batch = valid_sources[i : i + batch_size]
        sources_block_lines: list[str] = []
        for src in batch:
            txt = source_texts.get(src.id, "")
            sources_block_lines.append(
                f"=== SOURCE_ID: {src.id} | DOMAIN: {src.domain} | TIER: {src.tier} | "
                f"PUBLISHED: {src.published_date or 'unknown'} | TITLE: {src.title} ===\n"
                f"{txt}\n"
            )
        sources_payload = "\n".join(sources_block_lines)

        system_prompt = (
            f"Today's date is {current_date}. You are a precise market research extraction engine.\n"
            "Your task is to extract concrete facts, metrics, market trends, or arguments from the provided sources "
            "that help answer the research question and sub-questions.\n"
            "CRITICAL RULES:\n"
            "1. Every extracted item MUST include a `quote` copied VERBATIM (word-for-word, character-for-character) "
            "from the source text, in the ORIGINAL language of the source (DO NOT translate the quote).\n"
            "2. Each `quote` MUST be between 8 and 35 words (strictly <= 40 words). Do NOT use ellipses (...) inside a quote to skip words.\n"
            "3. `claim` must be written in clear Vietnamese summarizing the exact point proven by that quote.\n"
            "4. Extract 1 to 4 of the most informative claims per source if relevant. Skip boilerplate/menus."
        )

        user_prompt = (
            f"Research Question: {question}\n"
            f"Sub-questions: {', '.join(sub_questions)}\n\n"
            f"Sources to extract from:\n{sources_payload}"
        )

        batch_out = llm.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=BatchExtractLLMOutput,
            step_name=f"extract_batch_{i // batch_size + 1}",
        )

        batch_source_map = {s.id: s for s in batch}
        for raw_item in batch_out.extracted_claims:
            total_extracted += 1
            src_id = raw_item.source_id.strip()
            if src_id not in batch_source_map:
                rejected_quotes.append(
                    RejectedItem(
                        item_id=f"raw_{total_extracted}",
                        reason=f"LLM trả về source_id không hợp lệ ({src_id})",
                        detail=raw_item.quote[:120],
                    )
                )
                continue

            src_obj = batch_source_map[src_id]
            candidate_quote = _trim_quote_to_max_words(raw_item.quote, max_words=40)

            # Verify against truncated source text first, then full in-memory text if available
            trunc_text = source_texts.get(src_id, "")
            full_text = full_source_texts.get(src_id, trunc_text)

            is_ok, score, reason = verify_quote(candidate_quote, trunc_text)
            if not is_ok and full_text and full_text != trunc_text:
                is_ok, score, reason = verify_quote(candidate_quote, full_text)

            if is_ok:
                ev_id = f"E{evidence_counter}"
                evidence_counter += 1
                verified_evidences.append(
                    Evidence(
                        id=ev_id,
                        source_id=src_id,
                        quote=candidate_quote,
                        claim=raw_item.claim.strip(),
                        verified=True,
                        match_score=score,
                        highlight_url=build_text_fragment_url(src_obj.url, candidate_quote),
                    )
                )
            else:
                rejected_quotes.append(
                    RejectedItem(
                        item_id=f"{src_id}_quote_{total_extracted}",
                        reason=reason,
                        detail=candidate_quote[:140],
                    )
                )

    return verified_evidences, rejected_quotes, total_extracted
