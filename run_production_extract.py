#!/usr/bin/env python3
"""Full production extract → cleanup → merge → figures → postprocess (unbuffered logs)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _log(*args, **kwargs) -> None:
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def main() -> None:
    from pipeline.apply_figures import run_apply_figures
    from pipeline.cleanup import cleanup_all
    from pipeline.extract_chunk import extract_all_chunks
    from pipeline.merge_output import run_merge
    from pipeline.post_process import run_post_process

    _log("=== EXTRACT ===")
    outs = extract_all_chunks()
    _log(f"chunks {len(outs)}")

    _log("=== CLEANUP ===")
    reports = cleanup_all()
    _log(f"cleaned {len(reports)} fix_cats {sum(len(r['fixes']) for r in reports)}")

    _log("=== MERGE ===")
    run_merge()

    _log("=== FIGURES ===")
    try:
        _log(run_apply_figures())
    except Exception as exc:  # noqa: BLE001
        _log(f"figures skip: {exc}")

    _log("=== POSTPROCESS ===")
    try:
        _log(run_post_process())
    except Exception as exc:  # noqa: BLE001
        _log(f"postprocess: {exc}")

    final = ROOT / "final_output" / "CEFR_Companion_Volume.md"
    t = final.read_text(encoding="utf-8")
    pages = re.findall(r"<!-- page:(\d+) -->", t)
    dups = sum(1 for i in range(len(pages) - 1) if pages[i] == pages[i + 1])
    _log(f"FINAL size {final.stat().st_size}")
    _log(f"page markers {len(pages)} unique {len(set(pages))} consec_dups {dups}")
    _log(f"bold ** count {t.count('**')}")
    _log(f"Can formulate abstract {t.count('Can formulate abstract')}")
    _log(f"AGENT_VISION_PENDING {t.count('AGENT_VISION_PENDING')}")
    _log(f"sign language id present {'scale_sign_language_repertoire' in t}")


if __name__ == "__main__":
    main()
