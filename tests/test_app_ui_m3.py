"""Mission 3 UI test using streamlit.testing.v1.AppTest (BRIEF_M3 6.2)."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_shows_recency_banner_tab_and_section_7() -> None:
    """Verify M3 recency banner, tab '3. Độ mới & Ảnh hưởng (A2)', Section 7 in Markdown, and 4 metrics."""
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    at = AppTest.from_file(app_path).run(timeout=20)
    assert len(at.exception) == 0, f"App raised exceptions: {at.exception}"

    # Still exactly 1 title and 4 metrics (invariant 4.1)
    assert len(at.title) == 1
    assert len(at.metric) == 4
    metrics = [(m.label, m.value) for m in at.metric]
    assert any("100.0%" in val for _lbl, val in metrics)

    # Check banner (warning/info/success) contains "Độ mới dữ liệu, mức ảnh hưởng"
    banners = (
        [w.value for w in at.warning]
        + [i.value for i in at.info]
        + [s.value for s in at.success]
    )
    assert any("Độ mới dữ liệu, mức ảnh hưởng" in b for b in banners), (
        f"Expected recency banner, got: {banners}"
    )

    # Check tab "3. Độ mới & Ảnh hưởng (A2)" exists
    tab_labels = [t.label for t in at.tabs]
    assert any("Độ mới & Ảnh hưởng" in lbl for lbl in tab_labels), (
        f"Expected tab 'Độ mới & Ảnh hưởng', got: {tab_labels}"
    )

    # Check Markdown output contains Section 7
    all_md = "\n".join(m.value for m in at.markdown)
    assert "## 7. Độ mới của dữ liệu & Ảnh hưởng tới độ tin cậy (Change Request A2)" in all_md
