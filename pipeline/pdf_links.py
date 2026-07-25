"""PDF hyperlink annotations → prose URL appends (when not already footnoted)."""

from __future__ import annotations

import re
from collections import defaultdict

import fitz

from pipeline.utils import sanitize_urls_in_text

# Collapse whitespace for matching.
_ws = re.compile(r"\s+")

# Known multi-line CoE titles when annotation rects return garbage (C2-H1).
_KNOWN_LINK_TITLES: list[tuple[str, str]] = [
    (
        "Guide for the development and implementation of curricula for plurilingual and intercultural education",
        "https://rm.coe.int/16806ae621",
    ),
    (
        "Plurilingual and pluricultural competence",
        "https://rm.coe.int/168069d29b",
    ),
    (
        "Framework of reference for pluralistic approaches to languages and cultures",
        "http://carap.ecml.at/Accueil/tabid/3577/language/en-GB/Default.aspx",
    ),
    # L05-P41-URL — annotation anchor is short; force attach on known phrase
    (
        "CEFR 2001 Section 3.7",
        "https://rm.coe.int/1680459f97#page=36",
    ),
]


def page_http_links(page: fitz.Page) -> list[tuple[str, str]]:
    """Return (anchor_text, uri) for http(s) links on a page.

    Multi-rect annotations that share the same URI are merged in reading order
    so split titles (e.g. Guide for… / implementation of…) become one phrase.
    """
    by_uri: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    for link in page.get_links():
        uri = (link.get("uri") or "").strip()
        if not uri.startswith("http"):
            continue
        rect = link.get("from")
        if not rect:
            continue
        r = fitz.Rect(rect)
        raw = page.get_textbox(r).strip()
        anchor = _ws.sub(" ", raw).strip()
        if not anchor or len(anchor) < 3:
            continue
        if anchor.startswith("http"):
            continue
        by_uri[uri].append((r.y0, r.x0, anchor))

    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for uri, parts in by_uri.items():
        parts.sort(key=lambda t: (t[0], t[1]))
        # Merge unique consecutive fragments
        chunks: list[str] = []
        for _, _, a in parts:
            if not chunks or a not in chunks[-1]:
                # Avoid duplicating full phrase if rects overlap
                if chunks and (a in " ".join(chunks) or chunks[-1] in a):
                    if len(a) > len(chunks[-1]):
                        chunks[-1] = a
                    continue
                chunks.append(a)
        merged = _ws.sub(" ", " ".join(chunks)).strip()
        # Drop garbage anchors that look like mid-sentence wrap fragments
        if len(merged) < 8 and not merged[0:1].isupper():
            continue
        if re.match(r"^[a-z]", merged) and " " in merged and len(merged) < 40:
            # Mid-sentence fragment — keep URI via known-title map later
            key = ("", uri)
            if key not in seen:
                seen.add(key)
                out.append(("", uri))
            continue
        key = (merged.lower(), uri)
        if key in seen:
            continue
        seen.add(key)
        out.append((merged, uri))
    return out


def _already_has_url_nearby(text: str, anchor: str, uri: str) -> bool:
    """True if URI already appears **near this anchor** (L05-P32-LINK).

    Previously returned True if the URI existed *anywhere* in the page text,
    which blocked attaching the Guide URL to its title when the same URL had
    already been wrongly placed after \"language classroom\".
    """
    if not uri:
        return False
    # Fragment-insensitive base match for CoE ids
    base = uri.split("#", 1)[0]
    tail = base.rstrip("/").rsplit("/", 1)[-1]

    if not anchor:
        return uri in text or (tail and len(tail) > 6 and tail in text)

    # Search windows around each occurrence of the anchor
    lower = text.lower()
    a = anchor.lower()
    start = 0
    while True:
        idx = lower.find(a, start)
        if idx < 0:
            break
        window = text[max(0, idx - 20) : idx + len(anchor) + 120]
        if uri in window or base in window:
            return True
        if tail and len(tail) > 6 and tail in window:
            return True
        # Already has any parenthetical http immediately after anchor
        after = text[idx + len(anchor) : idx + len(anchor) + 12].lstrip()
        if after.startswith("(http"):
            return True
        start = idx + len(a)
    return False


def _fuzzy_attach(text: str, anchor: str, uri: str) -> str | None:
    """Attach (uri) after the best matching substring of anchor already in text."""
    if not anchor:
        return None
    if _already_has_url_nearby(text, anchor, uri):
        return text
    # Try full anchor with flexible whitespace
    pattern = re.escape(anchor)
    pattern = pattern.replace(r"\ ", r"\s+")
    repl_pat = re.compile(rf"({pattern})(?!\s*\(https?://)", re.I)
    result, n = repl_pat.subn(lambda m: f"{m.group(1)} ({uri})", text, count=1)
    if n:
        return result

    # Longest word-run substring present in text (min 24 chars)
    words = anchor.split()
    for length in range(len(words), 2, -1):
        for i in range(0, len(words) - length + 1):
            phrase = " ".join(words[i : i + length])
            if len(phrase) < 24:
                continue
            if phrase not in text and phrase.lower() not in text.lower():
                continue
            # Case-preserving find
            idx = text.lower().find(phrase.lower())
            if idx < 0:
                continue
            end = idx + len(text[idx : idx + len(phrase) + 5].split(phrase[:10])[0]) if False else idx + len(phrase)
            # More reliable: regex flexible space
            p2 = re.escape(phrase).replace(r"\ ", r"\s+")
            rp = re.compile(rf"({p2})(?!\s*\(https?://)", re.I)
            result, n = rp.subn(lambda m: f"{m.group(1)} ({uri})", text, count=1)
            if n:
                return result
    return None


def append_inline_link_urls(page: fitz.Page, text: str) -> str:
    """Append (url) after linked phrases that are not already covered by a footnote URL.

    Policy (docs/CONTRACTS.md §5): parenthetical URL only; merge multi-rect; fuzzy match;
    known-title fallback when annotation text is garbage.
    """
    if not text or not text.strip():
        return text

    result = text
    links = page_http_links(page)

    # Known titles for this page's URIs
    page_uris = {u for _, u in links}
    for title, uri in _KNOWN_LINK_TITLES:
        if uri in page_uris or uri in result:
            # Prefer attaching known title if present in prose
            if title in result or title.lower() in result.lower():
                links.append((title, uri))
            elif uri in page_uris:
                links.append((title, uri))

    # Longer anchors first
    for anchor, uri in sorted(links, key=lambda t: len(t[0] or ""), reverse=True):
        if _already_has_url_nearby(result, anchor or "", uri):
            continue
        if not anchor:
            # URI present on page via annotation but garbage text — try known titles only
            continue
        needle = f"{anchor} ({uri})"
        if needle in result:
            continue
        fuzzy = _fuzzy_attach(result, anchor, uri)
        if fuzzy is not None:
            result = fuzzy
            continue
        # Exact fallback
        if anchor in result:
            idx = result.find(anchor)
            if idx >= 0:
                end = idx + len(anchor)
                if not result[end : end + 12].lstrip().startswith("(http"):
                    result = result[:end] + f" ({uri})" + result[end:]

    # Second pass: known titles even if annotation missed the page text match
    for title, uri in _KNOWN_LINK_TITLES:
        if title not in result and not re.search(re.escape(title[:40]), result, re.I):
            continue
        if _already_has_url_nearby(result, title, uri):
            continue
        fuzzy = _fuzzy_attach(result, title, uri)
        if fuzzy is not None:
            result = fuzzy

    # L05-P32-LINK: if Guide URL is only after "language classroom", move it to title
    guide_uri = "https://rm.coe.int/16806ae621"
    guide_title = (
        "Guide for the development and implementation of curricula for "
        "plurilingual and intercultural education"
    )
    if guide_uri in result and guide_title in result:
        if not _already_has_url_nearby(result, guide_title, guide_uri):
            result = re.sub(
                rf"(language classroom)\s*\({re.escape(guide_uri)}\)",
                r"\1",
                result,
            )
            fuzzy = _fuzzy_attach(result, guide_title, guide_uri)
            if fuzzy is not None:
                result = fuzzy

    return sanitize_urls_in_text(result)
