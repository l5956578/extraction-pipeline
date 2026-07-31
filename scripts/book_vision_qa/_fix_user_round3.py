#!/usr/bin/env python3
"""User round-3 fixes: URL sanitization, callouts p29/31/37, headers, tables 175+180-181.

URLs are a *sanitization* issue (trailing footnote/punctuation glued into the URL
token), not an Obsidian-render-only issue.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
LOG_PATH = (
    ROOT
    / "work/cefr-companion-2020/metadata/book_qa/URL_CATALOG_AND_FIXES.md"
)

# Characters that may appear inside a real URL path/query
URL_BODY = re.compile(
    r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'*+,;=%]+"
)


def page_of(md: str, pos: int) -> int:
    m = re.search(r"<!-- page:(\d+) -->", md[pos:])
    return int(m.group(1)) if m else -1


def peel_url_token(raw: str) -> tuple[str, str]:
    """Split a greedy https?://\\S+ token into (clean_url, trailing_junk)."""
    if not raw.startswith("http"):
        return raw, ""
    # Start from full match; peel trailing junk that is never part of CoE URLs
    url = raw
    trail = ""
    # Peel markdown/punctuation/footnote glue from the end repeatedly
    changed = True
    while changed and url:
        changed = False
        for suf in ("**", "*", "”", "“", '"', "'", ">", "”", "“"):
            if url.endswith(suf):
                url = url[: -len(suf)]
                trail = suf + trail
                changed = True
        # trailing footnote digits only when preceded by non-hex path end
        m = re.search(r"([)\].,;:]+)(\d{1,2})$", url)
        if m:
            # e.g. )22  ).24  ,23  ;5
            url = url[: m.start()]
            trail = m.group(1) + m.group(2) + trail
            changed = True
            continue
        # lone trailing digits glued after letter/)/] (footnote) not after hex id
        m = re.search(r"([A-Za-z)/.\]])(\d{1,2})$", url)
        if m and not re.search(r"/[0-9a-fA-F]{6,}$", url[: m.start(2)] + "x"):
            # if ends like descriptions)22 or descriptors)16
            if url[m.start(1)] in ")]" or (
                url[m.start(1)].isalpha() and not re.search(r"/[0-9a-fA-F]{4,}\d{0,2}$", url)
            ):
                # only peel if looks like footnote after paren or after >
                if url[m.start(1)] in ")]":
                    url = url[: m.start(2)]
                    trail = m.group(2) + trail
                    changed = True
                    continue
        # trailing punctuation that is not URL
        if url and url[-1] in ",;:":
            # keep if query-like? generally peel
            if "?" not in url[-20:]:
                trail = url[-1] + trail
                url = url[:-1]
                changed = True
                continue
        if url.endswith(").") or url.endswith(");") or url.endswith("),"):
            trail = url[-2:] + trail
            url = url[:-2]
            changed = True
            continue
        if url.endswith(")"):
            # closing paren around URL is trail if URL is inside (url)
            trail = ")" + trail
            url = url[:-1]
            changed = True
            continue
        if url.endswith("."):
            # trailing period often sentence end; keep for path like .html
            if not re.search(r"\.[A-Za-z0-9]{1,6}$", url):
                trail = "." + trail
                url = url[:-1]
                changed = True
                continue
            # ends with .html. or .pdf. etc
            if re.search(r"\.(html|htm|pdf|aspx|php|asp)/?\.?$", url, re.I):
                if url.endswith("."):
                    trail = "." + trail
                    url = url[:-1]
                    changed = True
                    continue
    # restore one closing paren into trail structure is fine
    return url, trail


def sanitize_urls(md: str) -> tuple[str, list[str]]:
    """Clean every greedy URL token; rebuild correct surrounding form."""
    report: list[str] = []
    out: list[str] = []
    i = 0
    # Match optional angle open, url, optional junk
    # Also handle already-wrapped <https://...>
    token_re = re.compile(
        r"<?https?://[^\s<>]+>?"  # may include <url> or bare
    )

    while True:
        m = token_re.search(md, i)
        if not m:
            out.append(md[i:])
            break
        out.append(md[i : m.start()])
        raw = m.group(0)
        page = page_of(md, m.start())
        had_lt = raw.startswith("<")
        had_gt = raw.endswith(">")
        core = raw[1:-1] if had_lt and had_gt else raw.lstrip("<").rstrip(">")

        # If still has trailing junk inside, peel
        # First take longest plausible URL from start
        um = re.match(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'*+,;=%]+", core)
        if not um:
            out.append(raw)
            i = m.end()
            continue
        url = um.group(0)
        rest_in_core = core[len(url) :]
        # peel more from url if we over-ate
        url2, trail2 = peel_url_token(url + rest_in_core)
        if trail2 or rest_in_core or url2 != core:
            # determine reconstruction
            # After URL, original file may continue with more chars not in token
            after = md[m.end() : m.end() + 12]
            # Build: prefer keep angle wrap if footnote follows or was wrapped
            trail = trail2
            # Normalize double-paren footnote: URL was (http…))22 → trail starts with )22
            # Look at char before match
            before = md[max(0, m.start() - 2) : m.start()]
            rebuilt_trail = trail
            # If trail is )N or ).N or );N — fine
            # If trail is )N and before already has (, we need ).N or )N outside
            # User wants footnote OUTSIDE the URL token
            if re.match(r"\)+\d", rebuilt_trail):
                # ))22 style: one ) closes paren-url, rest is footnote
                # e.g. trail=)22 → ) + 22, or trail=))22
                mtrail = re.match(r"(\)+)([.,;]?)(\d{1,2})(.*)$", rebuilt_trail)
                if mtrail:
                    closes, punct, digits, extra = mtrail.groups()
                    # one close for the ( before URL
                    rebuilt_trail = ")" + (punct or ".") + digits + extra
            elif re.match(r",\d", rebuilt_trail):
                # ,23 after URL inside paren: → ).23 or ),23
                mtrail = re.match(r",(\d{1,2})(.*)$", rebuilt_trail)
                if mtrail:
                    rebuilt_trail = ")." + mtrail.group(1) + mtrail.group(2)
            elif re.match(r"\.\d", rebuilt_trail):
                pass  # ).24 already good if we have close paren
            elif re.match(r";\d", rebuilt_trail):
                pass
            elif re.match(r"\d{1,2}", rebuilt_trail):
                # bare digits after URL — need punctuation
                mtrail = re.match(r"(\d{1,2})(.*)$", rebuilt_trail)
                if mtrail:
                    # if before is ( then we need )
                    if before.endswith("(") or (len(before) >= 1 and md[m.start() - 1 : m.start()] == "("):
                        rebuilt_trail = ")." + mtrail.group(1) + mtrail.group(2)
                    else:
                        rebuilt_trail = mtrail.group(1) + mtrail.group(2)

            # Angle-wrap when followed by footnote-ish trail for safety
            needs_wrap = bool(re.search(r"\d", rebuilt_trail[:4])) or had_lt
            if needs_wrap:
                new = f"<{url2}>{rebuilt_trail}"
            else:
                new = url2 + rebuilt_trail

            if new != raw and (url2 != core.rstrip(">") or trail2):
                report.append(
                    f"p{page}: SANITIZE {raw[:80]!r} → {new[:80]!r}"
                )
            out.append(new)
        else:
            out.append(raw)
        i = m.end()

    new_md = "".join(out)

    # Specific known broken patterns (post-pass)
    replacements = [
        # p28 double-paren footnote 22
        (
            r"RLDs \(<?(https?://www\.coe\.int/en/web/common-european-framework-reference-languages/reference-level-descriptions)>?\)\)?\.?22",
            r"RLDs (<\1>).22",
        ),
        (
            r"RLDs \(<?(https?://www\.coe\.int/en/web/common-european-framework-reference-languages/reference-level-descriptions)>?\)\)22",
            r"RLDs (<\1>).22",
        ),
        # p29 fn 23 form (url),23
        (
            r"to the CEFR \(<?(https://rm\.coe\.int/1680667a2d)>?\),?\s*23",
            r"to the CEFR (<\1>).23",
        ),
        # p44 titles with ”,34 and ”,35
        (
            r"\(<?(https://rm\.coe\.int/1680697848)>?\)”?,?\s*34",
            r"(<\1>).34",
        ),
        (
            r"\(<?(https://transformingfsl\.ca/wp-content/uploads/2015/12/TAGGED_DOCUMENT_CSC605_Research_Guide_English_01\.pdf)>?\)?,?\s*35",
            r"(<\1>).35",
        ),
        # p45 mid-title URL split: framework and (url) portfolios
        (
            r"Common European framework and \(<?(https://rm\.coe\.int/168069ce6e)>?\) portfolios\*\*,?\s*38",
            r"Common European framework and portfolios** (<\1>).38",
        ),
        (
            r"Common European framework and \(<?(https://rm\.coe\.int/168069ce6e)>?\) portfolios",
            r"Common European framework and portfolios (<\1>)",
        ),
        # p24 ”.19
        (
            r"\(<?(https://rm\.coe\.int/168073ff31)>?\)”\.?\s*19",
            r"(<\1>).19",
        ),
        # bank supplementary )16
        (
            r"\(<?(https://www\.coe\.int/en/web/common-european-framework-reference-languages/bank-of-supplementary-descriptors)>?\)\s*16",
            r"(<\1>).16",
        ),
        # bibliography broken mid-word then URL (p272)
        (
            r"Executive summar \(<?(http://www\.oecd\.org/pisa/35070367\.pdf)>?\)y”",
            r"Executive summary” (<\1>)",
        ),
    ]
    for pat, repl in replacements:
        new_md, n = re.subn(pat, repl, new_md)
        if n:
            report.append(f"PATTERN {pat[:50]}… x{n}")

    # Fix remaining: (url))N or (url)N without angle
    def paren_fn(m: re.Match[str]) -> str:
        url, punct, digits = m.group(1), m.group(2) or ".", m.group(3)
        if not url.startswith("<"):
            url = f"<{url}>"
        elif not url.endswith(">"):
            url = url + ">"
        return f"({url}){punct}{digits}"

    new_md, n = re.subn(
        r"\((<?https?://[^)\s>]+>?)\)([.,;]?)(\d{1,2})\b",
        paren_fn,
        new_md,
    )
    if n:
        report.append(f"paren_fn normalize x{n}")

    # Collapse accidental <<url>>
    new_md = re.sub(r"<< (https?://[^>]+) >>", r"<\1>", new_md)
    new_md = re.sub(r"<<?(https?://[^>]+)>>?", r"<\1>", new_md)
    new_md = re.sub(r"\(<(<https?://[^>]+>)>\)", r"(\1)", new_md)

    return new_md, report


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
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


def fix_callouts(md: str) -> tuple[str, list[str]]:
    report: list[str] = []

    # --- p29: chapter list, one line each (PNG ground truth) ---
    p29 = page_body(md, 29)
    callout29 = """<!-- el:start type=artifact id=callout_a_reminder_of_cefr_2001_chapters page=29 -->
> **A reminder of CEFR 2001 chapters**
>
> Chapter 1: The Common European Framework in its political and educational context
>
> Chapter 2: Approach adopted
>
> Chapter 3: Common Reference Levels
>
> Chapter 4: Language use and the language user/learner
>
> Chapter 5: The user/learner’s competences
>
> Chapter 6: Language learning and teaching
>
> Chapter 7: Tasks and their role in language teaching
>
> Chapter 8: Linguistic diversification and the curriculum
>
> Chapter 9: Assessment
<!-- el:end id=callout_a_reminder_of_cefr_2001_chapters -->"""
    p29_new, n = re.subn(
        r"<!-- el:start type=artifact id=callout_a_reminder_of_cefr_2001_chapters page=29 -->.*?<!-- el:end id=callout_a_reminder_of_cefr_2001_chapters -->",
        callout29,
        p29,
        count=1,
        flags=re.S,
    )
    if n:
        md = replace_page(md, 29, p29_new)
        report.append("p29 callout: chapter list as separate lines (removed wrong relex URL soup)")
    else:
        report.append("p29 callout: PATTERN MISS")

    # --- p31: two paragraphs (PNG) ---
    p31 = page_body(md, 31)
    callout31 = """<!-- el:start type=artifact id=callout_p031_0 page=31 -->
> By a curious coincidence, 1996 was also the year in which the term “translanguaging” was first recorded (in relation to bilingual teaching in Wales). Translanguaging is an action undertaken by plurilingual persons, where more than one language may be involved. A host of similar expressions now exist, but all are encompassed by the term plurilingualism.
>
> Plurilingualism can in fact be considered from various perspectives: as a sociological or historical fact, as a personal characteristic or ambition, as an educational philosophy or approach, or – fundamentally – as the sociopolitical aim of preserving linguistic diversity. All these perspectives are increasingly common across Europe.
<!-- el:end id=callout_p031_0 -->"""
    p31_new, n = re.subn(
        r"<!-- el:start type=artifact id=callout_p031_0 page=31 -->.*?<!-- el:end id=callout_p031_0 -->",
        callout31,
        p31,
        count=1,
        flags=re.S,
    )
    if n:
        md = replace_page(md, 31, p31_new)
        report.append("p31 callout: 2 paragraphs (was 5 single-sentence lines)")
    else:
        report.append("p31 callout: PATTERN MISS")

    # --- p37: bold header + 2 paragraphs (PNG) ---
    p37 = page_body(md, 37)
    callout37 = """<!-- el:start type=artifact id=callout_p037_0 page=37 -->
> **Background to the CEFR levels**
>
> The six-level scheme is labelled upwards from A to C precisely because C2 is not the highest imaginable level for proficiency in an additional language. In fact, a scheme including a seventh level had been proposed by David Wilkins at an intergovernmental symposium held in 1977 to discuss a possible European unit credit scheme. The CEFR Working Party adopted Wilkins’ first six levels because Wilkins’ seventh level is beyond the scope of mainstream education.
>
> In the SNSF research project that empirically confirmed the levels and developed the CEFR illustrative descriptors published in 2001, the existence of this seventh level was confirmed. There were user/learners studying interpretation and translation at the University of Lausanne who were clearly above C2. Indeed, simultaneous interpreters at European institutions and professional translators operate at a level well above C2. For instance, C2 is the third of five levels for literary translation recently produced in the PETRA project. In addition many plurilingual writers display Wilkins’ seventh level of “ambilingual proficiency” without being bilingual from birth.
<!-- el:end id=callout_p037_0 -->"""
    p37_new, n = re.subn(
        r"<!-- el:start type=artifact id=callout_p037_0 page=37 -->.*?<!-- el:end id=callout_p037_0 -->",
        callout37,
        p37,
        count=1,
        flags=re.S,
    )
    if n:
        md = replace_page(md, 37, p37_new)
        report.append("p37 callout: bold header + 2 paragraphs (was 8 lines)")
    else:
        report.append("p37 callout: PATTERN MISS")

    return md, report


def fix_merged_headers(md: str) -> tuple[str, list[str]]:
    report: list[str] = []
    pairs = [
        (
            r"\*\*3\.4\.2\.1\.\s*Strategies to explain a new concept\s+Linking to previous knowledge\*\*",
            "**3.4.2.1. Strategies to explain a new concept**\n\n**Linking to previous knowledge**",
            "p118/119 strategies explain + Linking",
        ),
        (
            r"\*\*3\.4\.2\.2\.\s*Strategies to simplify a text\s+Amplifying a dense text\*\*",
            "**3.4.2.2. Strategies to simplify a text**\n\n**Amplifying a dense text**",
            "p121 strategies simplify + Amplifying",
        ),
    ]
    for pat, repl, label in pairs:
        md, n = re.subn(pat, repl, md)
        report.append(f"header {label}: {n} fix(es)")

    # General scan: **N.N.N. TitleCase phrase TitleCase phrase**
    def split_bold_header(m: re.Match[str]) -> str:
        num, rest = m.group(1), m.group(2)
        # split after first phrase when second starts with capital known scale verbs/nouns
        parts = re.split(
            r"(?<=[a-z])\s+(?=(?:Linking|Amplifying|Streamlining|Planning|Compensating|Monitoring|Taking|Co-operating|Asking|Building|Facilitating|Acting|Mediating|Expressing|Collaborating|Leading|Establishing|Developing)\b)",
            rest,
        )
        if len(parts) == 2:
            return f"**{num} {parts[0].strip()}**\n\n**{parts[1].strip()}**"
        return m.group(0)

    md2, n = re.subn(
        r"\*\*(\d+\.\d+(?:\.\d+)*\.)\s+([^*\n]{15,120})\*\*",
        split_bold_header,
        md,
    )
    if n:
        report.append(f"general bold header scan touches: {n}")
    return md2, report


def fix_table_175(md: str) -> tuple[str, list[str]]:
    """3-col user-band | level | descriptor (PNG p175)."""
    report: list[str] = []
    table = """<!-- el:start type=artifact id=scale_proficient_user page=175 -->
<!-- db:id=table_common_reference_levels_global type=descriptor_scale product_tier=base pages=175 -->

| | | |
| --- | --- | --- |
| **Proficient user** | **C2** | Can understand virtually all types of texts. Can summarise information from different oral and written sources, reconstructing arguments and accounts in a coherent presentation. Can express themselves spontaneously, very fluently and precisely, differentiating finer shades of meaning even in more complex situations. |
| | **C1** | Can understand a wide range of demanding, longer texts, and recognise implicit meaning. Can express themselves fluently and spontaneously without much obvious searching for expressions. Can use language flexibly and effectively for social, academic and professional purposes. Can produce clear, well-structured, detailed text on complex subjects, showing controlled use of organisational patterns, connectors and cohesive devices. |
| **Independent user** | **B2** | Can understand the main ideas of complex text on both concrete and abstract topics, including technical discussions in their field of specialisation. Can interact with a degree of fluency and spontaneity that makes regular interaction with users of the target language quite possible without imposing strain on either party. Can produce clear, detailed text on a wide range of subjects and explain a viewpoint on a topical issue giving the advantages and disadvantages of various options. |
| | **B1** | Can understand the main points of clear standard input on familiar matters regularly encountered in work, school, leisure, etc. Can deal with most situations likely to arise while travelling in an area where the language is spoken. Can produce simple connected text on topics which are familiar or of personal interest. Can describe experiences and events, dreams, hopes and ambitions and briefly give reasons and explanations for opinions and plans. |
| **Basic user** | **A2** | Can understand sentences and frequently used expressions related to areas of most immediate relevance (e.g. very basic personal and family information, shopping, local geography, employment). Can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar and routine matters. Can describe in simple terms aspects of their background, immediate environment and matters in areas of immediate need. |
| | **A1** | Can understand and use familiar everyday expressions and very basic phrases aimed at the satisfaction of needs of a concrete type. Can introduce themselves and others and can ask and answer questions about personal details such as where someone lives, people they know and things they have. Can interact in a simple way provided the other person talks slowly and clearly and is prepared to help. |
<!-- el:end id=scale_proficient_user -->"""

    p175 = page_body(md, 175)
    p175_new, n = re.subn(
        r"<!-- el:start type=artifact id=scale_proficient_user[^>]*-->.*?<!-- el:end id=scale_proficient_user -->",
        table,
        p175,
        count=1,
        flags=re.S,
    )
    if n:
        md = replace_page(md, 175, p175_new)
        report.append("p175: 3-column user-band table (Proficient/Independent/Basic + blank continuation rows)")
    else:
        report.append("p175: PATTERN MISS")
    return md, report


def fix_mediation_self_assessment(md: str) -> tuple[str, list[str]]:
    """Merge Mediating communication as 3rd column; one Mediation table (user p180-181)."""
    report: list[str] = []
    p177 = page_body(md, 177)

    # Text from PDF pages 180-181 (levels as rows for MD readability)
    mediation = """## Mediation

| Level | Mediating a text | Mediating concepts | Mediating communication |
| --- | --- | --- | --- |
| A1 | I can convey simple, predictable information given in short, simple texts like signs and notices, posters and programmes. | I can invite other people’s contributions using short, simple phrases. I can use simple words/signs and signals to show my interest in an idea and to confirm that I understand. I can express an idea very simply and ask others whether they understand me and what they think. | I can facilitate communication by showing my welcome and interest with simple words/signs and non-verbal signals, by inviting others to contribute and indicating whether I understand. I can communicate other people’s personal details and very simple, predictable information, provided other people help me with formulation. |
| A2 | I can convey the main point(s) involved in short, simple texts on everyday subjects of immediate interest, provided these are expressed clearly in simple language. | I can collaborate in simple, practical tasks, asking what others think, making suggestions and understanding responses, provided I can ask for repetition or reformulation from time to time. I can make suggestions in a simple way to move the discussion forward and can ask what people think of certain ideas. | I can contribute to communication by using simple words/signs to invite people to explain things, indicating when I understand and/or agree. I can communicate the main point of what is said in predictable, everyday situations about personal wants and needs. I can recognise when people disagree or when difficulties occur and can use simple phrases to seek compromise and agreement. |
| B1 | I can convey information given in clear, well-structured informational texts on subjects that are familiar or of personal or current interest. | I can help define a task in basic terms and ask others to contribute their expertise. I can invite other people to contribute, to clarify the reason(s) for their views or to elaborate on specific points they have made. I can ask appropriate questions to check understanding of concepts and can repeat back part of what someone has said to confirm mutual understanding. | I can support a shared culture by introducing people, exchanging information about priorities, and making simple requests for confirmation and/or clarification. I can communicate the main sense of what is said on subjects of personal interest, provided speakers articulate clearly and I can pause to plan how to express things. |
| B2 | I can convey detailed information and arguments reliably, e.g. the significant point(s) contained in complex but well-structured texts within my fields of professional, academic and personal interest. | I can encourage participation and pose questions that invite reactions from other group members or ask people to expand on their thinking and clarify their opinions. I can further develop other people’s ideas and link them into coherent lines of thinking, considering different sides of an issue. | I can encourage a shared culture by adapting the way I proceed, by expressing appreciation of different ideas, feelings and viewpoints, and by inviting participants to react to each other’s ideas. I can communicate the significance of important statements and viewpoints on subjects within my fields of interest, provided speakers give clarifications if needed. |
| C1 | I can convey clearly and fluently in well-structured language the significant ideas in long, complex texts, whether or not they relate to my own fields of interest, provided I can occasionally check particular technical concepts. | I can acknowledge different perspectives in guiding a group, asking a series of open questions that build on different contributions in order to stimulate logical reasoning, reporting on what others have said, summarising, elaborating and weighing up multiple points of view, and tactfully helping steer discussion towards a conclusion. | I can mediate a shared culture by managing ambiguity, demonstrating sensitivity to different viewpoints and heading off misunderstandings. I can communicate significant information clearly, fluently and concisely, and explain cultural references. I can use persuasive language diplomatically. |
| C2 | I can explain in clear, fluent, well-structured language the way facts and arguments are presented, conveying evaluative aspects and most nuances precisely, and pointing out sociocultural implications (e.g. use of register, understatement, irony and sarcasm). | I can guide the development of ideas in a discussion of complex abstract topics, encouraging others to elaborate on their reasoning, summarising, evaluating and linking the various contributions in order to create agreement for a solution or way forward. | I can mediate effectively and naturally between members of my own and other communities, taking account of sociocultural and sociolinguistic differences and communicating finer shades of meaning. |
"""

    # Replace from first ## Mediation through end of second mediation table
    p177_new, n = re.subn(
        r"## Mediation\n\n\| Level \| Mediating a text \| Mediating concepts \|.*?\| C2 \| I can mediate effectively and naturally between members of my own and other communities, taking account of sociocultural and sociolinguistic differences and communicating finer shades of meaning\. \|\n",
        mediation + "\n",
        p177,
        count=1,
        flags=re.S,
    )
    if n:
        md = replace_page(md, 177, p177_new)
        report.append(
            "p177: mediation self-assessment = ONE table with columns text|concepts|communication (removed duplicate second table)"
        )
    else:
        # try looser: replace both mediation sections
        p177_new2, n2 = re.subn(
            r"## Mediation\n\n\| Level \| Mediating a text.*?(?=<!-- el:end id=table_self_assessment)",
            mediation + "\n",
            p177,
            count=1,
            flags=re.S,
        )
        if n2:
            md = replace_page(md, 177, p177_new2)
            report.append("p177: mediation merged (looser match)")
        else:
            report.append("p177 mediation: PATTERN MISS")

    # Ensure 180/181 remain continuity-only (content lives in single grid on 177)
    for p in (180, 181):
        b = page_body(md, p)
        if "Mediating" in b and b.count("|") > 10:
            note = (
                f"<!-- table-continuity: self-assessment mediation columns live in single table on page 177 "
                f"(Mediating a text | Mediating concepts | Mediating communication); page {p} PDF slice not duplicated -->\n\n"
            )
            # keep chrome only
            chrome = ""
            for line in b.splitlines():
                if "Page" in line and ("**" in line or "▶" in line):
                    chrome = line
            new_b = note + (chrome + "\n" if chrome else "")
            md = replace_page(md, p, new_b)
            report.append(f"p{p}: cleared residual mediation slice (merged into p177)")
    return md, report


def catalog_urls(md: str) -> list[str]:
    lines = ["# URL catalog (post-sanitize scan)", ""]
    lines.append("| Page | Form | Snippet |")
    lines.append("|-----:|------|---------|")
    for m in re.finditer(r"https?://\S{5,200}", md):
        page = page_of(md, m.start())
        raw = m.group(0)
        ctx = md[max(0, m.start() - 25) : m.end() + 15].replace("\n", " ")
        # flag residual junk
        flag = ""
        if re.search(r"[)\].,;:]\d{1,2}$", raw) or re.search(r"\d{1,2}$", raw) and not re.search(
            r"/[0-9a-fA-F]{6,}", raw
        ):
            if re.search(r"(?:[)\].,;:]|html|pdf|aspx)\d{1,2}$", raw, re.I):
                flag = " **RESIDUAL?**"
        if " " in raw:
            flag = " **SPACE**"
        lines.append(f"| {page} | `{raw[:90]}`{flag} | …{ctx[:100]}… |")
    return lines


def residual_bad_urls(md: str) -> list[str]:
    bad = []
    for m in re.finditer(r"https?://\S+", md):
        raw = m.group(0)
        page = page_of(md, m.start())
        # residual: footnote digits still in token
        if re.search(r"\)\d{1,2}$", raw) or re.search(r"[.,;]\d{1,2}$", raw):
            bad.append(f"p{page}: {raw[:100]}")
        if re.search(r"https?://[^\\s]+\)\d", raw):
            bad.append(f"p{page} glue: {raw[:100]}")
        # url ends with ),23 style inside token
        if re.search(r",\d{1,2}$", raw):
            bad.append(f"p{page} comma-fn: {raw[:100]}")
    return bad


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    all_report: list[str] = []

    md, r = sanitize_urls(md)
    all_report += ["## URL sanitize", *r]

    md, r = fix_callouts(md)
    all_report += ["## Callouts", *r]

    md, r = fix_merged_headers(md)
    all_report += ["## Headers", *r]

    md, r = fix_table_175(md)
    all_report += ["## Table 175", *r]

    md, r = fix_mediation_self_assessment(md)
    all_report += ["## Self-assessment mediation 180-181", *r]

    # blank line after comment before tables
    md = re.sub(r"(-->)\n(\|)", r"\1\n\n\2", md)

    MD_PATH.write_text(md, encoding="utf-8")

    bad = residual_bad_urls(md)
    all_report += ["## Residual URL issues after fix", *(bad or ["(none detected by residual scanner)"])]

    catalog = catalog_urls(md)
    LOG_PATH.write_text(
        "\n".join(
            [
                "# User round-3 — URLs, callouts, headers, tables",
                "",
                "Source: user chat review (through Appendix 3 / self-assessment).",
                "",
                "**URL note:** This is a **sanitization** defect class (footnote/punctuation glued into the URL token), not an Obsidian-only render quirk.",
                "",
                *all_report,
                "",
                *catalog,
            ]
        ),
        encoding="utf-8",
    )
    for line in all_report:
        print(line)
    print("--- residual bad", len(bad))
    for b in bad[:30]:
        print(" ", b)


if __name__ == "__main__":
    main()
