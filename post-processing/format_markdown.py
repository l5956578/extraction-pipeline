"""Legacy CLI — formats the active job deliverable Markdown in place.

Post-processing is integrated into ``run_pipeline.py --step merge``.
Prefer ``iterate_format.py --job <id>`` for day-to-day polish.

    python post-processing/format_markdown.py
    python post-processing/format_markdown.py --job cefr-companion-2020
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Legacy format CLI (prefer iterate_format.py)"
    )
    parser.add_argument(
        "--job",
        default=None,
        help="Job id under input|work|output/<job>/ (default: cefr-companion-2020)",
    )
    args = parser.parse_args()

    from pipeline.config import load_job

    ctx = load_job(args.job)
    from pipeline.post_process import run_post_process

    result = run_post_process()
    print(f"Job: {ctx.job_id}")
    print(f"Formatted {result['output_path']}")
    print(f"  {result['input_lines']} -> {result['output_lines']} lines")


if __name__ == "__main__":
    main()
