"""Run raw-LLM baseline (single direct prompt without Retrieve/Verify/Score pipeline) on TC3 and TC4 for empirical comparison in TESTING.md."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

from pydantic import BaseModel, Field

from research.llm import LLMClient
from research.score import URL_REGEX

RESULTS_DIR = Path(__file__).resolve().parent / "results"


class RawLLMResponse(BaseModel):
    short_answer: str = Field(description="Câu trả lời trực tiếp cho câu hỏi nghiên cứu thị trường")
    key_claims: list[str] = Field(description="5 nhận định và con số chính")
    cited_urls_or_sources: list[str] = Field(
        description="Các nguồn hoặc URL mà mô hình tự trích dẫn từ trí nhớ"
    )
    self_rated_confidence: str = Field(
        description="Mức độ tự tin do LLM tự chấm (CAO / TRUNG BÌNH / THẤP)"
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    llm = LLMClient(use_cache=True)
    cases = [
        (
            "TC3",
            "Quy mô thị trường game mobile Việt Nam hiện nay là bao nhiêu?",
        ),
        (
            "TC4",
            "Doanh thu thể loại MMORPG mobile tại thị trường Campuchia năm 2025 là bao nhiêu?",
        ),
    ]

    output = []
    for cid, question in cases:
        res = llm.generate_structured(
            system_prompt=(
                "Bạn là chuyên viên nghiên cứu thị trường game. Hãy trả lời câu hỏi sau bằng tiếng Việt, "
                "đưa ra con số cụ thể, nguồn/URL tham khảo và tự đánh giá độ tin cậy (CAO / TRUNG BÌNH / THẤP)."
            ),
            user_prompt=question,
            response_model=RawLLMResponse,
            step_name=f"raw_baseline_{cid}",
        )
        all_text = " ".join([res.short_answer] + res.key_claims + res.cited_urls_or_sources)
        unverified_urls = URL_REGEX.findall(all_text)
        numbers = re.findall(
            r"\b\d+(?:[.,]\d+)?\s*(?:triệu|tỷ|million|billion|%|USD|\$)\b",
            all_text,
            re.IGNORECASE,
        )
        output.append(
            {
                "id": cid,
                "question": question,
                "raw_llm_output": res.model_dump(),
                "unverified_urls_count": len(unverified_urls),
                "unverified_numbers_count": len(numbers),
                "verified_quotes_count": 0,
            }
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "baseline_raw_llm.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved raw LLM baseline to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
