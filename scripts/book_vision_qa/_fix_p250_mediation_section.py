from pathlib import Path
import re

MD = Path("output/cefr-companion-2020/CEFR_Companion_Volume.md")
md = MD.read_text(encoding="utf-8")

missing = (
    "**RELATIONSHIP OF MEDIATION SCALES TO CEFR 2001 SCALES**\n\n"
    "Although the focus in the project was to provide descriptors for activities and strategies that were not already "
    "covered by CEFR 2001 descriptor scales, some aspects of the mediation scales, particularly at lower levels, are "
    "reminiscent of the kinds of activities described in existing CEFR scales. This is because some aspects of mediation, in "
    "the broader interpretation now being adopted, are already present in the illustrative descriptor scales published in "
    "2001. The new scales under “Mediating a text” for “Relaying specific information”, “Explaining data” and “Processing "
    "text”, for example, are an elaboration of concepts introduced in the existing scale for “Processing text” under "
    "“Text” in CEFR 2001 Section 4.6.3. Similarly, the scales particularly concerning group interaction in “Facilitating "
    "collaborative interaction with peers”, “Collaborating to construct meaning” and “Encouraging conceptual talk”, are "
    "in many ways a further development of concepts in the existing scale “Co-operating strategies under interaction "
    "strategies”. This underlines the difficulty of any scheme of categorisation. We should never underestimate the fact "
    "that categories are convenient, invented artefacts that make it easier for us to interpret the world. Boundaries "
    "are fuzzy and overlap is inevitable.\n\n"
    "**CROSS-LINGUISTIC MEDIATION**"
)

old = (
    "**RELATIONSHIP OF MEDIATION SCALES TO CEFR 2001 SCALES**\n\n\n"
    "**CROSS-LINGUISTIC MEDIATION**"
)
if old not in md:
    old = (
        "**RELATIONSHIP OF MEDIATION SCALES TO CEFR 2001 SCALES**\n\n"
        "**CROSS-LINGUISTIC MEDIATION**"
    )
print("found", old in md)
md = md.replace(old, missing, 1)

# also add For example lead-in before Can explain descriptor if missing
if "For example, the first descriptor" not in md:
    md = md.replace(
        "\n\nCan explain (in Language B) the relevance of specific information",
        "\n\nFor example, the first descriptor on the scale for “Relaying specific information in speech or sign”:\n\n"
        "Can explain (in Language B) the relevance of specific information",
        1,
    )
    print("added for example lead-in")

MD.write_text(md, encoding="utf-8")
print("relationship body", "invented artefacts" in MD.read_text(encoding="utf-8"))
