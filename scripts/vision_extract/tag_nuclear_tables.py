#!/usr/bin/env python3
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]


def tag(job: str) -> None:
    tag = "threshold" if "threshold" in job else "waystage"
    md = next((ROOT / "output" / job).glob("*.md"))
    t = md.read_text(encoding="utf-8")
    tid = f"{tag}_table_five_nuclear_tones"
    if tid in t:
        print("exists", job)
    else:
        needle = "| # | Name | Mark (notation) | Pitch description |"
        idx = t.find(needle)
        if idx < 0:
            print("needle missing", job)
            return
        inject = (
            f"<!-- el:start type=table id={tid} -->\n"
            f"<!-- db:id={tid} type=table product_tier=context -->\n\n"
        )
        t = t[:idx] + inject + t[idx:]
        m = re.search(r"(\| \*\*5\*\* \| \*\*Falling-rising\*\*[^\n]+\n)", t)
        if m:
            end = f"\n<!-- el:end id={tid} -->\n"
            t = t[: m.end(1)] + end + t[m.end(1) :]
        md.write_text(t, encoding="utf-8")
        print("tagged", job)
    vdir = ROOT / "output" / job / "versions" / "002"
    vdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(md, vdir / md.name)


if __name__ == "__main__":
    tag("cefr-threshold-1990")
    tag("cefr-waystage-1990")
