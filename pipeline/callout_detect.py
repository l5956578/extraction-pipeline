"""Detect CEFR Companion Volume blue feature boxes from PDF drawings.

These boxes are often **not** pdfplumber tables (p.30–31). Drawing fill colour
is the reliable signal (UV-06 / CONTRACTS §2–3).
"""

from __future__ import annotations

import re
from typing import Any

import fitz

# Light blue-ish fills used for feature boxes in this PDF (approx RGB 0–1).
def _is_callout_fill(fill: object) -> bool:
    if not fill or not isinstance(fill, (tuple, list)) or len(fill) < 3:
        return False
    r, g, b = float(fill[0]), float(fill[1]), float(fill[2])
    # Observed ~ (0.81, 0.82, 0.91) — blue-grey tint, not white/black
    if r > 0.95 and g > 0.95 and b > 0.95:
        return False
    if r < 0.05 and g < 0.05 and b < 0.05:
        return False
    # Prefer cool/blue-ish mid-light fills
    return b >= 0.75 and g >= 0.70 and r >= 0.70 and (b >= r - 0.05)


def _merge_vertical_stacks(
    rects: list[fitz.Rect], y_gap: float = 12.0, x_tol: float = 8.0
) -> list[fitz.Rect]:
    """Merge boxes stacked in the same column into one callout region."""
    if not rects:
        return []
    rects = sorted(rects, key=lambda r: (round(r.x0, 0), r.y0))
    stacks: list[list[fitz.Rect]] = []
    for r in rects:
        placed = False
        for stack in stacks:
            last = stack[-1]
            if abs(r.x0 - last.x0) <= x_tol and abs(r.x1 - last.x1) <= x_tol:
                if r.y0 <= last.y1 + y_gap:
                    stack.append(r)
                    placed = True
                    break
        if not placed:
            stacks.append([r])
    merged: list[fitz.Rect] = []
    for stack in stacks:
        x0 = min(s.x0 for s in stack)
        y0 = min(s.y0 for s in stack)
        x1 = max(s.x1 for s in stack)
        y1 = max(s.y1 for s in stack)
        merged.append(fitz.Rect(x0, y0, x1, y1))
    merged.sort(key=lambda r: (r.y0, r.x0))
    return merged


def detect_blue_callout_bboxes(page: fitz.Page, min_area: float = 4000.0) -> list[tuple[float, float, float, float]]:
    """Return merged (x0,y0,x1,y1) for blue feature boxes on a page."""
    raw: list[fitz.Rect] = []
    for d in page.get_drawings():
        if not _is_callout_fill(d.get("fill")):
            continue
        rect = d.get("rect")
        if not rect:
            continue
        r = fitz.Rect(rect)
        if r.width * r.height < min_area:
            continue
        # Ignore near-full-page backgrounds
        if r.width > page.rect.width * 0.85 and r.height > page.rect.height * 0.5:
            continue
        raw.append(r)
    merged = _merge_vertical_stacks(raw)
    return [(float(r.x0), float(r.y0), float(r.x1), float(r.y1)) for r in merged]


def _merge_band_continuations(texts: list[str]) -> list[str]:
    """Stitch bands cut mid-sentence and drop prefix/duplicate starts (log 04 #0.1)."""
    if not texts:
        return []
    merged: list[str] = []
    for t in texts:
        t = re.sub(r"\s+", " ", t).strip()
        if not t:
            continue
        if not merged:
            merged.append(t)
            continue
        prev = merged[-1]
        # Progressive stack: next contains previous → replace
        if prev in t and len(t) > len(prev) + 5:
            merged[-1] = t
            continue
        # Overlap stitch: end of prev is start of t
        stitched = False
        for k in range(min(100, len(prev), len(t)), 12, -1):
            if prev.endswith(t[:k]) or t.startswith(prev[-k:]):
                # Prefer longer unique continuation
                if t.startswith(prev[-k:]):
                    merged[-1] = prev + t[k:]
                else:
                    merged[-1] = prev + t[k:].lstrip()
                stitched = True
                break
            # prev ends mid-word/sentence and t continues after a shared phrase
            if prev[-k:] in t[: k + 20]:
                idx = t.find(prev[-k:])
                if idx >= 0:
                    merged[-1] = prev + t[idx + k :]
                    stitched = True
                    break
        if stitched:
            continue
        # Short fragment that is prefix of next — skip for now (next will be added)
        if len(t) < 80 and any(t in m or m.startswith(t[: max(20, len(t) - 3)]) for m in merged):
            continue
        merged.append(t)
    # Drop earlier items that are strict prefixes of later
    out: list[str] = []
    for i, t in enumerate(merged):
        if any(
            t != u and (t in u or u.startswith(t[: max(15, len(t) - 5)]))
            for u in merged[i + 1 :]
        ):
            # keep if later is only slightly longer (not a full replacement)
            later = next(
                (
                    u
                    for u in merged[i + 1 :]
                    if t in u or u.startswith(t[: max(15, len(t) - 5)])
                ),
                "",
            )
            if later and len(later) > len(t) + 15:
                continue
        out.append(t)
    return out


# Known CEFR Companion callout titles (split when glued onto body in first band).
# Longer / more specific titles first so "…levels" wins over "Background to the CEFR".
_KNOWN_CALLOUT_TITLES = (
    "Background to the CEFR levels",  # L05-P37
    "Background to the CEFR",
    "Priorities of the CEFR",
    "A reminder of CEFR 2001 chapters",
    '"Can do" descriptors as competence',
    "“Can do” descriptors as competence",
    "Can do descriptors as competence",
    "Can do” descriptors as competence",
    "CEFR descriptor research project",
    "Defining curriculum aims from a needs profile",
)


def _join_soft_wrapped_lines(lines: list[str]) -> list[str]:
    """Join PDF soft-wrap lines into logical paragraphs (keep Step/phase breaks)."""
    if not lines:
        return []
    out: list[str] = []
    for raw in lines:
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if not line:
            if out and out[-1] != "":
                out.append("")
            continue
        if not out or out[-1] == "":
            if out and out[-1] == "":
                out[-1] = line
            else:
                out.append(line)
            continue
        prev = out[-1]
        # Structural starts always open a new paragraph
        if re.match(r"^Step\s+\d+\s*:", line, re.I):
            out.append(line)
            continue
        if re.match(
            r"^(Intuitive|Qualitative|Quantitative)\s+phase\s*:",
            line,
            re.I,
        ):
            out.append(line)
            continue
        # Soft wrap: prev does not end sentence and line continues
        if not prev.rstrip().endswith((".", "?", "!", ":", ";", "…")) and (
            line[:1].islower()
            or line[:1] in "\"“'("
            or (len(prev) > 40 and not re.match(r"^(Step\s+\d+|Intuitive|Qualitative|Quantitative)", line, re.I))
        ):
            # Hyphenated wrap
            if prev.endswith("-") and line[:1].islower():
                out[-1] = prev[:-1] + line
            else:
                out[-1] = prev.rstrip() + " " + line
            continue
        # Prev ends mid-phrase with comma/and — continue
        if prev.rstrip().endswith((",", ";")) or prev.rstrip().endswith(
            (" and", " or", " the", " of", " to", " a", " an")
        ):
            out[-1] = prev.rstrip() + " " + line
            continue
        out.append(line)
    return [p for p in out if p.strip()]


def _apply_known_callout_splits(paras: list[str]) -> list[str]:
    """Forced multi-para splits for known CEFR callout bodies (L05-P27/P35)."""
    if not paras:
        return paras
    # Work on a single joined blob when structure is missing
    blob = " ".join(re.sub(r"\s+", " ", p).strip() for p in paras)
    blob = re.sub(r"\s+", " ", blob).strip()

    # L05-P27-CO: three paragraphs after title
    if "The CEFR was developed as a continuation" in blob and (
        "The CEFR and the related European Language Portfolio" in blob
        or "European Language Portfolio (ELP)" in blob
    ):
        # Drop title if glued
        body = blob
        for t in _KNOWN_CALLOUT_TITLES:
            if body.lower().startswith(t.lower()):
                body = body[len(t) :].lstrip(" :–-")
                break
        p1_end = "the first functional/ notional specification of language needs."
        # tolerate soft-hyphen form without space after /
        p1_end_alt = "the first functional/notional specification of language needs."
        p2_end = "educational sectors, regions and countries."
        end1 = p1_end if p1_end in body else (p1_end_alt if p1_end_alt in body else None)
        if end1 and p2_end in body:
            i1 = body.find(end1) + len(end1)
            i2 = body.find(p2_end) + len(p2_end)
            parts = [body[:i1].strip(), body[i1:i2].strip(), body[i2:].strip()]
            if all(parts):
                # Preserve title as first para if it was separate
                title_only = [
                    p
                    for p in paras
                    if re.sub(r"\s+", " ", p).strip().lower()
                    in {t.lower() for t in _KNOWN_CALLOUT_TITLES}
                    or re.match(r"^Background to the CEFR$", re.sub(r"\s+", " ", p).strip(), re.I)
                ]
                if title_only and not parts[0].lower().startswith("background"):
                    return [title_only[0]] + parts
                return parts

    # L05-P35-CO: two paragraphs after "achievement."
    if (
        "This “can do” approach was transferred" in blob
        or 'This "can do" approach was transferred' in blob
    ):
        marker = "levels of achievement."
        if marker in blob:
            body = blob
            for t in _KNOWN_CALLOUT_TITLES:
                if body.lower().startswith(t.lower().strip("“\"")):
                    body = body[len(t) :].lstrip(" :–-")
                    break
            # re-find marker on body
            if marker in body:
                i = body.find(marker) + len(marker)
                parts = [body[:i].strip(), body[i:].strip()]
                if all(parts):
                    title_only = [
                        p
                        for p in paras
                        if "can do" in re.sub(r"\s+", " ", p).strip().lower()
                        and len(p) < 80
                    ]
                    if title_only and not parts[0].lower().startswith("can"):
                        return [title_only[0]] + parts
                    return parts
    return paras


def _split_steps_and_phases(paras: list[str]) -> list[str]:
    """Ensure Step N: / * phase: markers open their own paragraphs."""
    out: list[str] = []
    for p in paras:
        p = re.sub(r"\s+", " ", p).strip()
        if not p:
            continue
        # Split before Step 2..N (and Step 1 if glued after title/lead)
        if re.search(r"\bStep\s+\d+\s*:", p, re.I):
            # Lead + steps
            m1 = re.match(
                r"^(.*?)(?=\bStep\s+1\s*:)",
                p,
                re.I | re.S,
            )
            rest = p
            if m1 and m1.group(1).strip():
                out.append(m1.group(1).strip())
                rest = p[m1.end() :].strip()
            parts = re.split(r"\s+(?=\bStep\s+\d+\s*:)", rest)
            for part in parts:
                part = part.strip()
                if part:
                    out.append(part)
            continue
        # Research phases (p.41 class)
        if re.search(
            r"\b(Intuitive|Qualitative|Quantitative)\s+phase\s*:",
            p,
            re.I,
        ):
            m_lead = re.match(
                r"^(.*?)(?=\bIntuitive\s+phase\s*:)",
                p,
                re.I | re.S,
            )
            rest = p
            if m_lead and m_lead.group(1).strip():
                out.append(m_lead.group(1).strip())
                rest = p[m_lead.end() :].strip()
            parts = re.split(
                r"\s+(?=\b(?:Intuitive|Qualitative|Quantitative)\s+phase\s*:)",
                rest,
                flags=re.I,
            )
            for part in parts:
                part = part.strip()
                if part:
                    out.append(part)
            continue
        out.append(p)
    return out


def _paras_from_full_textbox(full: str) -> list[str]:
    """Parse a full callout textbox into clean paragraphs (root of progressive fix)."""
    if not full or not full.strip():
        return []
    # Keep newlines for soft-wrap join; collapse only runs of spaces/tabs
    text = re.sub(r"[ \t]+", " ", full.replace("\r\n", "\n").replace("\r", "\n"))
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    raw_lines = text.split("\n")
    joined = _join_soft_wrapped_lines(raw_lines)
    # Collapse accidental empty markers
    paras = [re.sub(r"\s+", " ", p).strip() for p in joined if p.strip()]
    paras = _split_steps_and_phases(paras)
    paras = _apply_known_callout_splits(paras)
    # If still a single long blob without structure, sentence-split after period+capital
    if len(paras) == 1 and len(paras[0]) > 280:
        blob = paras[0]
        forced = _apply_known_callout_splits([blob])
        if len(forced) > 1:
            paras = forced
        else:
            parts = re.split(r"(?<=\.)\s+(?=[A-Z“\"])", blob)
            if len(parts) > 1:
                paras = [p.strip() for p in parts if p.strip()]
    return paras


def _bands_look_progressive_or_midcut(filtered: list[str]) -> bool:
    """True when band texts are progressive stacks or mid-sentence fragments."""
    if len(filtered) < 2:
        # Single band may still be fine; progressive check is multi-band
        return False
    # Progressive accumulation: each later contains earlier
    progressive = True
    for i in range(1, len(filtered)):
        prev, cur = filtered[i - 1], filtered[i]
        if prev not in cur and not cur.startswith(prev[: min(40, len(prev))]):
            progressive = False
            break
    if progressive:
        return True
    # Mid-cut: multiple long bands that do not end a sentence (single mid-phrase
    # band can be a legitimate soft title / list lead — do not over-trigger).
    mid = 0
    for p in filtered:
        if len(p) > 40 and not p.rstrip().endswith((".", "?", "!", ":", ";")):
            if not re.match(r"^(Step\s+\d+|Intuitive|Qualitative|Quantitative)", p, re.I):
                mid += 1
    if mid >= 2:
        return True
    # Overlap / continuation fragments: later starts mid-phrase of earlier
    for i in range(len(filtered)):
        for j in range(i + 1, len(filtered)):
            a, b = filtered[i], filtered[j]
            if len(a) > 30 and len(b) > 30:
                # Shared long substring mid-body → band dump risk
                for k in range(min(80, len(a), len(b)), 25, -1):
                    if a[-k:] in b or b[:k] in a:
                        return True
    return False


def callout_paragraphs_from_bbox(page: fitz.Page, bbox: tuple[float, float, float, float]) -> list[str]:
    """Extract paragraph-ish strings from a callout region (preserve multi-box stacks).

    Root fix (L06-P41 / L07-P42): prefer the **full merged textbox** with soft-wrap
    join + Step/phase splits. Progressive blue-band stacks must never dump mid-cut
    garbage — bands are only used when they are clean independent paragraphs.
    """
    # Always parse full textbox first (authoritative for progressive / soft-wrap).
    full = page.get_textbox(fitz.Rect(bbox)).strip()
    full_paras = _paras_from_full_textbox(full) if full else []

    x0, y0, x1, y1 = bbox
    pieces: list[tuple[float, str]] = []
    for d in page.get_drawings():
        if not _is_callout_fill(d.get("fill")):
            continue
        rect = d.get("rect")
        if not rect:
            continue
        r = fitz.Rect(rect)
        if r.y1 < y0 - 2 or r.y0 > y1 + 2:
            continue
        if r.x1 < x0 - 2 or r.x0 > x1 + 2:
            continue
        # Preserve newlines inside a band so Step/phase structure survives
        text = page.get_textbox(r).strip()
        if text:
            pieces.append((r.y0, text))
    if not pieces:
        return full_paras if full_paras else (
            [re.sub(r"\s+", " ", full).strip()] if full else []
        )

    pieces.sort(key=lambda t: t[0])
    # Parse each band via full-textbox logic (soft-wrap + structure)
    band_paras: list[str] = []
    for _, text in pieces:
        band_paras.extend(_paras_from_full_textbox(text))
    # Dedupe exact
    unique: list[str] = []
    for t in band_paras:
        t = re.sub(r"\s+", " ", t).strip()
        if not t or any(t == u for u in unique):
            continue
        unique.append(t)
    # Drop strict substrings of longer bands
    filtered: list[str] = []
    for t in unique:
        if any(t != u and t in u for u in unique):
            continue
        filtered.append(t)

    # Progressive accumulation: keep longest only then re-split from full
    if len(filtered) >= 2:
        progressive = True
        for i in range(1, len(filtered)):
            if filtered[i - 1] not in filtered[i] and not filtered[i].startswith(
                filtered[i - 1][: min(40, len(filtered[i - 1]))]
            ):
                progressive = False
                break
        if progressive:
            filtered = [max(filtered, key=len)]

    stitched = _merge_band_continuations(filtered)
    stitched = _split_steps_and_phases(stitched)
    stitched = _apply_known_callout_splits(stitched)

    # Prefer full textbox whenever bands look progressive/mid-cut OR full has
    # clearer structure (Steps / phases / more complete sentence ends).
    if full_paras:
        if _bands_look_progressive_or_midcut(filtered) or _bands_look_progressive_or_midcut(stitched):
            return full_paras
        full_has_structure = any(
            re.search(r"\bStep\s+\d+\s*:", p, re.I)
            or re.search(r"\b(Intuitive|Qualitative|Quantitative)\s+phase\s*:", p, re.I)
            for p in full_paras
        )
        stitched_has_structure = any(
            re.search(r"\bStep\s+\d+\s*:", p, re.I)
            or re.search(r"\b(Intuitive|Qualitative|Quantitative)\s+phase\s*:", p, re.I)
            for p in stitched
        )
        if full_has_structure and not stitched_has_structure:
            return full_paras
        mid_cut = any(
            len(p) > 40 and not p.rstrip().endswith((".", "?", "!", ":", ";"))
            for p in stitched
        )
        if mid_cut:
            return full_paras
        # Prefer fuller coverage from full textbox
        if sum(len(p) for p in full_paras) >= sum(len(p) for p in stitched) * 0.9 and len(
            full_paras
        ) >= len(stitched):
            return full_paras

    if stitched:
        return stitched
    return full_paras if full_paras else []


def _split_glued_title(para: str) -> tuple[str | None, str]:
    """If para starts with a known title then body, split them (log 04 #0.1, #3)."""
    p = re.sub(r"\s+", " ", para).strip()
    for t in _KNOWN_CALLOUT_TITLES:
        if p.lower().startswith(t.lower()):
            rest = p[len(t) :].lstrip(" :–-")
            return t.strip("“\""), rest
    # Generic: short Title Case phrase then capital sentence start
    m = re.match(
        r"^((?:A |The |“|\")?[A-Z][^.]{3,55}?)((?:The |This |It |In |As |One ).+)$",
        p,
    )
    if m and len(m.group(1)) < 70 and not m.group(1).endswith((".", ",")):
        return m.group(1).strip().strip("“\""), m.group(2).strip()
    return None, p


def _dedupe_partial_paras(paragraphs: list[str]) -> list[str]:
    """Drop paras that are prefixes of the next or start-of-next glue (log 04 #0.1)."""
    if len(paragraphs) < 2:
        return paragraphs
    out: list[str] = []
    for i, p in enumerate(paragraphs):
        pn = re.sub(r"\s+", " ", p).strip()
        if not pn:
            continue
        # Skip if this is a strict prefix of a later para
        if any(
            pn != re.sub(r"\s+", " ", q).strip()
            and re.sub(r"\s+", " ", q).strip().startswith(pn[: max(20, len(pn) - 5)])
            for q in paragraphs[i + 1 :]
        ):
            # Keep only if longer / more complete than the "later" that merely continues
            later_starts = [
                re.sub(r"\s+", " ", q).strip()
                for q in paragraphs[i + 1 :]
                if re.sub(r"\s+", " ", q).strip().startswith(pn[:20])
            ]
            if later_starts and len(later_starts[0]) > len(pn) + 10:
                continue
        # If previous ends mid-sentence and this continues it with overlap, strip overlap
        if out:
            prev = out[-1]
            # Overlap: last 40 chars of prev appear at start of this
            for k in range(min(80, len(prev)), 15, -1):
                tail = prev[-k:].strip()
                if len(tail) > 15 and pn.startswith(tail[: min(40, len(tail))]):
                    # Previous already has this fragment — skip duplicate start
                    # Find where unique content begins
                    for j in range(len(tail), 10, -1):
                        if pn.startswith(tail[:j]):
                            rest = pn[j:].lstrip()
                            if rest:
                                pn = rest
                            break
                    break
        out.append(pn)
    return out


def emit_callout_blockquote(
    paragraphs: list[str],
    title: str | None = None,
) -> str:
    """UV-01 / CONTRACTS §3 blockquote format. Single title, no partial para dups."""
    if not paragraphs and not title:
        return ""
    paragraphs = _dedupe_partial_paras(paragraphs)
    lines: list[str] = []
    title_norm = re.sub(r"\s+", " ", (title or "")).strip().lower()

    # Recover title glued onto first paragraph (stacked blue-band extraction)
    if paragraphs and not title:
        maybe_t, rest = _split_glued_title(paragraphs[0])
        if maybe_t:
            title = maybe_t
            title_norm = title.lower()
            if rest:
                paragraphs = [rest] + list(paragraphs[1:])
            else:
                paragraphs = list(paragraphs[1:])
    elif paragraphs and title:
        # First para may still glue title + body
        p0 = re.sub(r"\s+", " ", paragraphs[0]).strip()
        if p0.lower().startswith(title_norm):
            rest = p0[len(title) :].lstrip(" :–-")
            paragraphs = ([rest] if rest else []) + list(paragraphs[1:])

    # Dedupe again after title split (short rest is often prefix of next body para)
    paragraphs = _dedupe_partial_paras(paragraphs)
    # Drop short body frags that are strict prefixes of a later complete sentence
    cleaned: list[str] = []
    for i, p in enumerate(paragraphs):
        pn = re.sub(r"\s+", " ", p).strip()
        if not pn:
            continue
        if len(pn) < 100 and any(
            re.sub(r"\s+", " ", q).strip().startswith(pn) and len(q) > len(pn) + 20
            for q in paragraphs[i + 1 :]
        ):
            continue
        cleaned.append(pn)
    paragraphs = cleaned

    if title:
        # Clean title: drop accidental body continuation
        t_clean = re.sub(r"\s+", " ", title).strip()
        for known in _KNOWN_CALLOUT_TITLES:
            if t_clean.lower().startswith(known.lower()) and len(t_clean) > len(known) + 5:
                t_clean = known.strip("“\"")
                break
        lines.append(f"> **{t_clean}**")
        lines.append(">")
        title_norm = t_clean.lower()

    # L05-P29-CH: stitch soft-wrapped chapter / body lines before emit
    # Never join across Step N: or research-phase boundaries (L07-P42 / L06-P41).
    stitched_paras: list[str] = []
    for p in paragraphs:
        p = re.sub(r"\s+", " ", p).strip()
        if not p:
            continue
        if stitched_paras:
            prev = stitched_paras[-1]
            if re.match(r"^Step\s+\d+\s*:", p, re.I) or re.match(
                r"^(Intuitive|Qualitative|Quantitative)\s+phase\s*:", p, re.I
            ):
                stitched_paras.append(p)
                continue
            # Continuation: prev ends mid-phrase, this starts lowercase
            if (
                not prev.rstrip().endswith((".", "?", "!", ":", ";"))
                and p[:1].islower()
                and not re.match(r"^Step\s+\d+\s*:", prev, re.I)
            ):
                stitched_paras[-1] = prev.rstrip() + " " + p
                continue
            # Chapter soft-wrap: "Chapter N: … the" + "language user/learner"
            if re.search(r"^Chapter\s+\d+\s*:", prev, re.I) and p[:1].islower():
                stitched_paras[-1] = prev.rstrip() + " " + p
                continue
        stitched_paras.append(p)
    paragraphs = _split_steps_and_phases(stitched_paras)

    for para in paragraphs:
        p = re.sub(r"\s+", " ", para).strip()
        if not p:
            continue
        # Do not re-emit title as a second unbolded line (log 04 #3 / C2-ADJ).
        p_norm = p.lower().strip("*").strip().strip("“\"")
        if title_norm and (
            p_norm == title_norm
            or p_norm == title_norm.strip("“\"")
            or (
                p_norm.startswith(title_norm)
                and len(p_norm) < len(title_norm) + 15
            )
        ):
            if len(p_norm) <= len(title_norm) + 8:
                continue
            # Title + body glued: emit body only
            rest = p[len(title) :] if p.lower().startswith(title_norm) else p
            rest = rest.lstrip(" :–-")
            if not rest:
                continue
            p = rest
        # Title-like first line if short and no explicit title
        if not title and not lines and len(p) < 80 and not p.endswith("."):
            lines.append(f"> **{p}**")
            lines.append(">")
            title_norm = p.lower()
            title = p
            continue
        # L05-P37: title fragment "levels" alone after "Background to the CEFR"
        if (
            title_norm == "background to the cefr"
            and p_norm == "levels"
        ):
            # Upgrade title rather than emit orphan body line
            for li, ln in enumerate(lines):
                if ln.startswith("> **Background to the CEFR**"):
                    lines[li] = "> **Background to the CEFR levels**"
            continue
        if re.match(r"^Chapter\s+\d+\s*:", p, re.I):
            lines.append(f"> *{p}*")
        elif re.match(
            r"^(Intuitive|Qualitative|Quantitative)\s+phase\s*:",
            p,
            re.I,
        ):
            # Bold phase label, keep body after colon (L06-P41 clean form)
            m_ph = re.match(
                r"^((?:Intuitive|Qualitative|Quantitative)\s+phase\s*:)\s*(.*)$",
                p,
                re.I,
            )
            if m_ph:
                label = m_ph.group(1).strip()
                # Normalize "Intuitive phase:" capitalization
                label = re.sub(
                    r"^(intuitive|qualitative|quantitative)",
                    lambda m: m.group(1).capitalize(),
                    label,
                    flags=re.I,
                )
                body = m_ph.group(2).strip()
                if body:
                    lines.append(f"> **{label}** {body}")
                else:
                    lines.append(f"> **{label}**")
            else:
                lines.append(f"> {p}")
        else:
            lines.append(f"> {p}")
        lines.append(">")
    while lines and lines[-1] == ">":
        lines.pop()
    return "\n".join(lines).strip() + ("\n" if lines else "")


def load_callouts_registry() -> list[dict[str, Any]]:
    from pathlib import Path
    import json
    from pipeline.config import METADATA_DIR

    path = METADATA_DIR / "callouts_registry.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("callouts") or [])


def registry_callouts_for_page(page_num: int) -> list[dict[str, Any]]:
    return [c for c in load_callouts_registry() if c.get("page") == page_num]
