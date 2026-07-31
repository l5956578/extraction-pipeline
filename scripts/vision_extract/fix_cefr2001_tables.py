#!/usr/bin/env python3
"""Inject Companion-quality CEFR 2001 Tables 1–2 + Figure 1 into product MD."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-en-2001/CEFR_EN_2001.md"

TABLE1 = """
<!-- el:start type=table id=cefr2001_table_1_common_reference_levels_global_scale page=33 -->
<!-- db:id=cefr2001_table_1_common_reference_levels_global_scale type=table product_tier=base pages=33 -->

**Table 1. Common Reference Levels: global scale**

| Band | Level | Descriptor |
| --- | --- | --- |
| **Proficient User** | **C2** | Can understand with ease virtually everything heard or read. Can summarise information from different spoken and written sources, reconstructing arguments and accounts in a coherent presentation. Can express him/herself spontaneously, very fluently and precisely, differentiating finer shades of meaning even in more complex situations. |
|  | **C1** | Can understand a wide range of demanding, longer texts, and recognise implicit meaning. Can express him/herself fluently and spontaneously without much obvious searching for expressions. Can use language flexibly and effectively for social, academic and professional purposes. Can produce clear, well-structured, detailed text on complex subjects, showing controlled use of organisational patterns, connectors and cohesive devices. |
| **Independent User** | **B2** | Can understand the main ideas of complex text on both concrete and abstract topics, including technical discussions in his/her field of specialisation. Can interact with a degree of fluency and spontaneity that makes regular interaction with native speakers quite possible without strain for either party. Can produce clear, detailed text on a wide range of subjects and explain a viewpoint on a topical issue giving the advantages and disadvantages of various options. |
|  | **B1** | Can understand the main points of clear standard input on familiar matters regularly encountered in work, school, leisure, etc. Can deal with most situations likely to arise whilst travelling in an area where the language is spoken. Can produce simple connected text on topics which are familiar or of personal interest. Can describe experiences and events, dreams, hopes and ambitions and briefly give reasons and explanations for opinions and plans. |
| **Basic User** | **A2** | Can understand sentences and frequently used expressions related to areas of most immediate relevance (e.g. very basic personal and family information, shopping, local geography, employment). Can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar and routine matters. Can describe in simple terms aspects of his/her background, immediate environment and matters in areas of immediate need. |
|  | **A1** | Can understand and use familiar everyday expressions and very basic phrases aimed at the satisfaction of needs of a concrete type. Can introduce him/herself and others and can ask and answer questions about personal details such as where he/she lives, people he/she knows and things he/she has. Can interact in a simple way provided the other person talks slowly and clearly and is prepared to help. |

<!-- el:end id=cefr2001_table_1_common_reference_levels_global_scale -->
""".strip()

TABLE2 = """
<!-- el:start type=table id=cefr2001_table_2_self_assessment_grid page=35 -->
<!-- db:id=cefr2001_table_2_self_assessment_grid type=table product_tier=base pages=35-36 -->
<!-- book-qa: stitched multipage self-assessment grid (Table 2); one db:id / full grid -->

**Table 2. Common Reference Levels: self-assessment grid** (stitched pages 35–36)

| Skill | A1 | A2 | B1 | B2 | C1 | C2 |
| --- | --- | --- | --- | --- | --- | --- |
| **Listening** | I can recognise familiar words and very basic phrases concerning myself, my family and immediate concrete surroundings when people speak slowly and clearly. | I can understand phrases and the highest frequency vocabulary related to areas of most immediate personal relevance (e.g. very basic personal and family information, shopping, local area, employment). I can catch the main point in short, clear, simple messages and announcements. | I can understand the main points of clear standard speech on familiar matters regularly encountered in work, school, leisure, etc. I can understand the main point of many radio or TV programmes on current affairs or topics of personal or professional interest when the delivery is relatively slow and clear. | I can understand extended speech and lectures and follow even complex lines of argument provided the topic is reasonably familiar. I can understand most TV news and current affairs programmes. I can understand the majority of films in standard dialect. | I can understand extended speech even when it is not clearly structured and when relationships are only implied and not signalled explicitly. I can understand television programmes and films without too much effort. | I have no difficulty in understanding any kind of spoken language, whether live or broadcast, even when delivered at fast native speed, provided I have some time to get familiar with the accent. |
| **Reading** | I can understand familiar names, words and very simple sentences, for example on notices and posters or in catalogues. | I can read very short, simple texts. I can find specific, predictable information in simple everyday material such as advertisements, prospectuses, menus and timetables and I can understand short simple personal letters. | I can understand texts that consist mainly of high frequency everyday or job-related language. I can understand the description of events, feelings and wishes in personal letters. | I can read articles and reports concerned with contemporary problems in which the writers adopt particular attitudes or viewpoints. I can understand contemporary literary prose. | I can understand long and complex factual and literary texts, appreciating distinctions of style. I can understand specialised articles and longer technical instructions, even when they do not relate to my field. | I can read with ease virtually all forms of the written language, including abstract, structurally or linguistically complex texts such as manuals, specialised articles and literary works. |
| **Spoken Interaction** | I can interact in a simple way provided the other person is prepared to repeat or rephrase things at a slower rate of speech and help me formulate what I'm trying to say. I can ask and answer simple questions in areas of immediate need or on very familiar topics. | I can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar topics and activities. I can handle very short social exchanges, even though I can't usually understand enough to keep the conversation going myself. | I can deal with most situations likely to arise whilst travelling in an area where the language is spoken. I can enter unprepared into conversation on topics that are familiar, of personal interest or pertinent to everyday life (e.g. family, hobbies, work, travel and current events). | I can interact with a degree of fluency and spontaneity that makes regular interaction with native speakers quite possible. I can take an active part in discussion in familiar contexts, accounting for and sustaining my views. | I can express myself fluently and spontaneously without much obvious searching for expressions. I can use language flexibly and effectively for social and professional purposes. I can formulate ideas and opinions with precision and relate my contribution skilfully to those of other speakers. | I can take part effortlessly in any conversation or discussion and have a good familiarity with idiomatic expressions and colloquialisms. I can express myself fluently and convey finer shades of meaning precisely. If I do have a problem I can backtrack and restructure around the difficulty so smoothly that other people are hardly aware of it. |
| **Spoken Production** | I can use simple phrases and sentences to describe where I live and people I know. | I can use a series of phrases and sentences to describe in simple terms my family and other people, living conditions, my educational background and my present or most recent job. | I can connect phrases in a simple way in order to describe experiences and events, my dreams, hopes and ambitions. I can briefly give reasons and explanations for opinions and plans. I can narrate a story or relate the plot of a book or film and describe my reactions. | I can present clear, detailed descriptions on a wide range of subjects related to my field of interest. I can explain a viewpoint on a topical issue giving the advantages and disadvantages of various options. | I can present clear, detailed descriptions of complex subjects integrating sub-themes, developing particular points and rounding off with an appropriate conclusion. | I can present a clear, smoothly flowing description or argument in a style appropriate to the context and with an effective logical structure which helps the recipient to notice and remember significant points. |
| **Writing** | I can write a short, simple postcard, for example sending holiday greetings. I can fill in forms with personal details, for example entering my name, nationality and address on a hotel registration form. | I can write short, simple notes and messages relating to matters in areas of immediate need. I can write a very simple personal letter, for example thanking someone for something. | I can write simple connected text on topics which are familiar or of personal interest. I can write personal letters describing experiences and impressions. | I can write clear, detailed text on a wide range of subjects related to my interests. I can write an essay or report, passing on information or giving reasons in support of or against a particular point of view. I can write letters highlighting the personal significance of events and experiences. | I can express myself in clear, well-structured text, expressing points of view at some length. I can write about complex subjects in a letter, an essay or a report, underlining what I consider to be the salient issues. I can select a style appropriate to the reader in mind. | I can write clear, smoothly flowing text in an appropriate style. I can write complex letters, reports or articles which present a case with an effective logical structure which helps the recipient to notice and remember significant points. I can write summaries and reviews of professional or literary works. |

<!-- el:end id=cefr2001_table_2_self_assessment_grid -->
""".strip()

FIG1 = """
<!-- el:start type=figure id=cefr2001_figure_01_common_reference_levels page=32 -->
<!-- db:id=cefr2001_figure_01_common_reference_levels type=figure product_tier=context pages=32 -->

**Figure 1.** Common Reference Levels branching principle:

| Broad | Levels | Labels |
| --- | --- | --- |
| **A Basic User** | A1 / A2 | Breakthrough / Waystage |
| **B Independent User** | B1 / B2 | Threshold / Vantage |
| **C Proficient User** | C1 / C2 | Effective Operational Proficiency / Mastery |

<!-- source render: work/cefr-en-2001/page_renders/page_032.png -->
<!-- el:end id=cefr2001_figure_01_common_reference_levels -->
""".strip()


def main() -> None:
    text = MD.read_text(encoding="utf-8")

    # Remove bad auto Table 1
    text = re.sub(
        r"<!-- el:start type=table id=cefr2001_table_1_[^>]+-->.*?<!-- el:end id=cefr2001_table_1_[^>]+-->",
        "",
        text,
        flags=re.S,
    )
    # Remove any previous good Table 1/2 to re-inject cleanly
    text = re.sub(
        r"<!-- el:start type=table id=cefr2001_table_1_common_reference_levels_global_scale[^>]*-->.*?<!-- el:end id=cefr2001_table_1_common_reference_levels_global_scale -->",
        "",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"<!-- el:start type=table id=cefr2001_table_2_self_assessment_grid[^>]*-->.*?<!-- el:end id=cefr2001_table_2_self_assessment_grid -->",
        "",
        text,
        flags=re.S,
    )
    # Remove fragment tables on 35-36
    text = re.sub(
        r"<!-- el:start type=table id=cefr2001_p03[56]_table_\d+[^>]*-->.*?<!-- el:end id=cefr2001_p03[56]_table_\d+ -->",
        "",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"<!-- el:start type=table id=cefr2001_table_2[^>]*-->.*?<!-- el:end id=cefr2001_table_2[^>]*-->",
        "",
        text,
        flags=re.S,
    )

    # Inject Table 1 before page:33 end marker body — after <!-- page:32 --> content, before <!-- page:33 -->
    if "cefr2001_table_1_common_reference_levels_global_scale" not in text:
        m = re.search(r"(Table 1\. Common Reference Levels: global scale)", text)
        if m:
            text = text[: m.start()] + TABLE1 + "\n\n" + text[m.start() :]
            print("injected Table 1 near title")
        else:
            m2 = re.search(r"<!-- page:33 -->", text)
            if m2:
                text = text[: m2.start()] + TABLE1 + "\n\n" + text[m2.start() :]
                print("injected Table 1 before page:33")

    if "cefr2001_table_2_self_assessment_grid" not in text:
        m = re.search(r"(Table 2\. Common Reference Levels: self-assessment grid)", text)
        if m:
            text = text[: m.start()] + TABLE2 + "\n\n" + text[m.start() :]
            print("injected Table 2 near title")
        else:
            m2 = re.search(r"<!-- page:35 -->", text)
            if m2:
                text = text[: m2.start()] + TABLE2 + "\n\n" + text[m2.start() :]
                print("injected Table 2 before page:35")

    if "cefr2001_figure_01_common_reference_levels" not in text:
        m2 = re.search(r"<!-- page:32 -->", text)
        if m2:
            text = text[: m2.start()] + FIG1 + "\n\n" + text[m2.start() :]
            print("injected Figure 1")
    else:
        print("Figure 1 already present")

    MD.write_text(text, encoding="utf-8")
    vdir = ROOT / "output/cefr-en-2001/versions/002"
    vdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MD, vdir / "CEFR_EN_2001.md")
    print(
        "ok",
        "chars",
        len(text),
        "type=table",
        text.count("type=table"),
        "t1",
        "cefr2001_table_1_common_reference_levels_global_scale" in text,
        "t2",
        "cefr2001_table_2_self_assessment_grid" in text,
        "fig1",
        "cefr2001_figure_01_common_reference_levels" in text,
    )


if __name__ == "__main__":
    main()
