"""Step 2: Web search (Tavily + ddgs fallback), content & date extraction (trafilatura), ranking (<= 12 sources), and keyword-aware truncation (~6,000 chars)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from dotenv import load_dotenv
import httpx
import trafilatura

from research.dates import detect_date_with_method, infer_date_method, precision_of
from research.grade import grade_source
from research.schemas import RejectedItem, Source

load_dotenv()

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "retrieve"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
}

SKIP_EXTENSIONS = (".pdf", ".zip", ".rar", ".exe", ".dmg", ".apk", ".mp4", ".mp3", ".jpg", ".png")


def _get_secret(key: str, default: str = "") -> str:
    val = os.environ.get(key, "").strip()
    if val:
        return val
    try:
        import streamlit as st

        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


def canonicalize_url(url: str) -> str:
    """Normalize URL for deduplication (strip fragments and tracking query params)."""
    raw = (url or "").strip()
    if not raw or not raw.startswith(("http://", "https://")):
        return ""
    parsed = urlparse(raw)
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=False)
        if k.lower() not in TRACKING_PARAMS
    ]
    clean_path = parsed.path.rstrip("/") or "/"
    return urlunparse(
        (
            parsed.scheme.lower(),
            (parsed.netloc or "").lower(),
            clean_path,
            "",
            urlencode(query_pairs),
            "",
        )
    )


def _extract_date_fallback(url: str, text: str, title: str = "") -> Optional[str]:
    """Fallback date detector from URL path, title, or leading article text."""
    detected_date, _method = detect_date_with_method(url, text, title)
    return detected_date



def truncate_source_text(
    text: str, keywords: list[str], max_chars: int = 6000
) -> str:
    """Truncate source text to ~6,000 characters while prioritizing paragraphs with keywords and metrics."""
    clean = (text or "").strip()
    if len(clean) <= max_chars:
        return clean

    paragraphs = [p.strip() for p in re.split(r"\n{2,}|\r\n{2,}", clean) if p.strip()]
    if len(paragraphs) <= 1:
        paragraphs = [p.strip() for p in clean.split("\n") if p.strip()]
    if len(paragraphs) <= 1:
        return clean[:max_chars]

    kw_lower = [k.lower().strip() for k in keywords if k and len(k.strip()) >= 2]
    metric_pattern = re.compile(
        r"(\d+(?:\.\d+)?\s*(?:%|percent|billion|million|tỷ|triệu|usd|\$)|202[3-7])",
        re.IGNORECASE,
    )

    scored_paras: list[tuple[int, float, str]] = []
    for idx, para in enumerate(paragraphs):
        p_low = para.lower()
        score = 0.0
        # Always boost lead paragraph for context
        if idx == 0:
            score += 5.0
        elif idx == 1:
            score += 2.5

        for kw in kw_lower:
            if kw in p_low:
                score += 2.0
        metric_hits = len(metric_pattern.findall(para))
        score += min(metric_hits * 1.5, 6.0)
        scored_paras.append((idx, score, para))

    # Sort by score descending to pick best paragraphs, then restore original document order
    scored_paras.sort(key=lambda x: (-x[1], x[0]))
    selected_indices: list[int] = []
    current_chars = 0

    for idx, _sc, para in scored_paras:
        if current_chars + len(para) + 2 <= max_chars:
            selected_indices.append(idx)
            current_chars += len(para) + 2
        elif current_chars < int(max_chars * 0.75):
            remaining = max_chars - current_chars
            if remaining > 200:
                paragraphs[idx] = para[:remaining]
                selected_indices.append(idx)
            break

    selected_indices.sort()
    result = "\n\n".join(paragraphs[i] for i in selected_indices)
    return result[:max_chars]


def _search_tavily_single(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    api_key = _get_secret("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("No TAVILY_API_KEY")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_raw_content": True,
        "max_results": max_results,
    }
    with httpx.Client(timeout=18.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for item in data.get("results", []) or []:
            results.append(
                {
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "raw_content": item.get("raw_content") or "",
                    "published_date": item.get("published_date"),
                    "provider": "tavily",
                }
            )
        return results


def _search_ddgs_single(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    from ddgs import DDGS

    results = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "url": item.get("href") or item.get("url") or "",
                    "title": item.get("title") or "",
                    "snippet": item.get("body") or item.get("snippet") or "",
                    "raw_content": "",
                    "published_date": None,
                    "provider": "ddgs",
                }
            )
    return results


def search_query(
    query: str, max_results: int = 5, use_cache: bool = True
) -> tuple[list[dict[str, Any]], str]:
    """Run a single search query (top 5) using Tavily with automatic ddgs fallback and disk cache."""
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        q_hash = hashlib.sha256(f"search_v1::{query}::{max_results}".encode("utf-8")).hexdigest()[:24]
        cache_file = CACHE_DIR / f"search_{q_hash}.json"
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                return cached.get("results", []), cached.get("provider", "cache")
            except Exception:
                pass

    provider_used = "ddgs"
    results: list[dict[str, Any]] = []
    if _get_secret("TAVILY_API_KEY"):
        try:
            results = _search_tavily_single(query, max_results=max_results)
            provider_used = "tavily"
        except Exception:
            results = []

    if not results:
        try:
            results = _search_ddgs_single(query, max_results=max_results)
            provider_used = "ddgs"
        except Exception:
            results = []

    if use_cache and results:
        cache_file.write_text(
            json.dumps({"provider": provider_used, "results": results}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return results, provider_used


def fetch_page_content_and_date(
    url: str,
    existing_raw_content: str = "",
    existing_snippet: str = "",
    existing_date: Optional[str] = None,
    use_cache: bool = True,
    existing_title: str = "",
) -> tuple[str, Optional[str]]:
    """Fetch main text and publication date using httpx + trafilatura (with disk cache)."""
    cache_file: Optional[Path] = None
    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        u_hash = hashlib.sha256(f"fetch_v1::{url}".encode("utf-8")).hexdigest()[:24]
        cache_file = CACHE_DIR / f"page_{u_hash}.json"
        if cache_file.exists():
            try:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                c_text = cached.get("text", "")
                c_date = cached.get("published_date")
                if not c_date:
                    c_date = _extract_date_fallback(url, c_text, existing_title)
                    if c_date:
                        cache_file.write_text(
                            json.dumps({"url": url, "text": c_text, "published_date": c_date}, ensure_ascii=False),
                            encoding="utf-8",
                        )
                return c_text, c_date
            except Exception:
                pass

    text = (existing_raw_content or "").strip()
    pub_date = existing_date

    if len(text) < 400 or not pub_date:
        try:
            headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"}
            with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
                resp = client.get(url)
                if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", "").lower():
                    html = resp.text
                    extracted = trafilatura.bare_extraction(
                        html,
                        url=url,
                        include_comments=False,
                        include_tables=True,
                        favor_recall=True,
                    )
                    if extracted:
                        ext_dict = (
                            extracted
                            if isinstance(extracted, dict)
                            else extracted.as_dict()
                            if hasattr(extracted, "as_dict")
                            else {}
                        )
                        ext_text = (ext_dict.get("text") or "").strip()
                        if len(ext_text) > len(text):
                            text = ext_text
                        if not pub_date and ext_dict.get("date"):
                            pub_date = str(ext_dict.get("date"))
        except Exception:
            pass

    # Combine with search snippet if scraped text is short or snippet has extra context
    snippet_clean = (existing_snippet or "").strip()
    if snippet_clean and snippet_clean not in text:
        text = f"{snippet_clean}\n\n{text}".strip() if text else snippet_clean

    if not pub_date:
        pub_date = _extract_date_fallback(url, text, existing_title)

    if use_cache and text and cache_file is not None:
        cache_file.write_text(
            json.dumps({"url": url, "text": text, "published_date": pub_date}, ensure_ascii=False),
            encoding="utf-8",
        )

    return text, pub_date


def retrieve_and_grade_sources(
    queries: list[str],
    keywords: list[str],
    reference_date: Optional[date] = None,
    max_per_query: int = 5,
    max_kept_sources: int = 12,
    max_chars_per_source: int = 6000,
    use_cache: bool = True,
) -> tuple[
    list[Source],
    dict[str, str],
    dict[str, str],
    list[RejectedItem],
    dict[str, Any],
]:
    """Execute Step 2 & Step 3: Search top 5/query -> dedup -> fetch text+date -> grade -> keep <= 12 best.

    Returns:
        (kept_sources, truncated_texts, full_texts, rejected_sources, stats_dict)
    """
    ref_date = reference_date or date.today()
    raw_results: list[dict[str, Any]] = []
    providers_seen: set[str] = set()

    for q in queries:
        q_res, prov = search_query(q, max_results=max_per_query, use_cache=use_cache)
        providers_seen.add(prov)
        raw_results.extend(q_res)

    raw_count = len(raw_results)

    # Deduplicate by canonical URL
    dedup_map: dict[str, dict[str, Any]] = {}
    rejected_sources: list[RejectedItem] = []

    for item in raw_results:
        c_url = canonicalize_url(item.get("url", ""))
        if not c_url:
            continue
        if c_url.lower().endswith(SKIP_EXTENSIONS):
            rejected_sources.append(
                RejectedItem(
                    item_id=c_url[:80],
                    reason="Bỏ qua định dạng file nhị phân/tải xuống",
                )
            )
            continue
        if c_url not in dedup_map:
            item_copy = dict(item)
            item_copy["canonical_url"] = c_url
            dedup_map[c_url] = item_copy
        else:
            # Merge longer snippet/raw_content if duplicate appears across queries
            existing = dedup_map[c_url]
            if len(item.get("raw_content") or "") > len(existing.get("raw_content") or ""):
                existing["raw_content"] = item.get("raw_content")
            if item.get("snippet") and item["snippet"] not in (existing.get("snippet") or ""):
                existing["snippet"] = f"{existing.get('snippet', '')} {item['snippet']}".strip()

    dedup_candidates = list(dedup_map.values())
    dedup_count = len(dedup_candidates)

    # Pre-grade domains so we prioritize fetching Tier A/B first (cap fetch pool at 18 candidates for speed)
    def _pre_priority(cand: dict[str, Any]) -> tuple[int, int]:
        temp_src = grade_source(
            Source(id="tmp", url=cand["canonical_url"], domain="", title=cand.get("title") or ""),
            reference_date=ref_date,
        )
        cand["_pre_tier"] = temp_src.tier
        tier_rank = {"A": 0, "B": 1, "C": 2}.get(temp_src.tier, 2)
        has_raw = 0 if len(cand.get("raw_content") or "") > 300 else 1
        return (tier_rank, has_raw)

    dedup_candidates.sort(key=_pre_priority)
    fetch_pool = dedup_candidates[:18]
    for dropped in dedup_candidates[18:]:
        rejected_sources.append(
            RejectedItem(
                item_id=dropped["canonical_url"][:80],
                reason="Ngoài top 18 ứng viên ưu tiên sau khi khử trùng lặp",
            )
        )

    # Fetch content & date concurrently while preserving deterministic candidate order
    fetched_items: list[tuple[Source, str]] = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [
            (
                cand,
                pool.submit(
                    fetch_page_content_and_date,
                    cand["canonical_url"],
                    cand.get("raw_content") or "",
                    cand.get("snippet") or "",
                    cand.get("published_date"),
                    use_cache,
                    cand.get("title") or "",
                ),
            )
            for cand in fetch_pool
        ]
        for cand, fut in futures:
            c_url = cand["canonical_url"]
            try:
                full_text, pub_date = fut.result()
            except Exception as exc:
                rejected_sources.append(
                    RejectedItem(
                        item_id=c_url[:80],
                        reason=f"Lỗi tải trang ({type(exc).__name__})",
                    )
                )
                continue

            if len((full_text or "").strip()) < 120:
                rejected_sources.append(
                    RejectedItem(
                        item_id=c_url[:80],
                        reason="Nội dung trích xuất quá ngắn (< 120 ký tự) hoặc trang chặn bot",
                    )
                )
                continue

            title_clean = (cand.get("title") or c_url).strip()
            d_method = infer_date_method(
                c_url,
                full_text,
                title_clean,
                pub_date,
                cand.get("published_date"),
            )
            graded = grade_source(
                Source(
                    id="pending",
                    url=c_url,
                    domain="",
                    title=title_clean,
                    published_date=pub_date,
                    date_method=d_method,
                    date_precision=precision_of(d_method, pub_date),
                ),
                reference_date=ref_date,
            )
            fetched_items.append((graded, full_text))

    # Rank fetched sources: Tier (A > B > C), Freshness (fresh > aging > stale), keyword hits
    kw_low = [k.lower() for k in keywords if k]

    def _rank_key(pair: tuple[Source, str]) -> tuple[int, int, int]:
        src, txt = pair
        tier_score = {"A": 0, "B": 1, "C": 2}.get(src.tier, 2)
        fresh_score = {"fresh": 0, "aging": 1, "stale": 2}.get(src.freshness, 2)
        txt_low = txt.lower()
        kw_hits = sum(1 for k in kw_low if k in txt_low)
        return (tier_score, fresh_score, -kw_hits)

    fetched_items.sort(key=_rank_key)

    # When multiple articles from the same domain tie on (tier, freshness, keyword_hits),
    # prefer localized Vietnamese path (/vi/) at that domain's slot while preserving candidate order.
    same_dom_buckets: dict[tuple[str, tuple[int, int, int]], list[int]] = {}
    for idx_f, pair in enumerate(fetched_items):
        b_key = ((pair[0].domain or "").lower(), _rank_key(pair))
        same_dom_buckets.setdefault(b_key, []).append(idx_f)
    for b_indices in same_dom_buckets.values():
        if len(b_indices) > 1:
            sorted_group = sorted(
                (fetched_items[i] for i in b_indices),
                key=lambda p: (0 if "/vi/" in (p[0].url or "") else 1),
            )
            for pos, item_val in zip(b_indices, sorted_group):
                fetched_items[pos] = item_val

    # Prioritize domain diversity: take at most 2 sources per domain first, then fill remaining slots if needed
    primary_pass: list[tuple[Source, str]] = []
    overflow_pass: list[tuple[Source, str]] = []
    domain_counts: dict[str, int] = {}
    for pair in fetched_items:
        dom = (pair[0].domain or "").lower()
        cnt = domain_counts.get(dom, 0)
        if cnt < 1 or (pair[0].tier in ("A", "B") and cnt < 2):
            primary_pass.append(pair)
            domain_counts[dom] = cnt + 1
        else:
            overflow_pass.append(pair)

    ordered_items = primary_pass + overflow_pass

    kept_sources: list[Source] = []
    truncated_texts: dict[str, str] = {}
    full_texts: dict[str, str] = {}

    for idx, (src, full_txt) in enumerate(ordered_items):
        if idx < max_kept_sources:
            sid = f"S{idx + 1}"
            final_src = src.model_copy(update={"id": sid})
            kept_sources.append(final_src)
            full_texts[sid] = full_txt
            truncated_texts[sid] = truncate_source_text(
                full_txt, keywords=keywords, max_chars=max_chars_per_source
            )
        else:
            rejected_sources.append(
                RejectedItem(
                    item_id=src.url[:80],
                    reason=f"Vượt quá giới hạn {max_kept_sources} nguồn tốt nhất hoặc trùng lặp domain (Hạng {src.tier}, {src.freshness_label})",
                )
            )

    stats = {
        "search_provider": "+".join(sorted(providers_seen)) if providers_seen else "none",
        "raw_search_results_count": raw_count,
        "deduped_sources_count": dedup_count,
        "kept_sources_count": len(kept_sources),
    }
    return kept_sources, truncated_texts, full_texts, rejected_sources, stats
