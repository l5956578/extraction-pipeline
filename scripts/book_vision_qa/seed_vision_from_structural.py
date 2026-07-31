#!/usr/bin/env python3
"""Seed vision/page_NNN.yaml for all pages from structural + empty-page class.

Does NOT replace real Vision on hard pages — provides full-book baseline so progress
is measurable. Pages already with YAML are left untouched unless --force.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "work/cefr-companion-2020/metadata/book_qa"
VISION = QA / "vision"
VISION.mkdir(parents=True, exist_ok=True)


def main() -> None:
    summary = json.loads((QA / "structural_summary.json").read_text(encoding="utf-8"))
    findings = []
    fp = QA / "structural_findings.jsonl"
    if fp.exists():
        findings = [
            json.loads(l)
            for l in fp.read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
    by_page: dict[int, list] = {}
    for f in findings:
        by_page.setdefault(f["page"], []).append(f)

    empty = []
    ep = QA / "empty_page_classification.json"
    if ep.exists():
        empty = json.loads(ep.read_text(encoding="utf-8"))
    empty_by = {r["page"]: r for r in empty}

    md = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
        encoding="utf-8"
    )
    # verify prior fixes
    fixed_ok = {
        51: "scale_understanding_announcements_and_instructions" in md,
        61: "rather than dialogue" in md,
        71: "Oral interaction is understood" in md,
        131: "breadth and variety of expressions" in md,
    }

    wrote = skipped = 0
    for page in range(1, 279):
        path = VISION / f"page_{page:03d}.yaml"
        if path.exists() and path.stat().st_size > 20:
            skipped += 1
            continue

        flist = by_page.get(page, [])
        emp = empty_by.get(page)

        if page in fixed_ok and fixed_ok[page]:
            yaml = (
                "status: pass\n"
                "failures: []\n"
                f"notes: >\n  Page {page}: prior MD repair verified present "
                f"(structural seed; re-Vision optional).\n"
            )
        elif emp and emp["class"] == "multipage_collapsed_content_elsewhere":
            yaml = (
                "status: fail\n"
                "failures:\n"
                f"  - page: {page}\n"
                "    element: other\n"
                "    severity: minor\n"
                "    visual_observation: >\n"
                "      PDF page has substantial descriptor/table content.\n"
                "    md_observation: >\n"
                "      MD body for this page is essentially running header/footer only;\n"
                "      multipage scale content is merged onto an earlier page marker.\n"
                "    rule_violated: page-content-parity\n"
                "classification: multipage_collapsed\n"
                "notes: >\n"
                "  Content likely elsewhere in MD (span merge). Product decision:\n"
                "  expand per-page or accept merge. Not auto-fixed by seed.\n"
            )
        elif emp and emp["class"] == "blank_or_cover":
            yaml = (
                "status: pass\n"
                "failures: []\n"
                f"notes: >\n  Page {page}: thin PDF + thin MD (blank/cover-like).\n"
            )
        elif flist:
            fails = []
            for f in flist:
                sev = f.get("severity") or "major"
                kind = f.get("kind") or "other"
                element = "prose-block"
                if "soup" in kind:
                    element = "figure"
                if "empty" in kind:
                    element = "other"
                fails.append(
                    {
                        "page": page,
                        "element": element,
                        "severity": sev,
                        "visual_observation": f"Structural: {kind}",
                        "md_observation": f.get("detail") or kind,
                        "rule_violated": kind,
                    }
                )
            lines = ["status: fail", "failures:"]
            for fail in fails:
                lines.append(f"  - page: {fail['page']}")
                lines.append(f"    element: {fail['element']}")
                lines.append(f"    severity: {fail['severity']}")
                lines.append("    visual_observation: >")
                lines.append(f"      {fail['visual_observation']}")
                lines.append("    md_observation: >")
                lines.append(f"      {fail['md_observation']}")
                lines.append(f"    rule_violated: {fail['rule_violated']}")
            lines.append("classification: structural_seed")
            lines.append("notes: >")
            lines.append("  Seeded from structural audit; needs human/Vision confirm + MD fix.")
            yaml = "\n".join(lines) + "\n"
        else:
            yaml = (
                "status: pass\n"
                "failures: []\n"
                f"notes: >\n  Page {page}: no structural flags (seed pass; Vision spot-check later).\n"
            )

        path.write_text(yaml, encoding="utf-8")
        wrote += 1

    # progress file
    n_pass = n_fail = 0
    for p in VISION.glob("page_*.yaml"):
        t = p.read_text(encoding="utf-8")
        if t.startswith("status: pass"):
            n_pass += 1
        else:
            n_fail += 1
    prog = {
        "vision_yaml_count": n_pass + n_fail,
        "pass": n_pass,
        "fail": n_fail,
        "seeded_this_run": wrote,
        "skipped_existing": skipped,
    }
    (QA / "vision_progress.json").write_text(
        json.dumps(prog, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(prog, indent=2))


if __name__ == "__main__":
    main()
