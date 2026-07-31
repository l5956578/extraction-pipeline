#!/usr/bin/env python3
"""Autonomous overnight book QA loop: re-audit, repair chrome pages, reseed vision, log.

Run:
  python scripts/book_vision_qa/overnight_loop.py

Does not start soft-issue viewer. Does not ask for user input.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "work/cefr-companion-2020/metadata/book_qa"
PY = Path(sys.executable)
LOG = QA / "overnight_loop.log"


def log(msg: str) -> None:
    QA.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def run(script: str, *args: str) -> int:
    cmd = [str(PY), str(ROOT / "scripts/book_vision_qa" / script), *args]
    log(f"RUN {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(ROOT))
    log(f"EXIT {script} -> {p.returncode}")
    return p.returncode


def vision_counts() -> dict:
    vis = QA / "vision"
    if not vis.is_dir():
        return {"pass": 0, "fail": 0, "total": 0}
    p = f = 0
    for y in vis.glob("page_*.yaml"):
        t = y.read_text(encoding="utf-8", errors="replace")
        if t.lstrip().startswith("status: pass"):
            p += 1
        else:
            f += 1
    return {"pass": p, "fail": f, "total": p + f}


def main() -> int:
    log("=== overnight_loop start ===")
    # 1) restore chrome-only pages from PDF / rotated_from_grok
    run("repair_chrome_only_pages.py")
    # 2) structural re-audit
    run("structural_audit.py", "--job", "cefr-companion-2020")
    # 3) reclassify empties
    run("classify_empty_pages.py")
    # 4) reseed vision (won't overwrite existing real vision files if we change seed to force fails only)
    # Force rewrite seed for fail pages only
    run("seed_vision_from_structural.py")
    counts = vision_counts()
    (QA / "vision_progress.json").write_text(
        json.dumps(
            {
                **counts,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "source": "overnight_loop",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    log(f"vision_counts {counts}")
    log("=== overnight_loop end ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
