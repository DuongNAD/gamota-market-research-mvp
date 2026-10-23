"""Unit tests for comparability guard and fallback model configuration (BRIEF_M3_FIX section 5.2)."""

from __future__ import annotations

from datetime import date
import pytest

from research.comparability import (
    check_pair,
    guard_comparison,
    has_figure,
    period_granularity,
    region_tags,
    scope_category,
    unit_kinds,
)
from research.llm import DEFAULT_MODELS, LLMClient
from research.schemas import Evidence, RefreshComparison, Source


def test_real_tc7_e2_e29_downgraded_for_scope_and_period():
    """Test #1 (Change request): Cặp thật TC7 E2 ↔ E29 (S1 vs S13): CẬP NHẬT → KHÔNG TƯƠNG ĐƯƠNG."""
    s1 = Source(
        id="S1",
        title="Sensor Tower Southeast Asia Mobile Game Market Insights 2025",
        url="https://sensortower.com/blog/southeast-asia-mobile-gaming-2025",
        domain="sensortower.com",
        published_date="2025-05",
        tier="A",
    )
    e2 = Evidence(
        id="E2",
        source_id="S1",
        claim="Tại Đông Nam Á, doanh thu mua hàng trong ứng dụng (IAP) đạt 625 triệu USD trong quý 1 năm 2025.",
        quote="While SEA currently ranks seventh globally in in-app purchase (IAP) revenue at $625 million in Q1 2025, this figure signals significant untapped monetization potential.",
        verified=True,
        match_score=100.0,
        data_period="Q1/2025",
        data_period_end="2025-03-31",
    )
    s13 = Source(
        id="S13",
        title="State of Mobile Southeast Asia 2026 - sensortower.com",
        url="https://sensortower.com/blog/state-of-mobile-southeast-asia-2026",
        domain="sensortower.com",
        published_date="2026-06",
        tier="A",
    )
    e29 = Evidence(
        id="E29",
        source_id="S13",
        claim="Doanh thu IAP tại Đông Nam Á đạt 5,3 tỷ USD.",
        quote="In-app purchase revenue reached $5.3 billion, up 16.3% YoY, marking a new high for the market.",
        verified=True,
        match_score=100.0,
        data_period="",
        data_period_end=None,
    )

    cmp = RefreshComparison(
        old_evidence_id="E2",
        new_evidence_ids=["E29"],
        status="CẬP NHẬT",
        explanation="Cập nhật doanh thu IAP từ 625 triệu USD lên 5,3 tỷ USD.",
    )
    guarded = guard_comparison(
        cmp=cmp,
        old_ev=e2,
        old_src=s1,
        new_ev_map={"E29": e29},
        new_src_map={"S13": s13},
        ref=date(2026, 10, 23),
    )

    assert guarded.llm_status == "CẬP NHẬT"
    assert guarded.status == "KHÔNG TƯƠNG ĐƯƠNG"
    assert guarded.new_evidence_ids == ["E29"]
    joined_notes = "; ".join(guarded.guard_notes)
    assert "khác phạm vi" in joined_notes
    assert "không xác định được kỳ" in joined_notes


def test_real_tc10_e16_e23_downgraded_for_scope_and_granularity():
    """Test #2 (Change request): Cặp thật TC10 E16 ↔ E23: CẬP NHẬT → KHÔNG TƯƠNG ĐƯƠNG vì khác phạm vi và khác loại kỳ."""
    s10 = Source(
        id="S10",
        title="Southeast Asia Mobile Gaming Statistics 2026 - Icon Era",
        url="https://icon-era.com/statistics/southeast-asia-mobile-gaming",
        domain="icon-era.com",
        published_date="2026-06",
        tier="C",
    )
    e16 = Evidence(
        id="E16",
        source_id="S10",
        claim="Người chơi Đông Nam Á tải 1,93 tỷ lượt game mobile trong Q1/2025.",
        quote="Southeast Asian players downloaded 1.93 billion mobile games in Q1 2025 and spent $625 million through app stores. Sensor Tower ranks the region second worldwide on downloads and seventh on revenue.",
        verified=True,
        match_score=100.0,
        data_period="Q1/2025",
        data_period_end="2025-03-31",
    )
    s13 = Source(
        id="S13",
        title="State of Mobile Southeast Asia 2026 - sensortower.com",
        url="https://sensortower.com/blog/state-of-mobile-southeast-asia-2026",
        domain="sensortower.com",
        published_date="2026-06",
        tier="A",
    )
    e23 = Evidence(
        id="E23",
        source_id="S13",
        claim="Đông Nam Á đạt 18,1 tỷ lượt tải năm 2025.",
        quote="Southeast Asia remains a leading mobile-first market, with 18.1 billion downloads in 2025. Growth is increasingly driven by engagement and monetization, with IAP revenue rising 16.3% YoY.",
        verified=True,
        match_score=100.0,
        data_period="2025",
        data_period_end="2025-12-31",
    )

    cmp = RefreshComparison(
        old_evidence_id="E16",
        new_evidence_ids=["E23"],
        status="CẬP NHẬT",
        explanation="Cập nhật lượt tải từ 1,93 tỷ Q1/2025 lên 18,1 tỷ năm 2025.",
    )
    guarded = guard_comparison(
        cmp=cmp,
        old_ev=e16,
        old_src=s10,
        new_ev_map={"E23": e23},
        new_src_map={"S13": s13},
        ref=date(2026, 10, 23),
    )

    assert guarded.llm_status == "CẬP NHẬT"
    assert guarded.status == "KHÔNG TƯƠNG ĐƯƠNG"
    joined_notes = "; ".join(guarded.guard_notes)
    assert "khác loại kỳ (Q1/2025 ↔ 2025)" in joined_notes
    assert "khác phạm vi" in joined_notes


def test_valid_update_same_scope_region_unit_and_newer_quarter_kept():
    """Test #3 (Edge case): Cập nhật hợp lệ (cùng game, cùng Indonesia, cùng USD, Q1/2025 → Q1/2026): giữ CẬP NHẬT."""
    s_old = Source(
        id="S1",
        title="Indonesia Mobile Gaming Report 2025",
        url="https://sensortower.com/blog/indonesia-mobile-gaming-2025",
        domain="sensortower.com",
        tier="A",
    )
    ev_old = Evidence(
        id="E1",
        source_id="S1",
        claim="Doanh thu game mobile Indonesia Q1/2025 đạt 95 triệu USD.",
        quote="Indonesia mobile game revenue reached $95 million in Q1 2025.",
        verified=True,
    )
    s_new = Source(
        id="S2",
        title="Indonesia Mobile Gaming Report 2026",
        url="https://sensortower.com/blog/indonesia-mobile-gaming-2026",
        domain="sensortower.com",
        tier="A",
    )
    ev_new = Evidence(
        id="E2",
        source_id="S2",
        claim="Doanh thu game mobile Indonesia Q1/2026 đạt 112 triệu USD.",
        quote="Indonesia mobile game revenue climbed to $112 million in Q1 2026.",
        verified=True,
    )

    cmp = RefreshComparison(
        old_evidence_id="E1",
        new_evidence_ids=["E2"],
        status="CẬP NHẬT",
        explanation="Q1/2025 đạt 95 triệu USD, Q1/2026 tăng lên 112 triệu USD.",
    )
    guarded = guard_comparison(
        cmp=cmp,
        old_ev=ev_old,
        old_src=s_old,
        new_ev_map={"E2": ev_new},
        new_src_map={"S2": s_new},
        ref=date(2026, 10, 23),
    )

    assert guarded.llm_status == "CẬP NHẬT"
    assert guarded.status == "CẬP NHẬT"
    assert guarded.new_evidence_ids == ["E2"]
    assert guarded.guard_notes == []


def test_mixed_new_evidences_keeps_valid_and_records_note_for_invalid():
    """Test #4 (Edge case): Một cặp có 2 bằng chứng mới, 1 đạt 1 không: giữ nhãn với id đạt, có ghi chú cho id bị loại."""
    s_old = Source(
        id="S1",
        title="Indonesia Mobile Gaming 2025",
        url="https://sensortower.com/indonesia-gaming-2025",
        domain="sensortower.com",
    )
    ev_old = Evidence(
        id="E1",
        source_id="S1",
        claim="Doanh thu game mobile Indonesia Q1/2025 đạt 95 triệu USD.",
        quote="Indonesia mobile game revenue reached $95 million in Q1 2025.",
        verified=True,
    )
    s_new = Source(
        id="S2",
        title="SEA Mobile Gaming 2026",
        url="https://sensortower.com/sea-gaming-2026",
        domain="sensortower.com",
    )
    ev_good = Evidence(
        id="E2",
        source_id="S2",
        claim="Doanh thu game mobile Indonesia Q1/2026 đạt 112 triệu USD.",
        quote="Indonesia mobile game revenue reached $112 million in Q1 2026.",
        verified=True,
    )
    ev_bad = Evidence(
        id="E3",
        source_id="S2",
        claim="Lượt tải game mobile Thái Lan năm 2025 đạt 500 triệu.",
        quote="Thailand mobile game downloads reached 500 million in 2025.",
        verified=True,
    )

    cmp = RefreshComparison(
        old_evidence_id="E1",
        new_evidence_ids=["E2", "E3"],
        status="CẬP NHẬT",
        explanation="Cập nhật doanh thu Q1/2026.",
    )
    guarded = guard_comparison(
        cmp=cmp,
        old_ev=ev_old,
        old_src=s_old,
        new_ev_map={"E2": ev_good, "E3": ev_bad},
        new_src_map={"S2": s_new},
        ref=date(2026, 10, 23),
    )

    assert guarded.status == "CẬP NHẬT"
    assert guarded.new_evidence_ids == ["E2"]
    assert len(guarded.guard_notes) == 1
    assert guarded.guard_notes[0].startswith("E3:")


@pytest.mark.parametrize(
    "initial_status,quote_new,expected_allowed_statuses",
    [
        (
            "KHÔNG TƯƠNG ĐƯƠNG",
            "Indonesia mobile game revenue reached $112 million in Q1 2026.",
            {"KHÔNG TƯƠNG ĐƯƠNG"},
        ),
        (
            "KHÔNG TÌM THẤY DỮ LIỆU MỚI",
            "Indonesia mobile game revenue reached $112 million in Q1 2026.",
            {"KHÔNG TÌM THẤY DỮ LIỆU MỚI"},
        ),
        (
            "XÁC NHẬN",
            "Indonesia mobile game revenue reached $112 million in Q1 2026.",
            {"XÁC NHẬN", "KHÔNG TƯƠNG ĐƯƠNG"},
        ),
        (
            "CẬP NHẬT",
            "Indonesia mobile game revenue reached $112 million in Q1 2026.",
            {"CẬP NHẬT", "KHÔNG TƯƠNG ĐƯƠNG"},
        ),
        (
            "MÂU THUẪN",
            "Indonesia mobile game revenue reached $80 million in Q1 2025.",
            {"MÂU THUẪN", "KHÔNG TƯƠNG ĐƯƠNG"},
        ),
    ],
)
def test_invariant_never_upgrades_status_or_adds_ids(
    initial_status, quote_new, expected_allowed_statuses
):
    """Test #5 (Regression): Bất biến không nâng nhãn: KTĐ, KTT giữ nguyên; XN không thành CN; không thêm id."""
    s_old = Source(
        id="S1",
        title="Indonesia Mobile Gaming 2025",
        url="https://sensortower.com/indonesia-gaming-2025",
        domain="sensortower.com",
    )
    ev_old = Evidence(
        id="E1",
        source_id="S1",
        claim="Doanh thu game mobile Indonesia Q1/2025 đạt 95 triệu USD.",
        quote="Indonesia mobile game revenue reached $95 million in Q1 2025.",
        verified=True,
    )
    s_new = Source(
        id="S2",
        title="Indonesia Mobile Gaming 2026",
        url="https://sensortower.com/indonesia-gaming-2026",
        domain="sensortower.com",
    )
    ev_new = Evidence(
        id="E2",
        source_id="S2",
        claim="Số liệu mới.",
        quote=quote_new,
        verified=True,
    )
    ev_extra = Evidence(
        id="E99",
        source_id="S2",
        claim="Bằng chứng ngoài.",
        quote=quote_new,
        verified=True,
    )

    cmp = RefreshComparison(
        old_evidence_id="E1",
        new_evidence_ids=["E2"],
        status=initial_status,
        explanation="Giải thích.",
    )
    guarded = guard_comparison(
        cmp=cmp,
        old_ev=ev_old,
        old_src=s_old,
        new_ev_map={"E2": ev_new, "E99": ev_extra},
        new_src_map={"S2": s_new},
        ref=date(2026, 10, 23),
    )

    assert guarded.llm_status == initial_status
    assert guarded.status in expected_allowed_statuses
    assert set(guarded.new_evidence_ids).issubset({"E2"})


def test_conflict_different_periods_2024_vs_2025_downgraded():
    """Test #6 (Edge case): MÂU THUẪN khác kỳ (2024 ↔ 2025) → KHÔNG TƯƠNG ĐƯƠNG."""
    s1 = Source(
        id="S1",
        title="Vietnam Gaming Report 2024",
        url="https://newzoo.com/vn-gaming-2024",
        domain="newzoo.com",
    )
    e1 = Evidence(
        id="E1",
        source_id="S1",
        claim="Doanh thu game Việt Nam năm 2024 đạt 500 triệu USD.",
        quote="Vietnam mobile game revenue was $500 million in 2024.",
        verified=True,
    )
    s2 = Source(
        id="S2",
        title="Vietnam Gaming Report 2026",
        url="https://newzoo.com/vn-gaming-2026",
        domain="newzoo.com",
    )
    e2 = Evidence(
        id="E2",
        source_id="S2",
        claim="Doanh thu game Việt Nam năm 2025 đạt 825 triệu USD.",
        quote="Vietnam mobile game revenue reached $825 million in 2025.",
        verified=True,
    )

    cmp = RefreshComparison(
        old_evidence_id="E1",
        new_evidence_ids=["E2"],
        status="MÂU THUẪN",
        explanation="500 triệu USD vs 825 triệu USD.",
    )
    guarded = guard_comparison(
        cmp=cmp,
        old_ev=e1,
        old_src=s1,
        new_ev_map={"E2": e2},
        new_src_map={"S2": s2},
        ref=date(2026, 10, 23),
    )

    assert guarded.llm_status == "MÂU THUẪN"
    assert guarded.status == "KHÔNG TƯƠNG ĐƯƠNG"
    assert any("khác kỳ (2024 ↔ 2025)" in n for n in guarded.guard_notes)


def test_confirm_same_period_q1_2025_kept_with_repeat_note():
    """Test #7 (Edge case): XÁC NHẬN cùng kỳ Q1/2025: giữ XÁC NHẬN, có ghi chú 'nhắc lại'."""
    s1 = Source(
        id="S1",
        title="Sensor Tower SEA Mobile Gaming 2025",
        url="https://sensortower.com/sea-gaming-2025",
        domain="sensortower.com",
    )
    e3 = Evidence(
        id="E3",
        source_id="S1",
        claim="Indonesia đạt 870 triệu lượt tải game Q1/2025.",
        quote="Indonesia stands out as the leader in mobile game downloads, reaching 870 million in Q1 2025.",
        verified=True,
        data_period="Q1/2025",
        data_period_end="2025-03-31",
    )
    s17 = Source(
        id="S17",
        title="Indonesia Gaming Market 2026",
        url="https://digitalinasia.com/indonesia-gaming-market",
        domain="digitalinasia.com",
    )
    e31 = Evidence(
        id="E31",
        source_id="S17",
        claim="Indonesia đạt 870 triệu lượt tải game trong quý 1/2025.",
        quote="In the first quarter of 2025 the country pulled 870 million mobile game downloads.",
        verified=True,
        data_period="Q1/2025",
        data_period_end="2025-03-31",
    )

    cmp = RefreshComparison(
        old_evidence_id="E3",
        new_evidence_ids=["E31"],
        status="XÁC NHẬN",
        explanation="Xác nhận 870 triệu lượt tải Q1/2025.",
    )
    guarded = guard_comparison(
        cmp=cmp,
        old_ev=e3,
        old_src=s1,
        new_ev_map={"E31": e31},
        new_src_map={"S17": s17},
        ref=date(2026, 10, 23),
    )

    assert guarded.status == "XÁC NHẬN"
    assert guarded.new_evidence_ids == ["E31"]
    assert any("nhắc lại" in n and "Q1/2025" in n for n in guarded.guard_notes)


def test_openrouter_model_env_override_and_default_not_legacy_exp(monkeypatch):
    """Test #10 (Regression L5): OPENROUTER_MODEL ghi đè được model dự phòng; mặc định khác google/gemini-2.0-flash-exp:free."""
    assert DEFAULT_MODELS["openrouter"] != "google/gemini-2.0-flash-exp:free"

    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake_gemini_key")
    monkeypatch.setenv("GEMINI_API_KEYS", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake_or_key")
    monkeypatch.setenv("OPENROUTER_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")

    client = LLMClient(provider="gemini", model="gemini-3.8-flash", use_cache=False)

    def fail_gemini(system_prompt, user_prompt, model_name, api_key):
        raise RuntimeError("Simulated Gemini failure")

    captured_models: list[str] = []

    def fake_openai_compatible(base_url, api_key, model_name, system_prompt, user_prompt):
        captured_models.append(model_name)
        return '{"queries": ["test query 2026"]}'

    import research.llm as llm_mod

    monkeypatch.setattr(llm_mod.time, "sleep", lambda _s: None)
    monkeypatch.setattr(client, "_call_gemini", fail_gemini)
    monkeypatch.setattr(client, "_call_openai_compatible", fake_openai_compatible)

    out = client._raw_completion("sys", "usr")
    assert "test query 2026" in out
    assert captured_models == ["nvidia/nemotron-3-super-120b-a12b:free"]

    # Also verify default fallback when OPENROUTER_MODEL is empty
    captured_models.clear()
    monkeypatch.setenv("OPENROUTER_MODEL", "")
    client._raw_completion("sys", "usr")
    assert captured_models == [DEFAULT_MODELS["openrouter"]]
