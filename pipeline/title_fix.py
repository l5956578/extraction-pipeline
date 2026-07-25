"""Detect and fix reversed text from rotated PDF layers."""

from __future__ import annotations

import re

from pipeline.utils import COMMON_WORDS, english_word_score

# Domain + general English tokens used for reverse scoring (CEFR scale titles).
_DESCRIPTOR_WORDS = {
    "psychology", "argument", "leading", "group", "phonology", "coherence",
    "interaction", "fluency", "accuracy", "range", "vocabulary", "control",
    "reception", "production", "mediation", "description", "collaborating",
    "relating", "translating", "strategies", "concept", "concepts", "online",
    "overall", "reading", "writing", "written", "oral", "understanding",
    "conversation", "discussion", "comprehension", "communication", "examples",
    "domains", "education", "language", "learner", "learning", "specific",
    "diagrams", "graphs", "data", "explaining", "explain", "information",
    "relaying", "structure", "cultural", "appropriateness", "sociolinguistic",
    "repertoire", "sign", "text", "new", "case", "public", "announcements",
    "putting", "debate", "publication", "process", "media", "pragmatic",
    "linguistic", "phonological", "grammatical", "lexical", "discourse",
    "spoken", "speech", "signed", "signalling", "monitoring", "planning",
    "compensating", "turntaking", "cooperating", "co-operating", "note-taking",
    "translating", "interpreting", "facilitating", "mediating", "processing",
    "creative", "literature", "response", "personal", "expressing", "sustained",
    "monologue", "interviewing", "goal-oriented", "transactions", "collaboration",
    "plurilingual", "pluricultural", "competence", "repertoire", "descriptors",
    "level", "scale", "framework", "companion", "volume", "appendix",
    "written", "structure", "cultural", "appropriateness", "explain", "new",
    "to", "a", "the", "and", "or", "of", "in", "for", "with", "from", "into",
}

# Whole-token fixes when simple reverse yields a near-miss (e.g. cfiiceps → speciifc)
# Also known reversed fragments from rotated PDF layers that score poorly as "words".
_GARBLED_TOKEN_FIX = {
    "cfiiceps": "specific",
    "speciifc": "specific",
    "smargaid": "diagrams",
    "shparg": "graphs",
    "atad": "data",
    "gnittup": "putting",
    "cilbup": "public",
    "noitacilbup": "publication",
    "noitamrofni": "information",
    "ssecorp": "process",
    "txet": "text",
    "lortnoc": "control",
    "gnidnatsrednu": "understanding",
    "gninialpxe": "explaining",
    "nialpxe": "explain",
    "gnitirw": "writing",
    "nettirw": "written",
    "ssenetairporppa": "appropriateness",
    "larutluc": "cultural",
    "erutcurts": "structure",
    "stpecnoc": "concepts",
    "tpecnoc": "concept",
    "wen": "new",
    "ot": "to",
    "cte": "etc",
    # short reversed preposition (Collaborating ni a group → in)
    "ni": "in",
}

# Tokens that, when present in an artifact id, prove the slug is reversed/garbled.
GARBLED_ID_MARKERS = (
    "gnittup",
    "cilbup",
    "_ni_",
    "cfiiceps",
    "smargaid",
    "shparg",
    "noitacil",
    "noitamrofni",
    "cte_smargaid",
    "cte_",
    "gninialpxe",
    "nialpxe",
    "nettirw",
    "ssenetairporppa",
    "larutluc",
    "erutcurts",
    "stpecnoc",
    "collaborating_ni",
    "_ot_nialpxe",
    "ot_nialpxe",
    "_wen_",
    "strategies_ot_",
    "translating_a_nettirw",
    "sign_text_erutcurts",
    "sociolinguistic_ssenetairporppa",
)

_REVERSED_TOKEN = re.compile(
    r"^(yg|tn|pu|noitc|erio|gnid|krow|lortnoc|noitam|txet|sevit|tpecn|gnitar|"
    r"nett|nial|ssen|laru|erut|stpe|gnin|smarg|shpar|atad|cfiic|cilbu)",
    re.I,
)


def _is_known_english_token(word: str) -> bool:
    wl = (word or "").lower()
    if len(wl) < 2:
        return False
    if wl in _DESCRIPTOR_WORDS or wl in COMMON_WORDS:
        return True
    # english_word_score is fraction of known words in multi-token text; for one word 0 or 1
    return english_word_score(wl) >= 1.0


def title_readability_score(text: str) -> float:
    words = re.findall(r"[A-Za-z]{3,}", text)
    if not words:
        return 0.0
    hits = 0.0
    for w in words:
        wl = w.lower()
        if wl in _DESCRIPTOR_WORDS or wl in COMMON_WORDS:
            hits += 1.0
        elif _is_known_english_token(wl):
            hits += 0.85
        else:
            # Penalize known reverse tokens so garbled short headers lose to clean tables
            if wl in _GARBLED_TOKEN_FIX or wl[::-1] in _DESCRIPTOR_WORDS or wl[::-1] in COMMON_WORDS:
                hits -= 0.35
            else:
                hits += english_word_score(wl) * 0.4
    return hits / len(words)


def _apply_token_fix(word: str) -> tuple[str, bool]:
    """Fix one token; returns (fixed, changed)."""
    # Preserve punctuation attachments: word, word) word:
    m = re.match(r"^([^A-Za-z]*)([A-Za-z]+)([^A-Za-z]*)$", word)
    if not m:
        return word, False
    pre, core, post = m.group(1), m.group(2), m.group(3)
    low = core.lower()
    if low in _GARBLED_TOKEN_FIX:
        fixed = _GARBLED_TOKEN_FIX[low]
        if core.isupper():
            fixed = fixed.upper()
        elif core[0].isupper() and core[1:].islower():
            fixed = fixed[0].upper() + fixed[1:]
        elif core[0].isupper():
            fixed = fixed[0].upper() + fixed[1:]
        elif core[-1:].isupper() and len(core) > 3:
            # Reversed Title Case residue (gninialpxE → Explaining)
            fixed = fixed[0].upper() + fixed[1:]
        return f"{pre}{fixed}{post}", True
    return word, False


def _alpha_core(token: str) -> str:
    m = re.search(r"[A-Za-z]+", token or "")
    return m.group(0) if m else ""


def _tidy_reversed_punctuation(text: str) -> str:
    """Normalize punctuation left by character-reversed parentheticals.

    e.g. ``Explaining data in( ,graphs ,diagrams ).etc`` →
    ``Explaining data in graphs, diagrams (etc.)``
    """
    s = re.sub(r"\s+", " ", text).strip()
    # "in( ,graphs" / "in(,graphs" → "in graphs" then re-wrap later if needed
    s = re.sub(r"\bin\(\s*,\s*", "in ", s, flags=re.I)
    s = re.sub(r"\bin\(\s*", "in ", s, flags=re.I)
    # Leading commas glued to words: ",graphs" → ", graphs" then strip doubles
    s = re.sub(r"\s*,\s*", ", ", s)
    s = re.sub(r"\s*,\s*,", ",", s)
    # Trailing ").etc" / "). etc" → "(etc.)"
    s = re.sub(r"\s*\)\s*\.\s*etc\.?\s*$", " (etc.)", s, flags=re.I)
    s = re.sub(r"\s*\)\s*,?\s*etc\.?\s*$", " (etc.)", s, flags=re.I)
    s = re.sub(r"\s*\.\s*etc\.?\s*$", " (etc.)", s, flags=re.I)
    # Orphan leading ").etc" tokens mid-string
    s = re.sub(r"\)\s*\.\s*etc", "etc", s, flags=re.I)
    s = re.sub(r"\(\s*,\s*", "(", s)
    s = re.sub(r",\s*\)", ")", s)
    # "graphs , diagrams" already normalized; drop leading comma after space words
    s = re.sub(r"(\w)\s+,", r"\1,", s)
    # Collapse ", ," and spaces before punctuation
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    s = re.sub(r",\s*,", ",", s)
    s = re.sub(r"\s+", " ", s).strip(" ,")
    # If we have "Explaining data in graphs, diagrams etc" ensure (etc.)
    s = re.sub(r",?\s+etc\.?\s*$", " (etc.)", s, flags=re.I)
    # "in graphs, diagrams (etc.)" is good; fix double parens
    s = re.sub(r"\(\s*\(etc\.\)\s*\)", "(etc.)", s, flags=re.I)
    return s.strip()


def id_looks_garbled(artifact_id: str | None) -> bool:
    """True when a scale/table id still carries known reversed tokens."""
    if not artifact_id:
        return False
    aid = artifact_id.lower()
    if any(m in aid for m in GARBLED_ID_MARKERS):
        return True
    # Any underscore token that maps via _GARBLED_TOKEN_FIX
    for tok in aid.split("_"):
        if tok in _GARBLED_TOKEN_FIX:
            return True
    return False


def _case_preserve(src: str, fixed: str) -> str:
    if not src or not fixed:
        return fixed
    if src.isupper():
        return fixed.upper()
    if src[0].isupper() and (len(src) == 1 or src[1:].islower()):
        return fixed[0].upper() + fixed[1:]
    if src[0].isupper():
        return fixed[0].upper() + fixed[1:]
    if src[-1:].isupper() and len(src) > 3:
        return fixed[0].upper() + fixed[1:]
    return fixed


def fix_rotated_title(title: str) -> str:
    """Return the forward-reading form of a possibly reversed title."""
    if not title or not title.strip():
        return title
    # Collapse newlines from multi-line reversed table cells before token work
    forward = re.sub(r"[\r\n]+", " ", title).strip()
    forward = re.sub(r"\s+", " ", forward)
    # Split on whitespace but keep punctuation glued to words via _apply_token_fix
    words = forward.split()
    fixed_words: list[str] = []
    changed = False
    n_token_fixes = 0
    for word in words:
        mapped, did = _apply_token_fix(word)
        if did:
            fixed_words.append(mapped)
            changed = True
            n_token_fixes += 1
            continue
        # Alpha core length for reverse heuristics
        m = re.match(r"^([^A-Za-z]*)([A-Za-z]+)([^A-Za-z]*)$", word)
        if not m:
            fixed_words.append(word)
            continue
        pre, core, post = m.group(1), m.group(2), m.group(3)
        if len(core) < 2:
            fixed_words.append(word)
            continue
        # Title Case / ALL CAPS English: almost never PDF reverse — keep.
        # Exception: ends with capital (gninialpxE) — treat as reversed.
        if core[-1:].isupper() and core[:-1].islower() and len(core) > 4:
            rev_core = core[::-1]
            rev_core = rev_core[0].upper() + rev_core[1:].lower()
            fixed_words.append(f"{pre}{rev_core}{post}")
            changed = True
            n_token_fixes += 1
            continue
        rev_core = core[::-1]
        rev_low = rev_core.lower()
        low = core.lower()
        # Mapped reverse of core
        if rev_low in _GARBLED_TOKEN_FIX:
            rev_core = _GARBLED_TOKEN_FIX[rev_low]
            rev_core = _case_preserve(core, rev_core)
            fixed_words.append(f"{pre}{rev_core}{post}")
            changed = True
            n_token_fixes += 1
            continue
        # Reverse is known English while forward is not → un-reverse
        rev_is_en = _is_known_english_token(rev_low) or rev_low in _DESCRIPTOR_WORDS
        fwd_is_en = _is_known_english_token(low) or low in _DESCRIPTOR_WORDS
        if rev_is_en and not fwd_is_en and len(core) >= 3:
            fixed_words.append(f"{pre}{_case_preserve(core, rev_core)}{post}")
            changed = True
            n_token_fixes += 1
            continue
        # Title Case / ALL CAPS English: keep unless reverse is clearly better English
        if core.isupper() or (core[0].isupper() and core[1:].islower()):
            if rev_is_en and not fwd_is_en and len(core) >= 5:
                fixed_words.append(f"{pre}{_case_preserve(core, rev_core)}{post}")
                changed = True
                n_token_fixes += 1
            else:
                fixed_words.append(word)
            continue
        fwd_score = title_readability_score(core)
        rev_score = title_readability_score(rev_core)
        # Prefer reverse when it is a known English-ish improvement
        if rev_score > fwd_score + 0.05:
            fixed_words.append(f"{pre}{rev_core}{post}")
            changed = True
            n_token_fixes += 1
        elif fwd_score < 0.05 and (
            _REVERSED_TOKEN.match(core) or (rev_core[:1].isupper() and core[:1].islower())
        ):
            fixed_words.append(f"{pre}{rev_core}{post}")
            changed = True
            n_token_fixes += 1
        else:
            fixed_words.append(word)
    result = " ".join(fixed_words)
    if not changed:
        whole_rev = " ".join(
            (w[::-1] if w.isalpha() else w) for w in words
        )
        if title_readability_score(whole_rev) > title_readability_score(forward) + 0.05:
            return _tidy_reversed_punctuation(whole_rev)
    reversed_order = " ".join(reversed(fixed_words))
    # Fully reversed multi-token titles: last word Title Case, first low-score
    first_core = _alpha_core(fixed_words[0]) if fixed_words else ""
    last_core = _alpha_core(fixed_words[-1]) if fixed_words else ""
    order_flip = False
    if title_readability_score(reversed_order) > title_readability_score(result) + 0.03:
        order_flip = True
    elif (
        len(fixed_words) >= 2
        and last_core[:1].isupper()
        and first_core
        and first_core[:1].islower()
    ):
        order_flip = True
    elif (
        len(fixed_words) >= 3
        and n_token_fixes >= max(2, len(fixed_words) // 3)
        and last_core[:1].isupper()
        and title_readability_score(reversed_order) >= title_readability_score(result) - 0.02
    ):
        # Many tokens were un-reversed → word order is usually reversed too (p.97)
        order_flip = True
    if order_flip:
        result = reversed_order
    return _tidy_reversed_punctuation(result)


def _header_has_reverse_residue(text: str) -> bool:
    """True if any token is still a known reverse or reverse-of-English."""
    for w in re.findall(r"[A-Za-z]{2,}", text or ""):
        wl = w.lower()
        if wl in _GARBLED_TOKEN_FIX:
            return True
        rev = wl[::-1]
        if rev in _DESCRIPTOR_WORDS or rev in COMMON_WORDS:
            if wl not in _DESCRIPTOR_WORDS and wl not in COMMON_WORDS:
                return True
    return False


def preferred_display_title(header_title: str, table_title: str | None = None) -> str:
    """Choose the best display title from header vs first table title row.

    Prefer a table title when it is more readable (fixed body, garbled header).
    Never invent content — only pick between provided strings after token fix.
    """
    h_raw = (header_title or "").strip()
    h = fix_rotated_title(h_raw)
    if not table_title or not str(table_title).strip():
        return h
    t = fix_rotated_title(re.sub(r"\s+", " ", str(table_title).strip()))
    # Drop level-only cells
    if re.match(r"^(Pre-)?[ABC][12]\+?$", t, re.I):
        return h
    hs, ts = title_readability_score(h), title_readability_score(t)
    # Header still reverse-looking after fix attempt → prefer longer clean table title
    if _header_has_reverse_residue(h) and not _header_has_reverse_residue(t):
        return t
    if _header_has_reverse_residue(h_raw) and len(t) > len(h) + 3 and ts >= hs - 0.05:
        return t
    # Table contains header's non-garbled content as subsequence and is longer
    h_tokens = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", h) if w.lower() not in _GARBLED_TOKEN_FIX]
    t_low = t.lower()
    if (
        len(t) > len(h) + 8
        and h_tokens
        and all(tok in t_low for tok in h_tokens[:3])
        and ts >= hs - 0.15
    ):
        return t
    if ts > hs + 0.02:
        return t
    if hs > ts + 0.02:
        return h
    # Tie: prefer longer descriptive title (often full scale name in table)
    return t if len(t) > len(h) + 5 else h


def artifact_id_from_title(title: str, prefix: str = "scale") -> str:
    """Slugify a (preferably fixed) display title into an artifact id."""
    from pipeline.utils import slugify

    fixed = fix_rotated_title(title)
    return slugify(fixed, prefix=prefix)


def _id_readability(artifact_id: str) -> float:
    body = re.sub(r"^(scale|table)_", "", artifact_id or "")
    return title_readability_score(body.replace("_", " "))


def clean_artifact_id(artifact_id: str | None, display_title: str | None = None) -> str:
    """Return a non-garbled artifact id, re-slugging from title when needed."""
    aid = (artifact_id or "").strip()
    title = (display_title or "").strip()
    if not aid and not title:
        return "unknown"
    # Protect stable series / section ids (e.g. appendix_5_domain_examples).
    # Never rewrite them to scale_* from a display title — that orphans vision slugs.
    if aid and not aid.startswith(("scale_", "table_")):
        if not id_looks_garbled(aid):
            return aid
    prefix = "table" if aid.startswith("table_") else "scale"
    if title:
        derived = artifact_id_from_title(title, prefix=prefix)
    else:
        # Fix tokens inside the id itself then re-slug words
        raw = aid
        for bad, good in sorted(_GARBLED_TOKEN_FIX.items(), key=lambda kv: -len(kv[0])):
            raw = raw.replace(bad, good)
        raw = raw.replace("_ni_", "_in_")
        if raw.startswith("scale_") or raw.startswith("table_"):
            # Rebuild slug from fixed tokens to normalize order/doubles
            words = raw.split("_")[1:]  # drop prefix
            derived = artifact_id_from_title(" ".join(words), prefix=prefix)
        else:
            derived = artifact_id_from_title(raw.replace("_", " "), prefix=prefix)
    if not aid:
        return derived
    if not derived or derived in (f"{prefix}_", prefix):
        return aid
    # Prefer derived when old id is clearly garbled
    if id_looks_garbled(aid) and not id_looks_garbled(derived):
        return derived
    # Prefer derived when title-based slug is substantially more readable
    if derived != aid and _id_readability(derived) > _id_readability(aid) + 0.08:
        if not id_looks_garbled(derived):
            return derived
    # Title was reverse-fixed and yields a different clean slug
    if title and fix_rotated_title(title) != title and derived != aid and not id_looks_garbled(derived):
        if id_looks_garbled(aid) or _id_readability(derived) >= _id_readability(aid):
            return derived
    return aid


def is_probably_reversed(text: str) -> bool:
    original = text.strip()
    fixed = fix_rotated_title(original)
    if fixed == original:
        return False
    return title_readability_score(fixed) > title_readability_score(original) + 0.08
