"""Date detection, precision/range calculation, and quote data-period extraction (BRIEF_M3 4.3 & 4.4)."""

from __future__ import annotations

import calendar
from datetime import date
import math
import re
from typing import Optional

from research.grade import parse_published_date
from research.schemas import DatePrecision

MONTHS_MAP: dict[str, int] = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

DATE_METHOD_LABELS: dict[str, str] = {
    "url_date": "ngày trong đường dẫn URL",
    "url_month": "tháng/năm trong đường dẫn URL",
    "text_date": "ngày ghi trong tiêu đề/đầu bài viết",
    "month_year": "tháng/năm trong URL hoặc tiêu đề",
    "quarter": "suy từ quý ghi trong URL/tiêu đề",
    "year_only": "chỉ có năm trong URL/tiêu đề — ước tính sai số ±6 tháng",
    "search_metadata": "metadata từ công cụ tìm kiếm",
    "html_metadata": "metadata của trang",
    "legacy_url_date": "ngày trong đường dẫn URL",
    "legacy_url_month": "tháng/năm trong đường dẫn URL",
    "legacy_text_date": "ngày ghi trong tiêu đề/đầu bài viết",
    "legacy_month_year": "tháng/năm trong URL hoặc tiêu đề",
    "legacy_quarter": "suy từ quý ghi trong URL/tiêu đề",
    "legacy_year_only": "chỉ có năm trong URL/tiêu đề — ước tính sai số ±6 tháng",
    "legacy_metadata": "metadata — báo cáo cũ không lưu chi tiết",
    "user_override": "giả định do người dùng nhập",
    "unknown": "không xác định được",
}


def add_months(d: date, n: int) -> date:
    """Add `n` calendar months to `d`, clamping day to the end of the target month."""
    total_months = (d.year * 12 + (d.month - 1)) + n
    new_year = total_months // 12
    new_month = (total_months % 12) + 1
    max_day = calendar.monthrange(new_year, new_month)[1]
    return date(new_year, new_month, min(d.day, max_day))


def detect_date_with_method(
    url: str, text: str, title: str = ""
) -> tuple[Optional[str], str]:
    """Detect fallback publication date and the detection method code (exact rule order of _extract_date_fallback)."""
    url = url or ""
    text = text or ""
    title = title or ""

    # 1. Check URL for /YYYY/MM/DD/ or /YYYY-MM-DD
    m_url_full = re.search(
        r"/(202[0-6])[/-](0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])", url
    )
    if m_url_full:
        return (
            f"{m_url_full.group(1)}-{m_url_full.group(2)}-{m_url_full.group(3)}",
            "url_date",
        )
    m_url_month = re.search(r"/(202[0-6])/(0[1-9]|1[0-2])(?:/|$)", url)
    if m_url_month:
        return f"{m_url_month.group(1)}-{m_url_month.group(2)}", "url_month"

    # 2. Check text header for ISO date YYYY-MM-DD
    head = f"{title}\n{text[:1500]}"
    m_iso = re.search(r"\b(202[0-6])-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b", head)
    if m_iso:
        return f"{m_iso.group(1)}-{m_iso.group(2)}-{m_iso.group(3)}", "text_date"

    # 3. Check English Month DD, YYYY in header/title
    m_en = re.search(
        r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\s+(\d{1,2}),?\s+(202[0-6])\b",
        head,
        re.IGNORECASE,
    )
    if m_en:
        mm_num = MONTHS_MAP.get(m_en.group(1).lower(), 6)
        dd = int(m_en.group(2))
        yyyy = m_en.group(3)
        return f"{yyyy}-{mm_num:02d}-{dd:02d}", "text_date"

    # 4. Check Month YYYY in URL or title/header (e.g. "september-2026", "September 2026")
    combined_slug = f"{url} {title} {head[:600]}"
    m_month_yr = re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)"
        r"[\s\-_/]+(202[0-6])\b",
        combined_slug,
        re.IGNORECASE,
    )
    if m_month_yr:
        mm_num = MONTHS_MAP.get(m_month_yr.group(1).lower(), 6)
        return f"{m_month_yr.group(2)}-{mm_num:02d}", "month_year"

    # 5. Check Quarter YYYY in URL or title (e.g. "q1-2026", "Q3 2025")
    q_map = {"1": "03", "2": "06", "3": "09", "4": "12"}
    m_q_yr = re.search(
        r"\bq([1-4])[\s\-_/]+(202[0-6])\b", combined_slug, re.IGNORECASE
    )
    if m_q_yr:
        return f"{m_q_yr.group(2)}-{q_map[m_q_yr.group(1)]}", "quarter"

    # 6. Check explicit report year in URL slug or title (e.g. "-2025", "2026-report", "(2025)")
    m_url_yr = re.search(r"(?:[\-_/]|report[\-_/]?)(202[2-6])(?:[\-_/]|$)", url.lower())
    if m_url_yr:
        return f"{m_url_yr.group(1)}-06", "year_only"
    m_title_yr = re.search(r"\b(202[2-6])\b", title)
    if m_title_yr:
        return f"{m_title_yr.group(1)}-06", "year_only"

    return None, "unknown"


def infer_date_method(
    url: str,
    text: str,
    title: str,
    published_date: Optional[str],
    search_date: Optional[str] = None,
) -> str:
    """Infer how `published_date` was obtained during retrieval."""
    if not published_date or not str(published_date).strip():
        return "unknown"
    pub = str(published_date).strip()
    if search_date and str(search_date).strip() == pub:
        return "search_metadata"
    fb_date, fb_method = detect_date_with_method(url, text, title)
    if fb_date == pub:
        return fb_method
    return "html_metadata"


def infer_date_method_legacy(
    url: str, title: str, published_date: Optional[str]
) -> str:
    """Infer date detection method for legacy M2 reports that did not store `date_method`."""
    if not published_date or not str(published_date).strip():
        return "unknown"
    pub = str(published_date).strip()
    fb_date, fb_method = detect_date_with_method(url, "", title)
    if fb_date == pub and fb_method != "unknown":
        return f"legacy_{fb_method}"
    return "legacy_metadata"


def precision_of(method: str, published_date: Optional[str]) -> DatePrecision:
    """Return DatePrecision ('day', 'month', 'quarter', 'year', 'unknown') for a method and date string."""
    if not published_date or not str(published_date).strip():
        return "unknown"
    m = (method or "").strip()
    if m == "unknown":
        return "unknown"
    base = m[7:] if m.startswith("legacy_") else m
    if base in ("url_date", "text_date", "user_override"):
        return "day"
    if base in ("url_month", "month_year"):
        return "month"
    if base == "quarter":
        return "quarter"
    if base == "year_only":
        return "year"

    s = str(published_date).strip()
    if re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}", s):
        return "day"
    if re.match(r"^\d{4}[-/]\d{2}$", s):
        return "month"
    if re.match(r"^\d{4}$", s):
        return "year"
    parsed = parse_published_date(s)
    if parsed is not None:
        return "day"
    return "unknown"


def date_range(
    published_date: Optional[str], precision: DatePrecision
) -> Optional[tuple[date, date]]:
    """Return (range_start, range_end) possible publication dates given `published_date` and `precision`."""
    if not published_date or precision == "unknown":
        return None
    parsed = parse_published_date(published_date)
    if parsed is None:
        return None
    if precision == "day":
        return (parsed, parsed)
    if precision == "month":
        last_day = calendar.monthrange(parsed.year, parsed.month)[1]
        return (date(parsed.year, parsed.month, 1), date(parsed.year, parsed.month, last_day))
    if precision == "quarter":
        q_idx = (parsed.month - 1) // 3
        start_m = q_idx * 3 + 1
        end_m = start_m + 2
        last_day = calendar.monthrange(parsed.year, end_m)[1]
        return (date(parsed.year, start_m, 1), date(parsed.year, end_m, last_day))
    if precision == "year":
        return (date(parsed.year, 1, 1), date(parsed.year, 12, 31))
    return None


def format_date_display(
    published_date: Optional[str], precision: DatePrecision
) -> str:
    """Format publication date according to its true precision for Vietnamese UI/Markdown."""
    if not published_date or precision == "unknown":
        return "Không rõ ngày"
    parsed = parse_published_date(published_date)
    if parsed is None:
        return "Không rõ ngày"
    if precision == "day":
        return f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year:04d}"
    if precision == "month":
        return f"{parsed.month:02d}/{parsed.year:04d}"
    if precision == "quarter":
        q = (parsed.month - 1) // 3 + 1
        return f"Q{q}/{parsed.year:04d}"
    if precision == "year":
        return f"{parsed.year:04d} (chỉ biết năm)"
    return "Không rõ ngày"


def compute_age_metrics(
    published_date: Optional[str],
    precision: DatePrecision,
    reference_date: date,
    alert_months: int = 18,
) -> tuple[Optional[float], Optional[float], Optional[float], str, bool, bool]:
    """Return (age_months, age_months_min, age_months_max, age_display, older_than_alert, possibly_older_than_alert)."""
    parsed = parse_published_date(published_date)
    rng = date_range(published_date, precision)
    if parsed is None or rng is None or precision == "unknown":
        return None, None, None, "không rõ", False, True

    r_start, r_end = rng
    age_months = round(max(0.0, (reference_date - parsed).days / 30.4375), 1)
    age_min = round(max(0.0, (reference_date - r_end).days / 30.4375), 1)
    age_max = round(max(0.0, (reference_date - r_start).days / 30.4375), 1)

    older_than_alert = add_months(r_end, alert_months) < reference_date
    possibly_older_than_alert = add_months(r_start, alert_months) < reference_date

    if precision in ("year", "quarter"):
        min_disp = max(0, math.ceil((reference_date - r_end).days / 30.4375))
        max_disp = max(0, math.ceil((reference_date - r_start).days / 30.4375))
        age_display = f"{min_disp}–{max_disp} tháng"
    else:
        age_display = f"~{round(age_months)} tháng"

    return (
        age_months,
        age_min,
        age_max,
        age_display,
        older_than_alert,
        possibly_older_than_alert,
    )


def _normalize_two_digit_year(y_str: str) -> int:
    y = int(y_str)
    if y < 100:
        return 2000 + y
    return y


def extract_all_data_periods(
    text: str,
    ref: date,
    publication_bound: Optional[date] = None,
) -> list[tuple[str, date, date]]:
    """Extract all valid (label, start_date, end_date) periods mentioned in `text`."""
    if not text or not text.strip():
        return []

    raw_candidates: list[tuple[str, date, date, int]] = []
    consumed_spans: list[tuple[int, int]] = []

    def _overlaps(s: int, e: int) -> bool:
        return any(not (e <= cs or s >= ce) for cs, ce in consumed_spans)

    # 1. Quarter patterns
    # 1a. Q1 2025, Q2-2024, Q1'25, Q1/2025
    for m in re.finditer(
        r"\bQ([1-4])(?:[\s\-/]+|(?:['’]))(20[12]\d|[12]\d)\b", text, re.IGNORECASE
    ):
        q = int(m.group(1))
        yr = _normalize_two_digit_year(m.group(2))
        sm = (q - 1) * 3 + 1
        em = sm + 2
        s_dt = date(yr, sm, 1)
        e_dt = date(yr, em, calendar.monthrange(yr, em)[1])
        raw_candidates.append((f"Q{q}/{yr}", s_dt, e_dt, 3))
        consumed_spans.append((m.start(), m.end()))

    # 1b. first/second/third/fourth quarter of 2025
    q_words = {
        "first": 1,
        "1st": 1,
        "second": 2,
        "2nd": 2,
        "third": 3,
        "3rd": 3,
        "fourth": 4,
        "4th": 4,
    }
    for m in re.finditer(
        r"\b(first|second|third|fourth|1st|2nd|3rd|4th)\s+quarter\s+(?:of\s+)?(20[12]\d)\b",
        text,
        re.IGNORECASE,
    ):
        q = q_words[m.group(1).lower()]
        yr = int(m.group(2))
        sm = (q - 1) * 3 + 1
        em = sm + 2
        s_dt = date(yr, sm, 1)
        e_dt = date(yr, em, calendar.monthrange(yr, em)[1])
        raw_candidates.append((f"Q{q}/{yr}", s_dt, e_dt, 3))
        consumed_spans.append((m.start(), m.end()))

    # 1c. quý 1/2025, quý I năm 2025
    q_vi = {"1": 1, "2": 2, "3": 3, "4": 4, "i": 1, "ii": 2, "iii": 3, "iv": 4}
    for m in re.finditer(
        r"\bquý\s*(1|2|3|4|iv|iii|ii|i)\b[\s\-/]*(?:năm\s*)?(20[12]\d)\b",
        text,
        re.IGNORECASE,
    ):
        q = q_vi[m.group(1).lower()]
        yr = int(m.group(2))
        sm = (q - 1) * 3 + 1
        em = sm + 2
        s_dt = date(yr, sm, 1)
        e_dt = date(yr, em, calendar.monthrange(yr, em)[1])
        raw_candidates.append((f"Q{q}/{yr}", s_dt, e_dt, 3))
        consumed_spans.append((m.start(), m.end()))

    # 2. Half-year patterns
    # 2a. H1 2024, H2-2025, H1/2024, 1H 2024
    for m in re.finditer(
        r"\bH([12])(?:[\s\-/]+|(?:['’]))(20[12]\d|[12]\d)\b", text, re.IGNORECASE
    ):
        h = int(m.group(1))
        yr = _normalize_two_digit_year(m.group(2))
        s_dt = date(yr, 1, 1) if h == 1 else date(yr, 7, 1)
        e_dt = date(yr, 6, 30) if h == 1 else date(yr, 12, 31)
        raw_candidates.append((f"H{h}/{yr}", s_dt, e_dt, 2))
        consumed_spans.append((m.start(), m.end()))

    for m in re.finditer(r"\b([12])H[\s\-/]*(20[12]\d)\b", text, re.IGNORECASE):
        h = int(m.group(1))
        yr = int(m.group(2))
        s_dt = date(yr, 1, 1) if h == 1 else date(yr, 7, 1)
        e_dt = date(yr, 6, 30) if h == 1 else date(yr, 12, 31)
        raw_candidates.append((f"H{h}/{yr}", s_dt, e_dt, 2))
        consumed_spans.append((m.start(), m.end()))

    # 2b. first/second half of 2024
    for m in re.finditer(
        r"\b(first|second|1st|2nd)\s+half\s+(?:of\s+)?(20[12]\d)\b",
        text,
        re.IGNORECASE,
    ):
        h = 1 if m.group(1).lower() in ("first", "1st") else 2
        yr = int(m.group(2))
        s_dt = date(yr, 1, 1) if h == 1 else date(yr, 7, 1)
        e_dt = date(yr, 6, 30) if h == 1 else date(yr, 12, 31)
        raw_candidates.append((f"H{h}/{yr}", s_dt, e_dt, 2))
        consumed_spans.append((m.start(), m.end()))

    # 2c. nửa đầu năm 2024, 6 tháng đầu năm 2024
    for m in re.finditer(
        r"\b(?:nửa\s+(đầu|cuối)|(?:6|sáu)\s+tháng\s+(đầu|cuối))\s+(?:năm\s+)?(20[12]\d)\b",
        text,
        re.IGNORECASE,
    ):
        part = (m.group(1) or m.group(2) or "đầu").lower()
        h = 1 if part == "đầu" else 2
        yr = int(m.group(3))
        s_dt = date(yr, 1, 1) if h == 1 else date(yr, 7, 1)
        e_dt = date(yr, 6, 30) if h == 1 else date(yr, 12, 31)
        raw_candidates.append((f"H{h}/{yr}", s_dt, e_dt, 2))
        consumed_spans.append((m.start(), m.end()))

    # 3. Month patterns
    month_names_pat = (
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
    )
    # 3a. English Month range: "January to August 2024" -> take ending month
    for m in re.finditer(
        rf"\b({month_names_pat})\.?\s*(?:to|through|[\-–—])\s*({month_names_pat})\.?\s*,?\s+(20[12]\d)\b",
        text,
        re.IGNORECASE,
    ):
        m2 = MONTHS_MAP[m.group(2).lower().rstrip(".")]
        yr = int(m.group(3))
        s_dt = date(yr, m2, 1)
        e_dt = date(yr, m2, calendar.monthrange(yr, m2)[1])
        raw_candidates.append((f"{m2:02d}/{yr}", s_dt, e_dt, 4))
        consumed_spans.append((m.start(), m.end()))

    # 3b. English single Month YYYY (skip if followed by DD, YYYY which is a full date or already consumed)
    for m in re.finditer(
        rf"\b({month_names_pat})\.?\s*,?\s+(?:of\s+)?(20[12]\d)\b",
        text,
        re.IGNORECASE,
    ):
        if _overlaps(m.start(), m.end()):
            continue
        m_num = MONTHS_MAP[m.group(1).lower().rstrip(".")]
        yr = int(m.group(2))
        s_dt = date(yr, m_num, 1)
        e_dt = date(yr, m_num, calendar.monthrange(yr, m_num)[1])
        raw_candidates.append((f"{m_num:02d}/{yr}", s_dt, e_dt, 4))
        consumed_spans.append((m.start(), m.end()))

    # 3c. Vietnamese tháng M/YYYY, tháng M năm YYYY
    for m in re.finditer(
        r"\btháng\s*(0?[1-9]|1[0-2])(?:[\s\-/]+|\s+năm\s+)(20[12]\d)\b",
        text,
        re.IGNORECASE,
    ):
        if _overlaps(m.start(), m.end()):
            continue
        m_num = int(m.group(1))
        yr = int(m.group(2))
        s_dt = date(yr, m_num, 1)
        e_dt = date(yr, m_num, calendar.monthrange(yr, m_num)[1])
        raw_candidates.append((f"{m_num:02d}/{yr}", s_dt, e_dt, 4))
        consumed_spans.append((m.start(), m.end()))

    # 4. Year range: 2022–2027, 2022 - 2025
    for m in re.finditer(
        r"\b(20[12]\d)\s*[\-–—]\s*(20[123]\d)\b",
        text,
    ):
        if _overlaps(m.start(), m.end()):
            continue
        y1 = int(m.group(1))
        y2 = int(m.group(2))
        consumed_spans.append((m.start(), m.end()))
        if y2 < y1:
            continue
        # If ending year > ref.year, it is a forecast range -> drop the entire range
        if y2 > ref.year:
            continue
        s_dt = date(y2, 1, 1)
        e_dt = date(y2, 12, 31)
        raw_candidates.append((f"{y2}", s_dt, e_dt, 1))

    # 5. Standalone year: 2024, năm 2024, in 2024, FY2025, năm tài chính 2025
    skip_prefix_re = re.compile(
        r"(?:\bsince|\bby|\bforecast|kể\s+từ|từ\s+năm|đến\s+năm|dự\s+báo)\s*(?:năm\s*)?$",
        re.IGNORECASE,
    )
    for m in re.finditer(r"\b(?:FY\s*)?(20[123]\d)\b", text, re.IGNORECASE):
        if _overlaps(m.start(), m.end()):
            continue
        # Check 12 characters before the match (or before preceding 'năm ')
        pre_slice = text[max(0, m.start() - 12) : m.start()]
        if skip_prefix_re.search(pre_slice):
            continue
        yr = int(m.group(1))
        s_dt = date(yr, 1, 1)
        e_dt = date(yr, 12, 31)
        raw_candidates.append((f"{yr}", s_dt, e_dt, 1))

    # Filter out future periods (> ref) and forecast periods (> publication_bound when day precision)
    valid: list[tuple[str, date, date, int]] = []
    for label, s_dt, e_dt, prio in raw_candidates:
        if e_dt > ref:
            continue
        if publication_bound is not None and e_dt > publication_bound:
            continue
        valid.append((label, s_dt, e_dt, prio))

    # Sort by end_date ascending, then specificity priority ascending (so last element is newest & most specific)
    valid.sort(key=lambda x: (x[2], x[3]))
    return [(lbl, s_dt, e_dt) for lbl, s_dt, e_dt, _p in valid]


def detect_data_period(
    text: str,
    ref: date,
    publication_bound: Optional[date] = None,
) -> tuple[str, Optional[date]]:
    """Return the newest valid past data period (label, end_date) mentioned in `text`, or ('', None)."""
    periods = extract_all_data_periods(text, ref=ref, publication_bound=publication_bound)
    if not periods:
        return "", None
    lbl, _s_dt, e_dt = periods[-1]
    return lbl, e_dt
