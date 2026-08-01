"""Semantic compare of Companion MD baseline vs current output."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


def pages(t: str) -> list[str]:
    return re.findall(r"<!-- page:(\d+) -->", t)


def db_ids(t: str) -> list[str]:
    return re.findall(r"<!-- db:id=([^\s]+) ", t)


def figure_pngs(t: str) -> list[str]:
    return re.findall(r"!\[.*?\]\((assets/figures/[^)]+)\)", t)


def page_blocks(t: str) -> dict[int, str]:
    parts = re.split(r"(?=<!-- page:\d+ -->)", t)
    out: dict[int, str] = {}
    for p in parts:
        m = re.search(r"<!-- page:(\d+) -->", p)
        if m:
            out[int(m.group(1))] = p
    return out


def main() -> int:
    base_path = Path(sys.argv[1])
    new_path = Path(sys.argv[2])
    base = base_path.read_text(encoding="utf-8")
    new = new_path.read_text(encoding="utf-8")

    bp, np_ = pages(base), pages(new)
    bi, ni = db_ids(base), db_ids(new)
    print("=== SIZE ===")
    print(f"base_chars={len(base)} new_chars={len(new)} delta={len(new) - len(base)}")
    print(f"base_lines={base.count(chr(10)) + 1} new_lines={new.count(chr(10)) + 1}")
    print("=== PAGE MARKERS ===")
    print(
        f"base={len(bp)} unique={len(set(bp))} new={len(np_)} unique={len(set(np_))}"
    )
    print(
        "consec_dups_base="
        f"{sum(1 for i in range(len(bp) - 1) if bp[i] == bp[i + 1])} "
        f"new={sum(1 for i in range(len(np_) - 1) if np_[i] == np_[i + 1])}"
    )
    missing_pages = sorted(set(map(int, bp)) - set(map(int, np_)))
    extra_pages = sorted(set(map(int, np_)) - set(map(int, bp)))
    print(f"missing_pages={missing_pages[:20]} extra={extra_pages[:20]}")
    print("=== DB IDS ===")
    bs, ns = set(bi), set(ni)
    print(
        f"base_ids={len(bs)} new_ids={len(ns)} "
        f"only_base={len(bs - ns)} only_new={len(ns - bs)}"
    )
    if bs - ns:
        print("only_in_baseline sample:", list(sorted(bs - ns))[:15])
    if ns - bs:
        print("only_in_new sample:", list(sorted(ns - bs))[:15])
    print("=== VISION / QUALITY FLAGS ===")
    print(
        f"AGENT_VISION_PENDING base={base.count('AGENT_VISION_PENDING')} "
        f"new={new.count('AGENT_VISION_PENDING')}"
    )
    print(f"bold ** base={base.count('**')} new={new.count('**')}")
    print(
        "Can formulate abstract "
        f"base={base.count('Can formulate abstract')} "
        f"new={new.count('Can formulate abstract')}"
    )
    print(
        "sign_language_repertoire "
        f"base={'scale_sign_language_repertoire' in base} "
        f"new={'scale_sign_language_repertoire' in new}"
    )
    print("=== FIGURES ===")
    bf, nf = set(figure_pngs(base)), set(figure_pngs(new))
    print(
        f"png refs base={len(bf)} new={len(nf)} "
        f"only_base={sorted(bf - nf)[:10]} only_new={sorted(nf - bf)[:10]}"
    )
    print("=== HASH ===")
    print("base_sha256", hashlib.sha256(base.encode()).hexdigest()[:16])
    print("new_sha256", hashlib.sha256(new.encode()).hexdigest()[:16])
    print("identical", base == new)

    risk = [
        35,
        94,
        95,
        132,
        133,
        146,
        147,
        148,
        177,
        178,
        179,
        180,
        181,
        191,
        200,
        241,
    ]
    bb, nb = page_blocks(base), page_blocks(new)
    print("=== HIGH-RISK PAGE DELTAS ===")
    for p in risk:
        a, b = bb.get(p, ""), nb.get(p, "")
        if a == b:
            print(f"p{p:03d}: IDENTICAL len={len(a)}")
            continue
        n = min(len(a), len(b))
        i = 0
        while i < n and a[i] == b[i]:
            i += 1
        print(
            f"p{p:03d}: delta_len={len(b) - len(a)} first_diff_at={i} "
            f"base_len={len(a)} new_len={len(b)}"
        )
        if i < n:
            print("  base:", repr(a[max(0, i - 40) : i + 60].replace("\n", "\\n")))
            print("  new :", repr(b[max(0, i - 40) : i + 60].replace("\n", "\\n")))

    changed = [p for p in sorted(set(bb) | set(nb)) if bb.get(p) != nb.get(p)]
    print(f"=== PAGES CHANGED: {len(changed)} / {max(len(bb), len(nb))} ===")
    print("first 40 changed pages:", changed[:40])

    br = base_path.parent / "db_import_registry.json"
    nr = new_path.parent / "db_import_registry.json"
    if br.exists() and nr.exists():
        breg = {r["id"]: r for r in json.loads(br.read_text(encoding="utf-8"))}
        nreg = {r["id"]: r for r in json.loads(nr.read_text(encoding="utf-8"))}
        print("=== REGISTRY ===")
        print(
            f"base={len(breg)} new={len(nreg)} "
            f"only_base={len(set(breg) - set(nreg))} "
            f"only_new={len(set(nreg) - set(breg))}"
        )
        tier_changes = sum(
            1
            for i in set(breg) & set(nreg)
            if breg[i].get("product_tiers") != nreg[i].get("product_tiers")
        )
        print(f"product_tiers_changed={tier_changes}")

    ov = (
        new_path.parents[2]
        / "work"
        / "cefr-companion-2020"
        / "metadata"
        / "output_validation.json"
    )
    if ov.exists():
        data = json.loads(ov.read_text(encoding="utf-8"))
        print("=== OUTPUT_VALIDATION ===")
        issues = data.get("issues") if isinstance(data, dict) else data
        if isinstance(issues, list):
            print(f"issue_count={len(issues)}")
            for it in issues[:15]:
                if isinstance(it, dict):
                    print(
                        " -",
                        it.get("code") or it.get("type") or it.get("kind"),
                        it.get("message") or it.get("msg") or str(it)[:120],
                    )
                else:
                    print(" -", str(it)[:160])
        else:
            print(str(data)[:1200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
