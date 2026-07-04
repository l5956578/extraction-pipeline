"""Legacy CLI — formats final_output/CEFR_Companion_Volume.md in place.

Post-processing is integrated into ``run_pipeline.py --step merge``.
Use this only to re-run formatting without a full merge::

    python post-processing/format_markdown.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.post_process import run_post_process  # noqa: E402


def main() -> None:
    result = run_post_process()
    print(f"Formatted {result['output_path']}")
    print(f"  {result['input_lines']} -> {result['output_lines']} lines")


if __name__ == "__main__":
    main()