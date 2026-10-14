"""Unit tests for verbatim quote verification and Text Fragment URL builder in research/extract.py."""

from __future__ import annotations

from research.extract import (
    build_text_fragment_url,
    count_words,
    normalize_for_match,
    verify_quote,
)


SAMPLE_SOURCE = """
Southeast Asia mobile game revenue reached $4.2 billion in 2025, driven primarily by RPG and strategy titles in Indonesia, Thailand, and Vietnam.
According to Sensor Tower's latest regional analysis, hybrid-casual monetization combining in-app purchases (IAP) and rewarded video ads grew by 28% year-over-year across the Philippines and Indonesia.
"""


def test_verify_quote_exact_match() -> None:
    quote = "Southeast Asia mobile game revenue reached $4.2 billion in 2025, driven primarily by RPG and strategy titles"
    verified, score, reason = verify_quote(quote, SAMPLE_SOURCE)
    assert verified is True
    assert score == 100.0
    assert reason == ""


def test_verify_quote_curly_quotes_and_whitespace_normalization() -> None:
    source_with_curly = "“Hybrid-casual monetization combining in-app purchases (IAP) and rewarded video ads”\n\ngrew   by 28% year-over-year."
    quote_ascii = '"Hybrid-casual monetization combining in-app purchases (IAP) and rewarded video ads" grew by 28% year-over-year.'
    verified, score, reason = verify_quote(quote_ascii, source_with_curly)
    assert verified is True
    assert score >= 95.0
    assert reason == ""


def test_verify_quote_rejects_paraphrased_or_fabricated_quote() -> None:
    paraphrased = "Doanh thu game mobile Đông Nam Á đạt 4,2 tỷ USD nhờ dòng game nhập vai và chiến thuật."
    verified, score, reason = verify_quote(paraphrased, SAMPLE_SOURCE)
    assert verified is False
    assert score < 90.0
    assert "Không khớp nguyên văn" in reason


def test_verify_quote_rejects_over_40_words() -> None:
    long_quote = " ".join(["word"] * 41)
    long_source = long_quote + " extra text in source"
    verified, score, reason = verify_quote(long_quote, long_source, max_words=40)
    assert verified is False
    assert score == 0.0
    assert "vượt quá giới hạn 40 từ" in reason


def test_verify_quote_rejects_empty_or_too_short() -> None:
    v1, s1, r1 = verify_quote("", SAMPLE_SOURCE)
    assert v1 is False and s1 == 0.0 and "rỗng" in r1

    v2, s2, r2 = verify_quote("RPG", SAMPLE_SOURCE)
    assert v2 is False and s2 == 0.0 and "quá ngắn" in r2


def test_build_text_fragment_url_encodes_commas_and_spaces() -> None:
    url = "https://sensortower.com/blog/sea-games-2025#section-1"
    quote = "Southeast Asia mobile game revenue, including IAP, reached $4.2 billion in 2025."
    hl_url = build_text_fragment_url(url, quote, max_snippet_words=6)
    assert hl_url.startswith("https://sensortower.com/blog/sea-games-2025#:~:text=")
    # Commas must be percent-encoded as %2C per W3C Text Fragments spec
    assert "%2C" in hl_url
    assert "#section-1" not in hl_url


def test_count_words_and_normalize() -> None:
    assert count_words("  one   two\nthree ") == 3
    assert normalize_for_match("“Hello—World”") == '"hello-world"'
