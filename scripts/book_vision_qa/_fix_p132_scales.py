#!/usr/bin/env python3
"""Split mis-merged Grammatical accuracy + Vocabulary control tables on p.132."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

NEW132 = r"""
<!-- el:start type=prose id=prose_p132_s0 page=132 -->
**Grammatical accuracy**

This scale concerns both the user/learner’s ability to recall “prefabricated” expressions correctly and the capacity to focus on grammatical forms while articulating thought. This is difficult because, when formulating thoughts or performing more demanding tasks, the user/learner has to devote the majority of their mental processing capacity to fulfilling the task. This is why accuracy tends to drop during complex tasks. In addition, research in English, French and German suggests that inaccuracy increases at around B1 as the learner is beginning to use language more independently and creatively. The fact that accuracy does not increase in a linear manner is reflected in the descriptors. Key concepts operationalised in the scale include the following:

- control of a specific repertoire (A1 to B1);
- prominence of mistakes (B1 to B2);
- degree of control (B2 to C2).
<!-- el:end id=prose_p132_s0 -->

<!-- el:start type=artifact id=scale_grammatical_accuracy page=132 -->
<!-- db:id=scale_grammatical_accuracy type=descriptor_scale product_tier=assessment_action,detailed pages=132 -->
### Grammatical accuracy | scale_grammatical_accuracy

| Level | Grammatical accuracy |
| --- | --- |
| C2 | Maintains consistent grammatical control of complex language, even while attention is otherwise engaged (e.g. in forward planning, in monitoring others’ reactions). |
| C1 | Consistently maintains a high degree of grammatical accuracy; errors are rare and difficult to spot. |
| B2 | Good grammatical control; occasional “slips” or non-systematic errors and minor flaws in sentence structure may still occur, but they are rare and can often be corrected in retrospect.<br>Shows a relatively high degree of grammatical control. Does not make mistakes which lead to misunderstanding.<br>Has a good command of simple language structures and some complex grammatical forms, although they tend to use complex structures rigidly with some inaccuracy. |
| B1 | Communicates with reasonable accuracy in familiar contexts; generally good control, though with noticeable mother-tongue influence. Errors occur, but it is clear what they are trying to express.<br>Uses reasonably accurately a repertoire of frequently used “routines” and patterns associated with more predictable situations. |
| A2 | Uses some simple structures correctly, but still systematically makes basic mistakes; nevertheless, it is usually clear what they are trying to say. |
| A1 | Shows only limited control of a few simple grammatical structures and sentence patterns in a learnt repertoire. |
| Pre-A1 | Can employ very simple principles of word/sign order in short statements. |
<!-- el:end id=scale_grammatical_accuracy -->

<!-- el:start type=prose id=prose_p132_s2 page=132 -->
### Vocabulary control

This scale concerns the user/learner’s ability to choose an appropriate expression from their repertoire. As competence increases, such ability is driven increasingly by association in the form of collocations and lexical chunks, with one expression triggering another. Key concepts operationalised in the scale include the following:

- familiarity of topics (A1 to B1);
- degree of control (B2 to C2).
<!-- el:end id=prose_p132_s2 -->

<!-- el:start type=artifact id=scale_vocabulary_control page=132 -->
<!-- db:id=scale_vocabulary_control type=descriptor_scale product_tier=assessment_action,detailed pages=132-133 -->
### Vocabulary control | scale_vocabulary_control

| Level | Vocabulary control |
| --- | --- |
| C2 | Consistently correct and appropriate use of vocabulary. |
| C1 | Uses less common vocabulary idiomatically and appropriately.<br>Occasional minor slips, but no significant vocabulary errors. |
| B2 | Lexical accuracy is generally high, though some confusion and incorrect word/sign choice does occur without hindering communication. |
| B1 | Shows good control of elementary vocabulary but major errors still occur when expressing more complex thoughts or handling unfamiliar topics and situations.<br>Uses a wide range of simple vocabulary appropriately when discussing familiar topics. |
| A2 | Can control a narrow repertoire dealing with concrete, everyday needs. |
| A1 | No descriptors available |
| Pre-A1 | No descriptors available |
<!-- el:end id=scale_vocabulary_control -->

*Page **132** ▶ **CEFR – Companion volume***
"""


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    md = replace_page(md, 132, NEW132)
    MD.write_text(md, encoding="utf-8")
    print("scale_grammatical_accuracy", "scale_grammatical_accuracy" in md)
    print("scale_vocabulary_control", "scale_vocabulary_control" in md)
    print("mother-tongue", "mother-tongue influence" in md)


if __name__ == "__main__":
    main()
