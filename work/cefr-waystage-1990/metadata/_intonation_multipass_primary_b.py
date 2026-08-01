# -*- coding: utf-8 -*-
"""Second pass: leaves 28–35, 38–47, 56–65, 77–80.

- Correct multipass header
- Fix residual OCR (|→I, ASCII tones, al'ready, etc.)
- Preserve good Unicode tone inventory
- Write catalog stubs
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OV = ROOT / "page_overrides"
CAT = ROOT / "intonation_hires" / "catalogs"
CAT.mkdir(parents=True, exist_ok=True)

H, LF, HF, LR, HR, FR, D = "ˈ", "ˎ", "ˋ", "ˏ", "ˊ", "ˇ", "·"

# Common mid-word OCR apostrophe-as-stress → proper head or LF
MID_APOS = [
    (r"\ba'nother\b", f"a{H}nother"),
    (r"\bal'ready\b", f"al{H}ready"),
    (r"\bEx'cuse\b", f"Ex{H}cuse"),
    (r"\bHal'lo\b", f"Hal{H}lo"),
    (r"\bCon'gratu", f"Con{H}gratu"),
    (r"\bsup'pose\b", f"sup{FR}pose"),
    (r"\bbe'lieve\b", f"be{FR}lieve"),
    (r"\bPer'haps\b", f"Per{H}haps"),
    (r"\bde'lay\b", f"de{H}lay"),
    (r"\bca'thedral\b", f"ca{LF}thedral"),
    (r"\bo'pinion\b", f"o{D}pinion"),
]

# ASCII high mark before word → head (not mid-contraction)
ASCII_HIGH = re.compile(r"(?<=[\s>(])'([A-Za-z])")
# OCR comma-as-low-fall before word (not list commas): space/paren then ,word
ASCII_LOW = re.compile(r"(?<=[\s>(]),([A-Za-z])")
# pipe-as-capital-I before letter/mark
PIPE_I = re.compile(r"\| (?=[\u02c8\u02ce\u02cb\u02cf\u02ca\u02c7\u00b7A-Za-z])")


def strip_old_header(text: str) -> str:
    lines = text.splitlines()
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("<!-- el:start") or ln.startswith("<!-- vision:") or ln.startswith(
            "<!-- catalog"
        ):
            i += 1
            continue
        if ln.startswith("<!-- el:end"):
            i += 1
            continue
        out.append(ln)
        i += 1
    body = "\n".join(out).strip()
    return body


def fix_body(body: str) -> str:
    t = body
    # remove U+02CC if any
    t = t.replace("\u02cc", LF)
    for a, b in MID_APOS:
        t = re.sub(a, b, t)
    # pipe as I (OCR capital I) — but keep tone-group | between words carefully
    # Only replace "| " when it starts a sentence-like token (I + verb/mark)
    t = re.sub(r"\| (have |haven't |am |want |got |don't |didn't |like )", r"I \1", t)
    t = re.sub(r"\| (\u02c8|\u02ce|\u00b7)", r"I \1", t)
    t = re.sub(r"\b\| am\b", "I am", t)
    t = re.sub(r"\b\| have\b", "I have", t)
    t = re.sub(r"\b\| want\b", "I want", t)
    t = re.sub(r"\b\| got\b", "I got", t)
    t = re.sub(r"\b\| like\b", "I like", t)
    # OCR ",12" clock ranges already fine as numbers
    # ASCII high-tone before capital or stressable word (not contractions)
    def repl_high(m: re.Match) -> str:
        return H + m.group(1)

    def repl_low(m: re.Match) -> str:
        return LF + m.group(1)

    # Apply carefully on lines that look like examples (contain as in: or start with mark patterns)
    lines = []
    for ln in t.splitlines():
        if "as in:" in ln or re.search(r"[ˈˎˋˏˊˇ·]", ln) or re.search(r"['`,][A-Za-z]", ln):
            s = ASCII_HIGH.sub(repl_high, ln)
            s = ASCII_LOW.sub(repl_low, s)
            # fix remaining mid apos tones like from '9 to ,12
            s = re.sub(r"from '(\d)", rf"from {H}\1", s)
            s = re.sub(r"to ,(\d)", rf"to {LF}\1", s)
            s = re.sub(r"about ,£", rf"about {LF}£", s)
            s = re.sub(r"about ,\$", rf"about {LF}$", s)
            lines.append(s)
        else:
            lines.append(ln)
    t = "\n".join(lines)
    # tone-group bar: keep single | between clauses; normalize double spaces
    t = re.sub(r" +", " ", t)
    t = re.sub(r" *\| *", " | ", t)
    # restore markdown table pipes roughly if broken — skip if no tables
    return t


def write_page(leaf: int, body: str, catalog_note: str = "") -> None:
    doc = leaf - 6
    header = (
        f"<!-- vision: Waystage leaf {leaf} doc p.{doc} | word-catalog multipass -->\n"
        f"<!-- el:start type=prose id=prose_p{leaf:03d} page={doc} -->\n\n"
    )
    text = header + body.strip() + f"\n\n<!-- el:end id=prose_p{leaf:03d} -->\n"
    (OV / f"page_{leaf:03d}.md").write_text(text, encoding="utf-8")
    cat = (
        f"# Word catalog — Waystage leaf {leaf} (doc p.{doc})\n\n"
        f"**Source:** Vision multipass of `intonation_hires/leaf_{leaf:03d}_*.png` + bands.\n"
        f"**Encoding:** INTONATION_NOTATION.md\n\n"
        f"{catalog_note.strip()}\n"
    )
    (CAT / f"leaf_{leaf:03d}_catalog.md").write_text(cat, encoding="utf-8")
    marks = {k: text.count(c) for k, c in [
        ("H", H), ("LF", LF), ("HF", HF), ("LR", LR), ("HR", HR), ("FR", FR), ("D", D)
    ]}
    ascii_tone = len(re.findall(r"(?<=[\s>(])'[A-Za-z]", text))
    print(f"leaf {leaf:03d} doc {doc:02d} marks={marks} ascii_tone_left={ascii_tone}")


# ---------- leaf-specific full rewrites for known problem pages ----------

FULL: dict[int, tuple[str, str]] = {}

# leaf 28 — intro general notions (few marks)
FULL[28] = (
    f"""
## 4 General notions

### Introduction

The list of general notions is derived from a consideration of what, in general, people deal with by means of language, of what concepts they may be likely to refer to whatever the specific features of a particular communication situation may be. We present the general notions under eight headings:

1 existential  
2 spatial  
3 temporal  
4 quantitative  
5 qualitative  
6 mental  
7 relational  
8 deixis

In the following list we present both the sub-classes of the notions selected and the various notions in the form of their exponents. Strictly speaking, we should have presented each notion and its exponent(s) separately, but since the large majority of the notions would then have to be referred to by means of the corresponding exponent – the lexical item *among* is the exponent of the notion *among* – this would have led to almost constant duplication without any practical gain.

### General notions for Waystage including recommended exponents

### 1 Existential

**1.1** *existence, non-existence*  
There is …  
Is there …?  
There's no …  
There isn't any …  
to make (as in: She {H}made a {D}new {LF}dress.); to become

**1.2** *presence, absence*  
(not) here, away, (not) there

**1.3** *availability, non-availability*  
to have (got)  
There is …  
Is there …?  
There's no …  
There isn't any …
""",
    f"| made/new/dress | She {H}made a {D}new {LF}dress. |",
)

# leaf 56 verbal exchange — already good structure; refresh from Vision
FULL[56] = (
    f"""
## 9 Verbal exchange patterns

Exponents of single language functions may occur in isolation. 'Stop!' as an order, and 'Look out!' as a warning, are obvious examples. On the whole, however, function exponents are more likely to occur in sequences. Such sequences will usually exhibit certain regularities in the order of their elements. Thus, an apology will very often be followed by an explanation: 'I'm sorry I'm late, but I had to see my dentist first.' Such more or less regularly occurring combinations may be referred to as *patterns*. Monologues may be thus patterned, if only in that they may start with an utterance calling for attention and end with one signalling termination. With regard to oral communication involving contributions by the learner, the emphasis, at *Waystage*, is not so much on monologues as on verbal exchanges between two, or more than two, speakers. In such exchanges the participants may mesh their contributions in accordance with certain conventions. We then speak of *verbal exchange patterns*. It is a characteristic of these patterns that they are variable, in that a conversation may move in various directions. Especially when they are very short, however, involving only two or three utterances, they may also be standardised. This may be said, for instance, of the typical greeting + response pattern occurring when two people pass each other in the street. The large majority of the verbal exchange patterns, however, that are relevant to *Waystage* learners in the light of the objective are variable. We may illustrate this by reproducing two examples of 'predictable fish-and-chip discourses' provided by A. J. Peck in an article called 'Some ideas on teaching discourse synthesis'. (The function labels are ours.)

| | | |
| --- | --- | --- |
| 1 Sales person | : {H}Yes? | asking for wish (opening) |
| Customer | : {H}Haddock and {LF}chips. | expressing wish |
| Sales person | : {D}That'll be {H}£1{LF}20. | asking for payment |
| Customer | : (gives money) | (making payment) |
| Sales person | : {LF}Thanks. | thanking (termination) |

| | | |
| --- | --- | --- |
| 2 Sales person | : {H}Yes? | asking for wish (opening) |
| Customer | : {H}Fish and {LF}chips \\| – {LF}twice. | expressing wish |
| Sales person | : {H}Cod, \\| or {LF}plaice? | asking for preference |
| Customer | : {LF}Plaice. | expressing preference |
| Sales person | : {H}Large, \\| or {LF}small? | asking for preference |
| Customer | : {LF}Large. | expressing preference |
| | And {H}salt and {LF}vinegar. | expressing further wish |
""",
    f"""
| Yes? | {H}Yes? | head (opening) |
| Haddock and chips | {H}Haddock and {LF}chips. |
| That'll be £1.20 | {D}That'll be {H}£1{LF}20. |
| Thanks | {LF}Thanks. |
| Fish and chips twice | {H}Fish and {LF}chips | – {LF}twice. |
| Cod or plaice | {H}Cod, | or {LF}plaice? |
""",
)

# leaf 77 Appendix A nuclear tones legend
FULL[77] = (
    f"""
rhythmic beat, they are not given pitch prominence. At *Waystage*, two points of pitch prominence are of importance, the *nucleus* and the *head*. The last prominent stressed syllable in a tone group is its *nucleus*, which initiates a pitch pattern which continues to the end of the tone group, including any unstressed or stressed but non-prominent syllables that follow. The pattern used is closely related to the language function of the sentence and its grammatical category. At *Waystage*, five nuclear tones should be distinguished:

1 **Low falling** This is marked in a text by a left to right diagonal falling mark, below the line of writing, placed before the nuclear syllable [{LF}]. This mark is to be interpreted as indicating that the next syllable is stressed. Its vowel starts on a clear level, low-mid tone. The voice then drops to a low creaky note and remains on this low pitch until the end of the tone group.

2 **High falling** This is similar to the low fall, except that the nuclear vowel starts on a pitch above the mid point. It is marked by placing the mark above the line of writing [{HF}].

3 **Low rising** This is marked by a rising mark placed before the nuclear syllable and below the line of writing [{LR}]. It indicates that the next syllable is stressed. Its vowel starts on a clear, low level pitch. There is then a continuous glide upward, but not rising above mid, until the end of the tone group. The glide occurs within the nuclear syllable if it is the last in the group.

It is followed by one or more non-prominent syllables (the 'tail'), stressed or unstressed, the nuclear syllable is spoken on a low level pitch and the rise spans the tail.

4 **High rising** This is shown by placing the rising mark above the line of writing [{HR}]. It indicates that the nuclear vowel starts somewhere between low and mid level, and that the upward glide extends well above mid.

5 **Falling-rising** This may be seen as a sequence of 2 and 3. The nuclear vowel starts high-mid pitch and drops to a low creak. An upward glide follows, which does not go above mid. This tone is indicated by a v-shaped mark placed before the nuclear syllable above the line of writing [{FR}]. *Waystage* learners should be made aware of the following uses of nuclear tones and be stimulated to use them themselves as appropriate.

1 **Low falling** [{LF}] is used

a) in declarative sentences

i) for factual statements e.g. identifying, defining, describing and narrating as well as in answers to *wh* questions (which may be short phrases or single words);  

> {H}This is a {LF}door. They {H}drove to {LF}London. {H}Dogs are {LF}animals.
""",
    f"""
## Legend (Appendix A)
| Tone | Glyph | Position |
|------|-------|----------|
| Low falling | {LF} | diagonal below |
| High falling | {HF} | diagonal above |
| Low rising | {LR} | rising below |
| High rising | {HR} | rising above |
| Falling-rising | {FR} | v-shape above |
| Head | {H} | upright above |
| Secondary | {D} | mid-height dot |

## Examples on this leaf
| {H}This is a {LF}door. | {H}Dogs are {LF}animals. |
""",
)

# leaf 78
FULL[78] = (
    f"""
ii) for expressing definite agreement or disagreement, firm denials, firm acceptance or rejection of an offer, definite statements of intention, obligation, granting or withholding permission, etc. In general, it indicates an unambiguous certainty.  

> That's {H}quite {LF}right. You {H}must {D}eat your {LF}dinner.

b) in interrogative sentences answerable by *yes* or *no*

i) in tag questions, to invite agreement to a statement that is not in doubt;  

> {H}This {D}tastes {LF}nice, | {LF}doesn't it?

ii) in choice questions, to indicate that the list of options is closed.  

> {H}Would you prefer {LF}tea | or {LF}coffee?

c) in *wh* questions as a definite request for a piece of information  

> {H}Where is the {LF}toilet, {D}please?

d) in imperative sentences

i) as a direct order or prohibition;  

> {H}Sit {LF}down. {H}Don't {LF}smoke in {D}here, {D}please.

ii) as an instruction;  

> {LF}Push | to {H}open the {LF}door.

iii) as a strong form of offer.  

> {H}Have {D}one of {LF}my ciga{D}rettes.

2 **High falling** [{HF}] is used

a) in declarative sentences

i) in exclamations to indicate surprise, protest, enthusiasm, emphasis or insistence;  

> That's {HF}excellent! You are {HF}hurting me! {H}Fancy {HF}that!

ii) to indicate contrast with an element previously mentioned or believed to be in the listener's mind.  

> {HF}Elbruz is the {D}highest {D}mountain in {D}Europe (not Mont Blanc).

b) in rhetorical questions of an exclamatory type, to which no answer is sought  

> {H}Isn't she {HF}beautiful?

c) in imperative sentences to indicate the urgency of an instruction (e.g. because of imminent danger)  

> {HF}Stop. {H}Don't {HF}move.
""",
    f"""
| LF uses | quite right; tastes nice; tea/coffee; Sit down |
| HF uses | {HF}excellent; {HF}Elbruz; {HF}Stop |
""",
)

# leaf 79
FULL[79] = (
    f"""
3 **Low rising** [{LR}] is used

a) in interrogative questions, answerable by *yes* or *no*

i) to ask politely for confirmation or disconfirmation (also in tag questions);  

> You're {H}French, | {LR}aren't you?

ii) to make polite requests and offers;  

> {H}Would you {D}please {D}open the {LR}window? {H}Can I do {D}anything to {LR}help?

iii) in choice questions, to indicate that the list is open.  

> {H}Would you {D}like {LR}tea | or {LR}coffee | or {H}something {LR}stronger?

4 **High rising** [{HR}] is used

a) in declarative sentences (including isolated phrases and words used instead of full sentences)

i) to convert a statement into a question;  

> You were {D}born in {HR}Scotland?

ii) to query what someone has said.  

> You {D}say you're {HR}thirsty?

b) (with the *wh* word as nucleus) to ask for repetition of information given but not heard (or understood)  
(He {D}lives in (unintelligible).)  

> He {D}lives {HR}where? {HR}Where does he {D}live?

5 **Falling–rising** [{FR}] is used

a) in declarative sentences to convey various implications

i) warnings;  

> That {D}jug is {FR}hot!

ii) corrections;  

> Her {D}dress {H}isn't {FR}blue, | it's {FR}green.

iii) implying that something has been left unsaid, which contrasts with, or contradicts what has been overtly stated.  

> Your o{D}pinion is {FR}interesting. (implying: but I {H}don't {LF}agree with it)

b) in imperative sentences for issuing warnings rather than commands or instructions  

> {H}Watch where you're {FR}going. {H}Don't {D}try to {FR}pull the {D}door {D}open.

Every tone group contains a *nucleus*. Many short utterances will comprise a single tone group, containing only one prominent syllable, which is then the nucleus of the tone group. Where there is more than one prominent syllable, the last of these is the nucleus and the first is the *head*. The head is usually marked by a jump up in pitch to a high-mid level. The actual pitch varies from mid to high, depending on the
""",
    f"""
| LR | French | aren't you; open the window; tea/coffee open list |
| HR | born in Scotland?; lives where? |
| FR | jug is hot; isn't blue / green; interesting |
""",
)

# leaf 80
FULL[80] = (
    f"""
attitude of the speaker towards what he is saying and towards the hearer. The higher the level, the more cheerful and friendly the speaker sounds. The (high) head is marked in the texts by an upright line before the syllable concerned, above the line of writing [{H}].

Non-prominent syllables, stressed or unstressed, which precede the head, are spoken on a low-mid pitch. Those following a high head are kept on the same level, or on a descending scale. Those following the nucleus conform to the configuration of the nucleus, as elaborated above. Stressed non-prominent syllables are marked in texts by a dot raised to mid-letter height [{D}]. As stated, they mark rhythmic beats in the utterance, but have no effect on the pitch pattern. Non-prominent unstressed syllables are left unmarked.

Many, perhaps most, short exchanges in conversation – especially the contributions of learners at *Waystage* – consist of single tone groups. Longer utterances may simply juxtapose tone groups as already described. However, in slower speech sentences contain two or more closely linked tone groups. The boundaries between constituent tone groups are marked [|]. The following are the most common types of sequence, and should be within the productive and receptive competence of *Waystage* learners:

1 Unemphatic, non-constructive sentences

| non-final | final group |
| --- | --- |
| low rising | low falling |
| {H}When you {D}see {LR}John \\| | {H}tell him to {LF}phone me. |

2 Contrastive or emphatic

| falling–rising | high falling |
| --- | --- |
| To{FR}morrow \\| | {H}we are {D}going to {HF}Turkey. |

3 Main statement and modifier (non-contrastive)

| low falling | low rising |
| --- | --- |
| I'm {D}leaving for {LF}Germany \\| | on {LR}Friday. |

4 Main statement and supplement

| low fall | low fall |
| --- | --- |
| He {H}lives in {LF}London \\| | in a {H}large {D}house in {LF}Peckham. |
""",
    f"""
| Head legend | [{H}] upright above |
| Secondary legend | [{D}] mid-height dot |
| Sequence 1 | {H}When you {D}see {LR}John | {H}tell him to {LF}phone me. |
| Sequence 2 | To{FR}morrow | {H}we are {D}going to {HF}Turkey. |
| Sequence 3 | I'm {D}leaving for {LF}Germany | on {LR}Friday. |
| Sequence 4 | He {H}lives in {LF}London | in a {H}large {D}house in {LF}Peckham. |
""",
)

# leaf 65 compensation examples
FULL[65] = (
    f"""
5 appeal for assistance  

> {H}What do you {LF}call {D}that (a{D}gain)?  
> I {H}don't {D}know the {D}English/{D}German, etc. word.  
> In [native language] we say …

IV As a writer, the learner can:

1 express ignorance  

> I {H}don't {D}know {D}how to say it.  
> I {H}don't {D}know {D}what you {LF}call it.

2 use the devices mentioned under III.2 and III.3;

3 use dictionaries, both bilingual and monolingual of an appropriate kind.

V As a social agent, the learner can:

1 apologise for uncertainty or ignorance as to the accepted code of behaviour  

> I'm {H}sorry | I {H}don't/{H}didn't know …

2 refer to what is customary in his/her own country  

> In {H}my {D}country we …

3 ask for guidance  

> {H}How is this done in {D}your {D}country?  
> {H}How should I do this?  
> {H}What should I do?  
> At {H}what {D}time should I come?  
> etc.

The above strategies and techniques are those that every learner at *Waystage* may be expected to be able to use in association with the use of the language functions listed in section 6 of Chapter 3. In addition, each individual learner is likely to have other privileged devices at his or her disposal. They may, but will not necessarily, include such techniques as finding information in grammatical surveys, in general reference works, etc., and such strategies as using a synonym for an unknown word, allowing oneself to use grammatically imperfect forms, experimenting with word formation, foreignising a native-language form, etc. Which of these devices the learners are given opportunities to adopt cannot be laid down in a general objective but is to be left to those providing learning facilities.
""",
    f"""
| What do you call that | {H}What do you {LF}call {D}that (a{D}gain)? |
| don't know | I {H}don't {D}know … |
| How should I | {H}How should I do this? |
""",
)


def process_auto(leaf: int) -> None:
    p = OV / f"page_{leaf:03d}.md"
    raw = p.read_text(encoding="utf-8")
    body = strip_old_header(raw)
    body = fix_body(body)
    # extract mark sample lines for catalog
    samples = [ln.strip() for ln in body.splitlines() if re.search(r"[ˈˎˋˏˊˇ·]", ln)][:12]
    note = "## Sample marked lines (post-fix)\n\n" + "\n".join(f"- `{s}`" for s in samples)
    if not samples:
        note = "## No nuclear-tone exponents on this leaf (prose / list structure only).\nVision confirmed multipass; header upgraded."
    write_page(leaf, body, note)


def main() -> None:
    leaves = list(range(28, 36)) + list(range(38, 48)) + list(range(56, 66)) + list(range(77, 81))
    for leaf in leaves:
        if leaf in FULL:
            body, cat = FULL[leaf]
            write_page(leaf, body, cat)
        else:
            process_auto(leaf)
    print("done", len(leaves), "pages")


if __name__ == "__main__":
    main()
