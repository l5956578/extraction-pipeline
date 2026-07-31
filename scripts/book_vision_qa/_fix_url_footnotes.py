#!/usr/bin/env python3
"""Stop bare URLs from swallowing trailing footnote digits (Obsidian autolink)."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
URL = r"https?://[^\s<>\)\"”']+"


def main() -> None:
    md = MD.read_text(encoding="utf-8")

    # Normalize already-wrapped to avoid double work
    # (url)TRAIL where TRAIL is footnote glue
    def repl(m: re.Match[str]) -> str:
        url, trail = m.group(1), m.group(2)
        if url.startswith("<"):
            return m.group(0)
        return f"(<{url}>){trail}"

    # (https://...) then footnote chars: ;5  .10  ”.19  " .19  16
    md, c1 = re.subn(
        rf"\(({URL})\)([.;”\"'\s]*\d{{1,2}})\b",
        repl,
        md,
    )
    # Fix double wraps
    md = re.sub(rf"\(\s*<(<{URL}>)>\s*\)", r"(<\1>)", md)
    md = re.sub(rf"\(<({URL})>\)", r"(<\1>)", md)

    # Remaining: unwrapped (url) with no trail already handled
    # Cases like url)”.19 already inside paren form

    MD.write_text(md, encoding="utf-8")
    print("wraps", c1)
    # report remaining suspicious
    for m in re.finditer(rf"\(({URL})\)([.;”\"']?\d{{1,2}})\b", md):
        if not m.group(1).startswith("<") and "<" not in m.group(0)[:3]:
            print("still", m.group(0)[:90])
    # show samples user listed
    for s in ["16806ae621", "168073ff31", "mWYUH", "bank-of-supplementary"]:
        i = md.find(s)
        if i >= 0:
            print(repr(md[max(0, i - 25) : i + 55]))


if __name__ == "__main__":
    main()
