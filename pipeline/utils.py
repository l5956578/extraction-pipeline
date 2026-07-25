import re
from pathlib import Path

COMMON_WORDS = {
    "the", "and", "can", "for", "with", "understand", "language", "text", "information",
    "simple", "able", "their", "from", "that", "this", "have", "been", "which", "when",
    "about", "into", "through", "using", "other", "people", "different", "communicate",
    "interaction", "mediation", "production", "reception", "reading", "writing", "oral",
    "level", "descriptors", "competence", "activities", "strategies", "learner", "learning",
    # Reverse-detection support (rotated CEFR titles)
    "written", "structure", "cultural", "appropriateness", "explain", "explaining",
    "concept", "concepts", "new", "public", "putting", "specific", "diagrams", "graphs",
    "data", "publication", "process", "control", "understanding", "repertoire",
    "sociolinguistic", "translating", "sign", "group", "case", "debate", "announcements",
    "collaborating", "relaying", "mediation", "spoken", "speech", "signed", "media",
}


def slugify(text: str, prefix: str = "") -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if prefix:
        return f"{prefix}_{text}" if text else prefix
    return text or "untitled"


def clean_running_headers(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^Page\s+\d+$", stripped, re.I):
            continue
        if re.match(r"^\d+\s+CEFR", stripped):
            continue
        if re.match(r"^CEFR.*Companion volume$", stripped, re.I):
            continue
        if re.match(r"^Companion volume$", stripped, re.I):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def english_word_score(text: str) -> float:
    words = re.findall(r"[A-Za-z]{3,}", text)
    if not words:
        return 0.0
    hits = sum(1 for w in words if w.lower() in COMMON_WORDS)
    return hits / len(words)


def is_gibberish(text: str, threshold: float = 0.08) -> bool:
    if len(text.strip()) < 40:
        return False
    score = english_word_score(text)
    reversed_hits = len(re.findall(r"[a-z]{4,}", text)) - sum(
        1 for w in re.findall(r"[a-z]{4,}", text) if w in COMMON_WORDS
    )
    if score < threshold and reversed_hits > 10:
        return True
    return score < 0.05


def sanitize_urls_in_text(text: str) -> str:
    """Strip internal whitespace from http(s) URL tokens (C2-U1).

    Fixes patterns like ``https:// rm.coe.int/…`` and ``details. aspx`` inside a URL.
    Does not merge a URL with following prose words.
    Also splits footnote numbers that got glued onto a URL path (L05-FN-GLUE).
    """
    if not text:
        return text

    def _fix_url(m: re.Match) -> str:
        raw = m.group(0)
        trail = ""
        # Peel trailing sentence punctuation not part of the URL
        while raw and raw[-1] in ".,;:)]}\"'":
            # Keep trailing slash-ish paths; peel only pure punctuation
            if raw[-1] == "/" or raw[-1].isalnum():
                break
            trail = raw[-1] + trail
            raw = raw[:-1]
        cleaned = re.sub(r"\s+", "", raw)
        return cleaned + trail

    # 1) Space immediately after scheme: https:// rm.coe.int/...
    text = re.sub(r"(https?://)\s+", r"\1", text)

    # 2) Spaces inside a URL path only when the next fragment is path-like
    #    (not English prose). Examples: "details. aspx", "/1680 66a", "?x= 1"
    def _fix_internal(m: re.Match) -> str:
        return m.group(1) + m.group(2).replace(" ", "")

    # space before file extension / path segment / query
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']*)(\s+(?:[./?#%][^\s\)\]<>\"']*|[A-Za-z0-9_-]+\.(?:aspx|html?|php|pdf|json)[^\s\)\]<>\"']*))",
        _fix_internal,
        text,
        flags=re.I,
    )
    # repeated: "details. aspx" style mid-path (dot-space-extension)
    # Do NOT consume footnote numbers: ".24." after a CoE hex id (L05-FN-GLUE).
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']*\.)(\s+)([A-Za-z][A-Za-z0-9]{1,10}\b)",
        lambda m: m.group(1) + m.group(3),
        text,
    )
    # Hex / id fragments split by space inside path: /1680 667a2d
    # Guard: do not swallow a new footnote number (``24. ALTE``).
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']*)(\s+)([0-9a-fA-F]{4,})\b(?!\.\s*[A-Z])",
        lambda m: m.group(1) + m.group(3),
        text,
    )
    # L05-FN-GLUE: URL path + glued next footnote ``…/1680667a2d.24.ALTE``
    # CoE resource ids are hex; footnote continues with N. + capital author/title.
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']*?/[0-9a-fA-F]{6,})(?:\.)(\d{1,3})\.(\s*)([A-ZÀ-ÖØ-Þ])",
        r"\1\n\2. \4",
        text,
    )
    # Same glue without the hex-path assumption (generic URL end)
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']+)(?:\.)(\d{1,3})\.(\s*)([A-ZÀ-ÖØ-Þ])",
        r"\1\n\2. \4",
        text,
    )
    # Ensure space after footnote number when ``24.ALTE``
    text = re.sub(r"(?m)^(\d{1,3})\.([A-ZÀ-ÖØ-Þ])", r"\1. \2", text)
    # URL glued to following capitalised prose: ...621.Beacco → ...621. Beacco
    # Skip when the capital start is a glued footnote already handled.
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']+)(\.)([A-Z][a-z])",
        r"\1\2 \3",
        text,
    )
    return text


def repair_glued_footnotes(text: str) -> str:
    """Split multi-footnote runs that collapsed onto one line (L05-FN-GLUE).

    Safe patterns only: after a URL (or end of a citation URL line), a new
    ``N. Capital…`` footnote start must begin its own line.
    """
    if not text:
        return text
    # After URL, mid-line ``25. Name`` → newline (when not already at line start)
    text = re.sub(
        r"(https?://[^\s\)\]<>\"']+)\s*(\d{1,3}\.\s+[A-ZÀ-ÖØ-Þ])",
        r"\1\n\2",
        text,
    )
    # After ``aspx.`` / path end without scheme re-match already done
    text = re.sub(
        r"(available at:?\s+https?://[^\s\)\]<>\"']+)\s*(\d{1,3}\.\s)",
        r"\1\n\2",
        text,
        flags=re.I,
    )
    return text


def escape_md_cell(value: str) -> str:
    """Escape a table cell with phrase-aware ``<br>`` (UV-11 / C2-T3).

    PDF soft wraps usually continue mid-phrase (next line starts lowercase) →
    join with a space. A new visual phrase often starts with a capital letter
    on the next line (e.g. Table 4: ``Turntaking\\nCo-operating``) → ``<br>``.
    Blank lines always break phrases.
    """
    if value is None:
        return ""
    value = str(value).replace("\r\n", "\n").replace("\r", "\n")
    # Hard phrase breaks first
    blocks = re.split(r"\n\s*\n+", value)
    rendered: list[str] = []
    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if not lines:
            continue
        phrases: list[str] = [lines[0]]
        for line in lines[1:]:
            # Soft wrap: continuation of same phrase
            if line[:1].islower() or line.startswith(("and ", "or ", "of ", "the ", "to ", "a ", "an ")):
                phrases[-1] = phrases[-1] + " " + line
            else:
                # Capital / new token line → distinct phrase (Table 4 strategies)
                phrases.append(line)
        rendered.append("<br>".join(phrases))
    value = "<br>".join(rendered)
    value = re.sub(r"[ \t]+", " ", value).strip()
    # Collapse accidental double spaces only (keep <br>)
    value = re.sub(r" +", " ", value)
    value = value.replace("|", "\\|")
    return value


def table_to_markdown(rows: list[list]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    normalized = []
    for row in rows:
        padded = list(row) + [""] * (width - len(row))
        normalized.append([escape_md_cell(c) for c in padded])
    # C2-G1: do not emit empty / whitespace-only tables
    if all(not any(c.strip() for c in row) for row in normalized):
        return ""
    # Single empty column junk: | | / | --- | / | |
    if width <= 1 and all(
        all(not (c or "").strip() or (c or "").strip() == "---" for c in row)
        for row in normalized
    ):
        return ""
    header = normalized[0]
    body = normalized[1:] if len(normalized) > 1 else []
    # Drop if header and body cells are all empty
    if not any(c.strip() for c in header) and all(
        not any(c.strip() for c in row) for row in body
    ):
        return ""
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def artifact_header(
    artifact_id: str,
    display_name: str,
    artifact_type: str,
    product_tiers: list[str],
    pages: str,
) -> str:
    """Emit db:id + ### title | id header.

    For scale/table artifacts, re-derive a clean id from the fixed display title
    when the supplied id still contains known reversed tokens (RIE-005).
    """
    from pipeline.title_fix import clean_artifact_id, fix_rotated_title

    name = fix_rotated_title(display_name)
    aid = artifact_id
    if artifact_type in ("descriptor_scale", "table", "scale") or (
        isinstance(artifact_id, str)
        and (artifact_id.startswith("scale_") or artifact_id.startswith("table_"))
    ):
        # Always re-slug when id still looks garbled (RIE-005 / L07-ID root)
        aid = clean_artifact_id(aid, name)
    tiers = ",".join(product_tiers)
    # Trailing blank line so markdown tables after header render (L07-TABLE-BLANK root)
    return (
        f"<!-- db:id={aid} type={artifact_type} "
        f"product_tier={tiers} pages={pages} -->\n"
        f"### {name} | {aid}\n"
    )


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path