#!/usr/bin/env python3
"""Complete known multipage sentence cuts and trim orphan page starts."""

from __future__ import annotations

from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def main() -> None:
    md = MD.read_text(encoding="utf-8")

    # p39/40
    if "absolutely identical since they reflect" not in md:
        needle = "absolutely identical"
        if needle in md:
            md = md.replace(
                needle,
                "absolutely identical since they reflect the life experience "
                "of the person concerned as well as their inherent abilities, "
                "what the CEFR 2001 (Section 5.2) describes as their "
                '"general competences".',
                1,
            )
            print("p39 completed")

    orphan40 = (
        "<!-- el:start type=figure_page "
        "id=figure_08_plurilingual_proficiency_fewer_categories page=40 -->\n"
        "since they reflect the life experience of the person concerned as well "
        "as their inherent abilities, what the CEFR 2001 (Section 5.2) describes "
        'as their "general competences".'
    )
    # curly quotes variant
    orphan40b = orphan40.replace('"', "\u201c", 1).replace('"', "\u201d", 1)
    for o in (orphan40, orphan40b):
        if o in md:
            md = md.replace(
                o,
                "<!-- el:start type=figure_page "
                "id=figure_08_plurilingual_proficiency_fewer_categories page=40 -->",
                1,
            )
            print("p40 orphan trimmed")
            break
    else:
        # looser
        import re

        md2, n = re.subn(
            r"(<!-- el:start type=figure_page "
            r"id=figure_08_plurilingual_proficiency_fewer_categories page=40 -->)\n"
            r"since they reflect the life experience[\s\S]{0,200}?competences?\.\s*",
            r"\1\n",
            md,
            count=1,
        )
        if n:
            md = md2
            print("p40 orphan re-trimmed", n)

    # ensure p31/32 already fixed
    print(
        "p31 has complete",
        "strategies) in order to complete a task" in md,
    )
    print(
        "p32 starts Tasks",
        "figure_01_structure_cefr_descriptive_scheme page=32 -->\nTasks often"
        in md,
    )
    print(
        "p243 complete",
        "and organise these into the two main age groups" in md
        and "prose_p243" in md,
    )

    MD.write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
