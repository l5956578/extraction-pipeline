"""Insert figure assets and strip flattened diagram labels without removing prose."""

from __future__ import annotations

import re

from pipeline.toc_zone import is_toc_listing_line

_PROSE_START = re.compile(
    r"^(?:The |In |As |It |This |Although |One |A1,|Level |Mastery |Plus |All |Figure \d+,|"
    r"Key aspects|Page \d|Chapter |\d+\.\d+\.|With |Graphic |Profiles |Neither |Language |"
    r"By |Most |Mediation |At |However|Seeing |To |For |An |When |After |Before )",
)
_LEVEL_ONLY = re.compile(r"^(?:C2|C1|B2|B1|A2|A1|Pre-A1)$")
_CAPS_LABEL = re.compile(r"^[A-Z][A-Z /-]{2,}$")
_FIG_NUM = re.compile(r"^\*{0,2}\s*Figure\s+(\d+)\b", re.I)
_DB_FIG = re.compile(
    r"<!--\s*db:id=(figure_\d+_[^\s>]+)\s+type=figure[^>]*-->",
    re.I,
)


def _normalize_caption(line: str) -> str:
    s = re.sub(r"\s+", " ", line.strip())
    s = re.sub(r"\d+$", "", s)
    for dash in ("–", "—", "−"):
        s = s.replace(dash, "-")
    return s.lower()


def _figure_number_from_header(header: str) -> str | None:
    m = re.search(r"Figure\s+(\d+)", header, re.I)
    return m.group(1) if m else None


def _caption_matches(line: str, header: str) -> bool:
    """Match real figure captions only — not in-prose 'Figure 2, which appeared…'."""
    s = line.strip()
    if s.startswith("<!--"):
        return False
    if is_toc_listing_line(s):
        return False

    def _plain(x: str) -> str:
        x = re.sub(r"^\*+\s*", "", x.strip())
        x = re.sub(r"\s*\*+$", "", x)
        return re.sub(r"\s+", " ", x)

    # ### Figure N – title | id
    if s.startswith("### "):
        body = s.removeprefix("### ").split(" | ", 1)[0]
        norm_header = _normalize_caption(header)
        norm_line = _normalize_caption(body)
        if norm_line == norm_header or norm_line.startswith(norm_header):
            return True
        hn = _figure_number_from_header(header)
        ln = _figure_number_from_header(body)
        return bool(hn and ln and hn == ln)

    plain = _plain(s)
    # Require caption form: Figure N – Title (dash separator). Reject "Figure N, which…"
    if not re.match(r"^Figure\s+\d+\s*[–—\-]\s+\S", plain, re.I):
        return False

    norm_header = _normalize_caption(header)
    norm_line = _normalize_caption(plain)
    if norm_line == norm_header:
        return True
    if norm_line.startswith(norm_header[: min(40, len(norm_header))]):
        return True
    hn = _figure_number_from_header(header)
    ln = _figure_number_from_header(plain)
    # Dash-caption form already required above; number must match.
    return bool(hn and ln and hn == ln)


# Radar / needs-profile axis fragments (Figs 6–10) when OCR/text dump under PNG.
_RADAR_FRAG = re.compile(
    r"(Understanding conversation between other|Expressing a personal response|"
    r"Relaying specific information|Processing text in (?:speech|writing)|"
    r"Collaborating to construct meaning|Facilitating collaborative|"
    r"Facilitating pluricultural|Sustained monologue|Reading for orientation|"
    r"Reading for information|Reading as a leisure|Reading instructions|"
    r"Goal-oriented (?:co-operation|online)|Informal discussion|"
    r"Formal discussion|Understanding an interlocutor|"
    r"Watching TV, film and video|Creative writing|Reports and essays|"
    r"Addressing audiences|Encouraging conceptual|Explaining data|"
    r"Note-taking \(lectures|Online conversation and discussion|"
    r"Information exchange)",
    re.I,
)
# Mode axis header alone (not "Reception involves…" body prose — R1 / p.47 lead).
_MODE_HDR = re.compile(
    r"^\*{0,2}\s*(RECEPTION|PRODUCTION|INTERACTION|MEDIATION)\*{0,2}\s*$",
    re.I,
)


_LEVEL_ROW = re.compile(
    r"(?:Pre-A1|A1|A2\+?|B1\+?|B2\+?|C1|C2|Above C2)",
    re.I,
)
_LANG_AXIS = re.compile(
    r"\b(English|German|French|Spanish|Italian|Portuguese|Dutch|Russian)\b",
    re.I,
)

# text_diagram leaf / activity titles (Figs 1, 11–17 class) dual-emitted as prose (R1 p.47, Fig 12/13).
# MUST include every leaf of figures_catalog text diagrams — dual-emit after ``` is recurring.
_DIAGRAM_LEAF_PHRASES = (
    "Overall oral comprehension",
    "Understanding conversation between other people",
    "Understanding as a member of a live audience",
    "Understanding announcements and instructions",
    "Understanding audio (or signed) media and recordings",
    "Audio-visual comprehension",
    "Watching TV, film and video",
    "Overall reading comprehension",
    "Reading correspondence",
    "Reading for orientation",
    "Reading for information and argument",
    "Reading instructions",
    "Reading as a leisure activity",
    "Identifying cues and inferring",
    "Oral comprehension",
    "Reading comprehension",
    "Reception activities",
    "Reception strategies",
    "Production activities",
    "Production strategies",
    "Interaction activities",
    "Interaction strategies",
    "Mediation activities",
    "Mediation strategies",
    # Figure 12 production leaves (user p.61 dual-emit trash)
    "Overall oral production",
    "Overall written production",
    "Sustained monologue: describing experience",
    "Sustained monologue: giving information",
    "Sustained monologue: putting a case",
    "Public announcements",
    "Addressing audiences",
    "Creative writing",
    "Reports and essays",
    "Planning",
    "Compensating",
    "Monitoring and repair",
    # Figure 13 interaction leaves
    "Overall oral interaction",
    "Understanding an interlocutor",
    "Conversation",
    "Informal discussion",
    "Formal discussion",
    "Goal-oriented co-operation",
    "Obtaining goods and services",
    "Information exchange",
    "Interviewing and being interviewed",
    "Using telecommunications",
    "Overall written interaction",
    "Correspondence",
    "Notes, messages and forms",
    "Online conversation and discussion",
    "Goal-oriented online transactions and collaboration",
    "Turntaking",
    "Cooperating",
    "Clarifying",
    "Overall language proficiency",
    "General competences",
    "Communicative language competences",
    "Communicative language activities",
    "Communicative language strategies",
)
_DIAGRAM_LEAF_RE = re.compile(
    r"|".join(re.escape(p) for p in sorted(_DIAGRAM_LEAF_PHRASES, key=len, reverse=True)),
    re.I,
)
# Doubled / glued tree fragments: "Audio-visual  Oral comprehension comprehension"
_DOUBLED_COMPREHENSION = re.compile(
    r"comprehension\s+comprehension|"
    r"Audio-visual.{0,40}Oral comprehension|"
    r"Overall oral.{0,40}Watching TV|"
    r"Overall reading.{0,40}Identifying cues|"
    r"comprehension\s+and\s+video|"
    r"comprehension\s+and\s+inferring",
    re.I,
)


def _is_text_diagram_leaf_soup_line(line: str) -> bool:
    """Flattened text_diagram activity titles left as prose (R1 p.47 Fig 11)."""
    s = line.strip()
    if not s or s.startswith(("#", "!", "<!--", "|", ">", "```")):
        return False
    if any(ch in s for ch in ("├", "└", "│", "─")):
        return False
    # Never treat real §3.1 lead as soup
    if s.startswith("Reception involves") or "schemata" in s.lower():
        return False
    plain = re.sub(r"^\*+|\*+$", "", s).strip()
    plain = re.sub(r"\s+", " ", plain)
    plain_l = plain.lower()
    leaf_set = {p.lower() for p in _DIAGRAM_LEAF_PHRASES}
    # Exact leaf title (with optional bold already stripped)
    if plain_l in leaf_set:
        return True
    if _DIAGRAM_LEAF_RE.fullmatch(plain):
        return True
    # Bold/glued multi-leaf dumps without sentence end
    if _DOUBLED_COMPREHENSION.search(plain):
        return True
    # Real sentences keep
    if plain.endswith((".", "?", "!")) and len(plain) > 80:
        return False
    if not plain.endswith((".", "?", "!")) and len(plain) < 160:
        hits = _DIAGRAM_LEAF_RE.findall(plain)
        if len(hits) >= 2:
            return True
        # Single known leaf as whole line or with light bold/debris
        if plain_l in leaf_set:
            return True
        # Title-case activity fragment: Understanding / Reading / Watching / Overall …
        if re.match(
            r"^(Understanding|Reading|Watching|Overall|Identifying|Audio-visual)\b",
            plain,
            re.I,
        ) and len(plain.split()) <= 14:
            if not re.search(
                r"\b(involves|receives|processes|user|schema|hypothesis|provided)\b",
                plain,
                re.I,
            ):
                return True
    return False


def _is_level_language_row(line: str) -> bool:
    """Multi-level / language axis row under profile PNGs (review #2 p.40 Fig 10)."""
    s = line.strip()
    plain = re.sub(r"\*+", "", s)
    plain = re.sub(r"\s+", " ", plain).strip()
    levels = _LEVEL_ROW.findall(plain)
    langs = _LANG_AXIS.findall(plain)
    if len(levels) >= 4:
        return True
    if len(levels) >= 2 and len(langs) >= 2:
        return True
    if len(langs) >= 3 and not plain.endswith((".", "?", "!")):
        return True
    return False


def _is_radar_axis_soup_line(line: str) -> bool:
    """True for figure-specific label dumps under profile PNGs (log 04 #8)."""
    s = line.strip()
    if not s or s.startswith(("#", "!", "<!--", "|", ">", "```")):
        return False
    if _is_level_language_row(s):
        return True
    if _RADAR_FRAG.search(s):
        return True
    if _MODE_HDR.match(s):
        return True
    # Level tokens alone or glued to axis labels
    if re.match(r"^\*{0,2}(A1|A2|B1|B2|C1|C2|Pre-A1)\*{0,2}(\s|$)", s) and len(s) < 120:
        if _RADAR_FRAG.search(s) or _MODE_HDR.search(s) or len(s) < 40 or _LEVEL_ROW.search(s):
            return True
    # Multi short Title-Case segments without sentence end → axis list
    if not s.endswith((".", "?", "!")) and len(s) < 200:
        if s.count("  ") >= 1 and re.search(
            r"(Reading|Understanding|Relaying|Processing|Collaborating|Facilitating)",
            s,
            re.I,
        ):
            return True
    return False


def _is_label_soup_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if re.match(r"^Figure\s+\d+\s*–", s, re.I) or re.match(r"^\*\*Figure\s+\d+", s, re.I):
        # Polluted caption lines are soup once we've already emitted a clean block.
        return True
    if _is_text_diagram_leaf_soup_line(s):
        return True
    if _is_radar_axis_soup_line(s):
        return True
    if _is_level_language_row(s):
        return True
    # Real body prose after figures (keep) — check early, before radar/mode heuristics
    if s.startswith("Reception involves") or s.startswith("Mediation between"):
        return False
    if _PROSE_START.match(s) and not _is_radar_axis_soup_line(s):
        if s.startswith("However,") or s.startswith("The profile"):
            return False
        if len(s) > 100 and s.endswith((".", "?", "!")):
            return False
        if (
            not _RADAR_FRAG.search(s)
            and not _is_level_language_row(s)
            and not _is_text_diagram_leaf_soup_line(s)
        ):
            return False
    # Long finished sentences are never soup (neighbor protection)
    if len(s) > 100 and s.endswith((".", "?", "!")) and not _is_level_language_row(s):
        if not _is_text_diagram_leaf_soup_line(s) and not _DOUBLED_COMPREHENSION.search(s):
            return False
    if s.startswith("<!--") or s.startswith("![") or s.startswith("### "):
        return False
    if s.startswith("```"):
        return False
    # Keep structured text diagrams / tree characters
    if any(ch in s for ch in ("├", "└", "│", "─")):
        return False
    if _LEVEL_ONLY.match(s):
        return True
    if _CAPS_LABEL.match(s):
        return True
    # Flattened diagram rows: "Linguistic Savoir Reception Reception"
    soup_tokens = {
        "linguistic", "sociolinguistic", "pragmatic", "savoir", "savoir-faire",
        "savoir-être", "savoir", "apprendre", "reception", "production",
        "interaction", "mediation", "general", "competences", "communicative",
        "language", "activities", "strategies", "overall", "proficiency",
        "comprehension", "oral", "reading", "audio", "visual", "identifying",
        "cues", "inferring", "watching", "tv", "film", "video", "correspondence",
        "orientation", "instructions", "announcements", "audience", "media",
        "recordings", "leisure", "argument", "conversation", "people", "member",
        "live", "signed",
    }
    words = re.findall(r"[A-Za-zÀ-ÿ+\-]+", s.lower())
    soup_tokens |= {
        "language", "competences", "activities", "strategies",
        "overall", "general", "communicative", "proficiency",
    }
    if words and len(s) < 160 and all(
        w in soup_tokens or w in {"and", "or", "the", "of", "a", "as", "for", "between", "other"}
        for w in words
    ):
        return True
    # Bold multi-token competence soup after diagrams
    plain = re.sub(r"^\*+|\*+$", "", s).strip()
    if s.startswith("**") and len(s) < 280:
        if _is_level_language_row(s) or _is_text_diagram_leaf_soup_line(s):
            return True
        if sum(
            1
            for k in (
                "proficiency",
                "communicative",
                "competences",
                "savoir",
                "reception",
                "production",
                "comprehension",
            )
            if k in plain.lower()
        ) >= 2:
            return True
    # Short-line soup ONLY when diagram-ish tokens present (review #4)
    if len(s) < 90 and not s.endswith((".", ";", ":", "?", "!")):
        words2 = s.split()
        if len(words2) <= 8 and not s.startswith("#"):
            if (
                _LEVEL_ONLY.match(plain)
                or _CAPS_LABEL.match(plain)
                or _MODE_HDR.match(s)
                or _RADAR_FRAG.search(s)
                or _is_level_language_row(s)
                or _is_text_diagram_leaf_soup_line(s)
                or re.search(
                    r"\b(RECEPTION|PRODUCTION|INTERACTION|MEDIATION|A1|A2|B1|B2|C1|C2)\b",
                    plain,
                    re.I,
                )
            ):
                return True
            if s[0].islower() and len(s) < 40:
                return True
    return False


def _drop_soup_run(lines: list[str], start: int) -> int:
    """Advance index past soup lines; stop at structure or real prose."""
    j = start
    while j < len(lines):
        s = lines[j].strip()
        if not s:
            j += 1
            continue
        if s.startswith(
            ("<!-- page:", "<!-- db:id=", "<!-- el:", "### ", "## ", "| ", "> ")
        ) or re.match(r"^\d+\.\t", s) or re.match(r"^Page\s+\*\*", s) or re.match(
            r"^\*Page\s+\*\*", s
        ):
            break
        if (
            _is_label_soup_line(lines[j])
            or _is_radar_axis_soup_line(s)
            or _is_text_diagram_leaf_soup_line(s)
        ):
            j += 1
            continue
        # Long real sentence → keep
        if len(s) > 90 and s.endswith((".", "?", "!")) and not _RADAR_FRAG.search(s):
            if not _is_text_diagram_leaf_soup_line(s):
                break
        break
    return j


def strip_garbage_under_figure_images(text: str) -> str:
    """Remove figure-specific label dumps under PNG/text_diagram (replace semantics).

    Dual-emission fix (C2-ADJ / log 04 #8 / R1 p.47): when a PNG or text_diagram
    is present, do not leave the old rich_page diagram text underneath. Also
    drops leaf-title soup that appears after intervening real prose (e.g. after
    §3.1 lead following Fig 11), and level/language axis rows between multi-fig
    blocks (p.40 Fig 10 labels before db:id).
    """
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        is_img = bool(
            re.search(r"!\[[^\]]*\]\([^)]*figure_\d+[^)]*\.png\)", line)
        )
        # Closing fence of ```text diagram
        is_diagram_end = (
            line.strip() == "```"
            and i > 0
            and "```text" in "\n".join(lines[max(0, i - 40) : i])
        )
        if is_img or is_diagram_end:
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                out.append(lines[j])
                j += 1
            j = _drop_soup_run(lines, j)
            i = j
            continue
        i += 1
    text = "\n".join(out)
    text = strip_text_diagram_leaf_soup_global(text)
    return strip_figure_axis_soup_global(text)


def strip_figure_axis_soup_global(text: str) -> str:
    """Drop level/language axis rows on figure pages (even between figure blocks).

    p.40 residual: ``**Pre-A1 A1 …** **… English German…**`` between Fig 9 and 10.
    """
    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    on_figure_page = False
    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        if s.startswith("<!-- page:"):
            on_figure_page = False
            out.append(line)
            continue
        if re.search(r"db:id=figure_\d+|!\[[^\]]*\]\([^)]*figure_\d+", s):
            on_figure_page = True
        if on_figure_page and (
            _is_level_language_row(s) or _is_radar_axis_soup_line(s)
        ):
            # Keep table rows and real prose
            if s.startswith("|"):
                out.append(line)
                continue
            continue
        out.append(line)
    return "\n".join(out)


def strip_text_diagram_leaf_soup_global(text: str) -> str:
    """Drop dual-emitted leaf titles after a text_diagram ``` fence until el:end / page.

    R1 p.47 + Fig 12/13 p.61/71: leaves already inside the fence reappear as bare
    prose lines (``Public announcements``, ``Planning``, …). Never touches
    content *inside* ``` fences. Never drops real sentences (ending .?!, length).
    """
    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    after_text_diagram = False
    fence_leaves: set[str] = set()  # leaves seen in the most recent ```text fence
    for line in lines:
        s = line.strip()
        if s.startswith("```"):
            if not in_fence and (s.startswith("```text") or s == "```"):
                after_text_diagram = s.startswith("```text") or after_text_diagram
                if s.startswith("```text"):
                    fence_leaves = set()
            elif in_fence:
                # closing fence — stay after_text_diagram until page/el:end
                pass
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            # Harvest leaf labels from tree lines for post-fence soup match
            plain = re.sub(r"^[│├└─\s]+", "", s)
            plain = re.sub(r"^\*+|\*+$", "", plain).strip()
            if plain and len(plain) < 80 and not plain.startswith("#"):
                fence_leaves.add(plain.lower())
            out.append(line)
            continue
        if s.startswith("<!-- page:") or s.startswith("<!-- el:end"):
            after_text_diagram = False
            fence_leaves = set()
            out.append(line)
            continue
        # Real section headers / body prose after the figure are NOT soup
        if re.match(r"^#{1,4}\s+\d", s) or re.match(r"^\*\*\d+\.\d+", s):
            after_text_diagram = False
            out.append(line)
            continue
        if after_text_diagram:
            plain = re.sub(r"^\*+|\*+$", "", s).strip()
            plain_l = plain.lower()
            # Exact leaf from the fence we just closed (strongest signal)
            if plain_l in fence_leaves and not plain.endswith((".", "?", "!")):
                continue
            if _is_text_diagram_leaf_soup_line(line):
                continue
            if _is_label_soup_line(line) and not (
                len(s) > 90 and s.endswith((".", "?", "!"))
            ):
                if _DOUBLED_COMPREHENSION.search(s) or (
                    not s.endswith((".", "?", "!"))
                    and _DIAGRAM_LEAF_RE.search(s)
                    and len(s) < 120
                ):
                    continue
                # Short title-case line matching any catalog leaf
                if plain_l in {p.lower() for p in _DIAGRAM_LEAF_PHRASES}:
                    continue
        out.append(line)
    return "\n".join(out)


def _strip_soup_after_caption(lines: list[str], start_idx: int) -> int:
    """Return index after label-soup block."""
    i = start_idx
    while i < len(lines) and _is_label_soup_line(lines[i]):
        i += 1
    return i


def _page_region_end(lines: list[str], start_idx: int) -> int:
    i = start_idx
    while i < len(lines) and not lines[i].strip().startswith("<!-- page:"):
        i += 1
    return i


def _emit_page_without_soup(
    lines: list[str],
    out: list[str],
    start_idx: int,
) -> int:
    """Copy lines until next page marker, dropping diagram label soup."""
    end = _page_region_end(lines, start_idx)
    i = start_idx
    while i < end:
        if not _is_label_soup_line(lines[i]):
            out.append(lines[i])
        i += 1
    return i


def _has_image_for_fid(text: str, fid: str) -> bool:
    return bool(
        re.search(rf"!\[[^\]]*\]\([^)]*{re.escape(fid)}\.png\)", text)
        or re.search(rf"!\[[^\]]*\]\(assets/figures/{re.escape(fid)}\.png\)", text)
    )


def inject_png_figure(
    text: str,
    header: str,
    fid: str,
    asset_path: str,
    page: str,
    render_as: str = "png",
    list_section: tuple[int, int] | None = None,
) -> str:
    """Ensure PNG figure block is present at the correct caption, not document end.

    Prefer:
    1) Insert/replace at matching caption / db:id header.
    2) If db:id header exists without image, append image under it.
    3) Never dump orphans at EOF without a page context when a caption exists somewhere.
    """
    img_line = f"![{header}]({asset_path})"
    block = (
        f"<!-- db:id={fid} type=figure render_as={render_as} "
        f"product_tier=context pages={page} -->\n"
        f"### {header} | {fid}\n\n"
        f"{img_line}\n"
    )

    # Rewrite image under this figure's db:id to current asset path
    db_block_pat = re.compile(
        rf"(<!--\s*db:id={re.escape(fid)}\s+type=figure[^>]*-->\s*\n"
        rf"###[^\n]+\n)"
        rf"(?:\s*!\[[^\]]*\]\([^)]+\)\s*\n)?",
        re.I,
    )
    if db_block_pat.search(text):
        text = db_block_pat.sub(rf"\1\n{img_line}\n", text, count=1)
        text = _strip_polluted_captions(text, header)
        return strip_garbage_under_figure_images(text)

    # Path 1: db:id already present — attach image if missing.
    db_pat = re.compile(
        rf"(<!--\s*db:id={re.escape(fid)}\s+type=figure[^>]*-->\s*\n"
        rf"###[^\n]+\n)(?!\s*!\[)",
        re.I,
    )
    if db_pat.search(text):
        text = db_pat.sub(rf"\1\n{img_line}\n", text, count=1)
        text = _strip_polluted_captions(text, header)
        return strip_garbage_under_figure_images(text)

    if _has_image_for_fid(text, fid):
        return strip_garbage_under_figure_images(text)

    lines = text.splitlines()
    out: list[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        if list_section and list_section[0] <= i < list_section[1]:
            out.append(lines[i])
            i += 1
            continue
        line = lines[i]
        if not replaced and _caption_matches(line, header):
            out.append(block.rstrip())
            out.append("")
            # Skip soup after polluted caption; keep real prose on page.
            j = i + 1
            j = _strip_soup_after_caption(lines, j)
            # Also skip empty ### duplicates
            while j < len(lines) and (
                _caption_matches(lines[j], header)
                or lines[j].strip().startswith(f"<!-- db:id={fid}")
            ):
                j += 1
                j = _strip_soup_after_caption(lines, j)
            i = j
            replaced = True
            continue
        if replaced and _caption_matches(line, header):
            i = _strip_soup_after_caption(lines, i + 1)
            continue
        out.append(line)
        i += 1

    if not replaced:
        # Last resort: place before matching page marker if possible.
        page_pat = re.compile(rf"<!-- page:{re.escape(str(page))} -->")
        joined = "\n".join(out)
        m = page_pat.search(joined)
        if m:
            # Insert after page marker block start — find end of first content? append after marker line.
            idx = m.end()
            joined = joined[:idx] + "\n\n" + block.rstrip() + "\n" + joined[idx:]
            return strip_garbage_under_figure_images(joined)
        # True orphan only if page marker missing entirely.
        out.append(block.rstrip())
    return strip_garbage_under_figure_images("\n".join(out))


def _strip_polluted_captions(text: str, header: str) -> str:
    """Remove leftover polluted **Figure N – title…soup** lines when clean block exists.

    Never remove in-prose mentions like ``Figure 2, which appeared in the 1996…``.
    """
    hn = _figure_number_from_header(header)
    if not hn:
        return text
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        s = line.strip()
        plain = re.sub(r"^\*+\s*", "", s)
        plain = re.sub(r"\s*\*+$", "", plain)
        # Only strip real caption form (dash after number), optionally bold/polluted.
        if re.match(rf"^Figure\s+{re.escape(hn)}\s*[–—\-]\s+", plain, re.I):
            # Keep clean short captions that are the only content if somehow duplicated
            # as non-### lines; drop long polluted ones and plain caption duplicates.
            if " | " in s or s.startswith("###"):
                out.append(line)
                continue
            # Duplicate plain/bold caption after structured block
            continue
        out.append(line)
    return "\n".join(out)


def inject_text_diagram(
    text: str,
    header: str,
    body_block: str,
    list_section: tuple[int, int] | None = None,
) -> str:
    """Replace caption soup with catalog text_diagram block."""
    # Already injected (db:id in body_block)?
    fid_m = re.search(r"db:id=([^\s>]+)", body_block)
    if fid_m and re.search(rf"<!--\s*db:id={re.escape(fid_m.group(1))}\b", text):
        text = _strip_polluted_captions(text, header)
        # Drop leftover diagram-label soup lines on that page — never inside ``` fences.
        lines = text.splitlines()
        out: list[str] = []
        in_fig_page = False
        in_fence = False
        for line in lines:
            s = line.strip()
            if s.startswith("```"):
                in_fence = not in_fence
                out.append(line)
                continue
            if in_fence:
                out.append(line)
                continue
            if fid_m and fid_m.group(1) in line and "db:id=" in line:
                in_fig_page = True
                out.append(line)
                continue
            if in_fig_page and s.startswith("<!-- page:"):
                in_fig_page = False
            if in_fig_page and _is_label_soup_line(line):
                continue
            out.append(line)
        return "\n".join(out)

    lines = text.splitlines()
    out: list[str] = []
    i = 0
    replaced = False
    while i < len(lines):
        if list_section and list_section[0] <= i < list_section[1]:
            out.append(lines[i])
            i += 1
            continue
        line = lines[i]
        if not replaced and _caption_matches(line, header):
            out.append(body_block.rstrip())
            out.append("")
            i = _strip_soup_after_caption(lines, i + 1)
            # If next lines are more soup until prose, keep stripping
            while i < len(lines) and _is_label_soup_line(lines[i]):
                i += 1
            replaced = True
            continue
        if _caption_matches(line, header):
            i = _strip_soup_after_caption(lines, i + 1)
            continue
        out.append(line)
        i += 1

    if not replaced:
        # Try page placement from body_block pages= attr
        pm = re.search(r"pages=(\d+)", body_block)
        if pm:
            page = pm.group(1)
            joined = "\n".join(out)
            m = re.search(rf"<!-- page:{page} -->", joined)
            if m:
                idx = m.end()
                return joined[:idx] + "\n\n" + body_block.rstrip() + "\n" + joined[idx:]
        out.append(body_block.rstrip())
    return "\n".join(out)
