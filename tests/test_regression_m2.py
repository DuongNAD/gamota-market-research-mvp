"""Regression tests ensuring Mission 3 preserves Mission 2 behavior (BRIEF_M3 section 6.2)."""

from __future__ import annotations

from research.retrieve import _extract_date_fallback

# Golden table frozen in P0 BEFORE refactoring _extract_date_fallback (16 samples)
GOLDEN_EXTRACT_DATE_SAMPLES: list[tuple[str, str, str, str | None]] = [
    # 2 samples from tests/test_grade.py
    (
        "https://sensortower.com/blog/top-10-worldwide-mobile-games-by-revenue-in-september-2026",
        "Top 10 mobile games",
        "Top 10 Mobile Games September 2026",
        "2026-09",
    ),
    (
        "https://sensortower.com/blog/state-of-southeast-asia-mobile-gaming-2025",
        "SEA report body",
        "State of Southeast Asia Mobile Gaming 2025",
        "2025-06",
    ),
    # Real samples from eval/results/m2/TC1..TC6.json
    (
        "https://nextbiggames.com/2026/03/17/vietnam-mobile-games-market-825m-growth",
        "",
        "Vietnam Mobile Games Market $825M: 54M Players, Huge Growth ...",
        "2026-03-17",
    ),
    (
        "https://gamota.com/gamota-lab/gamota-launches-vietnam-mobile-gaming-industry-report-q1-2026",
        "",
        "Gamota ra mắt báo cáo Vietnam Mobile Gaming Industry Report Q1 2026",
        "2026-03",
    ),
    (
        "https://www.appsflyer.com/resources/reports/gaming-app-marketing-2024-report",
        "",
        "The 2024 state of gaming app marketing [Report] I AppsFlyer",
        "2024-06",
    ),
    (
        "https://www.appsflyer.com/resources/reports/app-marketing-monetization-report-2024",
        "",
        "The State of App Monetization - 2024 Edition - appsflyer.com",
        "2024-06",
    ),
    (
        "https://sensortower.com/state-of-mobile-games-in-sea-2025-report",
        "",
        "Southeast Asia: Mobile Game Market Insights 2025 Report",
        "2025-06",
    ),
    (
        "https://eog.gg/revenue",
        "",
        "Gacha Revenue August 2026: Top 100 Highest-Grossing Games",
        "2026-08",
    ),
    (
        "https://www.statista.com/topics/12574/mobile-gaming-in-indonesia",
        "",
        "Mobile gaming in Indonesia - statistics & facts | Statista",
        None,
    ),
    (
        "https://laodong.vn/cong-nghe/nganh-game-viet-nam-vuon-tam-khang-dinh-vi-the-lon-tren-the-gioi-1690320.ldo",
        "",
        "Ngành game Việt Nam vươn tầm, khẳng định vị thế lớn trên thế giới",
        None,
    ),
    (
        "https://newzoo.com/reports/global-games-market-report",
        "",
        "Newzoo's Global Games Market Report 2025",
        "2025-06",
    ),
    (
        "https://mytour.vn/vi/blog/bai-viet/bxh-doanh-thu-game-gacha-thang-9-mihoyo-co-cu-tro-lai-an-tuong-mot-sieu-pham-roi-tu-do-mytour.html",
        "",
        "Bảng xếp hạng doanh thu game Gacha tháng 9 - mytour.vn",
        None,
    ),
    # Additional samples covering URL month and text header ISO / English date patterns
    (
        "https://example.com/2025/04/mobile-games-sea",
        "Overview of SEA market",
        "SEA Mobile Games Overview",
        "2025-04",
    ),
    (
        "https://example.com/articles/market-update",
        "Published on May 3, 2026 by Research Team. Revenue grew strongly.",
        "Market Update",
        "2026-05-03",
    ),
    (
        "https://example.com/articles/vn-report",
        "Cập nhật ngày 2026-09-12: Doanh thu ngành game tiếp tục tăng.",
        "Báo cáo thị trường",
        "2026-09-12",
    ),
    (
        "https://example.com/blog/sea-trends",
        "Report covering Q3 2025 performance across Southeast Asia.",
        "SEA Q3 2025 Report",
        "2025-09",
    ),
]


def test_extract_date_fallback_golden_unchanged() -> None:
    for url, text, title, expected in GOLDEN_EXTRACT_DATE_SAMPLES:
        actual = _extract_date_fallback(url, text, title)
        assert actual == expected, f"Mismatch for ({url!r}, {title!r}): got {actual!r}, expected {expected!r}"
