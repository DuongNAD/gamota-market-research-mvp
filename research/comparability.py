"""Pure-Python comparability guard for targeted refresh comparisons (BRIEF_M3_FIX section 3.2)."""

from __future__ import annotations

import calendar
from datetime import date
import re
from typing import Optional

from research.dates import detect_data_period
from research.grade import parse_published_date
from research.schemas import ComparisonStatus, Evidence, RefreshComparison, Source

GAME_RE = re.compile(
    r"\b(games?|gaming|gamers?|gamedev|e-?sports?|hyper-?casual|hybrid-casual|mmorpg|moba|gacha)\b|trò chơi",
    re.IGNORECASE,
)

SEA_CASE_SENSITIVE_RE = re.compile(r"\bSEA\b")
SEA_INSENSITIVE_RE = re.compile(
    r"southeast asia|south-east asia|đông nam á|\basean\b",
    re.IGNORECASE,
)

REGION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ID", re.compile(r"indonesia", re.IGNORECASE)),
    ("PH", re.compile(r"philippines", re.IGNORECASE)),
    ("TH", re.compile(r"thailand|thái lan", re.IGNORECASE)),
    ("VN", re.compile(r"vietnam|viet nam|việt nam", re.IGNORECASE)),
    ("MY", re.compile(r"malaysia", re.IGNORECASE)),
    ("SG", re.compile(r"singapore", re.IGNORECASE)),
    ("KH", re.compile(r"cambodia|campuchia", re.IGNORECASE)),
    ("GLOBAL", re.compile(r"\bglobal(ly)?\b|worldwide|toàn cầu", re.IGNORECASE)),
]

UNIT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("usd", re.compile(r"\$|\bUSD\b|dollars?|triệu USD|tỷ USD", re.IGNORECASE)),
    ("downloads", re.compile(r"download|install|lượt tải|lượt cài", re.IGNORECASE)),
    ("percent", re.compile(r"%|percent", re.IGNORECASE)),
    ("users", re.compile(r"\bplayers?\b|\busers?\b|người chơi|người dùng", re.IGNORECASE)),
]

YEAR_STRIP_RE = re.compile(r"\b(?:19|20)\d{2}\b")


def scope_category(quote: str, title: str = "", url: str = "") -> str:
    """Return 'game' if quote, title, or url matches GAME_RE; otherwise 'không rõ là game'."""
    combined = f"{quote or ''} {title or ''} {url or ''}"
    if GAME_RE.search(combined):
        return "game"
    return "không rõ là game"


def region_tags(quote: str, title: str = "") -> set[str]:
    """Extract normalized market/region tags from quote and source title."""
    combined = f"{quote or ''} {title or ''}"
    tags: set[str] = set()
    if SEA_CASE_SENSITIVE_RE.search(combined) or SEA_INSENSITIVE_RE.search(combined):
        tags.add("SEA")
    for code, pat in REGION_PATTERNS:
        if pat.search(combined):
            tags.add(code)
    return tags


def unit_kinds(quote: str) -> set[str]:
    """Extract unit categories ('usd', 'downloads', 'percent', 'users') mentioned in quote."""
    text = quote or ""
    units: set[str] = set()
    for kind, pat in UNIT_PATTERNS:
        if pat.search(text):
            units.add(kind)
    return units


def has_figure(quote: str) -> bool:
    """Return True if quote contains any digit after stripping 4-digit years 19xx/20xx."""
    cleaned = YEAR_STRIP_RE.sub("", quote or "")
    return bool(re.search(r"\d", cleaned))


def period_granularity(label: str) -> str:
    """Return period granularity: 'quý', 'nửa năm', 'tháng', 'năm', '' (empty), or 'khác'."""
    s = (label or "").strip()
    if not s:
        return ""
    if re.match(r"^Q[1-4]/\d{4}$", s, re.IGNORECASE):
        return "quý"
    if re.match(r"^H[12]/\d{4}$", s, re.IGNORECASE):
        return "nửa năm"
    if re.match(r"^(?:0[1-9]|1[0-2])/\d{4}$", s):
        return "tháng"
    if re.match(r"^\d{4}$", s):
        return "năm"
    return "khác"


def _end_date_from_period_label(label: str) -> Optional[date]:
    s = (label or "").strip()
    if not s:
        return None
    m_q = re.match(r"^Q([1-4])/(\d{4})$", s, re.IGNORECASE)
    if m_q:
        q = int(m_q.group(1))
        yr = int(m_q.group(2))
        em = q * 3
        return date(yr, em, calendar.monthrange(yr, em)[1])
    m_h = re.match(r"^H([12])/(\d{4})$", s, re.IGNORECASE)
    if m_h:
        h = int(m_h.group(1))
        yr = int(m_h.group(2))
        return date(yr, 6, 30) if h == 1 else date(yr, 12, 31)
    m_m = re.match(r"^(0[1-9]|1[0-2])/(\d{4})$", s)
    if m_m:
        mm = int(m_m.group(1))
        yr = int(m_m.group(2))
        return date(yr, mm, calendar.monthrange(yr, mm)[1])
    m_y = re.match(r"^(\d{4})$", s)
    if m_y:
        return date(int(m_y.group(1)), 12, 31)
    return None


def _resolve_period(ev: Evidence, ref: date) -> tuple[str, Optional[date]]:
    """Return (data_period, data_period_end_date), recomputing via detect_data_period if empty."""
    lbl = (ev.data_period or "").strip()
    end_dt = parse_published_date(ev.data_period_end) if ev.data_period_end else None
    if not lbl:
        lbl, end_dt = detect_data_period(ev.quote or "", ref=ref)
    elif end_dt is None:
        end_dt = _end_date_from_period_label(lbl)
        if end_dt is None:
            _, end_dt = detect_data_period(ev.quote or "", ref=ref)
    return lbl, end_dt


def check_pair(
    status: str,
    old_ev: Evidence,
    old_src: Optional[Source],
    new_ev: Evidence,
    new_src: Optional[Source],
    ref: date,
) -> list[str]:
    """Check a single (old_ev, new_ev) pair under rules P, T, Đ, K. Empty list means valid."""
    if status not in ("XÁC NHẬN", "CẬP NHẬT", "MÂU THUẪN"):
        return []

    reasons: list[str] = []

    # Rule P: Scope category (game vs non-specific app market)
    old_scope = scope_category(
        old_ev.quote,
        old_src.title if old_src else "",
        old_src.url if old_src else "",
    )
    new_scope = scope_category(
        new_ev.quote,
        new_src.title if new_src else "",
        new_src.url if new_src else "",
    )
    if old_scope != new_scope:
        reasons.append(f"khác phạm vi ({old_scope} ↔ {new_scope})")

    # Rule T: Region / market tags intersection when both sides specify regions
    old_regs = region_tags(old_ev.quote, old_src.title if old_src else "")
    new_regs = region_tags(new_ev.quote, new_src.title if new_src else "")
    if old_regs and new_regs and not (old_regs & new_regs):
        reasons.append(
            f"khác thị trường ({'/'.join(sorted(old_regs))} ↔ {'/'.join(sorted(new_regs))})"
        )

    # Rule Đ: Figures & units
    old_fig = has_figure(old_ev.quote)
    new_fig = has_figure(new_ev.quote)
    old_units = unit_kinds(old_ev.quote)
    new_units = unit_kinds(new_ev.quote)

    if status in ("CẬP NHẬT", "MÂU THUẪN") and (not old_fig or not new_fig):
        reasons.append("một bên không có số liệu để so")
    elif old_fig and new_fig and not (old_units & new_units):
        old_u_str = "/".join(sorted(old_units)) or "?"
        new_u_str = "/".join(sorted(new_units)) or "?"
        reasons.append(f"khác đơn vị ({old_u_str} ↔ {new_u_str})")

    # Rule K: Data period checks for CẬP NHẬT and MÂU THUẪN
    if status in ("CẬP NHẬT", "MÂU THUẪN"):
        old_p, old_end = _resolve_period(old_ev, ref)
        new_p, new_end = _resolve_period(new_ev, ref)
        if not old_p or not new_p:
            reasons.append(
                f"không xác định được kỳ số liệu ({old_p or '?'} ↔ {new_p or '?'})"
            )
        else:
            old_gran = period_granularity(old_p)
            new_gran = period_granularity(new_p)
            if old_gran != new_gran:
                reasons.append(f"khác loại kỳ ({old_p} ↔ {new_p})")
            elif status == "CẬP NHẬT":
                if (
                    old_end is not None
                    and new_end is not None
                    and new_end <= old_end
                ) or new_p == old_p:
                    reasons.append(
                        f"kỳ mới không mới hơn kỳ cũ ({old_p} ↔ {new_p})"
                    )
            elif status == "MÂU THUẪN":
                if old_p != new_p:
                    reasons.append(
                        f"khác kỳ ({old_p} ↔ {new_p}), không phải mâu thuẫn cùng kỳ"
                    )

    return reasons


def guard_comparison(
    cmp: RefreshComparison,
    old_ev: Optional[Evidence],
    old_src: Optional[Source],
    new_ev_map: dict[str, Evidence],
    new_src_map: dict[str, Source],
    ref: date,
) -> RefreshComparison:
    """Validate and optionally downgrade a RefreshComparison. Never upgrades status or adds IDs."""
    orig_llm_status = cmp.llm_status or cmp.status
    current_status: ComparisonStatus = cmp.status

    if current_status not in ("XÁC NHẬN", "CẬP NHẬT", "MÂU THUẪN") or old_ev is None:
        return cmp.model_copy(update={"llm_status": orig_llm_status})

    if not cmp.new_evidence_ids:
        return cmp.model_copy(
            update={
                "llm_status": orig_llm_status,
                "status": "KHÔNG TƯƠNG ĐƯƠNG",
            }
        )

    passed_ids: list[str] = []
    notes: list[str] = []

    old_p, old_end = _resolve_period(old_ev, ref)

    for neid in cmp.new_evidence_ids:
        nev = new_ev_map.get(neid)
        if nev is None:
            notes.append(f"{neid}: không tìm thấy bằng chứng mới")
            continue
        nsrc = new_src_map.get(nev.source_id)
        pair_reasons = check_pair(
            status=current_status,
            old_ev=old_ev,
            old_src=old_src,
            new_ev=nev,
            new_src=nsrc,
            ref=ref,
        )
        if pair_reasons:
            notes.append(f"{neid}: {'; '.join(pair_reasons)}")
        else:
            passed_ids.append(neid)
            if current_status == "XÁC NHẬN":
                new_p, new_end = _resolve_period(nev, ref)
                if old_p and new_p:
                    if (
                        old_end is not None
                        and new_end is not None
                        and new_end <= old_end
                    ) or new_p == old_p:
                        notes.append(
                            f"{neid}: nhắc lại số liệu {new_p}, không phải dữ liệu mới hơn"
                        )

    if passed_ids:
        return cmp.model_copy(
            update={
                "llm_status": orig_llm_status,
                "status": current_status,
                "new_evidence_ids": passed_ids,
                "guard_notes": notes,
            }
        )

    return cmp.model_copy(
        update={
            "llm_status": orig_llm_status,
            "status": "KHÔNG TƯƠNG ĐƯƠNG",
            "new_evidence_ids": list(cmp.new_evidence_ids),
            "guard_notes": notes,
        }
    )
