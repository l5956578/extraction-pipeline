# -*- coding: utf-8 -*-
"""Fix residual table/false-head issues + final primary-band audit."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OV = ROOT / "page_overrides"
CAT = ROOT / "intonation_hires" / "catalogs"
HI = ROOT / "intonation_hires"

# Fix leaf 57
(OV / "page_057.md").write_text(
    """<!-- vision: Waystage leaf 57 doc p.51 | word-catalog multipass -->
<!-- el:start type=prose id=prose_p057 page=51 -->

| | | |
| --- | --- | --- |
| Sales person | : ·That'll be ˈ£2 ˎ30 | asking for payment |
| Customer | : (gives money) | (making payment: non-verbal termination) |

Apart from the variability (by no means exhausted here) of the fish-and-chip buying dialogue, we note the occurrence of sub-patterns as well as the integration of non-verbal turns. Communicative ability at *Waystage* implies the ability to play a part in verbal exchange patterns such as the ones illustrated above.

A number of dialogue types (which may, in fact, involve more than two participants) are explicitly or implicitly covered by our objective. They involve the occurrence of verbal exchange patterns with a certain measure of predictability. They are particularly associated with the following communicative events:

1 making purchases

a) in a shop

b) at a ticket counter, ticket from bus conductor, etc.

2 ordering food and drink  
restaurant, canteen, snack bar, etc.

3 making enquiries

a) non-personal (where to go, where to eat, about opening hours, about various facilities and services, etc.)

b) personal (about name, address, place of origin, etc.)

4 meeting people

a) strangers

b) friends, acquaintances

5 asking and showing the way

6 asking and telling the time

7 inviting and reacting to invitation

8 arranging accommodation

9 proposing a course of action and reacting to such proposals

10 having a discussion  
agreeing/disagreeing, exchanging views, etc.

However predictable the occurrence of certain verbal exchange patterns in the above dialogue types may be, there is always a strong element of unpredictability as well. When the more or less standardised patterns are broken, or even set aside completely,

<!-- el:end id=prose_p057 -->
""",
    encoding="utf-8",
)
print("fixed 057")

# Fix false heads on prose pages (quoted words mistaken as tone)
for leaf in (58, 59, 60, 61, 62, 63):
    p = OV / f"page_{leaf:03d}.md"
    t = p.read_text(encoding="utf-8")
    orig = t
    # reverse false head on common prose quotes
    t = re.sub(r"the ˈproper'", "the 'proper'", t)
    t = re.sub(r"the ˈproper\b", "the 'proper", t)
    t = re.sub(r"not ˈthrown'", "not 'thrown'", t)
    t = re.sub(r"not ˈthrown\b", "not 'thrown", t)
    t = re.sub(r"ˈtaught'", "'taught'", t)
    t = re.sub(r"being ˈtaught\b", "being 'taught", t)
    # ensure header
    if "word-catalog multipass" not in t:
        doc = leaf - 6
        body = t
        if body.startswith("<!--"):
            # already has some header
            pass
        t = (
            f"<!-- vision: Waystage leaf {leaf} doc p.{doc} | word-catalog multipass -->\n"
            + t
        )
    if t != orig:
        p.write_text(t, encoding="utf-8")
        print(f"fixed false heads leaf {leaf}")

# Fix leaf 56: ensure table tone-group bars OK and prose quotes not counted as tone
p56 = OV / "page_056.md"
t56 = p56.read_text(encoding="utf-8")
# leave 'Stop!' style quotes as ASCII apostrophe (not tone) — OK
if "word-catalog multipass" not in t56.splitlines()[0]:
    print("WARN 056 header")

# Fix remaining | as I on notions pages
for leaf in list(range(28, 36)) + list(range(38, 48)):
    p = OV / f"page_{leaf:03d}.md"
    t = p.read_text(encoding="utf-8")
    t2 = t
    t2 = re.sub(r"\| (have|haven't|am |want |got |like |don't )", r"I \1", t2)
    t2 = re.sub(r"\| (ˈ|ˎ|·)", r"I \1", t2)
    # a'nother residual
    t2 = t2.replace("a'nother", "aˈnother")
    t2 = t2.replace("al'ready", "alˈready")
    if t2 != t:
        p.write_text(t2, encoding="utf-8")
        print(f"pipe-I/midapos fix leaf {leaf}")

# Final audit
leaves = list(range(22, 36)) + list(range(38, 48)) + list(range(56, 66)) + list(range(77, 81))
issues = []
for i in leaves:
    t = (OV / f"page_{i:03d}.md").read_text(encoding="utf-8")
    h0 = t.splitlines()[0] if t else ""
    if f"Waystage leaf {i}" not in h0 or "word-catalog multipass" not in h0:
        issues.append(f"{i}: bad header: {h0[:90]}")
    if "\u02cc" in t:
        issues.append(f"{i}: U+02CC present")
    if not (CAT / f"leaf_{i:03d}_catalog.md").exists():
        # write minimal catalog if missing
        doc = i - 6
        samples = [ln.strip() for ln in t.splitlines() if re.search(r"[ˈˎˋˏˊˇ·]", ln)][:10]
        note = "\n".join(f"- `{s}`" for s in samples) or "(no marked exponents)"
        (CAT / f"leaf_{i:03d}_catalog.md").write_text(
            f"# Word catalog — Waystage leaf {i} (doc p.{doc})\n\n"
            f"**Source:** Vision multipass `intonation_hires/`\n\n{note}\n",
            encoding="utf-8",
        )
        print(f"catalog created {i}")
    if not (HI / f"leaf_{i:03d}_full4.png").exists():
        issues.append(f"{i}: missing hires full4")
    if not (HI / f"leaf_{i:03d}_left.png").exists():
        issues.append(f"{i}: missing left crop")

print("=== AUDIT ===")
print("pages_rewritten", len(leaves))
print("issues", issues or "none")
print(
    """
chapter_coverage:
  ch3 Language functions (doc 16-21): PDF 22-27
  ch4 General notions (doc 22-29): PDF 28-35
  ch5 Themes/specific notions (doc 32-41): PDF 38-47
  ch9 Verbal exchange (doc 50-55): PDF 56-61
  ch10 Compensation (doc 56-59): PDF 62-65
  Appendix A Pronunciation & intonation (doc 71-74): PDF 77-80
"""
)

# mark inventory summary
print("mark inventory (H LF HF LR HR FR D):")
for i in leaves:
    t = (OV / f"page_{i:03d}.md").read_text(encoding="utf-8")
    m = [t.count(c) for c in "ˈˎˋˏˊˇ·"]
    if sum(m):
        print(f"  {i:03d}: {m}")
