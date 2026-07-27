"""Legacy CLI — formats the active job deliverable Markdown in place.

Post-processing is integrated into ``run_pipeline.py --step merge``.
Prefer ``iterate_format.py --job <id>`` for day-to-day polish.

    python post-processing/format_markdown.py --job cefr-companion-2020
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(
        description="Legacy format CLI (prefer iterate_format.py)"
    )
    add_job_argument(parser)
    args = parser.parse_args()

    ctx = bootstrap_job(args.job, force_draft=args.force_draft)
    from pipeline.post_process import run_post_process

    result = run_post_process()
    print(f"Job: {ctx.job_id}")
    print(f"Formatted {result['output_path']}")
    print(f"  {result['input_lines']} -> {result['output_lines']} lines")


if __name__ == "__main__":
    main()
