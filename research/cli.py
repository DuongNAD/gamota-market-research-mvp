"""Command-line interface (`python -m research.cli "<câu hỏi>"`) for running the Gamota market research pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from research.pipeline import render_report_markdown, run


def main() -> int:
    # Ensure UTF-8 console output on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Gamota Game Market Research CLI (`python -m research.cli \"<câu hỏi>\"`)"
    )
    parser.add_argument("question", type=str, help="Câu hỏi nghiên cứu thị trường game")
    parser.add_argument(
        "--out-json",
        type=str,
        default="",
        help="Đường dẫn lưu file JSON output (tùy chọn)",
    )
    parser.add_argument(
        "--out-md",
        type=str,
        default="",
        help="Đường dẫn lưu file Markdown output (tùy chọn)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Tắt disk cache để chạy mới hoàn toàn",
    )
    args = parser.parse_args()

    def _cli_progress(step: str, detail: str) -> None:
        print(f">> {step}: {detail}", file=sys.stderr, flush=True)

    report = run(
        question=args.question,
        progress_callback=_cli_progress,
        use_cache=not args.no_cache,
    )

    md_text = render_report_markdown(report)
    print("\n" + "=" * 80)
    print(md_text)
    print("=" * 80)

    if args.out_json:
        out_json_path = Path(args.out_json)
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        out_json_path.write_text(
            json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n[Đã lưu JSON tại: {out_json_path}]", file=sys.stderr)

    if args.out_md:
        out_md_path = Path(args.out_md)
        out_md_path.parent.mkdir(parents=True, exist_ok=True)
        out_md_path.write_text(md_text, encoding="utf-8")
        print(f"[Đã lưu Markdown tại: {out_md_path}]", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
