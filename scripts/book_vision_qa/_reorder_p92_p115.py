#!/usr/bin/env python3
"""Reorder p92/p115: table → prose → chrome (match PDF)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def replace_page(md: str, n: int, body: str) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            end = m.start()
            b = body if body.startswith("\n") else "\n" + body
            if not b.endswith("\n"):
                b += "\n"
            return md[:start] + b + md[end:]
    raise SystemExit(f"no page {n}")


P92 = """
<!-- el:start type=prose id=prose_p092_table_restore page=92 -->
<!-- book-qa: PDF page 92 multipage table continuation (Overall mediation B2-Pre-A1) -->
| | Overall mediation |
| --- | --- |
| B2 | Can establish a supportive environment for sharing ideas and facilitate discussion of delicate issues, showing appreciation of different perspectives, encouraging people to explore issues and adjusting sensitively the way they express things. Can build on others' ideas, making suggestions for ways forward.<br>Can convey the main content of well-structured but long and propositionally complex texts on subjects within their fields of professional, academic and personal interest, clarifying the opinions and purposes of speakers/signers. |
| | Can work collaboratively with people from different backgrounds, creating a positive atmosphere by providing support, asking questions to identify common goals, comparing options for how to achieve them and explaining suggestions for what to do next. Can further develop others' ideas, pose questions that invite reactions from different perspectives and propose a solution or next steps. Can convey detailed information and arguments reliably, e.g. the significant point(s) contained in complex but well-structured texts within their fields of professional, academic and personal interest. |
| B1 | Can collaborate with people from other backgrounds, showing interest and empathy by asking and answering simple questions, formulating and responding to suggestions, asking whether people agree, and proposing alternative approaches. Can convey the main points made in long texts expressed in uncomplicated language on topics of personal interest, provided they can check the meaning of certain expressions. |
| | Can introduce people from different backgrounds, showing awareness that some questions may be perceived differently, and invite other people to contribute their expertise and experience as well as their views. Can convey information given in clear, well-structured informational texts on subjects that are familiar or of personal or current interest, although lexical limitations cause difficulty with formulation at times. |
| A2 | Can play a supportive role in interaction, provided other participants speak/sign slowly and that one or more of the participants helps them to contribute and to express their suggestions. Can convey relevant information contained in clearly structured, short, simple, informational texts, provided the texts concern concrete, familiar subjects and are formulated in simple everyday language. |
| | Can use simple words/signs to ask someone to explain something. Can recognise when difficulties occur and indicate in simple language the apparent nature of a problem. Can convey the main point(s) involved in short, simple conversations or texts on everyday subjects of immediate interest, provided these are expressed clearly in simple language. |
| A1 | Can use simple words/signs and non-verbal signals to show interest in an idea. Can convey simple, predictable information of immediate interest given in short, simple signs and notices, posters and programmes. |
| Pre-A1 | No descriptors available |
<!-- el:end id=prose_p092_table_restore -->

<!-- el:start type=prose id=prose_p092_s1 page=92 -->
##### 3.4.1.1. Mediating a text

For all the descriptors in the scales in this section, Language A and Language B may be different languages, varieties or modalities of the same language, different registers of the same variety, or any combination of the above. However, they may also be identical: the CEFR 2001 is clear that mediation may also be in one language. Alternatively, mediation may involve several languages, varieties or modalities; there may be a Language C and even conceivably a Language D in the communicative situation concerned. The descriptors for mediation are equally applicable in each case. Users may thus wish to specify precisely which languages/varieties/modalities are involved when adapting the descriptors to their context. For ease of use, reference is made in the descriptors to just Language A and Language B.

It is also important to underline that the illustrative descriptors offered in this section are not intended to describe the competences of professional interpreters and translators. The descriptors focus on language competences,
<!-- el:end id=prose_p092_s1 -->

*Page **92** ▶ **CEFR – Companion volume***

"""

P115 = """
<!-- el:start type=prose id=prose_p115_table_restore page=115 -->
<!-- book-qa: PDF page 115 multipage table continuation (Facilitating pluricultural space B2-Pre-A1) -->
| | Facilitating pluricultural space |
| --- | --- |
| B2 | Can exploit knowledge of sociocultural conventions in order to establish a consensus on how to proceed in a particular situation that is unfamiliar to everyone involved.<br>Can, in intercultural encounters, demonstrate appreciation of perspectives other than that of their own worldview, and express themselves in a way appropriate to the context.<br>Can clarify misunderstandings and misinterpretations during intercultural encounters, suggesting how things were actually meant in order to clear the air and move the discussion forward. |
| | Can encourage a shared communication culture by expressing understanding and appreciation of different ideas, feelings and viewpoints, and inviting participants to contribute and react to each other's ideas.<br>Can work collaboratively with people who have different cultural orientations, discussing similarities and differences in views and perspectives.<br>Can, when collaborating with people from other cultures, adapt the way they work in order to create shared procedures. |
| B1 | Can support communication across cultures by initiating conversation, showing interest and empathy by asking and answering simple questions, and expressing agreement and understanding.<br>Can act in a supportive manner in intercultural encounters, recognising the feelings and different worldviews of other members of the group. |
| | Can support an intercultural exchange using a limited repertoire to introduce people from different cultural backgrounds and to ask and answer questions, showing awareness that some questions may be perceived differently in the cultures concerned.<br>Can help develop a shared communication culture, by exchanging information in a simple way about values and attitudes to language and culture. |
| A2 | Can contribute to an intercultural exchange, using simple words/signs to ask people to explain things and to get clarification of what they say, while exploiting a limited repertoire to express agreement, to invite, to thank, etc. |
| A1 | Can facilitate an intercultural exchange by showing a welcoming attitude and interest with simple words/signs and non-verbal signals, by inviting others to contribute, and by indicating whether they understand when addressed directly. |
| Pre-A1 | No descriptors available |
<!-- el:end id=prose_p115_table_restore -->

<!-- el:start type=prose id=prose_p115_s1 page=115 -->
**Acting as an intermediary in informal situations (with friends and colleagues)**

This scale is intended for situations in which the user/learner as a plurilingual individual mediates across languages and cultures to the best of their ability in an informal situation in the public, private, occupational or educational domain. The scale is therefore not concerned with the activities of professional interpreters. The mediation may be in one direction (for example, during a welcome speech) or in two directions (for example, during a conversation). Key concepts operationalised in the scale include the following:

- informally communicating the sense of what speakers/signers are saying in a conversation;
- conveying important information (for example, in a situation at work);
- repeating the sense of what is expressed in speeches and presentations.

Progression up the scale is characterised as follows: at the A levels, the user/learner can assist in a very simple manner, but by A2+ and B1 they can mediate in predictable everyday situations. However, such assistance is dependent on the interlocutors being supportive in that they alter their expression or will repeat information as necessary. At B2, the user/learner can mediate competently within their fields of interest, given the pauses to do so, and by C1 they can do this fluently on a wide range of subjects. At C2 the user/learner can also convey the meaning of the interlocutors faithfully, reflecting the style, register and cultural context.
<!-- el:end id=prose_p115_s1 -->

*The CEFR Illustrative Descriptor Scales: communicative language activities and strategies ▶ Page **115***

"""


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    md = replace_page(md, 92, P92)
    md = replace_page(md, 115, P115)
    MD.write_text(md, encoding="utf-8")
    print("reordered p92 and p115")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
