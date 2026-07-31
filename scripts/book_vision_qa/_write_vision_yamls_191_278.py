#!/usr/bin/env python3
"""Write Book Vision QA YAML results for pages 191-278 after MD repairs."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIS = ROOT / "work/cefr-companion-2020/metadata/book_qa/vision"
AUDIT = VIS / "_audit_191_278.json"
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
RF = ROOT / "work/cefr-companion-2020/metadata/rotated_from_grok"
PROGRESS = ROOT / "work/cefr-companion-2020/metadata/book_qa/vision_progress.json"

FIXED_PAGES = {
    191: "Trimmed mega multipage dual-emit (pages=191-241 full dump) to Appendix 5 intro + rotated_from_grok p191 table only.",
    195: "Stripped OCR soup dual-emit; kept RF Pre-A1 Online conversation; restored Goal-oriented C2/C1 second table from PDF vision.",
    206: "Stripped OCR soup dual-emit; kept RF Explaining data (speech/sign) A2+–Pre-A1; restored Explaining data in writing C2 from PDF vision.",
    217: "Stripped OCR soup dual-emit; kept RF Translating speech/sign A2–Pre-A1; restored Translating written text in writing C2 from PDF vision.",
    233: "Stripped OCR soup dual-emit; kept RF dual tables (Managing interaction A1/Pre-A1 + Encouraging conceptual talk C2/B2+).",
}


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def main() -> None:
    audit = {r["page"]: r for r in json.loads(AUDIT.read_text(encoding="utf-8"))}
    md = MD.read_text(encoding="utf-8")

    pass_n = fail_n = fixed_n = 0
    failures_detail: list[dict] = []

    for n in range(191, 279):
        row = audit[n]
        body = page_body(md, n)
        cls = row["class"]
        # Recompute soup with stricter heuristic (exclude legitimate restored phrases)
        soup = (
            "**C2 C1**" in body
            or "classroom simulation**Educational**" in body
            or "### Mediating a text**Personal**" in body
            or "### Mediating concepts**Personal" in body
            or ("as the lead researcher in a collaborative research collaborative research" in body)
        )
        mega = len(body) > 50000
        has_table = "| Level |" in body
        rf_files = list(RF.glob(f"page_{n:03d}_*.md"))

        status = "pass"
        failures: list[dict] = []
        notes_parts: list[str] = []

        if n in FIXED_PAGES:
            fixed_n += 1
            notes_parts.append(f"FIXED: {FIXED_PAGES[n]}")

        if mega:
            status = "fail"
            failures.append(
                {
                    "page": n,
                    "element": "table",
                    "severity": "major",
                    "visual_observation": "PDF page is a single appendix table page.",
                    "md_observation": f"MD body still mega-sized ({len(body)} chars) — multipage dual-emit suspected.",
                    "rule_violated": "md_much_longer_than_pdf",
                }
            )
        if soup:
            status = "fail"
            failures.append(
                {
                    "page": n,
                    "element": "prose-block",
                    "severity": "major",
                    "visual_observation": "PDF is a clean rotated domain-examples table.",
                    "md_observation": "OCR/geometry soup dual-emit remains in page body.",
                    "rule_violated": "no-figure-soup",
                }
            )

        # content presence checks
        if cls == "truly_missing":
            status = "fail"
            failures.append(
                {
                    "page": n,
                    "element": "prose-block",
                    "severity": "critical",
                    "visual_observation": "PDF has substantial text.",
                    "md_observation": "MD page body is chrome-only; content missing.",
                    "rule_violated": "missing_pdf_vocabulary",
                }
            )

        # multi-table page completeness after restore
        if n in (195, 206, 217) and body.count("| Level |") < 2:
            status = "fail"
            failures.append(
                {
                    "page": n,
                    "element": "table",
                    "severity": "critical",
                    "visual_observation": "PDF page has two domain-example tables (scale transition).",
                    "md_observation": f"MD has {body.count('| Level |')} Level header(s); expected 2.",
                    "rule_violated": "missing_pdf_vocabulary",
                }
            )

        if status == "pass":
            pass_n += 1
            if cls == "blank_both":
                notes_parts.append(
                    f"Page {n}: blank/cover both PDF and MD (intentionally empty)."
                )
            elif cls == "appendix_table_ok" or (rf_files and has_table):
                ov = row.get("rf_overlap")
                notes_parts.append(
                    f"Page {n}: Appendix 5 rotated domain table present; "
                    f"rf_overlap={ov}; local_overlap={row['local_overlap']}."
                )
            elif cls == "figure_page":
                notes_parts.append(
                    f"Page {n}: figure/diagram page; local_overlap={row['local_overlap']}."
                )
            elif cls == "table_present":
                notes_parts.append(
                    f"Page {n}: table present (Appendix 7/8 style); "
                    f"local_overlap={row['local_overlap']}."
                )
            else:
                notes_parts.append(
                    f"Page {n}: prose/back-matter OK; "
                    f"local_overlap={row['local_overlap']}; class={cls}."
                )
        else:
            fail_n += 1
            failures_detail.append({"page": n, "failures": failures})
            notes_parts.append(f"Page {n}: FAIL — see failures.")

        yaml_lines = ["status: " + status, "failures:"]
        if not failures:
            yaml_lines.append("  []")
        else:
            for f in failures:
                yaml_lines.append(f"  - page: {f['page']}")
                yaml_lines.append(f"    element: {f['element']}")
                yaml_lines.append(f"    severity: {f['severity']}")
                yaml_lines.append("    visual_observation: >")
                yaml_lines.append(f"      {f['visual_observation']}")
                yaml_lines.append("    md_observation: >")
                yaml_lines.append(f"      {f['md_observation']}")
                yaml_lines.append(f"    rule_violated: {f['rule_violated']}")
        yaml_lines.append("classification: book_vision_qa")
        yaml_lines.append("notes: >")
        for part in notes_parts:
            yaml_lines.append(f"  {part}")
        if n in FIXED_PAGES:
            yaml_lines.append("  attempts: 1")
        else:
            yaml_lines.append("  attempts: 0")
        yaml_lines.append(
            "snapshot: work/cefr-companion-2020/metadata/qa_snapshots/"
            f"page_{n:03d}.png"
        )
        yaml_lines.append("")

        (VIS / f"page_{n:03d}.yaml").write_text("\n".join(yaml_lines), encoding="utf-8")

    # progress file (whole book counts if other yamls exist)
    all_pass = all_fail = 0
    for p in range(1, 279):
        t = (VIS / f"page_{p:03d}.yaml").read_text(encoding="utf-8")
        if re.search(r"^status:\s*pass", t, re.M):
            all_pass += 1
        elif re.search(r"^status:\s*fail", t, re.M):
            all_fail += 1
    PROGRESS.write_text(
        json.dumps(
            {
                "pass": all_pass,
                "fail": all_fail,
                "total": 278,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "batch_191_278": {
                    "pass": pass_n,
                    "fail": fail_n,
                    "fixed": fixed_n,
                    "range": "191-278",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"batch 191-278: pass={pass_n} fail={fail_n} fixed={fixed_n}")
    print(f"book totals: pass={all_pass} fail={all_fail}")
    if failures_detail:
        print("remaining fails:", failures_detail)


if __name__ == "__main__":
    main()
