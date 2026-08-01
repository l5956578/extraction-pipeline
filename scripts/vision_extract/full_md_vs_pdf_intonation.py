#!/usr/bin/env python3
"""Multi-iteration Threshold intonation residual gate (MD ↔ PDF skeleton + PNG locks).

Closed internal loop — does not exit after one write. Only exits when residual
assertions pass (or max iterations exhausted with hard fail).

Hierarchy (binding):
  1. PNG glyph (gold_intonation_locks / EXACT_GOLD) wins
  2. PDF text layer = skeleton / hint only
  3. Section title never invents ˏ/ˊ over a clear crop glyph
  4. Protected multi-form skeletons are never letter-skeleton-replaced
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

from gold_intonation_locks import (
    EXACT_GOLD_LINES,
    MULTIFORM_EXACT_SKELETONS,
    PROTECTED_SKELETONS,
    THR_MD,
    THR_OV,
    WAY_MD,
    apply_section_locks,
    gold_counts,
    residual_assertions,
    strip_skel,
    sync_override_leaves,
    waystage_residual_safety,
)

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "input/cefr-threshold-1990/source.pdf"
REPORT = ROOT / "work/cefr-threshold-1990/intonation_hires/qa_fix/full_md_vs_pdf_report.txt"

LEAVES = (
    list(range(34, 65))
    + list(range(66, 91))
    + list(range(104, 113))
    + list(range(124, 131))
)

MAX_ITERS = 5


def convert_line(raw: str, ctx: str = "") -> str:
    """Convert PDF mark encoding with light context (hint only)."""
    s = raw.replace("\u00a0", " ")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    ctx_l = ctx.lower()

    s = re.sub(r"\$+(?=[A-Za-z])", "ˎ", s)
    s = re.sub(r'(^|[\s(|/>])["”„]+[ ]*(?=[A-Za-z])', r"\1ˇ", s)
    s = re.sub(r'(?<=[\s(|])"+(?=[A-Za-z])', "ˇ", s)
    s = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", "·", s)
    s = re.sub(r"(^|[\s(|/>])\.(?=[A-Za-z])", r"\1·", s)
    s = s.replace("/.", "/·")
    s = re.sub(r"(?<=[A-Za-z]),(?=[A-Za-z])", "ˎ", s)

    # Low family: default LF — only force LR if heading explicitly says low-rising
    # (never invent on "confirmation" alone)
    low_rise_ctx = bool(re.search(r"low[- ]rising|non-conduc", ctx_l))
    low_mark = "ˏ" if low_rise_ctx else "ˎ"
    s = re.sub(r"(^|[\s(|/>]),(?=[A-Za-z])", rf"\1{low_mark}", s)

    # High family: context split is HINT only; gold locks re-assert after
    if re.search(r"contrastive stress", ctx_l):
        high_mark = "ˋ"
    elif re.search(r"high[- ]rising", ctx_l):
        high_mark = "ˊ"
    else:
        high_mark = "ˈ"

    s = re.sub(r"(^|[\s(|/>])['`´]+(?=[A-Za-z])", rf"\1{high_mark}", s)

    def mid_high(m: re.Match) -> str:
        left, right = m.group(1), m.group(2)
        # multi-char right so I'll / you're / we've stay contractions
        if right.lower() in {
            "t",
            "s",
            "ll",
            "re",
            "ve",
            "d",
            "m",
            "clock",
            "all",
        }:
            return m.group(0)
        if left.lower() in {"in", "e"} and right.lower() in {"deed", "xactly"}:
            return left + "ˋ" + right
        return left + "ˈ" + right

    s = re.sub(r"([A-Za-z])'([A-Za-z]+)", mid_high, s)
    s = re.sub(r"\s+I\s+", " | ", s)
    s = re.sub(r" {2,}", " ", s)
    return s.strip()


def page_context_lines(page: fitz.Page) -> list[tuple[str, str]]:
    text = page.get_text("text")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: list[tuple[str, str]] = []
    ctx_buf: list[str] = []
    for ln in lines:
        is_mark = bool(
            re.search(r"['`,\.\"][A-Za-z]|[A-Za-z]['\"]|[A-Za-z],[A-Za-z]", ln)
        ) or ('"' in ln and re.search(r"[A-Za-z]", ln))
        if not is_mark:
            if not re.match(r"^\d+(\.\d+)*\s*$", ln):
                ctx_buf.append(ln)
                if len(ctx_buf) > 6:
                    ctx_buf.pop(0)
            continue
        if re.match(r"^\d+(\.\d+)*\s*$", ln):
            continue
        ctx = " ".join(ctx_buf[-4:])
        conv = convert_line(ln, ctx)
        if re.search(r"[ˈˎˋˏˊˇ·]", conv) and re.search(r"[A-Za-z]{2,}", conv):
            out.append((ctx, conv))
    return out


def collect_gold() -> tuple[dict[str, str], list[str]]:
    doc = fitz.open(PDF)
    gmap: dict[str, str] = {}
    raw_lines: list[str] = []
    for leaf in LEAVES:
        if leaf > doc.page_count:
            continue
        for ctx, conv in page_context_lines(doc[leaf - 1]):
            k = strip_skel(conv)
            if len(k) < 5:
                continue
            score = sum(conv.count(c) for c in "ˈˎˋˏˊˇ·")
            if k not in gmap or score >= sum(gmap[k].count(c) for c in "ˈˎˋˏˊˇ·"):
                gmap[k] = conv
            raw_lines.append(f"L{leaf}\t{conv}")
    doc.close()

    # PNG EXACT gold overwrites PDF convert — but NEVER multi-form pairs
    # (bedroom LF vs HF, train 1.2.1 vs 1.3.1). Those are section-lock-only.
    for g in EXACT_GOLD_LINES:
        k = strip_skel(g)
        if k in MULTIFORM_EXACT_SKELETONS:
            # Remove any PDF convert for this skeleton so last-wins cannot collapse
            gmap.pop(k, None)
            continue
        gmap[k] = g

    # Drop map entries that still contain broken contraction→tone forms
    bad_frag = (
        "youˈre",
        "Youˈre",
        "Iˈll",
        "Iˈve",
        "Iˈm",
        "weˈre",
        "theyˈre",
        "donˈt",
        "canˈt",
        "wonˈt",
        "isnˈt",
        "didnˈt",
        "oˈclock",
    )
    for k in list(gmap.keys()):
        if k in MULTIFORM_EXACT_SKELETONS or any(b in gmap[k] for b in bad_frag):
            del gmap[k]
    return gmap, raw_lines


def patch_md_skeleton(md: str, gmap: dict[str, str]) -> tuple[str, int]:
    """Letter-skeleton patch — skips PROTECTED multi-form pairs."""
    n = 0
    protected = {strip_skel(s) if " " in s else s for s in PROTECTED_SKELETONS}
    # PROTECTED_SKELETONS already stripped

    def repl(m: re.Match) -> str:
        nonlocal n
        prefix, body = m.group(1), m.group(2).strip()
        bare = re.sub(r"^\*+|\*+$", "", body).strip()
        key = strip_skel(bare)
        if key in PROTECTED_SKELETONS or key in protected:
            return m.group(0)
        if key in gmap:
            g = gmap[key]
            if g != bare and re.search(r"[ˈˎˋˏˊˇ·]", g):
                n += 1
                return f"{prefix}{g}"
        return m.group(0)

    md = re.sub(r"^(>\s*)(.+)$", repl, md, flags=re.M)
    md = re.sub(r"^([ \t]*)([ˈˎˋˏˊˇ·].+)$", repl, md, flags=re.M)
    return md, n


def ensure_blockquotes_tone_lines(md: str) -> tuple[str, int]:
    n = 0
    lines = md.splitlines(keepends=True)
    out = []
    for line in lines:
        if re.match(r"^[ˈˎˋˏˊˇ·]", line.strip()) and not line.lstrip().startswith(">"):
            if line.strip().startswith("**"):
                out.append(line)
                continue
            indent = re.match(r"^(\s*)", line).group(1)
            core = line.strip()
            out.append(
                f"{indent}> {core}\n" if line.endswith("\n") else f"{indent}> {core}"
            )
            n += 1
        else:
            out.append(line)
    return "".join(out), n


def one_iteration(md: str, gmap: dict[str, str], iter_i: int) -> tuple[str, dict]:
    stats: dict = {"iter": iter_i}
    md, n1 = patch_md_skeleton(md, gmap)
    stats["skel"] = n1
    md, ops = apply_section_locks(md)
    stats["lock_ops"] = ops
    md, n3 = ensure_blockquotes_tone_lines(md)
    stats["bq"] = n3
    # locks again after bq
    md, ops2 = apply_section_locks(md)
    stats["lock_ops2"] = ops2
    stats["fails"] = residual_assertions(md)
    stats["counts"] = gold_counts(md)
    return md, stats


def run_threshold_loop() -> int:
    print("collecting PDF skeleton gold (hint)...")
    gmap, raw_lines = collect_gold()
    print(f"gold map {len(gmap)} lines (protected={len(PROTECTED_SKELETONS)})")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    (REPORT.parent / "native_converted_all_primary.txt").write_text(
        "\n".join(raw_lines), encoding="utf-8"
    )

    md = THR_MD.read_text(encoding="utf-8")
    all_stats = []
    final_fails: list[str] = ["not run"]

    for i in range(1, MAX_ITERS + 1):
        print(f"\n=== iteration {i}/{MAX_ITERS} ===")
        md, stats = one_iteration(md, gmap, i)
        THR_MD.write_text(md, encoding="utf-8")
        all_stats.append(stats)
        fails = stats["fails"]
        print(f"  skel={stats['skel']} bq={stats['bq']} lock_ops={stats['lock_ops']}")
        print(f"  counts: {stats['counts']}")
        print(f"  residual fails: {len(fails)}")
        for f in fails[:15]:
            print(f"    - {f}")
        final_fails = fails
        if not fails:
            print(f"PASS residual gate on iteration {i}")
            break
    else:
        print(f"FAIL residual gate after {MAX_ITERS} iterations")

    # Sync overrides (section locks only — never thin density)
    n_ov = sync_override_leaves(LEAVES)
    print(f"overrides section-locked: {n_ov}")

    # Final re-read assert (no "one write theater")
    md = THR_MD.read_text(encoding="utf-8")
    final_fails = residual_assertions(md)
    counts = gold_counts(md)

    rep = [
        f"gold_map={len(gmap)}",
        f"iters={len(all_stats)}",
        f"final_residual_issues={len(final_fails)}",
        f"overrides_touched={n_ov}",
        "",
        "=== FINAL GOLD COUNTS ===",
    ]
    for k, v in counts.items():
        rep.append(f"{k!r}: {v}")
    rep.append("")
    rep.append("=== FINAL FAILS ===")
    rep.extend(final_fails or ["NONE"])
    rep.append("")
    rep.append("=== ITER STATS ===")
    for st in all_stats:
        rep.append(
            f"iter={st['iter']} skel={st['skel']} bq={st['bq']} fails={len(st['fails'])}"
        )
    REPORT.write_text("\n".join(rep), encoding="utf-8")
    print("\n" + REPORT.read_text(encoding="utf-8")[-2500:])

    return 0 if not final_fails else 1


def run_waystage_optional() -> None:
    if not WAY_MD.exists():
        return
    print("\n=== Waystage residual safety (no invent) ===")
    md = WAY_MD.read_text(encoding="utf-8")
    md2, ops = waystage_residual_safety(md)
    if ops:
        WAY_MD.write_text(md2, encoding="utf-8")
        for o in ops:
            print(f"  {o}")
    else:
        print("  no residual ASCII/OCR ops")
    # do not invent Threshold-style ˋ on Waystage contrastive without PNG


def main() -> None:
    rc = run_threshold_loop()
    run_waystage_optional()
    if rc != 0:
        print("DONE with residual failures", file=sys.stderr)
        sys.exit(rc)
    print("DONE full_md_vs_pdf_intonation multi-iter PASS")


if __name__ == "__main__":
    main()
