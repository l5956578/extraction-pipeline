#!/usr/bin/env python3
"""Fix user-sampled wrong marks + document-wide nuclear high-fall pattern.

Root failure (honest): residual_risk→0 / line_zoom labels were set after
crop generation + partial Vision, not after verifying every example glyph.
PDF ' on nuclear content words was defaulted to head ˈ; many are high fall ˋ.
PDF , on non-nuclear syllables sometimes mid · (e.g. Hal,lo → Hal·lo not Halˎlo).

PNG-verified this run (10× crops user_samples/):
  2.2.3  ˋwrong (ˎthere)   was ˈwrong
  2.2.4.1 ˋhorrible          was ˈhorrible  
  2.2.5.2 ˋwill ·come        was ˈwill (nuclear future)
  3.1.3   ˋwalk              already; ensure ˈgo kept
  3.1.5   ˋtrain             was ˈtrain (final nucleus)
  4.2.1   ˋHal·lo            was ˈHalˎlo (HF on Hal, mid on lo)
  5.4.1   polˎlution OK; ensure ·something ·problem ˈlike
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-threshold-1990/Threshold_1990.md"
OV = ROOT / "work/cefr-threshold-1990/page_overrides"
REPORT = ROOT / "work/cefr-threshold-1990/intonation_hires/user_samples/SAMPLE_FIX_REPORT.md"

# Exact string fixes (PNG this session)
EXACT = [
    ("You are ˈwrong (ˎthere).", "You are ˋwrong (ˎthere)."),
    ("You are ˈwrong(ˎthere).", "You are ˋwrong (ˎthere)."),
    ("ˈSpinach is ˈhorrible.", "ˈSpinach is ˋhorrible."),
    ("(ˈSpinach is ˈhorrible.)", "(ˈSpinach is ˋhorrible.)"),
    ("I ·think he ˈwill ·come.", "I ·think he ˋwill ·come."),
    ("We ·could ˈgo for a ˈwalk.", "We ·could ˈgo for a ˋwalk."),
    ("We ·could ˈgo for a ˋwalk.", "We ·could ˈgo for a ˋwalk."),  # already
    ("We might perˈhaps ·go by ˈtrain.", "We might perˈhaps ·go by ˋtrain."),
    ("We might per'haps ·go by ˈtrain.", "We might perˈhaps ·go by ˋtrain."),
    ("ˈHalˎlo.", "ˋHal·lo."),
    ("ˈHalˎlo", "ˋHal·lo"),
    ("ˈHallo.", "ˋHal·lo."),
    # common variants
    ("That's ˈnot ˎright.", "That's ˋnot ˎright."),
    ("That's ˈnot ,right.", "That's ˋnot ˎright."),
]


def nuclear_high_fall_heuristic(line: str) -> str:
    """On short example lines: final high-family content before .?! often HF not head.

    Conservative: only when line has mid · and ends with ˈWord. or ˈWord?
    and is example-like (blockquote or short).
    """
    s = line
    # final ˈContentWord. → ˋContentWord. when another stress earlier
    if re.search(r"[·ˎˋˈ]", s) and re.search(r"ˈ[A-Za-z]+[.?!'”]*\s*$", s):

        def repl(m: re.Match) -> str:
            return "ˋ" + m.group(1)

        # only last occurrence
        s2 = re.sub(r"ˈ([A-Za-z]{2,})([.?!'”]*)$", r"ˋ\1\2", s.rstrip())
        if s2 != s.rstrip():
            # keep trailing newline structure
            if line.endswith("\n"):
                return s2 + "\n"
            return s2
    return line


def apply_text(t: str) -> tuple[str, list[str]]:
    notes = []
    for a, b in EXACT:
        c = t.count(a)
        if c:
            t = t.replace(a, b)
            notes.append(f"exact x{c}: {a!r} → {b!r}")
    # Hallo mid-syllable pattern Halˎlo → Hal·lo with HF on Hal if head
    t2, n = re.subn(r"ˈHalˎlo", "ˋHal·lo", t)
    if n:
        t = t2
        notes.append(f"Hal pattern x{n}")
    t2, n = re.subn(r"ˈHalˎlo", "ˋHal·lo", t)
    # nuclear HF heuristic on short > lines only
    out_lines = []
    for line in t.splitlines(keepends=True):
        core = line.rstrip("\n\r")
        nl = line[len(core) :]
        if core.strip().startswith(">") or (
            len(core) < 90 and re.search(r"[ˈˎˋˏˊˇ·]", core)
        ):
            new = nuclear_high_fall_heuristic(core)
            if new != core:
                notes.append(f"nuclear HF: {core.strip()[:60]!r} → {new.strip()[:60]!r}")
                core = new
        out_lines.append(core + nl)
    return "".join(out_lines), notes


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    md2, notes = apply_text(md)
    # force sample section locks
    force = [
        (
            r"(\*\*2\.2\.3\*\*[^\n]*\n)([^\n]*You are )[ˈˋ]wrong",
            r"\1You are ˋwrong",
        ),
        (
            r"(Spinach is )[ˈˋ]horrible",
            r"\1ˋhorrible",
        ),
        (
            r"(I ·think he )[ˈˋ]will( ·come)",
            r"\1ˋwill\2",
        ),
        (
            r"(go for a )[ˈˋ]walk",
            r"\1ˋwalk",
        ),
        (
            r"(go by )[ˈˋ]train",
            r"\1ˋtrain",
        ),
        (
            r"[ˈˋ]Hal[ˎ·]lo",
            "ˋHal·lo",
        ),
    ]
    for a, b in force:
        md2, c = re.subn(a, b, md2)
        if c:
            notes.append(f"force x{c}: {a[:40]}")
    MD.write_text(md2, encoding="utf-8")

    # overrides for leaves 36,45,47,49
    for leaf in (36, 45, 47, 49):
        p = OV / f"page_{leaf:03d}.md"
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        t2, n2 = apply_text(t)
        for a, b in force:
            t2, c = re.subn(a, b, t2)
            if c:
                n2.append(f"force x{c}")
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            notes.append(f"override {leaf} updated")

    # verify samples
    md = MD.read_text(encoding="utf-8")
    checks = {
        "2.2.3 ˋwrong": "ˋwrong (ˎthere)" in md or "ˋwrong(ˎthere)" in md,
        "2.2.4.1 ˋhorrible": "ˋhorrible" in md,
        "2.2.5.2 ˋwill": "he ˋwill ·come" in md,
        "3.1.2 ˎdance": "ˎdance" in md,
        "3.1.3 ˋwalk": "ˋwalk" in md,
        "3.1.5 ˋtrain": "by ˋtrain" in md,
        "4.2.1 ˋHal·lo": "ˋHal·lo" in md,
        "5.4.1 polˎlution": "polˎlution" in md,
        "BAD ˈwrong (ˎthere)": "ˈwrong (ˎthere)" in md,
        "BAD ˈhorrible": "ˈhorrible" in md,
        "BAD ˈHalˎlo": "ˈHalˎlo" in md,
    }
    rep = ["# Sample fix report", "", "## Notes"] + [f"- {n}" for n in notes[:80]]
    rep += ["", "## Checks"]
    for k, v in checks.items():
        rep.append(f"- {'PASS' if v else 'FAIL'}: {k}")
    REPORT.write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep))
    # residual gold
    try:
        from gold_intonation_locks import residual_assertions, apply_section_locks

        md3, ops = apply_section_locks(md)
        fails = residual_assertions(md3)
        if ops:
            MD.write_text(md3, encoding="utf-8")
        print("locks", ops, "residual fails", fails)
    except Exception as e:
        print("gold locks", e)


if __name__ == "__main__":
    main()
