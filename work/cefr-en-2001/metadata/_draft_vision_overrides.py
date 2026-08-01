"""Draft CEFR 2001 page_overrides from OCR for vision polish (v2)."""
from pathlib import Path
import re

ocr_dir = Path("work/cefr-en-2001/page_ocr")
out_dir = Path("work/cefr-en-2001/page_overrides")
out_dir.mkdir(parents=True, exist_ok=True)

LEVELS = ["C2", "C1", "B2", "B1", "A2", "A1"]

# Known illustrative scale titles (uppercase keys)
KNOWN_SCALES = {
    "MONITORING AND REPAIR",
    "OVERALL LISTENING COMPREHENSION",
    "UNDERSTANDING INTERACTION BETWEEN NATIVE SPEAKERS",
    "LISTENING AS A MEMBER OF A LIVE AUDIENCE",
    "LISTENING TO ANNOUNCEMENTS AND INSTRUCTIONS",
    "LISTENING TO AUDIO MEDIA AND RECORDINGS",
    "OVERALL READING COMPREHENSION",
    "READING CORRESPONDENCE",
    "READING FOR ORIENTATION",
    "READING FOR INFORMATION AND ARGUMENT",
    "READING INSTRUCTIONS",
    "WATCHING TV AND FILM",
    "OVERALL SPOKEN INTERACTION",
    "UNDERSTANDING A NATIVE SPEAKER INTERLOCUTOR",
    "CONVERSATION",
    "INFORMAL DISCUSSION (WITH FRIENDS)",
    "FORMAL DISCUSSION AND MEETINGS",
    "GOAL-ORIENTED CO-OPERATION",
    "TRANSACTIONS TO OBTAIN GOODS AND SERVICES",
    "INFORMATION EXCHANGE",
    "INTERVIEWING AND BEING INTERVIEWED",
    "OVERALL WRITTEN INTERACTION",
    "CORRESPONDENCE",
    "NOTES, MESSAGES & FORMS",
    "NOTES, MESSAGES AND FORMS",
    "TAKING THE FLOOR (TURNTAKING)",
    "CO-OPERATING",
    "ASKING FOR CLARIFICATION",
    "NOTE-TAKING (LECTURES, SEMINARS, ETC.)",
    "PROCESSING TEXT",
    "PLANNING",
    "COMPENSATING",
    "CREATIVE WRITING",
    "REPORTS AND ESSAYS",
    "OVERALL ORAL PRODUCTION",
    "OVERALL WRITTEN PRODUCTION",
    "PUBLIC ANNOUNCEMENTS",
    "ADDRESSING AUDIENCES",
    "SUSTAINED MONOLOGUE: DESCRIBING EXPERIENCE",
    "SUSTAINED MONOLOGUE: PUTTING A CASE (E.G. IN A DEBATE)",
    "GENERAL LINGUISTIC RANGE",
    "VOCABULARY RANGE",
    "VOCABULARY CONTROL",
    "GRAMMATICAL ACCURACY",
    "PHONOLOGICAL CONTROL",
    "ORTHOGRAPHIC CONTROL",
    "SOCIOLINGUISTIC APPROPRIATENESS",
    "FLEXIBILITY",
    "TURNTAKING",
    "THEMATIC DEVELOPMENT",
    "COHERENCE AND COHESION",
    "SPOKEN FLUENCY",
    "PROPOSITIONAL PRECISION",
    "IDENTIFYING CUES AND INFERRING (SPOKEN & WRITTEN)",
    "IDENTIFYING CUES AND INFERRING",
}


def clean_text(s: str) -> str:
    s = s.replace("\ufb01", "fi").replace("\ufb02", "fl")
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = s.replace("–", "–").replace("—", "—")
    # normalize weird hyphens mid-word from line breaks later
    return s


def is_scale_title(s: str) -> bool:
    u = re.sub(r"\s+", " ", s.strip()).upper()
    if u in KNOWN_SCALES:
        return True
    # heuristic: mostly caps, long enough, not a sentence
    letters = re.sub(r"[^A-Za-z]", "", s)
    if len(letters) < 8:
        return False
    if s.strip().startswith("Common European") or s.strip().startswith("Language use"):
        return False
    upper = sum(1 for c in letters if c.isupper())
    if upper / len(letters) < 0.9:
        return False
    if s.strip().endswith(".") and not s.strip().endswith("ETC."):
        return False
    return True


def format_page(n: int) -> str:
    raw = (ocr_dir / f"page_{n:03d}.txt").read_text(encoding="utf-8", errors="replace")
    raw = clean_text(raw)
    lines = [ln.rstrip() for ln in raw.splitlines()]

    # strip chrome
    body = []
    for ln in lines:
        s = ln.strip()
        if not s:
            body.append("")
            continue
        if s.startswith("Common European Framework"):
            continue
        if s.startswith("Language use and the language user"):
            continue
        if re.fullmatch(r"\d{1,3}", s):
            continue
        body.append(s)

    # collapse blanks
    compact = []
    prev_blank = False
    for s in body:
        blank = not s
        if blank and prev_blank:
            continue
        compact.append(s)
        prev_blank = blank

    out: list[str] = [
        f"<!-- el:start type=prose id=prose_p{n:03d} page={n} -->",
        f"<!-- vision: CEFR 2001 PDF page {n} -->",
        "",
    ]

    i = 0
    scale_title: str | None = None
    scale_rows: list[tuple[str, str]] = []
    in_box = False
    box_items: list[str] = []
    para: list[str] = []

    def flush_para() -> None:
        nonlocal para
        if para:
            text = " ".join(para)
            text = re.sub(r"\s+", " ", text).strip()
            # fix hyphenation across lines already joined
            text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
            out.append(text)
            out.append("")
            para = []

    def flush_scale() -> None:
        nonlocal scale_title, scale_rows
        if not scale_title:
            return
        out.append(f"**{scale_title}**")
        out.append("")
        out.append("| Level | Descriptor |")
        out.append("| --- | --- |")
        merged: list[list[str]] = []
        for lev, txt in scale_rows:
            txt = re.sub(r"\s+", " ", txt).strip()
            txt = re.sub(r"(\w)-\s+(\w)", r"\1\2", txt)
            if merged and merged[-1][0] == lev:
                merged[-1][1] = (merged[-1][1] + " " + txt).strip()
            else:
                merged.append([lev, txt])
        for lev, txt in merged:
            out.append(f"| **{lev}** | {txt.replace('|', '\\|')} |")
        out.append("")
        scale_title = None
        scale_rows = []

    def flush_box() -> None:
        nonlocal in_box, box_items
        if not in_box:
            return
        out.append("> **Users of the Framework may wish to consider and where appropriate state:**")
        out.append(">")
        for it in box_items:
            it = re.sub(r"\s+", " ", it).strip().rstrip(";")
            it = re.sub(r"(\w)-\s+(\w)", r"\1\2", it)
            out.append(f"> - *{it}*")
        out.append("")
        in_box = False
        box_items = []

    while i < len(compact):
        s = compact[i]
        i += 1
        if not s:
            if not in_box:
                flush_para()
            continue

        # User boxes
        if s.startswith("Users of the Framework may wish"):
            flush_para()
            flush_scale()
            in_box = True
            box_items = []
            continue

        if in_box:
            if s in LEVELS or is_scale_title(s) or re.match(r"^(4\.\d|5\.\d)", s):
                flush_box()
                i -= 1
                continue
            if s in ("•", "·", "-"):
                continue
            if s.startswith("•") or s.startswith("·"):
                box_items.append(s.lstrip("•· ").strip())
            else:
                if box_items:
                    box_items[-1] = (box_items[-1] + " " + s).strip()
                else:
                    # stray text after box header before bullets
                    pass
            continue

        # Section headers: "4.4.2 Title" or "4.4.2" alone then title next
        m = re.match(r"^(4\.\d+(?:\.\d+){0,3}|5\.\d+(?:\.\d+){0,3})\s*(.*)$", s)
        if m:
            flush_para()
            flush_scale()
            flush_box()
            num = m.group(1)
            title = m.group(2).strip()
            depth = num.count(".")
            hashes = "###" if depth == 1 else "####"
            # if title empty, peek next non-empty non-bullet line as title if short
            if not title and i < len(compact):
                nxt = compact[i]
                if (
                    nxt
                    and nxt not in LEVELS
                    and not nxt.startswith("•")
                    and not nxt.startswith("Users of")
                    and not is_scale_title(nxt)
                    and not re.match(r"^(4\.\d|5\.\d)", nxt)
                    and len(nxt) < 120
                    and not nxt[0].islower()
                ):
                    # only take if it looks like a title (starts capital, not a full para)
                    if len(nxt.split()) <= 12:
                        title = nxt
                        i += 1
            if title:
                out.append(f"{hashes} {num} {title}")
            else:
                out.append(f"{hashes} {num}")
            out.append("")
            continue

        # Scale title
        if is_scale_title(s):
            flush_para()
            flush_box()
            if scale_title:
                flush_scale()
            scale_title = re.sub(r"\s+", " ", s.strip())
            scale_rows = []
            continue

        # Level under a scale
        if s in LEVELS and scale_title is not None:
            parts: list[str] = []
            while i < len(compact):
                ns = compact[i]
                if not ns:
                    i += 1
                    if parts:
                        break
                    continue
                if ns in LEVELS:
                    break
                if is_scale_title(ns):
                    break
                if ns.startswith("Users of the Framework"):
                    break
                if re.match(r"^(4\.\d|5\.\d)", ns):
                    break
                if ns.startswith("Note:") or ns.startswith("NOTE:"):
                    break
                if ns in ("•", "·") or ns.startswith("•") or ns.startswith("·"):
                    break
                if ns.startswith("Illustrative scales"):
                    break
                parts.append(ns)
                i += 1
            scale_rows.append((s, " ".join(parts).strip() or "No descriptor available"))
            continue

        # Notes
        if s.startswith("Note:") or s.startswith("NOTE:"):
            flush_para()
            if scale_title:
                flush_scale()
            out.append(s)
            out.append("")
            continue

        # Bullets
        if s in ("•", "·"):
            flush_para()
            if scale_title:
                flush_scale()
            parts = []
            while i < len(compact):
                ns = compact[i]
                if not ns:
                    i += 1
                    if parts:
                        break
                    continue
                if ns in ("•", "·") or ns.startswith("•") or ns.startswith("·"):
                    break
                if ns in LEVELS:
                    break
                if is_scale_title(ns) or re.match(r"^(4\.\d|5\.\d)", ns):
                    break
                if ns.startswith("Users of the Framework"):
                    break
                if ns.startswith("Illustrative"):
                    break
                parts.append(ns)
                i += 1
            if parts:
                t = " ".join(parts)
                t = re.sub(r"\s+", " ", t).strip()
                t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
                out.append(f"- {t}")
            continue

        if s.startswith("•") or s.startswith("·"):
            flush_para()
            if scale_title:
                flush_scale()
            out.append(f"- {s.lstrip('•· ').strip()}")
            continue

        # Normal prose — if we hit prose while scale open, close scale first
        if scale_title and s not in LEVELS and not is_scale_title(s):
            # might still be scale desc without level? uncommon
            flush_scale()

        para.append(s)

    flush_para()
    flush_scale()
    flush_box()
    out.append(f"<!-- el:end id=prose_p{n:03d} -->")
    out.append("")
    return "\n".join(out)


def main() -> None:
    # Never overwrite hand-crafted pages 51-73
    for n in range(74, 141):
        md = format_page(n)
        p = out_dir / f"page_{n:03d}.md"
        p.write_text(md, encoding="utf-8")
        print(f"wrote {n}")


if __name__ == "__main__":
    main()
