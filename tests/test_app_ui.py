"""Automated UI test for Streamlit app.py using streamlit.testing.v1.AppTest."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_app_renders_cached_runs_and_metrics() -> None:
    app_path = Path(__file__).resolve().parent.parent / "app.py"
    at = AppTest.from_file(app_path).run(timeout=20)
    assert len(at.exception) == 0, f"App raised exceptions: {at.exception}"
    assert len(at.title) == 1
    assert "Gamota" in at.title[0].value

    # Verify 4 self-check quality metric cards are displayed
    metrics = [(m.label, m.value) for m in at.metric]
    assert len(metrics) == 4
    assert any("100.0%" in val for _lbl, val in metrics)

    # Verify markdown body contains verified insights table and #:~:text= links
    all_md = "\n".join(m.value for m in at.markdown)
    assert "## 2. Bảng nhận định có căn cứ (Verified Insights)" in all_md
    assert "#:~:text=" in all_md
    assert "## 5. Danh sách nguồn thông tin (Source Grading)" in all_md
