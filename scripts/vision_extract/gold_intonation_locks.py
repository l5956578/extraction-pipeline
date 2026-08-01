#!/usr/bin/env python3
"""Section-aware gold locks for Threshold intonation (leaf 34–35 PNG critic).

RULES (binding):
1. PNG glyph wins over PDF text layer and section titles.
2. PDF text is skeleton/hint only.
3. Letter-skeleton merge MUST NOT collapse multi-form pairs
   (1.1.3 vs 1.3.1 bedroom; 1.2.1 vs 1.3.1 train).
4. Do not invent ˏ on tags just because the section says "confirmation"
   if PNG shows low fall.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THR_MD = ROOT / "output/cefr-threshold-1990/Threshold_1990.md"
THR_OV = ROOT / "work/cefr-threshold-1990/page_overrides"
WAY_MD = ROOT / "output/cefr-waystage-1990/Waystage_1990.md"

# Full gold block 1.1.3–1.3.4 (PNG-critic locked)
# Prefer straight apostrophe in contractions (ASCII ') so block compare is stable.
GOLD_BLOCK_113_134 = """**1.1.3** the + NP/this, that, these, those (+ NP) + *be* + NP

> ˈThis is the ˎbedroom.  
> The ˇanimal over ·there | is my ˎdog.

**1.1.4** I, you, he, she, it, we, they + *be* + NP

> ˈHe is the ˎowner of the ·restaurant.

#### 1.2 reporting (describing and narrating)

**1.2.1** declarative sentences

> The ˈtrain has ˎleft.

**1.2.2** NP + say, think + complement clause

> He ·says the ˈshop is ˎshut.

#### 1.3 correcting

**1.3.1** As 1.1 and 1.2, with contrastive stress

> ˋThis is the ·bedroom.
> The ·train ˋhas ·left.

**1.3.2** (correcting a positive statement)  
(e.g. Vaˈletta is in ˎItaly.)  
**No** (+ tag)

> ˈNo it ˇisn't.

**1.3.3** negative sentences

> Va·letta ˈisn't in ˇItaly.

**1.3.4** (correcting a negative statement)  
(e.g. We ˈdidn't go to ˎLondon.)  
**Yes** (+ tag)

> ˈYes you ˇdid.
"""

# Exact gold lines (leaf 34–35). Straight apostrophes only — strip_skel normalizes curly.
EXACT_GOLD_LINES = [
    "ˈThis is the ˎbedroom.",
    "The ˇanimal over ·there | is my ˎdog.",
    "ˈHe is the ˎowner of the ·restaurant.",
    "The ˈtrain has ˎleft.",
    "He ·says the ˈshop is ˎshut.",
    "ˋThis is the ·bedroom.",
    "The ·train ˋhas ·left.",
    "ˈNo it ˇisn't.",
    "Va·letta ˈisn't in ˇItaly.",
    "ˈYes you ˇdid.",
    "You ˇdid ·go to ·London.",
    "ˊDid you ˎsee him?",
    "You ˊsaw him?",
    "They ˎlost the ·match, | ˎdidn't they?",
    "ˈPlease can you ·tell me the ·way to the ˎstation?",
]

# Multi-form skeletons: never fold into a single skel→line map (section locks only).
# Both bedroom (LF vs HF) and train (1.2.1 vs 1.3.1) share letters but differ by marks.
MULTIFORM_EXACT_SKELETONS = {
    "this is the bedroom",
    "the train has left",
}

# Skeletons with multiple legitimate markings — never letter-skeleton replace
PROTECTED_SKELETONS = {
    "this is the bedroom",
    "the train has left",
    "no it isnt",
    "yes you did",
    "did you see him",
    "you saw him",
    "they lost the match didnt they",
    "please can you tell me the way to the station",
    "the animal over there is my dog",
    "he is the owner of the restaurant",
}

# Full right-hand sides of English contractions (matched greedily)
CONTRACTION_RIGHT = {
    "t",
    "s",
    "ll",
    "re",
    "ve",
    "d",
    "m",
    "clock",
    "all",  # y'all
}


def strip_skel(s: str) -> str:
    """Letter skeleton for matching. Normalize curly apostrophes first so
    didn't / isn’t / EXACT gold / product MD share one key."""
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = re.sub(r"[ˈˎˋˏˊˇ·ˌ'`´,.\"|\$]+", "", s)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s).lower().strip()
    return re.sub(r"\s+", " ", s)


def midword_high(s: str) -> str:
    """ASCII mid-word high (pre'fer, e'specially, In'deed) → Unicode; keep contractions.

    IMPORTANT: right side must be multi-char-aware so I'll → stays I'll
    (not I + ' + l → Iˈll). Left side is multi-letter so In'deed → Inˋdeed
    (not n'deed with dead single-char special-case).
    """
    s = s.replace("\u2019", "'").replace("\u2018", "'")

    def repl(m: re.Match) -> str:
        left, right = m.group(1), m.group(2)
        if right.lower() in CONTRACTION_RIGHT:
            return m.group(0)
        # Indeed / Exactly style often high fall mid-word in book
        if left.lower() in {"in", "e"} and right.lower() in {"deed", "xactly"}:
            return left + "ˋ" + right
        return left + "ˈ" + right

    return re.sub(
        r"([A-Za-z]+)'([A-Za-z]+)",
        repl,
        s,
    )


def repair_broken_contractions(md: str) -> tuple[str, int]:
    """Undo mistaken Iˈll / youˈre style conversions back to apostrophe.

    Note: Python \\w treats modifier-letter tone marks (ˈ etc.) as word chars,
    so \\b is unreliable next to tones — use plain substring patterns.
    """
    pairs = [
        ("Iˈll", "I'll"),
        ("Iˈve", "I've"),
        ("Iˈm", "I'm"),
        ("Iˈd", "I'd"),
        ("youˈre", "you're"),
        ("Youˈre", "You're"),
        ("weˈre", "we're"),
        ("Weˈre", "We're"),
        ("theyˈre", "they're"),
        ("Theyˈre", "They're"),
        ("itˈs", "it's"),
        ("Itˈs", "It's"),
        ("thatˈs", "that's"),
        ("Thatˈs", "That's"),
        ("whatˈs", "what's"),
        ("Whatˈs", "What's"),
        ("thereˈs", "there's"),
        ("Thereˈs", "There's"),
        ("hereˈs", "here's"),
        ("Hereˈs", "Here's"),
        ("letˈs", "let's"),
        ("Letˈs", "Let's"),
        ("heˈs", "he's"),
        ("Heˈs", "He's"),
        ("sheˈs", "she's"),
        ("Sheˈs", "She's"),
        ("whoˈs", "who's"),
        ("Whoˈs", "Who's"),
        ("donˈt", "don't"),
        ("Donˈt", "Don't"),
        ("didnˈt", "didn't"),
        ("Didnˈt", "Didn't"),
        ("isnˈt", "isn't"),
        ("Isnˈt", "Isn't"),
        ("arenˈt", "aren't"),
        ("Arenˈt", "Aren't"),
        ("wonˈt", "won't"),
        ("Wonˈt", "Won't"),
        ("canˈt", "can't"),
        ("Canˈt", "Can't"),
        ("hasnˈt", "hasn't"),
        ("havenˈt", "haven't"),
        ("hadnˈt", "hadn't"),
        ("couldnˈt", "couldn't"),
        ("wouldnˈt", "wouldn't"),
        ("shouldnˈt", "shouldn't"),
        ("mustnˈt", "mustn't"),
        ("wasnˈt", "wasn't"),
        ("werenˈt", "weren't"),
        ("youˈll", "you'll"),
        ("Youˈll", "You'll"),
        ("weˈll", "we'll"),
        ("Weˈll", "We'll"),
        ("theyˈll", "they'll"),
        ("Theyˈll", "They'll"),
        ("heˈll", "he'll"),
        ("sheˈll", "she'll"),
        ("youˈve", "you've"),
        ("weˈve", "we've"),
        ("theyˈve", "they've"),
        ("oˈclock", "o'clock"),
    ]
    n = 0
    for a, b in pairs:
        c = md.count(a)
        if c:
            md = md.replace(a, b)
            n += c
    return md, n


def _norm_apos(s: str) -> str:
    return s.replace("\u2019", "'").replace("\u2018", "'")


def apply_section_locks(md: str) -> tuple[str, list[str]]:
    """Force PNG-locked section forms. Returns (md, ops)."""
    ops: list[str] = []

    # --- Full 1.1.3–1.3.4 block replace when anchors exist ---
    # Preserve page markers / comments between 1.3.4 and 1.3.5 (lookahead only
    # after optional interstitial material is captured separately).
    pat = re.compile(
        r"(\*\*1\.1\.3\*\*.*?)((?:\n\s*(?:\*Page[^\n]*\n|<!--[^>]*-->\s*\n)*)*)"
        r"(?=\*\*1\.3\.5\*\*)",
        re.S,
    )
    m = pat.search(md)
    if m:
        old_block = m.group(1).strip()
        interstitial = m.group(2)
        gold = GOLD_BLOCK_113_134.strip()
        # Compare with normalized apostrophes so curly/straight doesn't thrash
        if _norm_apos(old_block) != _norm_apos(gold):
            # ensure page-28 markers if interstitial was emptied by a prior pass
            if not interstitial.strip():
                interstitial = (
                    "\n\n*Page **28***\n\n"
                    "<!-- page:28 -->\n\n"
                    "<!-- vision: leaf 35 doc p.29 | word-catalog multipass ch5-6 -->\n"
                )
            md = md[: m.start()] + gold + interstitial + md[m.end() :]
            ops.append("replaced 1.1.3–1.3.4 gold block (kept interstitial)")
        elif "\u2019" in old_block or "\u2018" in old_block:
            # Normalize curly → straight without full rewrite thrash logs
            md = md[: m.start()] + _norm_apos(old_block) + interstitial + md[m.end() :]
            ops.append("normalized apostrophes in 1.1.3–1.3.4")
    else:
        # Fallback: section-local regex locks
        ops.append("1.1.3–1.3.4 block anchor missing; applying local locks")

    # --- 1.1.3 local (LF bedroom + animal/dog only; train is 1.2.1 / 1.3.1) ---
    m113 = re.search(r"(\*\*1\.1\.3\*\*[\s\S]*?)(\*\*1\.1\.4\*\*)", md)
    if m113:
        block, fixed = m113.group(1), m113.group(1)
        fixed = re.sub(
            r">\s*[ˈˋ]This is the ·bedroom\.",
            "> ˈThis is the ˎbedroom.",
            fixed,
        )
        fixed = re.sub(
            r">\s*ˈThis is the ·bedroom\.",
            "> ˈThis is the ˎbedroom.",
            fixed,
        )
        # owner is 1.1.4 but dog is on 1.1.3 animal line
        fixed = fixed.replace("my ·dog", "my ˎdog")
        if fixed != block:
            md = md[: m113.start(1)] + fixed + md[m113.end(1) :]
            ops.append("1.1.3 local LF locks")

    # --- 1.1.4 owner LF ---
    m114 = re.search(r"(\*\*1\.1\.4\*\*[\s\S]*?)(####\s*1\.2\b|\*\*1\.2\.1\*\*)", md)
    if m114:
        block, fixed = m114.group(1), m114.group(1)
        fixed = fixed.replace("the ·owner of the", "the ˎowner of the")
        if fixed != block:
            md = md[: m114.start(1)] + fixed + md[m114.end(1) :]
            ops.append("1.1.4 owner LF")

    # --- 1.2.1 non-contrastive train ---
    m121 = re.search(r"(\*\*1\.2\.1\*\*[\s\S]*?)(\*\*1\.2\.2\*\*)", md)
    if m121:
        block, fixed = m121.group(1), m121.group(1)
        fixed = re.sub(
            r">\s*The ·train [ˈˋ]has ·left\.",
            "> The ˈtrain has ˎleft.",
            fixed,
        )
        fixed = re.sub(
            r">\s*The ˈtrain has ·left\.",
            "> The ˈtrain has ˎleft.",
            fixed,
        )
        if fixed != block:
            md = md[: m121.start(1)] + fixed + md[m121.end(1) :]
            ops.append("1.2.1 train LF")

    # --- 1.3.1 contrastive (HF This/has, mid bedroom/train/left) ---
    m131 = re.search(
        r"(\*\*1\.3\.1\*\*[\s\S]*?)(\*\*1\.3\.2\*\*|\*\*1\.3\.5\*\*|####\s*1\.4\b)",
        md,
    )
    if m131:
        block, fixed = m131.group(1), m131.group(1)
        fixed = re.sub(
            r">\s*[ˈˋ]This is the ˎbedroom\.",
            "> ˋThis is the ·bedroom.",
            fixed,
        )
        fixed = re.sub(
            r">\s*[ˈˋ]This is the ·bedroom\.",
            "> ˋThis is the ·bedroom.",
            fixed,
        )
        fixed = re.sub(
            r">\s*The ˈtrain has ˎleft\.",
            "> The ·train ˋhas ·left.",
            fixed,
        )
        fixed = re.sub(
            r">\s*The ·train ˈhas ·left\.",
            "> The ·train ˋhas ·left.",
            fixed,
        )
        fixed = re.sub(
            r">\s*The ·train has ˎleft\.",
            "> The ·train ˋhas ·left.",
            fixed,
        )
        fixed = re.sub(
            r">\s*The ·train ˋhas ˎleft\.",
            "> The ·train ˋhas ·left.",
            fixed,
        )
        if fixed != block:
            md = md[: m131.start(1)] + fixed + md[m131.end(1) :]
            ops.append("1.3.1 contrastive HF locks")

    # --- 1.4.1.1 / 1.4.1.2 / 1.4.1.3 / 1.4.2.2 PNG gold (global but unique phrases) ---
    pairs = [
        (r"[ˈˊ]'?Did you ˎsee him\?", "ˊDid you ˎsee him?"),
        (r">\s*[ˈˊ]Did you ˎsee him\?", "> ˊDid you ˎsee him?"),
        (r">\s*ˈDid you ˎsee him\?", "> ˊDid you ˎsee him?"),
        (r">\s*You [ˈˊ]saw him\?", "> You ˊsaw him?"),
        (
            r">\s*They ˎlost the ·match,\s*\|\s*[ˎˏ]didn(['’]?)t they\?",
            r"> They ˎlost the ·match, | ˎdidn\1t they?",
        ),
        (
            r">\s*They [ˎˏ]lost the ·match,\s*\|\s*[ˎˏ]didn(['’]?)t they\?",
            r"> They ˎlost the ·match, | ˎdidn\1t they?",
        ),
        (
            r">\s*[ˈˊ]Please can you ·tell me the ·way to the ˎstation\?",
            "> ˈPlease can you ·tell me the ·way to the ˎstation?",
        ),
        (r"the ·owner of the", "the ˎowner of the"),
        (r"\bmy ·dog\b", "my ˎdog"),
        (r"ˈNo it ˋisn", "ˈNo it ˇisn"),
        (r"ˈNo it ˈisn", "ˈNo it ˇisn"),
        (r"ˈYes you ˋdid\b", "ˈYes you ˇdid"),
        (r"ˈYes you ˈdid\b", "ˈYes you ˇdid"),
        # IPA secondary mis-encode
        (r"(?<=\s)ˌ(?=[A-Za-z])", "ˎ"),
    ]
    for a, b in pairs:
        md2, c = re.subn(a, b, md)
        if c and md2 != md:
            md = md2
            ops.append(f"global {a[:40]!r} x{c}")
        elif c:
            # pattern matched but replacement identical — no-op
            pass

    # Mid-word ASCII high on tone-bearing example lines
    # Include curly apostrophe U+2019 as mid-word high source
    lines = []
    mh = 0
    for line in md.splitlines(keepends=True):
        if line.lstrip().startswith("<!--"):
            lines.append(line)
            continue
        # Normalize curly apostrophe mid-word before convert
        work = line.replace("\u2019", "'")
        if re.search(r"[A-Za-z]'[A-Za-z]", work) and (
            re.search(r"[ˈˎˋˏˊˇ·]", work)
            or work.lstrip().startswith(">")
            or re.search(r"e'[Ss]pecially|In'[Dd]eed|pre'[Ff]er", work)
        ):
            nl = midword_high(work)
            if nl != line:
                mh += 1
            lines.append(nl)
        else:
            lines.append(line)
    if mh:
        md = "".join(lines)
        ops.append(f"midword_high lines={mh}")

    # Explicit known mid-word forms (PDF high mark mid-word)
    explicit = [
        ("e'specially", "eˈspecially"),
        ("E'specially", "Eˈspecially"),
        ("In'deed", "Inˋdeed"),
        ("in'deed", "inˋdeed"),
        ("pre'fer", "preˈfer"),
        ("Pre'fer", "Preˈfer"),
    ]
    for a, b in explicit:
        if a in md:
            md = md.replace(a, b)
            ops.append(f"explicit midword {a}→{b}")

    # Repair any prior bad contraction→tone conversions
    md, n_rep = repair_broken_contractions(md)
    if n_rep:
        ops.append(f"repair_broken_contractions x{n_rep}")

    # Restore page-28 markers if still missing before 1.3.5
    if "<!-- page:28 -->" not in md and re.search(r"\*\*1\.3\.4\*\*", md):
        md2, c = re.subn(
            r"(\*\*1\.3\.4\*\*[\s\S]*?>\s*ˈYes you ˇdid\.\s*\n)(\s*)(\*\*1\.3\.5\*\*)",
            r"\1\n\n*Page **28***\n\n<!-- page:28 -->\n\n"
            r"<!-- vision: leaf 35 doc p.29 | word-catalog multipass ch5-6 -->\n\3",
            md,
            count=1,
        )
        if c:
            md = md2
            ops.append("restored page-28 markers before 1.3.5")

    return md, ops


def residual_assertions(md: str) -> list[str]:
    """Return hard residual failures (empty = pass)."""
    fails: list[str] = []

    def need(s: str, n: int = 1, label: str | None = None) -> None:
        c = md.count(s)
        if c < n:
            fails.append(f"NEED {label or s!r}: got {c}, want >={n}")

    def ban(s: str, label: str | None = None) -> None:
        if s in md:
            fails.append(f"BAN {label or s!r}: count={md.count(s)}")

    # Gold musts
    need("ˋThis is the ·bedroom", 1)
    need("The ·train ˋhas ·left", 1)
    need("ˈThis is the ˎbedroom", 1)
    need("The ˈtrain has ˎleft", 1)  # 1.2.1 (and only there ideally)
    need("ˊDid you ˎsee him", 1)
    need("You ˊsaw him", 1)
    if "ˎdidn’t they" not in md and "ˎdidn't they" not in md:
        fails.append("NEED ˎdidn't they tag")
    need("ˈPlease can you", 1)
    need("ˎowner", 1)
    need("my ˎdog", 1)
    need("The ˇanimal", 1)

    # Bad forms (section-agnostic residual)
    ban("ˈThis is the ·bedroom", "wrong mid-bedroom with head (not 1.1.3/1.3.1 gold)")
    ban("The ·train ˈhas ·left", "contrastive train with head not HF")
    ban("ˈDid you ˎsee him", "Did should be high-rise ˊ")
    ban("ˏdidn’t they", "tag is LF not LR invent")
    ban("ˏdidn't they", "tag is LF not LR invent")
    ban("ˊPlease can you", "Please is head not high-rise")
    ban("the ·owner of the", "owner LF")
    ban("my ·dog", "dog LF")

    # 1.3.1 must not still have non-contrastive train form
    m131 = re.search(
        r"\*\*1\.3\.1\*\*[\s\S]*?(?=\*\*1\.3\.2\*\*|\*\*1\.3\.5\*\*)", md
    )
    if m131:
        b = m131.group(0)
        if "The ˈtrain has ˎleft" in b:
            fails.append("BAN in 1.3.1: The ˈtrain has ˎleft (must be ·train ˋhas ·left)")
        if "ˋThis is the ·bedroom" not in b:
            fails.append("NEED in 1.3.1: ˋThis is the ·bedroom")
        if "The ·train ˋhas ·left" not in b:
            fails.append("NEED in 1.3.1: The ·train ˋhas ·left")

    # 1.1.3 must keep LF
    m113 = re.search(r"\*\*1\.1\.3\*\*[\s\S]*?(?=\*\*1\.1\.4\*\*)", md)
    if m113:
        b = m113.group(0)
        if "ˈThis is the ˎbedroom" not in b:
            fails.append("NEED in 1.1.3: ˈThis is the ˎbedroom")
        if "my ˎdog" not in b and "my ˎdog" not in md:
            fails.append("NEED dog LF near 1.1.3")

    # 1.2.1 train form
    m121 = re.search(r"\*\*1\.2\.1\*\*[\s\S]*?(?=\*\*1\.2\.2\*\*)", md)
    if m121 and "The ˈtrain has ˎleft" not in m121.group(0):
        fails.append("NEED in 1.2.1: The ˈtrain has ˎleft")

    # ASCII high as tone on short example lines
    for i, line in enumerate(md.splitlines(), 1):
        if (
            re.search(r"(^|>\s*)'[A-Za-z]", line)
            and len(line) < 120
            and re.search(r"[A-Za-z].*[.?]", line)
        ):
            fails.append(f"ASCII high tone L{i}: {line.strip()[:70]}")
            if len(fails) > 40:
                break

    if "ˌ" in md:
        fails.append(f"IPA secondary ˌ present x{md.count('ˌ')}")

    # Primary mid-word residual on known forms
    if "e'specially" in md:
        fails.append("BAN e'specially (should be eˈspecially)")

    # Broken contractions (tone mark where apostrophe belongs)
    for bad in ("Iˈll", "Iˈve", "youˈre", "Youˈre", "weˈre", "Weˈre", "donˈt", "canˈt"):
        if bad in md:
            fails.append(f"BAN broken contraction {bad!r}")

    return fails


def gold_counts(md: str) -> dict[str, int]:
    keys = [
        "ˋThis is the ·bedroom",
        "The ·train ˋhas ·left",
        "The ˈtrain has ˎleft",
        "ˈThis is the ˎbedroom",
        "ˈThis is the ·bedroom",
        "The ·train ˈhas ·left",
        "ˊDid you ˎsee him",
        "ˈDid you ˎsee him",
        "You ˊsaw him",
        "ˎdidn’t they",
        "ˎdidn't they",
        "ˏdidn’t they",
        "ˏdidn't they",
        "ˈPlease can you",
        "ˊPlease can you",
        "the ·owner",
        "my ·dog",
        "ˎowner",
        "my ˎdog",
        "The ˇanimal",
        "ˇisn",
        "e'specially",
        "eˈspecially",
    ]
    return {k: md.count(k) for k in keys}


def apply_to_path(path: Path) -> tuple[list[str], list[str]]:
    md = path.read_text(encoding="utf-8")
    md2, ops = apply_section_locks(md)
    path.write_text(md2, encoding="utf-8")
    fails = residual_assertions(md2)
    return ops, fails


def sync_override_leaves(leaves: list[int] | None = None) -> int:
    """Apply section locks to page overrides for primary leaves."""
    if leaves is None:
        leaves = list(range(34, 65)) + list(range(66, 91)) + list(range(104, 113)) + list(
            range(124, 131)
        )
    n = 0
    for leaf in leaves:
        p = THR_OV / f"page_{leaf:03d}.md"
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        t2, ops = apply_section_locks(t)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            n += 1
            if ops:
                print(f"  ov leaf {leaf}: {ops}")
    return n


def _is_example_tone_line(line: str) -> bool:
    """Gate residual OCR→tone rewrites to mark-bearing / example lines only.

    Never rewrite ordinary prose (mid-paragraph contractions, quote-as-punctuation).
    """
    s = line.strip()
    if not s or s.startswith("<!--"):
        return False
    # Already carries Unicode intonation inventory
    if re.search(r"[ˈˎˋˏˊˇ·]", s):
        return True
    # Blockquote exponent lines
    if s.startswith(">"):
        return True
    # Short OCR-encoded example (token-start ' / , / . before letter, or mid-word comma LF)
    if len(s) > 160:
        return False
    if re.search(r"(^|[\s>|*(])['`´,][A-Za-z]", s):
        # Multi-quote prose without low-family OCR → skip
        if s.count("'") >= 2 and not re.search(
            r"(^|[\s>|*(]),[A-Za-z]|[A-Za-z],[A-Za-z]", s
        ):
            return False
        return True
    if re.search(r"[A-Za-z],[A-Za-z]{2,}", s) and (
        s.startswith(">")
        or re.search(r"\b(a,gree|ar,rive|pre,fer|a,fraid|o,pinion|p,m)\b", s, re.I)
    ):
        return True
    return False


def waystage_residual_safety(md: str) -> tuple[str, list[str]]:
    """Convert residual ASCII tone / midword high on **example lines only**.

    Binding safety: never rewrite prose apostrophes into tones document-wide.
    """
    ops: list[str] = []
    out_lines: list[str] = []
    n_high = n_comma = n_mh = 0
    for line in md.splitlines(keepends=True):
        body = line.rstrip("\n\r")
        nl = line[len(body) :]
        if not _is_example_tone_line(body):
            out_lines.append(line)
            continue
        work = body
        # token-start ASCII high on this example line only
        work2, c = re.subn(r"(^|[\s>|])'(?=[A-Za-z])", r"\1ˈ", work)
        if c:
            work = work2
            n_high += c
        # token-start ASCII comma low fall
        work2, c = re.subn(r"(^|[\s>|]),(?=[A-Za-z])", r"\1ˎ", work)
        if c:
            work = work2
            n_comma += c
        # midword high only when line already has tones or is blockquote (not bare prose)
        if re.search(r"[A-Za-z]'[A-Za-z]", work) and re.search(
            r"[ˈˎˋˏˊˇ·>]", work
        ):
            work2 = midword_high(work)
            if work2 != work:
                n_mh += 1
                work = work2
        out_lines.append(work + nl)
    md = "".join(out_lines)
    if n_high:
        ops.append(f"waystage ASCII high→ˈ (example lines only) x{n_high}")
    if n_comma:
        ops.append(f"waystage ASCII comma→ˎ (example lines only) x{n_comma}")
    if n_mh:
        ops.append(f"waystage midword_high example_lines={n_mh}")
    # owner LF (unique phrase; safe global)
    md2, c = re.subn(r"the ·owner of the", "the ˎowner of the", md)
    if c:
        md = md2
        ops.append(f"waystage owner LF x{c}")
    md2, c = re.subn(r"(?<=\s)ˌ(?=[A-Za-z])", "ˎ", md)
    if c:
        md = md2
        ops.append(f"waystage IPA ˌ→ˎ x{c}")
    return md, ops


def main() -> None:
    print("=== apply gold locks Threshold ===")
    ops, fails = apply_to_path(THR_MD)
    for o in ops:
        print(f"  op: {o}")
    md = THR_MD.read_text(encoding="utf-8")
    print("counts:", gold_counts(md))
    print("fails:", fails or "NONE")
    n = sync_override_leaves([34, 35])
    print(f"overrides 34-35 touched: {n}")


if __name__ == "__main__":
    main()
