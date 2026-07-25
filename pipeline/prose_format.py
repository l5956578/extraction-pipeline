"""Normalize prose formatting for Markdown output."""

from __future__ import annotations

import re

_BULLET_MARKERS = re.compile(r"^(\s*)(?:f|▶|▸|►|•|▪|‣)\s+", re.I)
_SPLIT_BULLET = re.compile(r"^(\s*)-\s*$")
_SECTION_HEAD = re.compile(
    r"^(?:#{1,6}\s|<!-- db:|<!-- page:|Page \d|Chapter \d|Appendix \d|"
    r"\d+\.\d+\.|LIST OF |TABLE \d|FIGURE \d|Figure \d|"
    r"- (?:Foreword|Preface|CHAPTER|APPENDIX|FIGURE|TABLE|[A-Z]))",
    re.I,
)
_TOC_LINE = re.compile(r" — \d{1,3}$")
_PAGE_MARKER = re.compile(r"<!-- page:\d+ -->")
_SENTENCE_END = re.compile(r"[.!?;:]\s*$")


def _merge_split_bullets(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _SPLIT_BULLET.match(line) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and not _SECTION_HEAD.match(nxt):
                indent = _SPLIT_BULLET.match(line).group(1)
                out.append(f"{indent}- {nxt}")
                i += 2
                continue
        out.append(line)
        i += 1
    return out


def _convert_f_bullets(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        m = _BULLET_MARKERS.match(line)
        if m:
            out.append(f"{m.group(1)}- {line[m.end():].lstrip()}")
        else:
            out.append(line)
    return out


def _format_level_callouts(lines: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("Level C2,") or s.startswith("Level A1 (Breakthrough)"):
            block = [s]
            i += 1
            while i < len(lines):
                nxt = lines[i].strip()
                if not nxt or _SECTION_HEAD.match(nxt) or nxt.startswith("Level ") or nxt.startswith("**Background"):
                    break
                if nxt.startswith("**Mastery") or nxt.startswith("A1,"):
                    break
                block.append(nxt)
                i += 1
                if _SENTENCE_END.search(nxt):
                    break
            out.append(f"- {' '.join(block)}")
            continue
        if s in ("**Background to the CEFR levels**", "Background to the CEFR levels"):
            out.append("**Background to the CEFR levels**")
            out.append("")
            i += 1
            paras: list[str] = []
            cur: list[str] = []
            while i < len(lines):
                nxt = lines[i].strip()
                if nxt.startswith("The following descriptors"):
                    if cur:
                        paras.append(" ".join(cur))
                    break
                if (
            _SECTION_HEAD.match(nxt)
            or _PAGE_MARKER.search(nxt)
            or _TOC_LINE.search(nxt)
            or nxt.startswith("## Contents")
            or nxt.startswith("## List of")
        ):
                    if cur:
                        paras.append(" ".join(cur))
                        cur = []
                    break
                if not nxt:
                    if cur:
                        paras.append(" ".join(cur))
                        cur = []
                    i += 1
                    continue
                if nxt.startswith("- ") and cur:
                    paras.append(" ".join(cur))
                    cur = []
                cur.append(nxt)
                i += 1
            # Background section is normal prose (and optional true list items),
            # not a forced bullet list — forcing "- " broke Ch2 body paragraphs.
            for p in paras:
                if p.startswith("- "):
                    out.append(p)
                else:
                    out.append(p)
                out.append("")
            continue
        out.append(lines[i])
        i += 1
    return out


def fix_ocr_typos(text: str) -> str:
    """Fix obvious OCR/hyphenation errors without touching bold marker spacing.

    Bold normalization is handled separately by ``fix_bold_markdown`` so post-processing
    cannot undo extraction-time spacing fixes (Session 1 + Session 2 integration).
    """
    replacements = {
        "teacheror": "teacher or",
        "selfassessments": "self-assessments",
        "selfassessment": "self-assessment",
        "useror": "user or",
        "complémentaire": "complémentaire",
        "Langauge": "Language",
        "langue**s": "langues",
        "E mail:": "E-mail:",
        "Pre–A1": "Pre-A1",
        "oneor": "one or",
        "problemsolving": "problem-solving",  # L05-P33-HY
        "problem solving language": "problem-solving language",
        "situationspecific": "situation-specific",  # L06
        "situation specific phrases": "situation-specific phrases",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"(?<=\n)-\*\*", "- **", text)
    text = re.sub(r"\ufeff\s*Page\s+(\d+)", r"<!-- Page \1 -->", text)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    # Soft-join artifact: period glued to next sentence capital (e.g. inclusive.Any)
    text = re.sub(r"\.([A-Z])", r". \1", text)
    # Dingbat arrow mis-decoded as ASCII "3" in page footers (FFDingbats-ArrowsOne).
    text = re.sub(
        r"(Page\s+\*?\*?\d+\*?\*?\s+)3(\s+\*?\*?CEFR)",
        r"\1▶\2",
        text,
        flags=re.I,
    )
    text = text.replace("\xad", "")
    return text


def fix_bold_markdown(text: str) -> str:
    """Public alias for bold normalization used by cleanup and post-processing."""
    return _fix_bold_artifacts(text)


def _fix_bold_artifacts(text: str) -> str:
    """Normalize bold markdown without stripping spaces around bold markers."""
    text = re.sub(
        r"\*\*([^*]+)\*\*\s*\n\s*\*\*([^*]+)\*\*",
        r"**\1 \2**",
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*\*\*([^*]+)\*\*", r"**\1 \2**", text)
    text = re.sub(
        r"\*\*([^*]+)\*\*\s+\*\*([^*]+)\*\*",
        r"**\1 \2**",
        text,
    )

    def _trim_bold_edges(m: re.Match[str]) -> str:
        inner = m.group(1).strip()
        if not inner:
            return ""
        return f"**{inner}**"

    text = re.sub(r"\*\*([^*]+)\*\*", _trim_bold_edges, text)
    text = _fix_bold_boundary_spacing(text)
    # Page numbers must stay tight: Page **27** not Page ** 27 **
    # (boundary spacing can re-introduce spaces around digit-only bold runs.)
    text = re.sub(r"\*\*\s+(\d+)\s+\*\*", r"**\1**", text)
    # Re-trim interior spaces on single-line word/phase bold only
    # (e.g. `** Intuitive phase: **` → `**Intuitive phase:**`).
    # Do not match symbol-only interiors (`** ▶ **`) or span newlines
    # (closing `**` + blank + next open would corrupt `Page **27**`).
    def _trim_padded_bold(m: re.Match[str]) -> str:
        inner = m.group(1).strip()
        if not inner or not re.search(r"[A-Za-z0-9]", inner):
            return m.group(0)
        return f"**{inner}**"

    text = re.sub(r"\*\*\s+([^*\n]{1,100}?)\s+\*\*", _trim_padded_bold, text)
    text = re.sub(r"\*\*\s+([A-Za-z0-9][^*\n]{0,99}?)\*\*", r"**\1**", text)
    text = re.sub(r"\*\*([^*\n]{0,99}?[A-Za-z0-9:.])\s+\*\*", r"**\1**", text)
    return text


def _fix_bold_boundary_spacing(text: str) -> str:
    out: list[str] = []
    i = 0
    in_bold = False
    while i < len(text):
        if text.startswith("**", i):
            if not in_bold and out and out[-1] not in " \t\n":
                out.append(" ")
            out.append("**")
            in_bold = not in_bold
            i += 2
            if not in_bold and i < len(text) and text[i] not in " \t\n":
                if text[i] == "(" or text[i].isalnum():
                    out.append(" ")
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _strip_bullet_page_markers(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if _PAGE_MARKER.search(line):
            out.append(re.sub(r"^-\s+", "", line.strip()))
        else:
            out.append(line)
    return out


def _preserve_fenced_blocks(lines: list[str]) -> tuple[list[str], list[str]]:
    """Extract ``` blocks so prose normalizers do not alter diagram content."""
    out: list[str] = []
    placeholders: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("```"):
            block = [lines[i]]
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i])
                i += 1
            placeholders.append("\n".join(block))
            out.append(f"@@FENCE{len(placeholders) - 1}@@")
            continue
        out.append(lines[i])
        i += 1
    return out, placeholders


def _restore_fenced_blocks(lines: list[str], placeholders: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        m = re.match(r"^@@FENCE(\d+)@@$", line.strip())
        if m:
            out.extend(placeholders[int(m.group(1))].splitlines())
            continue
        out.append(line)
    return out


def _split_list_glued_callout_leads(lines: list[str]) -> list[str]:
    """Detach callout/prose that was glued onto the last list item (C2-CO2 / C2-L3).

    Example: ``- exploit paralinguistics (… etc.). The linked concepts of…``
    → list item ends at ``etc.).`` then a new paragraph with the lead sentence.
    """
    lead_starts = (
        "The linked concepts of plurilingualism",
        "The linked concepts of plurilingualism/",
    )
    out: list[str] = []
    for line in lines:
        if not line.lstrip().startswith("- "):
            out.append(line)
            continue
        split_at = None
        for lead in lead_starts:
            idx = line.find(lead)
            if idx > 10:
                # Prefer split after sentence end before lead
                before = line[:idx]
                if re.search(r"[.!?)]\s*$", before.rstrip()) or before.rstrip().endswith("."):
                    split_at = idx
                    break
                # Also split after ``etc.). `` pattern
                m = re.search(r"(etc\.\))\s+" + re.escape(lead), line)
                if m:
                    split_at = m.start(0) + len(m.group(1)) + 1
                    # find lead again
                    split_at = line.find(lead)
                    break
        if split_at is None:
            # Generic: list item ending with ``). `` then capital The/A/This…
            m = re.search(r"(\.\)|\.\))\s+(The |A |This |In |Plurilingual )", line)
            if m and line.lstrip().startswith("- "):
                # Only if remainder is long (callout-sized)
                rest = line[m.end() - len(m.group(2)) :]
                if len(rest) > 80:
                    split_at = m.end() - len(m.group(2))
        if split_at is not None:
            head = line[:split_at].rstrip()
            tail = line[split_at:].lstrip()
            out.append(head)
            out.append("")
            out.append(tail)
        else:
            out.append(line)
    return out


def _blockquote_known_callout_blocks(text: str) -> str:
    """Ensure known narrative callout titles use blockquote form (UV-01 / C2-CO1).

    Converts standalone ``**Title**`` + following paragraphs into ``> **Title**`` form.
    """
    patterns = [
        re.compile(r"^\*\*(A reminder of CEFR 2001 chapters)\*\*\s*$", re.M),
        re.compile(
            r'^\*\*([“"]Can do[”"] descriptors as competence)\*\*\s*$',
            re.M,
        ),
    ]
    for pat in patterns:
        m = pat.search(text)
        if not m:
            continue
        title_line = m.group(1)
        # Already blockquote for this title?
        if re.search(rf"^>\s*\*\*{re.escape(title_line)}\*\*", text, re.M):
            continue
        start = m.start()
        rest = text[m.end() :]
        body_lines: list[str] = []
        consumed = 0
        blank_run = 0
        for line in rest.splitlines(keepends=True):
            s = line.rstrip("\n").strip()
            if s.startswith(("<!--", "#", "|", ">")):
                break
            if not s:
                blank_run += 1
                if blank_run >= 2 and body_lines:
                    consumed += len(line)
                    break
                consumed += len(line)
                continue
            blank_run = 0
            body_lines.append(s)
            consumed += len(line)
            if len(body_lines) >= 12:
                break
        if not body_lines and "reminder" not in title_line.lower():
            continue
        bq = [f"> **{title_line}**", ">"]
        for para in body_lines:
            if re.match(r"^Chapter\s+\d+\s*:", para, re.I):
                bq.append(f"> *{para}*")
            else:
                bq.append(f"> {para}")
            bq.append(">")
        while bq and bq[-1] == ">":
            bq.pop()
        text = text[:start] + "\n".join(bq) + "\n" + rest[consumed:]
    return text


def normalize_prose(text: str) -> tuple[str, list[str]]:
    fixes: list[str] = []
    lines = text.splitlines()
    lines, fences = _preserve_fenced_blocks(lines)
    lines = _convert_f_bullets(lines)
    lines = _merge_split_bullets(lines)
    lines = _split_list_glued_callout_leads(lines)
    lines = _format_level_callouts(lines)
    lines = _strip_bullet_page_markers(lines)
    lines = _restore_fenced_blocks(lines, fences)
    text = "\n".join(lines)
    text = _fix_bold_artifacts(text)
    text = _blockquote_known_callout_blocks(text)
    from pipeline.utils import sanitize_urls_in_text

    text = sanitize_urls_in_text(text)
    if "f " in text or re.search(r"^\s*-\s*$", text, re.M):
        fixes.append("normalized bullets")
    if "**" in text:
        fixes.append("preserved bold spans")
    return text, fixes