#!/usr/bin/env python3
"""Restore missing Processing speed (p167) and merge Signing fluency (p168-169)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

P167 = """
<!-- el:start type=prose id=prose_p167_processing_speed page=167 -->
### Processing speed

This scale includes competences that describe the ease or effort in comprehending a sign language. The processing speed may depend on familiar versus unfamiliar signs, on the degree of grammatical complexity or on the familiarity with fingerspelling, to give examples. The scale therefore captures how different competences of other scales can be used, how automatised competences already are and how many resources must be allocated in interpretation or are available for further processing of messages. The individual’s experience of challenging communication, depending on the language used, relates to this. Processing speed indicates the level of training of a recipient and how well they can grasp and understand conveyed information.

Key concepts operationalised in the scale include the following:

- strain of comprehending texts and expressions of differing length, explicitness and complexity;
- ability to assess the signing speed, regularity and rhythm of others and to monitor oneself;
- ability to capture actions that are produced with different articulators simultaneously;
- ability to follow actions with several characters and complex settings;
- ability to follow messages or texts even if the transitions between the different parts of the text are smoothly signed;
- ability to understand fluently produced fingerspelling;
- ability to follow the content despite assimilations, interruptions, gaps, pauses, production errors or unclear signing.
<!-- el:end id=prose_p167_processing_speed -->

<!-- el:start type=artifact id=scale_processing_speed page=167 -->
<!-- db:id=scale_processing_speed type=descriptor_scale product_tier=assessment_action,detailed pages=167-168 -->
### Processing speed | scale_processing_speed

| | Processing speed |
| --- | --- |
| C2 | Can follow texts that are enacted in parallel (e.g., with two signers).<br>Can keep track of who is to take the next turn when several signers are involved, for example, in a panel discussion, by monitoring requests for a turn.<br>Can list the various aspects mentioned in a text even if the signer mentions them quickly one after the other.<br>Can easily understand fluently fingerspelled signs, even if they do not see every letter but perhaps only ergonomic word shapes. |
| C1 | Can follow a long fluidly signed text.<br>Can follow complicated reports without difficulty.<br>Can easily understand complex actions and relationships between objects/persons/places that are described using various classifier constructions.<br>Can follow how people react to one another’s communication behaviour even when several signers are involved, for example in a panel discussion.<br>Can understand a signed text even if the signer uses only one hand.<br>Can follow a text even when it contains several unknown signs.<br>Can understand a text even when certain signs or sentences are incomplete or not visible.<br>Can spot signing errors and correct them for themselves without query. |
| B2 | Can follow unexpected news or video messages without preparation. |
| | Can easily understand descriptions of actions even if the signer uses different classifier constructions (e.g., manipulators, substitutors).<br>Can follow even unexpected twists in a text.<br>Can understand rhythmically presented movement sequences and actions, and recognise their aesthetic quality. |
| B1 | Can follow a long and slowly signed text, provided it is shown several times.<br>Can follow the narration of a well-known story without difficulty.<br>Can recognise and imitate various handshapes, even when the signer uses them in rapid succession.<br>Can spot signing errors and ask for more precision or clarification. |
| | Can follow a longer, fluidly signed text, provided it is repeated.<br>Can understand a relatively long text in one go, provided it is signed slowly.<br>Can understand designations (name, fingerspelled items, functions) for persons in a text and subsequent reference to them. |
| A2 | Can follow the interlocutor’s signs, provided they are clearly visible. |
| | Can understand fluent fingerspelling of letters, provided the producer repeats it, if necessary. |
| A1 | Can understand short, slowly and clearly signed texts in one go. |
<!-- el:end id=scale_processing_speed -->

*The CEFR Illustrative Descriptor Scales: Signing competences ▶ Page **167***
"""

P168 = """
<!-- el:start type=prose id=prose_p168_signing_fluency page=168 -->
### Signing fluency

This scale is a direct equivalent of the scale for fluency under communicative language competences. Key concepts operationalised in the scale include the following:

- the pace, regularity and rhythm of signing;
- ability to pause where appropriate;
- ability to articulate simultaneous constructions with different articulators;
- ability to articulate signs one after another with smooth transitions and without distortion;
- ability to fingerspell in a fluid sequence to express words for unknown signs (A levels) or context-dependent emphasis (B level and beyond), or as a means of bilingual contact signing (all levels).
<!-- el:end id=prose_p168_signing_fluency -->

<!-- el:start type=artifact id=scale_signing_fluency page=168 -->
<!-- db:id=scale_signing_fluency type=descriptor_scale product_tier=assessment_action,detailed pages=168-169 -->
### Signing fluency | scale_signing_fluency

| | Signing fluency |
| --- | --- |
| C2 | No descriptors available; see C1 |
| C1 | Can sign rapidly in a steady rhythm.<br>Can sign a longer text fluently and rhythmically.<br>Can employ an extended hold of a sign (hold) as a rhetorical or prosodic feature. |
| B2 | Can sign at a fluent pace, even though some pauses for planning are still necessary.<br>Can relate fluently in a sign language a story that they know.<br>Can hold a sign with one hand in order to demonstrate something static (hold), while simultaneously using the other hand to continue signing.49 |
| | Can sign at a comfortable pace, without needing to think about the individual signs.<br>Can use pauses for effect at appropriate points.<br>Can rhythmically represent the stages of a movement or activity (e.g. leaves falling down, hail).<br>Can fingerspell fluently, connecting or blending elements smoothly. |
| B1 | Can sign a fluent transition between related points. |
| | Can sign a short text rhythmically.<br>Can employ sequences of handshapes and/or the handshapes for fingerspelling fluently. |
| A2 | Can sign a simple sentence rhythmically. |
| | Can indicate the end of a sentence clearly by leaving a pause. |
| A1 | No descriptors available |
<!-- el:end id=scale_signing_fluency -->

49.\t These constructions are also known as “fragment buoys”.

*Page **168** ▶ **CEFR – Companion volume***
"""

P169 = """
*The CEFR Illustrative Descriptor Scales: Signing competences ▶ Page **169***
"""


def replace_page_region(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    if idx < 0:
        raise SystemExit(f"marker missing page {page}")
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    md = replace_page_region(md, 169, P169)
    md = replace_page_region(md, 168, P168)
    md = replace_page_region(md, 167, P167)
    md = md.replace(
        "TheCommon Reference Levels can be presented",
        "The Common Reference Levels can be presented",
    )
    MD_PATH.write_text(md, encoding="utf-8")
    print("wrote", MD_PATH)
    print("processing_speed el starts", len(re.findall(r"id=scale_processing_speed", md)))
    print("signing_fluency el starts", len(re.findall(r"id=scale_signing_fluency", md)))
    print("has C2 parallel", "enacted in parallel" in md)
    print("TheCommon left", "TheCommon" in md)
    for n in (167, 168, 169):
        b = page_body(md, n)
        core = re.sub(r"<!--.*?-->", "", b, flags=re.S).strip()
        print(f"p{n} core_len={len(core)}")


if __name__ == "__main__":
    main()
