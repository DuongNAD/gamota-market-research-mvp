"""Command-line interface (`python -m research.cli "<câu hỏi>"`) for running the Gamota market research pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from research.grade import parse_published_date
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
        "--reference-date",
        type=str,
        default="",
        help="Ngày tham chiếu YYYY-MM-DD (tùy chọn)",
    )
    parser.add_argument(
        "--refresh-old",
        action="store_true",
        help="Tự động chạy vòng làm mới nguồn then chốt cũ sau khi chạy pipeline",
    )
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
        "--save",
        type=str,
        default="",
        help="Tiền tố đường dẫn lưu cả .json và .md (tùy chọn)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Tắt disk cache để chạy mới hoàn toàn",
    )
    args = parser.parse_args()

    ref_date = None
    if args.reference_date:
        ref_date = parse_published_date(args.reference_date)
        if ref_date is None:
            raise ValueError(f"Ngày --reference-date không hợp lệ: {args.reference_date}")

    def _cli_progress(step: str, detail: str) -> None:
        print(f">> {step}: {detail}", file=sys.stderr, flush=True)

    report = run(
        question=args.question,
        progress_callback=_cli_progress,
        use_cache=not args.no_cache,
        reference_date=ref_date,
    )

    if args.refresh_old:
        from research.refresh import refresh_old_sources

        report = refresh_old_sources(
            report=report,
            reference_date=ref_date,
            use_cache=not args.no_cache,
            progress_callback=_cli_progress,
        )

    out_json = args.out_json or (f"{args.save}.json" if args.save else "")
    out_md = args.out_md or (f"{args.save}.md" if args.save else "")

    md_text = render_report_markdown(report)
    print("\n" + "=" * 80)
    print(md_text)
    print("=" * 80)

    if out_json:
        out_json_path = Path(out_json)
        out_json_path.parent.mkdir(parents=True, exist_ok=True)
        out_json_path.write_text(
            json.dumps(report.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n[Đã lưu JSON tại: {out_json_path}]", file=sys.stderr)

    if out_md:
        out_md_path = Path(out_md)
        out_md_path.parent.mkdir(parents=True, exist_ok=True)
        out_md_path.write_text(md_text, encoding="utf-8")
        print(f"[Đã lưu Markdown tại: {out_md_path}]", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
