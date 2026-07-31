#!/usr/bin/env python3
"""Clean dual-emit soup on restored 85-120 pages; emit vision YAML + batch report."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
VISION = ROOT / "work/cefr-companion-2020/metadata/book_qa/vision"
SLICES = VISION / "_slices"


def page_body_span(md: str, n: int) -> tuple[int, int, str] | None:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return start, m.start(), md[start : m.start()]
    return None


def strip_dual_prose_after_tables(body: str) -> str:
    """
    Restored multipage pages often have:
      - clean markdown table(s)
      - then dual-emit truncated prose restating the same cells
    Keep tables + unique intro paragraphs; drop dual restatement blocks.
    """
    # Find last markdown table end (line with only |...| pattern after --- header)
    lines = body.splitlines(keepends=True)
    # Identify restore blocks
    if "book-qa restore" not in body:
        return body

    # Split into: comments/header, tables+prose before dual, dual soup, chrome end
    # Dual soup typically starts at a **Title** line after tables, repeating scale names
    # Keep: comments, tables, and prose that is intro (contains "This scale" / "Key concepts" / "Progression")
    # Drop: lines that are bare **Level** headers + single-descriptor paragraphs after dual starts

    out: list[str] = []
    i = 0
    n = len(lines)
    seen_table = False
    in_table = False
    dual_mode = False
    kept_intro = False

    while i < n:
        ln = lines[i]
        s = ln.strip()

        # always keep structural comments and blank-ish early content
        if s.startswith("<!--"):
            dual_mode = False
            out.append(ln)
            i += 1
            continue

        # page chrome at end
        if re.match(r"^\*(?:Page |\w)", s) and "Page **" in s:
            dual_mode = False
            out.append(ln)
            i += 1
            continue

        # table lines
        if s.startswith("|"):
            dual_mode = False
            seen_table = True
            in_table = True
            out.append(ln)
            i += 1
            continue
        if in_table and not s:
            out.append(ln)
            i += 1
            # peek: if next is not table, leave table mode
            if i < n and not lines[i].strip().startswith("|"):
                in_table = False
            continue

        if dual_mode:
            i += 1
            continue

        # After a table, detect dual-emit: bold title repeating scale name then level heads
        if seen_table and s.startswith("**") and s.endswith("**") and not s.startswith("**This"):
            # Could be unique section title for intro OR dual restatement
            # Look ahead for level markers like **C2** **A2** **B1** without prose intro
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            nxt = lines[j].strip() if j < n else ""
            is_level = bool(re.match(r"^\*\*(?:Pre-)?[ABC][12]\+?\*\*$", nxt) or nxt in (
                "**Pre-A1**", "**C2**", "**C1**", "**B2**", "**B2+**", "**B1**", "**B1+**",
                "**A2**", "**A2+**", "**A1**",
            ))
            # Unique intros start with "This scale" / "This first scale" etc. after heading
            k = j
            while k < n and not lines[k].strip():
                k += 1
            after = lines[k].strip() if k < n else ""
            if is_level or (after.startswith("Can ") and "This scale" not in after):
                dual_mode = True
                i += 1
                continue
            # Keep heading + following intro prose until next dual or table
            out.append(ln)
            i += 1
            kept_intro = True
            continue

        # Intro-like prose (before dual)
        if (
            "This scale" in s
            or "This first scale" in s
            or "This scale represents" in s
            or "Key concepts operationalised" in s
            or "Progression up the scale" in s
            or s.startswith("f ")
            or s.startswith("- ")
            or (kept_intro and s and not s.startswith("**"))
        ):
            out.append(ln)
            i += 1
            continue

        # Bare level headers in dual soup
        if re.match(r"^\*\*(?:Pre-)?[ABC][12]\+?\*\*$", s) or s in ("**No descriptors available**",):
            dual_mode = True
            i += 1
            continue

        # Default: keep if not dual
        out.append(ln)
        i += 1

    text = "".join(out)
    # collapse excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


# Hand-crafted clean bodies for messy restores (safer than heuristic for critical pages)
CLEAN: dict[int, str] = {}

CLEAN[86] = r"""
<!-- el:start type=prose id=prose_p086_restored page=86 -->
<!-- book-qa restore: page 86 content was chrome-only; reconstructed from PDF; dual-emit soup removed -->

### Online conversation and discussion

| | Online conversation and discussion |
| --- | --- |
| A2 | Can engage in basic social communication online (e.g. a simple message on a virtual card for special occasions, sharing news and making/confirming arrangements to meet).<br>Can make brief positive or negative comments online about embedded links and media using a repertoire of basic language, though they will generally have to refer to an online translation tool and other resources. |
| A1 | Can formulate very simple messages and personal online postings as a series of very short sentences about hobbies, likes/dislikes, etc., relying on the aid of a translation tool.<br>Can use formulaic expressions and combinations of simple words/signs to post short positive and negative reactions to simple online postings and their embedded links and media, and can respond to further comments with standard expressions of thanks and apology. |
| Pre-A1 | Can post simple online greetings, using basic formulaic expressions and emoticons.<br>Can post online short simple statements about themselves (e.g. relationship status, nationality, occupation), provided they can select them from a menu and/or refer to an online translation tool. |

### Goal-oriented online transactions and collaboration

This scale focuses on the potentially collaborative nature of online interaction and transactions that have specific goals, as a regular feature of contemporary life. A rigid separation between written and oral does not really apply to online transactions, where multimodality is increasingly a key feature and resource, and the descriptors therefore assume the exploitation of different online media and tools according to context. Key concepts operationalised in the scale include the following:

- purchasing goods and services online;
- engaging in transactions requiring negotiation of conditions, in a service as well as client role;
- participation in collaborative project work;
- dealing with communication problems.

Progression up the scale is characterised as follows: the move towards higher levels expands from basic transactions and information exchange at the A levels towards more sophisticated collaborative project work that is goal-oriented. This can be seen as a progression from filling in predictable online forms at Pre-A1, to solving various problems in order for the transaction to take place at the B levels, through to being able to participate in, and ultimately co-ordinate, group project work online at the C levels. One can also see such competences as progressing from reactive to proactive participation, and from simple to complex. Simple collaborative tasks appear at A2+, with a co-operative interlocutor, with small group project work from B1 and the ability to take a lead role in collaborative work from B2+. By C1, the user/learner can co-ordinate a group that is working on a project online, formulating and revising detailed instructions, evaluating proposals from team members, and providing clarifications in order to accomplish the shared tasks.

| | Goal-oriented online transactions and collaboration |
| --- | --- |
| C2 | Can resolve misunderstandings and deal effectively with frictions that arise during the collaborative process.<br>Can provide guidance and add precision to the work of a group at the redrafting and editing stages of collaborative work. |
| C1 | Can co-ordinate a group that is working on a project online, formulating and revising detailed instructions, evaluating proposals from team members, and providing clarifications in order to accomplish the shared tasks.<br>Can deal with complex online transactions in a service role (e.g. applications with complicated requirements), adjusting language flexibly to manage discussions and negotiations.<br>Can participate in complex projects requiring collaborative writing and redrafting as well as other forms of online collaboration, following and relaying instructions with precision in order to reach the goal.<br>Can deal effectively with communication problems and cultural issues that arise in an online collaborative or transactional exchange by reformulating, clarifying and providing examples through media (visual, audio, graphic). |
<!-- el:end id=prose_p086_restored -->

*Page **86** ▶ **CEFR – Companion volume***

"""

CLEAN[95] = r"""
<!-- el:start type=artifact id=scale_relaying_specific_information_p095 page=95 -->
<!-- book-qa restore: page 95 multipage continuation; table from rotated_from_grok; dual-emit removed -->
<!-- db:id=scale_relaying_specific_information type=descriptor_scale product_tier=assessment_action,detailed pages=94-95 -->

| Level | Relaying specific information in speech or sign | Relaying specific information in writing |
|-------|--------------------------------------------------|------------------------------------------|
| A2 | Can relay (in Language B) the point made in a clear announcement (in Language A) concerning familiar everyday subjects, though they may have to simplify the message and search for words/signs.<br>Can relay (in Language B) specific, relevant information contained in short, simple texts, labels and notices (in Language A) on familiar subjects. | Can relay in writing (in Language B) specific information contained in short simple informational texts (in Language A), provided the texts concern concrete, familiar subjects and are composed in simple everyday language. |
|  | Can relay (in Language B) the point made in short, clear, simple messages, instructions and announcements, provided these are expressed slowly and clearly in simple language (in Language A).<br>Can relay (in Language B) in a simple way a series of short, simple instructions, provided the original (in Language A) is clearly and slowly articulated. | Can list (in Language B) the main points of short, clear, simple messages and announcements (given in Language A), provided they are clearly and slowly articulated.<br>Can list (in Language B) specific information contained in simple texts (in Language A) on everyday subjects of immediate interest or need. |
| A1 | Can relay (in Language B) simple, predictable information about times and places given in short, simple statements (delivered in Language A). | Can list (in Language B) names, numbers, prices and very simple information of immediate interest in oral texts (in Language A), provided the articulation is very slow and clear, with repetition. |
| Pre-A1 | Can relay (in Language B) simple instructions about places and times (given in Language A), provided these are repeated very slowly and clearly.<br>Can relay (in Language B) very basic information (e.g. numbers and prices) from short, simple, illustrated texts (in Language A). | Can list (in Language B) names, numbers, prices and very simple information from texts (in Language A) that are of immediate interest, that are composed in very simple language and contain illustrations. |
<!-- el:end id=scale_relaying_specific_information_p095 -->

*The CEFR Illustrative Descriptor Scales: communicative language activities and strategies ▶ Page **95***

"""

CLEAN[100] = r"""
<!-- el:start type=artifact id=scale_processing_text_p100 page=100 -->
<!-- book-qa restore: page 100 multipage continuation; table from rotated_from_grok; dual-emit removed -->

| Level | Processing text in speech or sign | Processing text in writing |
|-------|-----------------------------------|---------------------------|
| B2 | Can synthesise and report (in Language B) information and arguments from a number of sources (in Language A).<br>Can summarise (in Language B) a wide range of factual and imaginative texts (in Language A), commenting on and discussing contrasting points of view and the main themes.<br>Can summarise (in Language B) the important points made in longer, complex texts (in Language A) on subjects of current interest, including their fields of special interest.<br>Can recognise the intended audience of a text (in Language A) on a topic of interest and explain (in Language B) the purpose, attitudes and opinion of the author.<br>Can summarise (in Language B) extracts from news items, interviews or documentaries containing opinions, arguments and discussions (in Language A).<br>Can summarise (in Language B) the plot and sequence of events in a film or play (in Language A). | Can summarise in writing (in Language B) the main content of complex texts (in Language A) on subjects related to their fields of interest and specialisation. |
| B1+ | Can summarise (in Language B) the main points made in long texts (in Language A) on topics in their fields of interest, provided they can check the meaning of certain expressions.<br>Can summarise (in Language B) a short narrative or article, talk, discussion, interview or documentary (in Language A) and answer further questions about details.<br>Can collate short pieces of information from several sources (in Language A) and summarise them (in Language B) for somebody else. | Can summarise in writing (in Language B) the information and arguments contained in texts (in Language A) on subjects of general or personal interest. |
<!-- el:end id=scale_processing_text_p100 -->

*Page **100** ▶ **CEFR – Companion volume***

"""

CLEAN[101] = r"""
<!-- el:start type=artifact id=scale_processing_text_p101 page=101 -->
<!-- book-qa restore: page 101 multipage continuation; table from rotated_from_grok; dual-emit removed -->

| Level | Processing text in speech or sign | Processing text in writing |
|-------|-----------------------------------|---------------------------|
| B1 | Can summarise (in Language B) the main points made in clear, well-structured texts (in Language A) on subjects that are familiar or of personal interest, although lexical limitations cause difficulty with formulation at times.<br>Can summarise simply (in Language B) the main information content of straightforward texts (in Language A) on familiar subjects (e.g. a short record of an interview, magazine article, travel brochure).<br>Can summarise (in Language B) the main points made during a conversation (in Language A) on a subject of personal or current interest, provided people articulated clearly.<br>Can summarise (in Language B) the main points made in long texts delivered orally (in Language A) on topics in their fields of interest, provided they can listen or view several times.<br>Can summarise (in Language B) the main points or events in TV programmes and video clips (in Language A), provided they can view them several times. | Can summarise in writing (in Language B) the main points made in straightforward, informational texts (in Language A) on subjects that are of personal or current interest, provided oral texts are clearly articulated.<br>Can paraphrase short passages in a simple fashion, using the original text wording and ordering. |
| A2 | Can report (in Language B) the main points made in simple TV or radio news items (in Language A) reporting events, sports, accidents, etc., provided the topics concerned are familiar and the delivery is slow and clear.<br>Can report in simple sentences (in Language B) the information contained in clearly structured, short, simple texts (in Language A) that have illustrations or tables.<br>Can summarise (in Language B) the main point(s) in simple, short informational texts (in Language A) on familiar topics. | Can list as a series of bullet points (in Language B) the relevant information contained in short simple texts (in Language A), provided the texts concern concrete, familiar subjects and contain only simple everyday language.<br>Can pick out and reproduce key words and phrases or short sentences from a short text within the learner's limited competence and experience. |
|  | Can convey (in Language B) the main point(s) contained in clearly structured, short, simple texts (in Language A), supplementing their limited repertoire with other means (e.g. gestures, drawings, words/signs from other languages) in order to do so. | Can use simple language to convey (in Language B) the main point(s) contained in very short texts (in Language A) on familiar and everyday themes that contain the highest frequency vocabulary; despite errors, the text remains comprehensible.<br>Can copy out short texts in printed or clearly handwritten format. |
| A1 | Can convey (in Language B) simple, predictable information given in short, very simple signs and notices, posters and programmes (in Language A). | Can, with the help of a dictionary, convey (in Language B) the meaning of simple phrases (in Language A) on familiar and everyday themes.<br>Can copy out single words and short texts presented in standard printed format. |
| Pre-A1 | No descriptors available | No descriptors available |
<!-- el:end id=scale_processing_text_p101 -->

*The CEFR Illustrative Descriptor Scales: communicative language activities and strategies ▶ Page **101***

"""

CLEAN[104] = r"""
<!-- el:start type=artifact id=scale_translating_written_text_p104 page=104 -->
<!-- book-qa restore: page 104 multipage continuation; table from rotated_from_grok; dual-emit removed -->

| Level | Translating a written text in speech or sign | Translating a written text in writing |
|-------|-----------------------------------------------|---------------------------------------|
| A2 | Can provide an approximate oral translation (into Language B) of short, simple, everyday texts (e.g. brochure entries, notices, instructions, letters or e-mails) (written in Language A). |  |
|  | Can provide a simple, rough oral translation (into Language B) of short, simple texts (e.g. notices on familiar subjects) (written in Language A), capturing the most essential point.<br>Can provide a simple, rough oral translation (into Language B) of routine information on familiar everyday subjects that is written in simple sentences (in Language A) (e.g. personal news, short narratives, directions, notices or instructions). | Can use simple language to provide an approximate translation (from Language A into Language B) of very short texts on familiar and everyday themes that contain the highest frequency vocabulary; despite errors, the translation remains comprehensible. |
| A1 | Can provide a simple, rough oral translation (into Language B) of simple everyday words/signs and phrases (written in Language A) that are encountered on signs and notices, posters, programmes, leaflets, etc. | Can, with the help of a dictionary, translate simple words/signs and phrases (from Language A into Language B), but may not always select the appropriate meaning. |
| Pre-A1 | No descriptors available | No descriptors available |
<!-- el:end id=scale_translating_written_text_p104 -->

*Page **104** ▶ **CEFR – Companion volume***

"""

CLEAN[107] = r"""
<!-- el:start type=prose id=prose_p107_restored page=107 -->
<!-- book-qa restore: page 107 content was chrome-only; reconstructed from PDF; dual-emit soup removed -->

### Expressing a personal response to creative texts (including literature)

| | Expressing a personal response to creative texts (including literature) |
| --- | --- |
| B1 | Can explain why certain parts or aspects of a work especially interested them.<br>Can explain in some detail which character they most identified with and why.<br>Can relate events in a story, film or play to similar events they have experienced or heard about.<br>Can relate the emotions experienced by a character to emotions they have experienced.<br>Can describe the emotions they experienced at a certain point in a story, e.g. the point(s) in a story when they became anxious for a character, and explain why.<br>Can explain briefly the feelings and opinions that a work provoked in them.<br>Can describe the personality of a character.<br>Can describe a character’s feelings and explain the reasons for them. |
| A2 | Can express their reactions to a work, reporting their feelings and ideas in simple language.<br>Can state in simple language which aspects of a work especially interested them.<br>Can state whether they liked a work or not and explain why in simple language. |
| A1 | Can use simple words/signs to state how a work made them feel. |
| Pre-A1 | No descriptors available |

### Analysis and criticism of creative texts (including literature)

This scale represents an approach more common at an upper secondary and university level. It concerns more formal, intellectual reactions. Aspects analysed include the significance of events in a novel, the treatment of the same themes in different works and other links between them, the extent to which a work follows conventions, and more global evaluation of the work as a whole. Key concepts operationalised in the scale include:

- comparing different works;
- giving a reasoned opinion of a work;
- critically evaluating features of a work, including the effectiveness of its techniques.

Progression up the scale is characterised as follows: there are no descriptors for A1 and A2. Until B2, the focus is on description rather than evaluation. At B2, the user/learner can analyse similarities and differences between works, giving a reasoned opinion and referring to the views of others. At C1, analysis becomes more subtle, concerned with the way the work engages the audience, the extent to which it is conventional, or whether it employs irony. At C2, the user/learner can recognise finer linguistic and stylistic subtleties, unpack connotations and give more critical appraisals of the way in which structure, language and rhetorical devices are exploited in a work of literature for a particular purpose.

| | Analysis and criticism of creative texts (including literature) |
| --- | --- |
| C2 | Can give a critical appraisal of work of different periods and genres (e.g. novels, poems and plays), appreciating subtle distinctions of style and implicit as well as explicit meaning.<br>Can recognise the finer subtleties of nuanced language, rhetorical effect and stylistic language use (e.g. metaphors, abnormal syntax, ambiguity), interpreting and “unpacking” meanings and connotations.<br>Can critically evaluate the way in which structure, language and rhetorical devices are exploited in a work for a particular purpose and give a reasoned argument concerning their appropriateness and effectiveness.<br>Can give a critical appreciation of deliberate breaches of linguistic conventions in a piece of writing. |
| C1 | Can critically appraise a wide variety of texts including literary works of different periods and genres.<br>Can evaluate the extent to which a work follows the conventions of its genre.<br>Can describe and comment on ways in which the work engages the audience (e.g. by building up and subverting expectations). |
<!-- el:end id=prose_p107_restored -->

*The CEFR Illustrative Descriptor Scales: communicative language activities and strategies ▶ Page **107***

"""

CLEAN[111] = r"""
<!-- el:start type=artifact id=scale_collaborating_in_a_group_p111 page=111 -->
<!-- book-qa restore: page 111 multipage continuation; table from rotated_from_grok; dual-emit removed -->

| Level | Facilitating collaborative interaction with peers | Collaborating to construct meaning |
|-------|--------------------------------------------------|-----------------------------------|
| B1 | Can collaborate on a shared task, e.g. formulating and responding to suggestions, asking whether people agree, and proposing alternative approaches.<br>Can collaborate in simple, shared tasks and work towards a common goal in a group by asking and answering straightforward questions.<br>Can define the task in basic terms in a discussion and ask others to contribute their expertise and experience. | Can organise the work in a straightforward collaborative task by stating the aim and explaining in a simple manner the main issue that needs to be resolved.<br>Can use questions, comments and simple reformulations to maintain the focus of a discussion. |
|  | Can invite other people in a group to contribute their views. | Can ask a group member to give the reason(s) for their views.<br>Can repeat part of what someone has said to confirm mutual understanding and help keep the development of ideas on course. |
|  | Can collaborate in simple, shared tasks, provided other participants articulate slowly and one or more people help them contribute and express their suggestions. | Can ensure that the person they are addressing understands what they mean by asking appropriate questions. |
| A2 | Can collaborate in simple, practical tasks, asking what others think, making suggestions and understanding responses, provided they can ask for repetition or reformulation from time to time. | Can make simple remarks and pose occasional questions to indicate that they are following.<br>Can make suggestions in a simple way. |
| A1 | Can invite others' contributions to very simple tasks using short, simple phrases prepared in advance. Can indicate that they understand and ask whether others understand. | Can express an idea and ask what others think, using very simple words/signs and phrases, provided they can prepare in advance. |
| Pre-A1 | No descriptors available | No descriptors available |
<!-- el:end id=scale_collaborating_in_a_group_p111 -->

*The CEFR Illustrative Descriptor Scales: communicative language activities and strategies ▶ Page **111***

"""

CLEAN[120] = r"""
<!-- el:start type=artifact id=scale_strategies_explain_concept_p120 page=120 -->
<!-- book-qa restore: page 120 multipage continuation; table from rotated_from_grok; dual-emit removed -->

| Level | Linking to previous knowledge | Adapting language | Breaking down complicated information |
|-------|------------------------------|-------------------|--------------------------------------|
| B1 | Can explain how something works by providing examples that draw on people's everyday experiences. | Can paraphrase more simply the main points made in short, straightforward texts on familiar subjects (e.g. short magazine articles, interviews) to make the contents accessible for others. | Can make a short instructional or informational text easier to understand by presenting it as a list of separate points. |
|  | Can show how new information is related to what people are familiar with by asking simple questions. | Can paraphrase short passages in a simple fashion, using the original order of the text. | Can make a set of instructions easier to understand by repeating them slowly, a few words/signs at a time, employing verbal and non-verbal emphasis to facilitate understanding. |
| A2 | No descriptors available | Can repeat the main point of a simple message on an everyday subject, using different formulation to help someone else understand it. | No descriptors available |
| A1 | No descriptors available | No descriptors available | No descriptors available |
| Pre-A1 | No descriptors available | No descriptors available | No descriptors available |
<!-- el:end id=scale_strategies_explain_concept_p120 -->

*Page **120** ▶ **CEFR – Companion volume***

"""


def replace_page_body(md: str, page: int, new_body: str) -> str:
    span = page_body_span(md, page)
    if not span:
        raise SystemExit(f"no page {page}")
    start, end, _ = span
    body = new_body if new_body.startswith("\n") else "\n" + new_body
    if not body.endswith("\n"):
        body += "\n"
    return md[:start] + body + md[end:]


# Vision YAML specs per page (after cleanup)
# classification: pass | multipage_collapsed | dual_emit_cleaned | content_ok_minor | fail

YAML_SPECS: dict[int, dict] = {
    85: {
        "status": "pass",
        "class": "content_present",
        "notes": "Online conversation progression prose + full scale C2–Pre-A1 match PNG; multipage span notes pages=85-86.",
    },
    86: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only multipage collapse; restored Online A2–Pre-A1 + Goal-oriented intro + C2/C1. Dual-emit soup cleaned.",
        "prior": "multipage_collapsed",
    },
    87: {
        "status": "pass",
        "class": "content_present",
        "notes": "Goal-oriented B2–Pre-A1 table + §3.3.2 Interaction strategies prose match PNG. C2/C1 live on p86 (PDF layout).",
    },
    88: {
        "status": "pass",
        "class": "content_present",
        "notes": "Turntaking intro + scale present; partial phrase flags were PDF line-wrap false positives.",
    },
    89: {
        "status": "pass",
        "class": "content_present",
        "notes": "Co-operating scale present; bullet f→- formatting only.",
    },
    90: {
        "status": "pass",
        "class": "content_present",
        "notes": "§3.4 MEDIATION prose + Figure 14 text_diagram tree present; no dual-emit soup after fence.",
    },
    91: {
        "status": "pass",
        "class": "content_present",
        "notes": "§3.4.1 Mediation activities prose + Overall mediation full scale (pages=91-92) present.",
    },
    92: {
        "status": "fail",
        "class": "multipage_collapsed",
        "failures": [
            {
                "element": "table",
                "severity": "major",
                "visual": "Full-page Overall mediation table continues B2–Pre-A1; §3.4.1.1 prose begins under table.",
                "md": "MD page body has only §3.4.1.1 prose (starts mid multi-page paragraph). Overall mediation rows for this page are merged into the full scale on page 91 (pages=91-92). Not lost from MD.",
                "rule": "prose-mass-retained",
            }
        ],
        "notes": "multipage_collapsed for Overall mediation table; prose present. Content fully earlier (p91).",
    },
    93: {
        "status": "pass",
        "class": "content_present",
        "notes": "Continuation of mediating-a-text prose + Relaying specific information intro match PDF body.",
    },
    94: {
        "status": "pass",
        "class": "content_present",
        "notes": "Relaying specific information dual-column scale full C2–Pre-A1 present (pages=94-95).",
    },
    95: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only; restored A2–Pre-A1 continuation table. Dual-emit truncated prose removed. Full scale also on p94.",
        "prior": "multipage_collapsed",
    },
    96: {
        "status": "pass",
        "class": "content_present",
        "notes": "Explaining data intro present; line-wrap phrase false positives only.",
    },
    97: {
        "status": "pass",
        "class": "content_present",
        "notes": "Explaining data scale content present.",
    },
    98: {
        "status": "pass",
        "class": "content_present",
        "notes": "Processing text intro prose present.",
    },
    99: {
        "status": "pass",
        "class": "content_present",
        "notes": "Processing text rotated multipage table fully merged on p99 (pages=99-101). Matches PDF content; layout is upright MD table vs rotated PDF (expected product path).",
    },
    100: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only; restored B2/B1+ continuation. Dual-emit truncated soup removed. Full scale also on p99.",
        "prior": "multipage_collapsed",
    },
    101: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only; restored B1–Pre-A1 continuation. Dual-emit truncated soup removed. Full scale also on p99.",
        "prior": "multipage_collapsed",
    },
    102: {
        "status": "pass",
        "class": "content_present",
        "notes": "Translating a written text intro/prose present.",
    },
    103: {
        "status": "pass",
        "class": "content_present",
        "notes": "Translating a written text scale present (pages span into 104).",
    },
    104: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only; restored A2–Pre-A1 continuation. Dual-emit truncated soup removed.",
        "prior": "multipage_collapsed",
    },
    105: {
        "status": "pass",
        "class": "content_present",
        "notes": "Note-taking intro + scale present; f-bullet → - list only.",
    },
    106: {
        "status": "pass",
        "class": "content_present",
        "notes": "Creative texts response intro + Expressing personal response scale start present.",
    },
    107: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only; restored Expressing personal response B1–Pre-A1 + Analysis intro + C2/C1. Dual-emit soup removed.",
        "prior": "multipage_collapsed",
    },
    108: {
        "status": "pass",
        "class": "content_present",
        "notes": "Analysis and criticism scale continuation/prose present.",
    },
    109: {
        "status": "pass",
        "class": "content_present",
        "notes": "Facilitating collaborative interaction intro present.",
    },
    110: {
        "status": "pass",
        "class": "content_present",
        "notes": "Collaborating in a group scale start present (pages into 111).",
    },
    111: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only; restored B1–Pre-A1 dual-column continuation. Dual-emit truncated soup removed.",
        "prior": "multipage_collapsed",
    },
    112: {
        "status": "pass",
        "class": "content_present",
        "notes": "Managing interaction intro present.",
    },
    113: {
        "status": "pass",
        "class": "content_present",
        "notes": "Managing interaction / Encouraging conceptual talk scale content present.",
    },
    114: {
        "status": "pass",
        "class": "content_present",
        "notes": "§3.4.1.3 Mediating communication + Facilitating pluricultural space intro + full scale (pages=114-115).",
    },
    115: {
        "status": "fail",
        "class": "multipage_collapsed",
        "failures": [
            {
                "element": "table",
                "severity": "major",
                "visual": "PNG shows Facilitating pluricultural space table B2–Pre-A1 upper page, then Acting as an intermediary intro below.",
                "md": "MD page body has Acting as an intermediary intro only. Pluricultural B2–Pre-A1 rows are in the full scale on page 114 (pages=114-115). Not lost from MD.",
                "rule": "prose-mass-retained",
            }
        ],
        "notes": "multipage_collapsed for pluricultural table portion; intermediary prose present.",
    },
    116: {
        "status": "pass",
        "class": "content_present",
        "notes": "Acting as intermediary scale / related content present.",
    },
    117: {
        "status": "pass",
        "class": "content_present",
        "notes": "Facilitating communication in delicate situations scale/prose present.",
    },
    118: {
        "status": "pass",
        "class": "content_present",
        "notes": "Mediation strategies / Linking to previous knowledge intro present.",
    },
    119: {
        "status": "pass",
        "class": "content_present",
        "notes": "Strategies to explain a new concept scale start present (pages into 120).",
    },
    120: {
        "status": "pass",
        "class": "restored_was_multipage_collapsed",
        "notes": "Was chrome-only; restored B1–Pre-A1 triple-column continuation. Dual-emit truncated soup removed.",
        "prior": "multipage_collapsed",
    },
}


def emit_yaml(page: int, spec: dict) -> str:
    status = spec["status"]
    if status == "pass":
        y = "status: pass\nfailures: []\n"
    else:
        y = "status: fail\nfailures:\n"
        for f in spec.get("failures", []):
            y += f"  - page: {page}\n"
            y += f"    element: {f['element']}\n"
            y += f"    severity: {f['severity']}\n"
            y += f"    visual_observation: >\n      {f['visual']}\n"
            y += f"    md_observation: >\n      {f['md']}\n"
            y += f"    rule_violated: {f['rule']}\n"
    # notes + classification (allowed extension for book QA batch)
    notes = spec.get("notes", "")
    cls = spec.get("class", "")
    prior = spec.get("prior", "")
    y += f"classification: {cls}\n"
    if prior:
        y += f"prior_class: {prior}\n"
    y += f"notes: >\n  {notes}\n"
    return y


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    changed = []
    for p, body in CLEAN.items():
        md2 = replace_page_body(md, p, body)
        if md2 != md:
            changed.append(p)
            md = md2
            print(f"cleaned page {p}")
        else:
            print(f"page {p} unchanged")

    # Minor: fix p87 glued punctuation if still present
    old = '“Asking for clarification” **.**Notice that “Taking the floor” (“Turntaking”)**,** is in fact'
    new = '“Asking for clarification”. Notice that “Taking the floor” (“Turntaking”) is in fact'
    if old in md:
        md = md.replace(old, new)
        changed.append("87-punct")
        print("fixed p87 punctuation glue")

    MD.write_text(md, encoding="utf-8")
    print("wrote MD, changes:", changed)

    VISION.mkdir(parents=True, exist_ok=True)
    pass_n = fail_n = 0
    collapsed = restored = present = 0
    for p in range(85, 121):
        spec = YAML_SPECS[p]
        ypath = VISION / f"page_{p:03d}.yaml"
        ypath.write_text(emit_yaml(p, spec), encoding="utf-8")
        if spec["status"] == "pass":
            pass_n += 1
        else:
            fail_n += 1
        c = spec["class"]
        if c == "multipage_collapsed":
            collapsed += 1
        elif c == "restored_was_multipage_collapsed":
            restored += 1
        else:
            present += 1

    # Re-export slices
    for p in range(85, 121):
        span = page_body_span(md, p)
        if span:
            SLICES.mkdir(parents=True, exist_ok=True)
            (SLICES / f"page_{p:03d}.md").write_text(span[2], encoding="utf-8")

    report = f"""# Book Vision QA batch — pages 85–120

**Job:** cefr-companion-2020  
**PDF:** `input/cefr-companion-2020/source.pdf`  
**MD:** `output/cefr-companion-2020/CEFR_Companion_Volume.md`  
**Snapshots:** `work/cefr-companion-2020/metadata/qa_snapshots/page_NNN.png`  
**YAML out:** `work/cefr-companion-2020/metadata/book_qa/vision/page_NNN.yaml`  
**Soft-issue viewer:** out of scope  

## Counts

| Metric | Count |
|--------|------:|
| Pages in batch | 36 (85–120) |
| Vision `pass` | {pass_n} |
| Vision `fail` | {fail_n} |
| `content_present` | {present} |
| `restored_was_multipage_collapsed` (cleaned) | {restored} |
| `multipage_collapsed` (still layout-differ) | {collapsed} |
| `truly_missing` | **0** |

## Classification summary

### multipage_collapsed (content fully present earlier; page-local body differs from PDF)

| Page | PDF shows | Where content lives in MD |
|-----:|-----------|---------------------------|
| 92 | Overall mediation B2–Pre-A1 table + start of §3.4.1.1 | Full scale on **p91** (`pages=91-92`); §3.4.1.1 prose on p92–93 |
| 115 | Facilitating pluricultural space B2–Pre-A1 + Acting as intermediary intro | Full scale on **p114** (`pages=114-115`); intermediary intro on p115 |

These are **not** content loss. Product default keeps multipage merge on span-start pages.

### restored_was_multipage_collapsed (were chrome-only; content restored page-locally)

| Page | Content restored | Cleanup this batch |
|-----:|------------------|--------------------|
| 86 | Online conversation A2–Pre-A1 + Goal-oriented intro + C2/C1 | Dual-emit prose soup removed; tables + intro kept |
| 95 | Relaying specific information A2–Pre-A1 | Dual-emit truncated soup removed |
| 100 | Processing text B2 / B1+ | Dual-emit truncated soup removed |
| 101 | Processing text B1–Pre-A1 | Dual-emit truncated soup removed |
| 104 | Translating a written text A2–Pre-A1 | Dual-emit truncated soup removed |
| 107 | Expressing personal response B1–Pre-A1 + Analysis intro + C2/C1 | Dual-emit soup removed |
| 111 | Collaborating in a group B1–Pre-A1 | Dual-emit truncated soup removed |
| 120 | Strategies to explain a new concept B1–Pre-A1 | Dual-emit truncated soup removed |

Prior structural class for these was `multipage_collapsed_content_elsewhere` (global vocab overlap ~1.0). Restores make page-local bodies non-empty; full multipage tables on earlier pages were **not** destroyed.

### truly_missing

**None** in 85–120 after restore + verification. Goal-oriented intro / C2–C1 (PDF p86) are present. Partial-missing phrase hits on 88–90, 96, 98–99, 105–106, 109, 112, 118 were **PDF line-wrap / bullet `f` vs `-` false positives** (local+global overlap ≈ 1.0).

## Vision fail pages (layout differs; content not lost)

1. **page_092.yaml** — multipage table collapsed to p91  
2. **page_115.yaml** — multipage table collapsed to p114  

## MD fixes applied this batch

1. Cleaned dual-emit / truncated restatement soup on restored pages: **86, 95, 100, 101, 104, 107, 111, 120**  
2. Fixed p87 Interaction strategies punctuation glue (`**.`Notice` → proper period)  
3. Did **not** re-run full pipeline extract  
4. Did **not** touch `rotated_from_grok/` bulk  

## Paths

- Vision YAMLs: `D:\\y\\lang-platform\\pipelines\\extraction-pipeline\\work\\cefr-companion-2020\\metadata\\book_qa\\vision\\page_085.yaml` … `page_120.yaml`  
- Batch report: `...\\vision\\_batch_085_120.md`  
- Audit JSON: `...\\vision\\_audit_085_120.json`  
- MD slices: `...\\vision\\_slices\\page_NNN.md`  
- Deliverable MD: `D:\\y\\lang-platform\\pipelines\\extraction-pipeline\\output\\cefr-companion-2020\\CEFR_Companion_Volume.md`  

## Residual / open

- Page-local layout still differs from PDF on multipage continuations when only the span-start carries the full table (92, 115) — intentional merge unless product expands per-page continuation.  
- Rotated PDF tables (e.g. p99) remain upright markdown tables (product path; not vision bulk rewrite).  
- p87 Goal-oriented scale artifact still starts at B2 (C2/C1 on p86 restore) matching PDF page split.  
"""
    (VISION / "_batch_085_120.md").write_text(report, encoding="utf-8")
    print("wrote batch report")
    print(f"PASS={pass_n} FAIL={fail_n} restored={restored} collapsed={collapsed} truly_missing=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
