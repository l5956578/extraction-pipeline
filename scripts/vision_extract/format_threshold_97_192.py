#!/usr/bin/env python3
"""Vision-format Threshold 1990 PDF pages 97–192 → page_overrides/page_NNN.md.

Uses:
- existing page_ocr + Vision-informed structure rules
- tesseract column split for two-column grammar / word / subject indexes
- Unicode nuclear-tone marks ˎ ˋ ˏ ˊ ˇ + head ˈ + stress ·

All outputs tagged: <!-- vision: Threshold PDF page N -->
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore

ROOT = Path(__file__).resolve().parents[2]
JOB = "cefr-threshold-1990"
WORK = ROOT / "work" / JOB
OCR = WORK / "page_ocr"
RENDERS = WORK / "page_renders"
OUT = WORK / "page_overrides"

# Nuclear tones (van Ek–Trim App A)
LF, HF, LR, HR, FR = "\u02ce", "\u02cb", "\u02cf", "\u02ca", "\u02c7"
HEAD, STRESS = "\u02c8", "\u00b7"
MINOR, MAJOR = "|", "||"

RUNNING = re.compile(
    r"^(?:"
    r"(?:[A-Z]\s+){2,}[A-Z]?|"  # spaced running head
    r"\d{1,3}|"
    r"APPENDIX\s*[A-D]?|"
    r"APPENDIX[A-D]|"
    r"PRONUNCIATION AND INTONATION|"
    r"SUBJECT INDEX|"
    r"\d+\s+(?:READING|WRITING|SOCIOCULTURAL|COMPENSATION|LEARNING|DEGREE).*"
    r")$",
    re.I,
)
PAGE_ONLY = re.compile(r"^\d{1,3}$")
CHROME_NUM = re.compile(r"^\d{1,3}\s+[A-Z]")


def clean(t: str) -> str:
    t = t.replace("\u00ad", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    t = t.replace("\ufb01", "fi").replace("\ufb02", "fl")
    t = t.replace("satisfylng", "satisfying")
    t = t.replace("middleclass", "middle-class")
    t = t.replace("adoped", "adopted")
    t = t.replace("AngleSaxon", "Anglo-Saxon")
    t = t.replace("dialectical variation", "dialectal variation")
    t = t.replace("temporaryvisitors", "temporary visitors")
    t = t.replace("useofcapitals", "use of capitals")
    t = t.replace("toa", "to a")
    t = t.replace("jhelp", "help")
    t = t.replace("acom,", "a com")
    t = t.replace("o-pinion", "opinion")
    t = t.replace("a-gree", "agree")
    t = t.replace("a-fraid", "afraid")
    t = t.replace("de-tached", "detached")
    t = t.replace("ciga-rettes", "cigarettes")
    t = t.replace("be,fore", "before")
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def is_chrome(t: str) -> bool:
    s = t.strip()
    if not s:
        return True
    if PAGE_ONLY.match(s):
        return True
    if RUNNING.match(s):
        return True
    if re.match(r"^([A-Z]\s+){3,}[A-Z]?$", s):
        return True
    # book page + spaced head fragments
    if re.match(r"^\d{1,3}\s+([A-Z]\s+){2,}", s):
        return True
    if re.match(r"^(9|10|11|12|13|14|15|16)\s+[A-Z\s]{6,}$", s):
        return True
    return False


def read_ocr(pnum: int) -> str:
    p = OCR / f"page_{pnum:03d}.txt"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def tesseract_columns(pnum: int, mid_frac: float = 0.5, top_frac: float = 0.08) -> tuple[str, str]:
    """OCR left then right column of page PNG."""
    assert pytesseract is not None
    im = Image.open(RENDERS / f"page_{pnum:03d}.png")
    w, h = im.size
    mid = int(w * mid_frac)
    top = int(h * top_frac)
    left = im.crop((int(w * 0.04), top, mid - 4, h - int(h * 0.03)))
    right = im.crop((mid - 4, top, w - int(w * 0.04), h - int(h * 0.03)))
    cfg = "--psm 6"
    lt = pytesseract.image_to_string(left, config=cfg)
    rt = pytesseract.image_to_string(right, config=cfg)
    return lt, rt


def wrap_page(pnum: int, body: str, extra: str = "") -> str:
    body = body.strip() + "\n"
    pid = f"prose_p{pnum:03d}"
    bits = [
        f"<!-- el:start type=prose id={pid} page={pnum} -->",
        f"<!-- vision: Threshold PDF page {pnum} -->",
    ]
    if extra:
        bits.append(extra)
    bits.append("")
    bits.append(body.rstrip())
    bits.append("")
    bits.append(f"<!-- el:end id={pid} -->")
    bits.append("")
    return "\n".join(bits)


# ---------- Prose / chapter pages (97–120) ----------

def format_prose_from_ocr(pnum: int, text: str) -> str:
    lines = [clean(ln) for ln in text.splitlines()]
    out: list[str] = []
    para: list[str] = []
    list_mode = False

    def flush_para() -> None:
        nonlocal para
        if not para:
            return
        t = " ".join(para)
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
        if t:
            out.append(t)
            out.append("")
        para = []

    for raw in lines:
        t = raw
        if is_chrome(t):
            continue
        # strip leading book page number
        t = re.sub(r"^\d{1,3}\s+(?=[A-Z*•])", "", t).strip()
        if not t or is_chrome(t):
            continue

        # Chapter titles like "10 Writing" / "11 Sociocultural competence"
        m = re.match(
            r"^(1[0-6]|[0-9])\s+(Writing|Sociocultural competence|Compensation strategies|"
            r"Learning to learn|Degree of skill|Dealing with texts|Reading and listening|"
            r"Verbal exchange patterns)\b(.*)$",
            t,
            re.I,
        )
        if m:
            flush_para()
            list_mode = False
            title = f"{m.group(1)} {m.group(2)}"
            rest = (m.group(3) or "").strip()
            out.append(f"## {title}")
            out.append("")
            if rest:
                para.append(rest)
            continue

        # Numbered section heads: "1 Target…" / "3 The present…"
        if re.match(r"^\d{1,2}\s+[A-Z]", t) and len(t) < 80 and not t.endswith((".", ",", ";")):
            # could be short head or start of numbered para
            words = t.split()
            if len(words) <= 8 and not re.match(r"^\d+\s+(The|In|On|As|It|This|A|An|When|Where|What)\b", t):
                flush_para()
                list_mode = False
                out.append(f"### {t}")
                out.append("")
                continue

        # bullets
        if re.match(r"^[*•·▪]\s+", t) or t.startswith("* "):
            flush_para()
            item = re.sub(r"^[*•·▪]\s+", "", t).strip()
            out.append(f"- {item}")
            list_mode = True
            continue
        if re.match(r"^[-–—]\s+\S", t) and not re.match(r"^[-–—]\s+(and|or|but|the)\b", t, re.I):
            flush_para()
            item = re.sub(r"^[-–—]\s+", "", t).strip()
            out.append(f"- {item}")
            list_mode = True
            continue

        # lettered / numbered list items that start mid-line
        if re.match(r"^[a-z]\)\s+", t) or re.match(r"^[ivx]+\)\s+", t, re.I):
            flush_para()
            out.append(t)
            list_mode = True
            continue

        # continuation after list
        if list_mode and t and t[0].islower():
            # append to last list item
            if out and out[-1].startswith(("-", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "i")):
                out[-1] = out[-1] + " " + t
                continue
            list_mode = False

        if list_mode and t and t[0].isupper():
            list_mode = False
            out.append("")

        # join paragraphs
        if para and t and t[0].islower():
            para.append(t)
            continue
        if para and t and t[0].isupper():
            # new sentence/para
            flush_para()
        para.append(t)

    flush_para()
    body = "\n".join(out).strip()
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body


# ---------- Appendix A (121–130) hand-structured from Vision ----------

def app_a_page(pnum: int) -> str:
    """Return body only for App A pages (Vision-structured)."""
    # Full carefully formatted content for each page
    pages: dict[int, str] = {}

    pages[121] = f"""## Appendix A — Pronunciation and intonation

Communication depends upon mutual intelligibility. That is to say that it is only possible if the language forms produced by the speaker are identified and understood by the listener. It is therefore the responsibility of speakers to pronounce them as *intelligibly* as possible, and it is also the responsibility of listeners actively to seek to identify what has been said and to use appropriate repair procedures if they are unable to do so. The ease of communication depends largely on the extent to which speaker and listener share a common practice.

Speakers of the same dialect understand each other without difficulty, but widely separated dialects may well be mutually unintelligible. For purposes of national (or international) communication standard languages with standard pronunciations have generally developed, based usually on the speech of educated people in capital cities, or that of some other prestigious social group. The standard language is widely used in the education system, in the serious media and in middle-class life and culture. This is not to say that all users of a standard pronunciation sound alike. The speaker's socio-regional provenance may be clearly marked and easily detectable by an experienced listener. It may well be important to the individual's sense of identity that this should be so (e.g. Scottish English), but conformity to national norms is sufficient to ensure ready mutual intelligibility on a national scale. In Britain, this role is played by Received Pronunciation (RP) as codified by D. Jones, A. C. Gimson and others, and generally adopted by broadcasting authorities, dictionary makers, language course designers, etc. In its pure form, RP is the practice of a small but influential minority, but with increasing mobility and media exposure a high proportion of speakers use, either habitually or as required, a regionally-coloured approximation to RP which is universally intelligible. Regional variants differ mainly in vowel colouring. The consonant system (which has been shown to play the larger role in identifying speech) is relatively uniform and stable.

On a global scale, English is polycentric. There is no one form of English universally accepted as authoritative. Ireland, the USA, Canada and Australia have their own norms, each related to standard written English and to spoken dialectal variation in much the same way as RP. These norms are fully mutually intelligible and acceptable. All are products of the modern period and have undergone no major sound changes. There is increasingly frequent communication among the communities involved. In countries where English is not the native language, the British norm predominates in educational systems in countries which have recently become independent (India, Africa) and
"""

    pages[122] = f"""more generally in Europe. The General American norm predominates in the Americas and is widely used in the entertainments industry and in industrial management, in which areas it has considerable influence on British usage. Those (e.g. teachers) who have spent a considerable period in one or another English-speaking country are, of course, likely to have learned to conform to its linguistic norms.

At the present time it seems reasonable in a European context to continue (as in the case of Spanish and French) to adhere to the norms of the European rather than the American variety.

At Threshold Level, learners should be able:

- as listeners, to identify the words and expressions used by native speakers of the (regionally coloured) standard variants of English (RP, Polite Scottish, Irish, General American and Australian) and by non-native speakers whose speech, though also regionally coloured, approximates to those norms;
- as speakers, to produce spoken English which is readily intelligible both to native speakers and to non-native speakers who approximate to standard norms.

Among the implications of these objectives are:

- learners should be given experience in listening to a variety of norms, and/or regionally coloured speech (including the principal non-native varieties) which approximate to those norms and remain fully intelligible;
- learners should target one of the native norms (which in a European context may well be British RP), but should not be required or expected to approximate to it more closely than is required for full intelligibility, not only to native English speakers, but also to other non-native learners who have reached Threshold Level.

Accordingly, learners at Threshold Level should be aware of the pronunciation in RP of the words and expressions proposed as exponents. That is to say:

- they will be aware of the relation between the sound and spelling of English words, avoiding simple orthoepic errors;
- they will be aware of and preserve in their own speech the vowel and, particularly, consonant contrasts of the English model they adopt;
- they will be aware of and preserve in their own speech the placement of stress in polysyllabic words;
- they will be able to distinguish by ear non-homophonous English words and expressions;
- they will be aware of some of the principal meaningful contrasts in
"""

    pages[123] = f"""utterances carried by stress placement and intonation and will be able to recognise and understand them in the speech of others;

- they will be aware of the principal respects in which the accent of learners with their mother tongue background deviates from RP in ways which are likely to impede recognition and thus communication.

Some form of phonetic transcription conforming to the principles of the International Phonetic Association (IPA), e.g. that used in D. Jones: *An English Pronouncing Dictionary* (14th edn. ed. A. C. Gimson) or in one of the major monolingual or bilingual dictionaries may be found useful for raising awareness and for reference purposes, but does not in itself constitute part of the Threshold Level objective.

### Intonation

The intonation of English (RP) is described in detail in such works as G. F. Arnold and J. D. O'Connor: *The Intonation of Colloquial English*. It is used by native speakers on the one hand to indicate the informational structure of sentences and on the other to express nuances of meaning, to indicate unspoken implications or reservations and to convey attitudes and emotional states. As such it plays a very important part in communication and is a frequent source of intercultural misunderstandings. Learners at Threshold Level should recognise and understand the most common intonations used in RP for such purposes. In their own speech they should organise the phrasing, stressing and rhythm of tone groups in accordance with RP norms, and employ rising and falling nuclei appropriately.

Where language forms are cited in this book (e.g. as exponents of language functions or examples of grammatical or lexical entries) the most common intonation pattern (not always the only one possible) is shown in accordance with the conventions shown below. These conventions are similar, but not identical, to those used by Arnold and O'Connor.

A full treatment of English intonation is beyond the scope of this book. The most important features at Threshold Level are tone groups. For the most part, learners at Threshold Level will express themselves in fairly short simple sentences, each consisting of a single tone group. Within the tone group, stressed syllables are spoken in a regular rhythm, unstressed syllables being made to fit in between the beats. The stressed syllables of words which convey lexical information (mainly nouns, adjectives, principal verbs and adverbs) are given prominence in the intonation pattern, unless the information has already been mentioned or is obvious in context. In that case, whilst continuing to mark the rhythmic beat, they are not given pitch prominence. At
"""

    pages[124] = f"""<!-- db:id=threshold_appendix_a type=section product_tier=context pages=121-130 -->

*Threshold Level*, two points of pitch prominence are of importance, the *nucleus* and the *head*. The last prominent stressed syllable in a tone group is its **nucleus**, which initiates a pitch pattern which continues to the end of the tone group, including any unstressed or stressed but non-prominent syllables that follow. The pattern used is closely related to the language function of the sentence and its grammatical category.

At *Threshold Level*, **five nuclear tones** should be distinguished:

<!-- el:start type=artifact id=threshold_appendix_a_nuclear_tones page=124 -->
<!-- db:id=threshold_five_nuclear_tones type=section_block product_tier=context pages=124-129 -->

### Five nuclear tones (Threshold 1990)

**Critical notation.** Marks are placed **before** the nuclear syllable. Above vs below the line of writing is distinctive.

| # | Name | Mark | Position | Pitch description |
|---|------|------|----------|-------------------|
| **1** | **Low falling** | **{LF}** | **Below** the line | Nuclear vowel starts on a clear, level **low-mid** tone; voice drops to a **low creaky** note and remains low to the end of the tone group. |
| **2** | **High falling** | **{HF}** | **Above** the line | Like low fall, but nuclear vowel starts on a pitch **above the mid point**. |
| **3** | **Low rising** | **{LR}** | **Below** the line | Nuclear vowel starts **low level**; continuous upward glide **not rising above mid**. If a non-prominent “tail” follows, nucleus stays low and the **rise spans the tail**. |
| **4** | **High rising** | **{HR}** | **Above** the line | Nuclear vowel starts somewhere between **low and mid**; upward glide extends **well above mid**. |
| **5** | **Falling-rising** | **{FR}** | **Above** the line (v-shaped) | Sequence of high fall + low rise: starts **high-mid**, drops to **low creak**, then upward glide **not above mid**. |

**Other marks**

| Mark | Meaning |
|------|---------|
| **{HEAD}** | Head (first prominent syllable; upright mark **above** the line) |
| **{STRESS}** | Stressed non-prominent syllable (rhythmic beat; mid-height dot) |
| **{MINOR}** | End of minor tone group |
| **{MAJOR}** | End of major tone group |

*Threshold Level* learners should be made aware of the following uses of nuclear tones and be stimulated to use them themselves as appropriate.

#### 1 Low falling **{LF}** is used

**a) in declarative sentences**

i) for factual statements e.g. identifying, defining, describing and narrating as well as in answers to *wh* questions (which may be short phrases or single words);

> {HEAD}This is a {LF}door. They {HEAD}drove to {LF}London. {HEAD}Dogs are {LF}animals.

ii) for expressing definite agreement or disagreement, firm denials, firm acceptance or rejection of an offer, definite
<!-- el:end id=threshold_appendix_a_nuclear_tones -->
"""

    pages[125] = f"""statements of intention, obligation, granting or withholding permission, etc. In general, it indicates an unambiguous certainty.

> That's {HEAD}quite {LF}right. You {HEAD}must {STRESS}eat your {LF}dinner.

**b) in interrogative sentences answerable by *yes* or *no***

i) in interrogation, to indicate that an answer is demanded;

> {HEAD}Have you {STRESS}seen this {STRESS}man be{LF}fore?

ii) in requests to indicate that they are in effect orders;

> {HEAD}May I {STRESS}see your {STRESS}driving {STRESS}licence, {STRESS}please? {STRESS}Will you {HEAD}please be {LF}quiet.

iii) when a series of *yes/no* questions is posed in rapid succession;

> {HEAD}Is it {LF}red? {HEAD}Can you {LF}eat it? {HEAD}Is it a {LF}cabbage?

iv) in tag questions, to invite agreement to a statement that is not in doubt;

> {HEAD}This {STRESS}tastes {LF}nice, {MINOR} {LF}doesn't it?

v) in choice questions, to indicate that the list of options is closed.

> {HEAD}Would you prefer {LF}tea {MINOR} or {LF}coffee?

**c) in *wh* questions** as a definite request for a piece of information

> {HEAD}Where is the {LF}toilet, {STRESS}please?

**d) in imperative sentences**

i) as a direct order or prohibition;

> {HEAD}Sit {LF}down. {HEAD}Don't {STRESS}smoke in {LF}here, {STRESS}please.

ii) as an instruction;

> {LF}Push to {HEAD}open the {LF}door.

iii) as a strong form of offer.

> {HEAD}Have {STRESS}one of {STRESS}my ciga{LF}rettes.

#### 2 High falling **{HF}** is used

**a) in declarative sentences**

i) in exclamations to indicate surprise, protest, enthusiasm, emphasis or insistence;

> That's {HF}excellent! You are {HF}hurting me! {HEAD}Fancy {HF}that!

ii) to indicate contrast with an element previously mentioned or believed to be in the listener's mind.

> {HF}No, {MINOR} Mount {HF}Elburz is the {STRESS}highest {STRESS}mountain in {STRESS}Europe.

**b) in interrogative sentences**, both those answerable by *yes* or *no* and *wh* questions

i) to insist on an answer being given;

> {HEAD}Did you {HF}post {STRESS}that {STRESS}letter?
"""

    pages[126] = f"""ii) to indicate surprise or irritation;

> {HEAD}Are you {HF}still {STRESS}not {STRESS}ready?

iii) in rhetorical questions of an exclamatory type, to which no answer is sought;

> {HEAD}Isn't she {HF}beautiful?

iv) in tag questions, to insist on the hearer's agreement to a proposition.

> I told {STRESS}you {MINOR} {HF}didn't I?

**c) in imperative sentences**

i) to insist on an order or prohibition where compliance is in doubt;

> {HF}Stop it, {MINOR} {STRESS}say. {HEAD}Don't {HF}listen {STRESS}to him.

ii) to indicate the urgency of an instruction (e.g. because of imminent danger);

> {HF}Stop. {HEAD}Don't {HF}move.

iii) to insist on the acceptance of an offer.

> {HEAD}Do let me {HF}help you.

#### 3 Low rising **{LR}** is used

**a) in declarative sentences**

i) (with preceding low pitches) to indicate difference or resentment, guardedness, suspicion;

> It doesn't {LR}matter. You {STRESS}shouldn't {STRESS}blame {LR}me.

ii) (with preceding high pitch) to reassure.

> There's {HEAD}no {STRESS}need to be {LR}worried.

**b) in interrogative questions, answerable by *yes* or *no***

i) to ask politely for confirmation or disconfirmation (also in tag questions);

> You're {HEAD}French, {LR}aren't you?

ii) to make polite requests and offers;

> {HEAD}Would you {STRESS}please {STRESS}open the window? {HEAD}Can I do {STRESS}anything to {LR}help?

iii) in choice questions, to indicate that the list is open.

> {HEAD}Would you {STRESS}like {LR}tea {MINOR} or {LR}coffee {MINOR} or something stronger?

**c) in *wh* questions**

i) to indicate polite interest rather than a need for information;

> {HEAD}Where are you {STRESS}spending your {LR}holidays?

ii) to avoid the appearance of interrogation or peremptory questioning.

> {HEAD}What are you {LR}doing {STRESS}there?
"""

    pages[127] = f"""**d) in imperative sentences** for gentle commands, especially to children, hospital patients, etc.

> {HEAD}Come and {STRESS}have your {STRESS}nice {LR}bath. {HEAD}Just {STRESS}drink this {LR}medicine {STRESS}nicely.

#### 4 High rising **{HR}** is used

**a) in declarative sentences** (including isolated phrases and words used instead of full sentences)

i) to convert a statement into a question;

> You were {STRESS}born in {HR}Scotland?

ii) to query what someone has said.

> You {STRESS}say you're {HR}thirsty?

**b) in interrogative questions answerable by *yes* or *no***

i) (with preceding low pitch) to indicate a casual enquiry;

> (Would you) {STRESS}care for a {HR}sandwich?

ii) to repeat a question (with change of 1st and 2nd person) before answering.

> A {HR}sandwich? Would I {STRESS}care for a {HR}sandwich?

**c) in *wh* questions**

i) to repeat a question (with change of 1st and 2nd person) before answering;

> ({HEAD}Where do you live?) {STRESS}Where do I {HR}live?

ii) (with the *wh* word as nucleus) to ask for repetition of information given but not heard (or understood).

> (He {STRESS}lives in (unintelligible).) He {STRESS}lives {HR}where? {HR}Where does he {STRESS}live?

**d) in imperative sentences** to repeat an order, instruction or offer while deciding whether or how to comply

> ({HEAD}Sit down, {STRESS}please.) {STRESS}Sit {HR}down? {MINOR} {HEAD}Why {LR}not?

#### 5 Falling-rising **{FR}** is used

**a) in declarative sentences** to convey various implications

i) warnings;

> That {STRESS}jug is {FR}hot!

ii) corrections;

> Her {STRESS}dress {HEAD}is {FR}green, you know. {MINOR} It {HEAD}isn't {FR}blue.

iii) demurral and limited agreement (with implied disagreement on the major issue);

> I {HEAD}don't {STRESS}know if I a{STRESS}gree with {FR}that.
> {HEAD}Yes, {MINOR} he {HEAD}is an {FR}active {STRESS}person.
"""

    pages[128] = f"""iv) mental reservations in making promises;

> {HEAD}Yes, {MINOR} I {FR}will be {STRESS}good. {MAJOR} At {STRESS}least, I'll {FR}try.

v) uncertainty and hesitation;

> {FR}Yes {FR}possibly. {MINOR} I {HEAD}can't be {FR}certain.

vi) to soften the effect of bad news, conflict of views, etc.;

> You {HEAD}haven't {STRESS}done very {FR}well, I'm a{STRESS}fraid.
> You're {FR}wrong, you {STRESS}know.

vii) (with attached tag questions) anxious query;

> You {HEAD}do {FR}love me, {STRESS}don't you?

viii) discouragement of a possible course of action;

> You can {HEAD}go to the {STRESS}cinema if you {FR}like.

ix) tentative advice;

> If I were {FR}you …

x) implying that something has been left unsaid, which contrasts with, or contradicts what has been overtly stated;

> Your o{STRESS}pinion is {FR}interesting. (implying: but I {HEAD}don't agree with it).

xi) to query what has been said, implying that it is mistaken or untrue.

> {HEAD}Seven {STRESS}eights are {STRESS}fifty {FR}four?

**b) in interrogative questions answered by *yes* or *no***

i) to add a note of warning or doubt;

> Are you {FR}sure you {STRESS}locked the {STRESS}door?

ii) when giving the answer to the question may be unwelcome to the person giving it.

> {HEAD}Have you {STRESS}thought what might {STRESS}happen if you {FR}did?

**c) in *wh* questions**

i) to repeat a question, focusing on the key issue in contrast with other possible issues;

> {HEAD}What did I {STRESS}do on {FR}Friday of {STRESS}last {STRESS}week?

ii) (with the *wh* word as nucleus) to query a statement, implying scepticism regarding the element queried by the *wh* word employed.

> {FR}Where did he {STRESS}find your {STRESS}purse?

**d) in imperative sentences**

i) for issuing warnings rather than commands or instructions;

> {HEAD}Watch where you're {FR}going. {HEAD}Don't {STRESS}try to {STRESS}pull the {FR}door {STRESS}open.

ii) (with the imperative as nucleus) for pleading.

> {HEAD}Do {STRESS}try to be a {STRESS}little more {STRESS}careful.
"""

    pages[129] = f"""Every tone group contains a nucleus. Many short utterances will comprise a single tone group, containing only one prominent syllable, which is then the nucleus of the tone group. Where there is more than one prominent syllable, the last of these is the nucleus and the first is the **head**. The head is usually marked by a jump up in pitch to a high-mid level. The actual pitch varies from mid to high, depending on the attitude of the speaker towards what he is saying and towards the hearer. The higher the level, the more cheerful and friendly the speaker sounds. The (high) head is marked in the texts by an upright line before the syllable concerned, above the line of writing **{HEAD}**.

Non-prominent syllables, stressed or unstressed, which precede the head, are spoken on a low mid pitch. Those following a high head are kept on the same level, or form a descending sequence. Those following the nucleus conform to the configuration of the nucleus, as elaborated above. Stressed non-prominent syllables are marked in texts by a dot raised to mid-letter height **{STRESS}**. As stated, they mark rhythmic beats in the utterance, but have no effect on the pitch pattern. Non-prominent unstressed syllables are left unmarked.

Many, perhaps most, short exchanges in conversation — especially the contributions of learners at *Threshold Level* — consist of single tone groups. Longer utterances may simply juxtapose tone groups as already described. However, compound (*and*, *but*, *either*, *or*) and complex (*if*, *because*, *when*) sentences may have two or more closely linked tone groups. Only in the last of these has the nucleus the functions listed above. The sequence is then termed a **major tone group**, and its completion is shown in a text with the mark **{MAJOR}**. The constituent **minor tone groups** are marked **{MINOR}**. The following are the most common types of sequence, and should be within the productive and receptive competence of *Threshold Level* learners:

#### 1 Unemphatic, non-constructive sentences

| non-final | final group |
|-----------|-------------|
| low rising | low falling |

> {HEAD}When you {STRESS}see John {MINOR} {HEAD}tell him to phone me.{MAJOR}

#### 2 Contrasting

| | |
|--|--|
| falling-rising | high falling |

> But {HEAD}when you see {FR}Harry {MINOR} {HEAD}tell him I've {STRESS}left the {HF}country.{MAJOR}

#### 3 Main statement and modifier (non-contrastive)

| | |
|--|--|
| low falling | low rising |

> I'm {HEAD}leaving for {LF}Germany {MINOR} on {LR}Friday.{MAJOR}

#### 4 Main statement and supplement

| | |
|--|--|
| low fall | low fall |

> He {STRESS}lives in {LF}London {MINOR} in a {HEAD}semi-de{STRESS}tached {STRESS}house in {LF}Peckham.{MAJOR}
"""

    pages[130] = f"""#### 5 Apposition

In all cases of apposition, the same nuclear tone is used for both tone groups. The word *too* similarly repeats the tone of its antecedent nucleus.

> John {LF}Smith, {MINOR} a com{LF}puter {STRESS}programmer {MINOR} {STRESS}lives in {LF}Cambridge, {MINOR} a university {LF}city.{MAJOR}
> His {HEAD}brother {STRESS}lives {LF}there, {MINOR} {LF}too.{MAJOR}

**Note.** In this document, **{MAJOR}** is omitted at the end of examples consisting of a single sentence.
"""

    return pages[pnum]


# ---------- Column formatters ----------

def format_index_lines(text: str, kind: str) -> list[str]:
    """Format word or subject index column text into structured lines."""
    lines_out: list[str] = []
    buf = ""
    for raw in text.splitlines():
        t = clean(raw)
        if not t or is_chrome(t):
            continue
        # strip residual title fragments
        if re.match(r"^Appendix\s*[CD]", t, re.I):
            continue
        if re.match(r"^Word index$", t, re.I):
            continue
        if re.match(r"^Subject index$", t, re.I):
            continue
        if re.match(r"^Index of language", t, re.I):
            continue
        if re.match(r"^ord index$", t, re.I):  # split "Word"
            continue
        if re.match(r"^[A-Z]$", t) and kind == "word":
            lines_out.append("")
            lines_out.append(f"### {t}")
            lines_out.append("")
            continue
        # letter head with IPA: A [ei]
        m = re.match(r"^([A-Z])\s*[\[\(].+$", t)
        if m and kind == "word" and len(t) < 20:
            lines_out.append("")
            lines_out.append(f"### {t}")
            lines_out.append("")
            continue

        # word index entry: lemma pos: refs
        if kind == "word":
            # join wrap lines that continue with refs only
            if buf and (re.match(r"^[\d,\.\s]+$", t) or re.match(r"^\d", t) and ":" not in t and not re.match(r"^[a-z]", t)):
                buf = buf.rstrip(",") + (", " if not buf.endswith(",") else " ") + t
                continue
            if buf:
                lines_out.append(f"- {buf}")
                buf = ""
            # new entry typically starts with lowercase or lettered word
            if re.match(r"^[A-Za-z'’\-\(\)]", t):
                buf = t
            else:
                lines_out.append(t)
            continue

        # subject index: headword then indented sub-entries
        if kind == "subject":
            if re.match(r"^\d", t) and buf:
                # continuation of refs
                buf = buf + " " + t
                continue
            # indented sub-entry (starts lower or is continuation phrase with refs)
            is_sub = (
                t[:1].islower()
                or re.match(
                    r"^(enquiring|expressing|accepting|offering|physical|cost|residential|"
                    r"types|while|customer|friend|stranger|someone|for |on |denying|"
                    r"foreign|private|public|in |with |asking|order)\b",
                    t,
                    re.I,
                )
            )
            # main entry: often ends with refs or is bare headword
            if buf:
                lines_out.append(buf)
                buf = ""
            if is_sub and lines_out:
                lines_out.append(f"  - {t}")
            else:
                # main head
                if re.search(r"\d+\.\d+", t) and not re.match(r"^[A-Z][a-z]+$", t.split()[0] if t.split() else ""):
                    # "absence 6.1.2" style single line
                    lines_out.append(f"- **{t}**" if not re.search(r":\s*\d", t) else f"- {t}")
                else:
                    # headword alone or head + first sub
                    if re.match(r"^[a-z][a-z/\-]+$", t) or re.match(r"^[a-z].*[a-z]$", t) and not re.search(r"\d", t):
                        lines_out.append(f"- **{t}**")
                    else:
                        lines_out.append(f"- {t}")
            continue

    if buf:
        if kind == "word":
            lines_out.append(f"- {buf}")
        else:
            lines_out.append(buf)
    return lines_out


def format_grammar_column(text: str) -> list[str]:
    """Hierarchical grammar outline from one column of text."""
    out: list[str] = []
    para: list[str] = []

    def flush() -> None:
        nonlocal para
        if para:
            t = " ".join(para)
            t = re.sub(r"\s+", " ", t)
            t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)
            if t:
                out.append(t)
                out.append("")
            para = []

    for raw in text.splitlines():
        t = clean(raw)
        if not t or is_chrome(t):
            continue
        if re.match(r"^Appendix\s*B", t, re.I):
            continue
        # dotted leaders
        if re.match(r"^\.+$", t) or re.match(r"^[·•\.]{3,}$", t):
            continue

        # Section letters: A Word level / B Phrase level
        m = re.match(r"^([A-D])\s+(.+)$", t)
        if m and len(t) < 60 and not re.match(r"^[A-D]\d", t):
            flush()
            out.append(f"## {m.group(1)} {m.group(2).strip()}")
            out.append("")
            continue

        # A1 Nouns / A2 …
        m = re.match(r"^([A-D]\d+)\s+(.+)$", t)
        if m and len(t) < 70:
            flush()
            out.append(f"### {m.group(1)} {m.group(2).strip()}")
            out.append("")
            continue

        # numbered outline 1.1 / 1.1.1 / 1.2.1.1
        m = re.match(r"^(\d+(?:\.\d+){0,4})\s+(.+)$", t)
        if m:
            flush()
            num, rest = m.group(1), m.group(2).strip()
            depth = min(num.count(".") + 1, 4)
            # short heading vs body
            if len(rest) < 70 and not rest.endswith((",", ";")) and rest[0:1].islower() is False or re.match(
                r"^(Types|Number|proper|common|regular|irregular|abstract|names|nouns|verbs|adjectives|adverbs|prepositions|pronouns|articles|determiners|forms|Usage|be |have |do |modal)",
                rest,
                re.I,
            ):
                out.append("#" * min(depth + 2, 6) + f" {num} {rest}")
                out.append("")
            else:
                out.append(f"- **{num}** {rest}")
            continue

        # plural examples table-ish: "s address, addresses"
        if re.match(r"^(s|x|z|sh|ch|o|y|f|fe)\s+\S", t, re.I) and len(t) < 50:
            flush()
            out.append(f"  - `{t}`")
            continue

        if para and t[0:1].islower():
            para.append(t)
        else:
            flush()
            para.append(t)
    flush()
    return out


def format_two_col_page(pnum: int, kind: str, title: str | None = None) -> str:
    left, right = tesseract_columns(pnum, mid_frac=0.50, top_frac=0.07 if kind != "grammar" else 0.12)
    parts: list[str] = []
    if title:
        parts.append(title)
        parts.append("")
    if kind == "word":
        # Prefer left-then-right full reading order
        for col_name, col in (("left", left), ("right", right)):
            lines = format_index_lines(col, "word")
            parts.extend(lines)
        # de-dupe blank runs
    elif kind == "subject":
        for col in (left, right):
            parts.extend(format_index_lines(col, "subject"))
    else:  # grammar
        # intro may span full width on first pages — also merge top OCR
        ocr = read_ocr(pnum)
        # If left has intro prose before A Word level, keep reading order: process left fully then right
        # But content interleaves: left continues into right on same logical stream for numbered sections.
        # Best: left column then right column (as book reading of multi-col outline often is L then R).
        parts.extend(format_grammar_column(left))
        parts.extend(format_grammar_column(right))

    body = "\n".join(parts)
    body = re.sub(r"\n{3,}", "\n\n", body)
    # OCR cleanup
    body = body.replace("|", "I") if kind == "word" and False else body
    body = re.sub(r"(?m)^-\s*$", "", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def format_app_b_intro(pnum: int) -> str:
    """Pages 131 (and maybe early B) are mostly prose intro."""
    text = read_ocr(pnum)
    body = format_prose_from_ocr(pnum, text)
    if pnum == 131:
        # ensure title
        if "Appendix B" not in body and "Grammatical" not in body:
            body = "## Appendix B — Grammatical summary\n\n" + body
        else:
            body = re.sub(
                r"(?i)^##?\s*Appendix\s*B\s*Grammatical\s*summary",
                "## Appendix B — Grammatical summary",
                body,
                count=1,
            )
            if not body.startswith("##"):
                body = "## Appendix B — Grammatical summary\n\n" + body
    return body


def format_word_index_start(pnum: int) -> str:
    left, right = tesseract_columns(pnum, mid_frac=0.50, top_frac=0.10)
    parts = ["## Appendix C — Word index", ""]
    # letter head from left
    for col in (left, right):
        parts.extend(format_index_lines(col, "word"))
    body = "\n".join(parts)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def format_subject_index_start(pnum: int) -> str:
    left, right = tesseract_columns(pnum, mid_frac=0.50, top_frac=0.14)
    ocr = read_ocr(pnum)
    parts = [
        "## Appendix D — Subject index",
        "",
        "### Index of language functions and notional categories",
        "",
        "In the following index numbers refer to chapters and items or sections. "
        "The chapters referred to are 5, 6 and 7. All references beginning with 5 are to "
        "language functions, those beginning with 6 to general notions and those "
        "beginning with 7 are references to themes or sub-themes.",
        "",
    ]
    for col in (left, right):
        parts.extend(format_index_lines(col, "subject"))
    body = "\n".join(parts)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


# ---------- Special prose polish for known chapter pages ----------

def polish_writing_pages(pnum: int, body: str) -> str:
    if pnum == 98:
        return """## 10 Writing

The objective for writing at *Threshold Level* is very limited. It is assumed that for this skill the actual needs of the majority of the members of the target group who are expected to be temporary visitors do not go beyond the ability to fill in certain forms, to write a few types of standard letter, and to write simple personal letters on subjects of common interest to themselves and friends or acquaintances. All this falls strictly within items 1 and 2 of the extended characterisation. It may be specified as follows:

The learners will be able to complete forms:

- hotel registration forms
- forms required when entering or leaving a foreign country

The learners will be able to write standard letters:

- enquiring about price and conditions of accommodation
- stating wishes as to size of rooms, arrangement (full board, etc.), amenities, view
- enquiring about tourist attractions, sights, etc.
- booking accommodation

The learners will be able to conduct personal correspondence:

- simple messages such as greetings and congratulations
- simple private letters concerning matters of common interest to themselves and friends or acquaintances

The writing requirements of temporary residents, as set out in the extended characterisation, are of a somewhat different character. These learners will almost certainly be called upon to complete a wider range of official forms. They may need to write letters enquiring about accommodation to rent, and if need be, letters of complaint to landlords. They may send written invitations and write brief letters of thanks for hospitality received. They may have to note down and relay messages (e.g. by telephone). They may have to write letters of application for jobs, to report briefly on accidents and complete insurance claims. As parents, they may need to write notes to school explaining a child's absence. In carrying out the above tasks, the learner should be able to observe conventions regarding:

- basic letter layout
- opening and closing formulae (See Language Functions 5.27–28)
- representation of dates (See General Notions 3.3)
"""
    if pnum == 99:
        return """- use of capitals and punctuation ( . , ; : ? ! )

These tasks can be accomplished within the limits of the resources required for the tasks specified at *Threshold Level*, using the techniques set out in Chapters 12 and 13.
"""
    return body


def process_page(pnum: int) -> str:
    print(f"  page {pnum}…", flush=True)

    # blank end page
    if pnum == 192:
        png = RENDERS / f"page_{pnum:03d}.png"
        return wrap_page(
            pnum,
            "<!-- empty / blank page (end matter) -->",
            extra="<!-- vision-verified blank -->",
        )

    # Appendix A: vision hand structure
    if 121 <= pnum <= 130:
        return wrap_page(pnum, app_a_page(pnum))

    # Appendix B intro
    if pnum == 131:
        return wrap_page(pnum, format_app_b_intro(pnum))

    # Appendix B grammar two-col (and residual prose on 132+)
    if 132 <= pnum <= 162:
        body = format_two_col_page(pnum, "grammar")
        # prepend any full-width intro from OCR if page still has top prose
        if pnum == 132:
            intro = (
                "The summary is not conceived as a teaching or reference grammar of "
                "English, but as a guide to the resources to which a learner has access as "
                "a result of learning English to *Threshold Level*.\n\n"
                "We trust that with a little experience users will find that the systematic "
                "presentation enables reference to be made quickly and efficiently as a "
                "further aid to curricular planning and course construction.\n"
            )
            body = intro + "\n" + body
        return wrap_page(pnum, body)

    # Appendix C Word index
    if pnum == 163:
        return wrap_page(pnum, format_word_index_start(pnum))
    if 164 <= pnum <= 183:
        body = format_two_col_page(pnum, "word")
        return wrap_page(pnum, body)

    # Appendix D Subject index
    if pnum == 184:
        return wrap_page(pnum, format_subject_index_start(pnum))
    if 185 <= pnum <= 191:
        body = format_two_col_page(pnum, "subject")
        if not body.strip() and pnum == 191:
            # try full-page tesseract
            if pytesseract:
                im = Image.open(RENDERS / f"page_{pnum:03d}.png")
                full = pytesseract.image_to_string(im, config="--psm 6")
                body = "\n".join(format_index_lines(full, "subject"))
                if not body.strip():
                    body = "<!-- subject index continuation; sparse OCR — see PNG -->\n" + full
        return wrap_page(pnum, body if body.strip() else "<!-- sparse page -->")

    # Prose chapters 97–120
    ocr = read_ocr(pnum)
    if not ocr.strip() and pytesseract:
        im = Image.open(RENDERS / f"page_{pnum:03d}.png")
        ocr = pytesseract.image_to_string(im, config="--psm 6")
    body = format_prose_from_ocr(pnum, ocr)
    body = polish_writing_pages(pnum, body)
    if not body.strip():
        body = "<!-- vision: low OCR; check PNG -->"
    return wrap_page(pnum, body)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    start = 97
    end = 192
    if len(sys.argv) >= 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    elif len(sys.argv) == 2:
        start = end = int(sys.argv[1])

    n = 0
    for pnum in range(start, end + 1):
        md = process_page(pnum)
        dest = OUT / f"page_{pnum:03d}.md"
        dest.write_text(md, encoding="utf-8")
        n += 1
    print(f"Wrote {n} overrides to {OUT}", flush=True)


if __name__ == "__main__":
    main()
