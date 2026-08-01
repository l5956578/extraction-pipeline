#!/usr/bin/env python3
"""Full production extract → cleanup → merge → figures → postprocess (unbuffered logs)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _log(*args, **kwargs) -> None:
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def main() -> None:
    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(
        description="Full production extract → cleanup → merge → figures → postprocess"
    )
    add_job_argument(parser)
    parser.add_argument(
        "--skip-regression",
        action="store_true",
        help="Skip automatic regression suite + versions/NNN snapshot after write",
    )
    args = parser.parse_args()

    ctx = bootstrap_job(args.job, force_draft=args.force_draft)
    _log(f"Job: {ctx.job_id}  pdf={ctx.pdf_path}  output={ctx.final_dir}")

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

    # JOB_MANIFEST is also written inside post_process / run_merge; ensure once more
    # so production extract always leaves a current envelope even if postprocess path
    # was skipped. Raise on failure (do not report a successful extract with no envelope).
    from pipeline.job_manifest import write_job_manifest

    _log("=== JOB_MANIFEST ===")
    _log(write_job_manifest(ctx))

    final = ctx.final_markdown
    t = final.read_text(encoding="utf-8")
    pages = re.findall(r"<!-- page:(\d+) -->", t)
    dups = sum(1 for i in range(len(pages) - 1) if pages[i] == pages[i + 1])
    _log(f"FINAL size {final.stat().st_size}")
    _log(f"page markers {len(pages)} unique {len(set(pages))} consec_dups {dups}")
    _log(f"bold ** count {t.count('**')}")
    _log(f"Can formulate abstract {t.count('Can formulate abstract')}")
    _log(f"AGENT_VISION_PENDING {t.count('AGENT_VISION_PENDING')}")
    _log(f"sign language id present {'scale_sign_language_repertoire' in t}")

    if args.skip_regression:
        _log("=== REGRESSION skipped (--skip-regression) ===")
        return

    # After live output is written: regression suite; if pass → versions/NNN/
    from pipeline.regression import run_regression_and_maybe_version

    _log("=== REGRESSION + AUTO-VERSION ===")
    result = run_regression_and_maybe_version(create_version=True)
    rep = result["regression"]
    _log(f"regression passed={rep['passed']} hard={len(rep['issues'])} soft={len(rep['soft_issues'])}")
    for it in rep["issues"][:20]:
        _log(f"  HARD [{it['code']}] {it['detail']}")
    if result.get("version_path"):
        _log(f"version snapshot: {result['version_path']}")
    elif not rep["passed"]:
        _log("no version snapshot (regression failed — live output still updated)")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
