"""Rule-based source grading (Tier A/B/C and recency/freshness)."""

from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Optional
from urllib.parse import urlparse

import yaml

from research.schemas import FreshnessCode, Source, SourceTier

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "source_tiers.yaml"


@lru_cache(maxsize=1)
def load_source_tiers_config(config_path: Optional[Path] = None) -> dict[str, Any]:
    """Load and cache the source tier rules from YAML."""
    path = config_path or CONFIG_PATH
    if not path.exists():
        return {"tier_a": {"domains": {}}, "tier_b": {"domains": {}}, "tier_c": {}}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def extract_hostname(url_or_domain: str) -> str:
    """Extract normalized lowercase hostname (preserving subdomains except www.)."""
    raw = (url_or_domain or "").strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        parsed = urlparse(raw)
        host = parsed.hostname or ""
    else:
        host = raw.split("/")[0].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


def _match_domain_map(hostname: str, domain_map: dict[str, str]) -> Optional[tuple[str, str]]:
    """Check if hostname equals or is a subdomain of any key in domain_map."""
    if not hostname or not domain_map:
        return None
    if hostname in domain_map:
        return hostname, domain_map[hostname]
    for domain, reason in domain_map.items():
        domain_clean = domain.lower().strip()
        if hostname == domain_clean or hostname.endswith("." + domain_clean):
            return domain_clean, reason
    return None


def grade_source_domain(
    url_or_domain: str, config: Optional[dict[str, Any]] = None
) -> tuple[SourceTier, str, str]:
    """Return (tier, tier_reason, normalized_domain) using deterministic YAML rules."""
    cfg = config if config is not None else load_source_tiers_config()
    hostname = extract_hostname(url_or_domain)
    if not hostname:
        return (
            "C",
            "Không xác định được domain hợp lệ -> xếp hạng C mặc định",
            "unknown",
        )

    tier_a_cfg = cfg.get("tier_a", {}) or {}
    tier_b_cfg = cfg.get("tier_b", {}) or {}
    tier_c_cfg = cfg.get("tier_c", {}) or {}

    # 1. Check Tier A subdomain prefixes (e.g., ir.*, investor.*)
    for prefix in tier_a_cfg.get("subdomain_prefixes", []) or []:
        if hostname.startswith(prefix.lower()):
            return (
                "A",
                f"Chuyên trang Quan hệ nhà đầu tư / Báo cáo tài chính ({hostname})",
                hostname,
            )

    # 2. Check Tier A government suffix patterns (e.g., .gov, .gov.vn)
    for suffix in tier_a_cfg.get("suffix_patterns", []) or []:
        sfx = suffix.lower()
        if hostname.endswith(sfx):
            return (
                "A",
                f"Cổng thông tin cơ quan nhà nước ({hostname})",
                hostname,
            )

    # 3. Check Tier A explicit domain list
    matched_a = _match_domain_map(hostname, tier_a_cfg.get("domains", {}) or {})
    if matched_a:
        matched_domain, reason = matched_a
        return "A", reason, matched_domain

    # 4. Check Tier B explicit domain list
    matched_b = _match_domain_map(hostname, tier_b_cfg.get("domains", {}) or {})
    if matched_b:
        matched_domain, reason = matched_b
        return "B", reason, matched_domain

    # 5. Default to Tier C
    default_c_reason = tier_c_cfg.get(
        "default_reason",
        "Nguồn hạng C (mặc định): Blog, trang SEO, diễn đàn, thông cáo báo chí hoặc domain chưa kiểm chứng",
    )
    return "C", f"{default_c_reason} ({hostname})", hostname


def parse_published_date(date_str: Optional[str]) -> Optional[date]:
    """Parse flexible date string (YYYY-MM-DD, YYYY-MM, ISO datetime, or YYYY) into a date."""
    if not date_str:
        return None
    s = str(date_str).strip()
    if not s:
        return None

    # Try YYYY-MM-DD at start of string
    m_full = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m_full:
        try:
            return date(int(m_full.group(1)), int(m_full.group(2)), int(m_full.group(3)))
        except ValueError:
            pass

    # Try YYYY/MM/DD
    m_slash = re.match(r"^(\d{4})/(\d{2})/(\d{2})", s)
    if m_slash:
        try:
            return date(int(m_slash.group(1)), int(m_slash.group(2)), int(m_slash.group(3)))
        except ValueError:
            pass

    # Try YYYY-MM
    m_month = re.match(r"^(\d{4})-(\d{2})$", s)
    if m_month:
        try:
            return date(int(m_month.group(1)), int(m_month.group(2)), 15)
        except ValueError:
            pass

    # Try standalone 4-digit year YYYY
    m_year = re.match(r"^(\d{4})$", s)
    if m_year:
        try:
            return date(int(m_year.group(1)), 6, 30)
        except ValueError:
            pass

    # Fallback: try datetime.fromisoformat
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.date()
    except ValueError:
        return None


def compute_freshness(
    published_date: Optional[str], reference_date: Optional[date] = None
) -> tuple[FreshnessCode, str]:
    """Compute recency bucket according to BRIEF section 4.2:
    - <= 12 months (<= 366 days): 'fresh' ('Mới (<=12 tháng)')
    - 12–24 months (367–731 days): 'aging' ('Cũ dần (12-24 tháng)')
    - > 24 months (> 731 days) or unknown: 'stale' ('Cũ (>24 tháng hoặc không rõ ngày)')
    """
    ref = reference_date or date.today()
    parsed = parse_published_date(published_date)
    if parsed is None:
        return "stale", "Cũ (>24 tháng hoặc không rõ ngày)"

    delta_days = (ref - parsed).days
    # Future dates slightly ahead due to timezone or upcoming reports are treated as fresh
    if delta_days <= 366:
        return "fresh", "Mới (<=12 tháng)"
    if delta_days <= 731:
        return "aging", "Cũ dần (12-24 tháng)"
    return "stale", "Cũ (>24 tháng hoặc không rõ ngày)"


def grade_source(
    source: Source,
    reference_date: Optional[date] = None,
    config: Optional[dict[str, Any]] = None,
) -> Source:
    """Populate tier, tier_reason, domain, freshness, and freshness_label on a Source."""
    tier, reason, norm_domain = grade_source_domain(
        source.url or source.domain, config=config
    )
    freshness_code, freshness_label = compute_freshness(
        source.published_date, reference_date=reference_date
    )
    return source.model_copy(
        update={
            "domain": norm_domain if norm_domain != "unknown" else source.domain,
            "tier": tier,
            "tier_reason": reason,
            "freshness": freshness_code,
            "freshness_label": freshness_label,
        }
    )
