"""Detect and fix reversed text from rotated PDF layers."""

from __future__ import annotations

import re

from pipeline.utils import english_word_score

_DESCRIPTOR_WORDS = {
    "psychology", "argument", "leading", "group", "phonology", "coherence",
    "interaction", "fluency", "accuracy", "range", "vocabulary", "control",
    "reception", "production", "mediation", "description", "collaborating",
    "relating", "translating", "strategies", "concept", "online", "overall",
    "reading", "writing", "oral", "understanding", "conversation", "discussion",
    "comprehension", "communication", "examples", "domains", "education",
    "language", "learner", "learning",
}

_REVERSED_TOKEN = re.compile(
    r"^(yg|tn|pu|noitc|erio|gnid|krow|lortnoc|noitam|txet|sevit|tpecn|gnitar)",
    re.I,
)


def title_readability_score(text: str) -> float:
    words = re.findall(r"[A-Za-z]{3,}", text)
    if not words:
        return 0.0
    hits = 0.0
    for w in words:
        wl = w.lower()
        if wl in _DESCRIPTOR_WORDS:
            hits += 1.0
        else:
            hits += english_word_score(wl)
    return hits / len(words)


def fix_rotated_title(title: str) -> str:
    """Return the forward-reading form of a possibly reversed title."""
    if not title or not title.strip():
        return title
    forward = title.strip()
    words = forward.split()
    fixed_words: list[str] = []
    changed = False
    for word in words:
        if not word.isalpha() or len(word) < 3:
            fixed_words.append(word)
            continue
        if word.isupper() or (word[0].isupper() and title_readability_score(word) >= 0.15):
            fixed_words.append(word)
            continue
        rev = word[::-1]
        fwd_score = title_readability_score(word)
        rev_score = title_readability_score(rev)
        if rev_score > fwd_score + 0.05:
            fixed_words.append(rev)
            changed = True
        elif fwd_score < 0.05 and (_REVERSED_TOKEN.match(word) or rev[0].isupper()):
            fixed_words.append(rev)
            changed = True
        else:
            fixed_words.append(word)
    result = " ".join(fixed_words)
    if not changed:
        whole_rev = " ".join(w[::-1] if w.isalpha() else w for w in words)
        if title_readability_score(whole_rev) > title_readability_score(forward) + 0.05:
            return whole_rev
    reversed_order = " ".join(reversed(fixed_words))
    if title_readability_score(reversed_order) > title_readability_score(result) + 0.03:
        return reversed_order
    if (
        len(fixed_words) >= 2
        and fixed_words[-1][:1].isupper()
        and fixed_words[0][:1].islower()
    ):
        return reversed_order
    return result


def is_probably_reversed(text: str) -> bool:
    original = text.strip()
    fixed = fix_rotated_title(original)
    if fixed == original:
        return False
    return title_readability_score(fixed) > title_readability_score(original) + 0.08