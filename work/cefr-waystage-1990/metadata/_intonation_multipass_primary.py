# -*- coding: utf-8 -*-
"""High-precision Waystage intonation multipass rewrite — primary bands.

PDF leaves: 22–35, 38–47, 56–65, 77–80
Protocol: INTONATION_NOTATION.md word-catalog multipass
Marks: ˈˎˋˏˊˇ· only (never ASCII ' or ˌ as tone)
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OV = ROOT / "page_overrides"
CAT = ROOT / "intonation_hires" / "catalogs"
CAT.mkdir(parents=True, exist_ok=True)

H = "ˈ"  # head U+02C8
LF = "ˎ"  # low fall U+02CE
HF = "ˋ"  # high fall U+02CB
LR = "ˏ"  # low rise U+02CF
HR = "ˊ"  # high rise U+02CA
FR = "ˇ"  # fall-rise U+02C7
D = "·"  # mid stress U+00B7


def hdr(leaf: int) -> str:
    doc = leaf - 6
    return (
        f"<!-- vision: Waystage leaf {leaf} doc p.{doc} | word-catalog multipass -->\n"
        f"<!-- el:start type=prose id=prose_p{leaf:03d} page={doc} -->\n"
    )


def end(leaf: int) -> str:
    return f"\n<!-- el:end id=prose_p{leaf:03d} -->\n"


def write(leaf: int, body: str, catalog: str | None = None) -> None:
    doc = leaf - 6
    text = hdr(leaf) + "\n" + body.strip() + end(leaf)
    (OV / f"page_{leaf:03d}.md").write_text(text, encoding="utf-8")
    if catalog:
        (CAT / f"leaf_{leaf:03d}_catalog.md").write_text(
            f"# Word catalog — Waystage leaf {leaf} (doc p.{doc})\n\n"
            f"**Source:** Vision of `intonation_hires/leaf_{leaf:03d}_*.png` + bands (multipass).\n"
            f"**Encoding:** INTONATION_NOTATION.md — never ASCII `'` as tone.\n\n"
            + catalog.strip()
            + "\n",
            encoding="utf-8",
        )
    # verify no forbidden low-vertical and count marks
    bad = "\u02cc" in text
    marks = {
        "H": text.count(H),
        "LF": text.count(LF),
        "HF": text.count(HF),
        "LR": text.count(LR),
        "HR": text.count(HR),
        "FR": text.count(FR),
        "D": text.count(D),
    }
    print(f"leaf {leaf:03d} doc {doc:02d} marks={marks} bad02CC={bad} chars={len(text)}")


# ---------------------------------------------------------------------------
# LEAF 22 = doc 16 — Language functions start
# ---------------------------------------------------------------------------
write(
    22,
    f"""
do something' directly, whereas *'It's getting late'* – in its conventional meaning fulfilling the function of 'reporting' – may serve the same purpose indirectly. The possibilities for the indirect fulfilment of language functions vary in accordance with the situational and the linguistic context of a communicative act.

This variation is such that a systematic description and selection on behalf of our objective is not possible. The exponents we propose, therefore, are on the whole those which may be considered to fulfil the functions concerned directly. This does not mean that the indirect fulfilment of language functions should be avoided in course materials designed for *Waystage*. On the contrary, an attempt to do so might lead to highly unnatural language use.

### Language functions for *Waystage* with recommended exponents

### 1 Imparting and seeking factual information

**1.1 identifying (defining)**  
(with pointing gesture) this (one), that (one), these, those  
me, you, him, her, us, them  
the, this, that, these, those, (+N) + *be* + NP  

> {H}This is the {LF}bedroom.

I, you, he, she, it, we, they + *be* + NP  

> {H}He is the {LF}owner of the {D}restaurant.

**1.2 reporting (describing and narrating)**  
declarative sentences  

> The {H}train has {LF}left.

NP + say, think + complement clause  

> He {D}says the {H}shop is {LF}shut.

**1.3 correcting**  
As 1.1 and 1.2, with contrastive stress  

> {H}This is the {D}bedroom.  
> The {D}train {H}has {D}left.

(correcting a positive statement)  
No (+ tag)  

> {H}No.  
> {H}No it {FR}isn't.

negative sentences  

> Va{D}letta {H}isn't in {FR}Italy.

(correcting a negative statement)  
Yes (+ tag)  

> {H}Yes.  
> {H}Yes you {FR}did.

**1.4 asking**  
**a** for confirmation  
interrogative sentences  

> {H}Did you {LF}see him?

declarative sentences with high-rising intonation  

> You {HR}saw him? ®

short questions  

> {LR}Are you? ®

**b** for information  
wh questions  
(time) {LR}when?  
(place) {LR}where?  
(manner) {LR}how?
""",
    catalog=f"""
## 1.1
| Word | Mark | Notes |
|------|------|-------|
| This | {H} | head upright above |
| bedroom | {LF} | low fall below — not mid-dot |
| He | {H} | |
| owner | {LF} | low fall — not mid-dot |
| restaurant | {D} | mid secondary |

## 1.2
| train={H} left={LF} | says={D} shop={H} shut={LF} |

## 1.3 contrastive
| This={H} bedroom={D} | train={D} has={H} left={D} |

## 1.3 correcting +/−
| No={H} | isn't={FR} fall-rise | Va={D} isn't={H} Italy={FR} | Yes={H} did={FR} |

## 1.4
| Did={H} see={LF} | saw={HR} high rise above | Are={LR} low rise below | when/where/how={LR} |
""",
)

# ---------------------------------------------------------------------------
# LEAF 23 = doc 17
# ---------------------------------------------------------------------------
write(
    23,
    f"""
(degree) how {LF}far/{LF}much/{LF}long/{LF}hot/etc.?  
(reason) {LF}why?

**c** seeking identification  
wh questions  
(person) {LF}who?  
(possession) whose + NP?  

> {H}Whose {LF}watch is {D}this?

(thing) {LF}what?  
which + NP?  

> {H}Which {LF}sport do you {D}play? ®

**1.5 answering questions**  
**a** for confirmation  
Yes, No (+ tag)  

> {LF}Yes (he {LF}is).  
> {LF}No (he {LF}isn't).

**b** for information  
declarative sentences  
({H}Where did you {LF}go?)  

> I {D}went to {LF}London.

(time)  
adverb, prepositional phrase  

> {LF}yesterday. At {H}ten o'{LF}clock.

(place)  
adverb, prepositional phrase  

> {LF}There. {H}On the {LF}table.

(manner)  
adverb, prepositional phrase  

> {LF}Fast. With a {LF}spoon.

(degree)  
adverb, prepositional phrase  

> ({H}How {LF}hot is it?) {LF}Very.  
> ({H}How {D}much do you {LF}like it?)  
> {H}Better than {FR}water.

(reason) (because +) declarative sentence  
({H}Why did you {LF}leave?)  

> Because I was {LF}tired.

**c** seeking identification – see 1.1

### 2 Expressing and finding out attitudes

#### Factual: agreement, etc.

**2.1 expressing agreement with a statement**  

> I a{LF}gree.  
> {H}That's {LF}right. ®

(with a positive statement)  
{H}Yes (+ tag).  
(She's {H}nice!)  

> {H}Yes, she {HF}is!

Of {LF}course. ®  
{LF}Certainly. ®  
(with a negative statement)  
{LF}No (+ tag)  
(He {H}doesn't look {LF}well.)  

> {LF}No, he {LF}doesn't.

Of {LF}course {D}not. ®  
{H}Certainly {LF}not. ®

**2.2 expressing disagreement with a statement**  

> That's {H}not {LF}right.  
> I {H}don't a{LF}gree. ®

(with a positive statement)  
{LF}No (+ tag).  
{H}Certainly {LF}not. ®  

> I {H}don't {FR}think so.

(with a negative statement)  
Yes (+ tag).  
(They {H}aren't {LF}French)  

> {H}Yes, they {FR}are

I think + positive statement  

> I {D}think he {H}will {D}come.

**2.3 enquiring about agreement and disagreement**  
Do(n't) you think + complement clause?  

> {H}Do you {D}think it'll {LF}rain?  
> {H}Do(n't) you {LF}think so ({LF}too)?  
> {H}Do(n't) you a{LF}gree? ®

**2.4 denying something**  
No (+ negative tag)  
(You {LF}saw him)  

> {LF}No, I {LF}didn't.
""",
    catalog=f"""
| far/much/long/hot/why/who/what | {LF} |
| Whose watch this | {H}Whose {LF}watch is {D}this? |
| Which sport play | {H}Which {LF}sport do you {D}play? ® |
| Yes/No answers | {LF}Yes (he {LF}is). / {LF}No (he {LF}isn't). |
| went London | I {D}went to {LF}London. |
| Better water | {H}Better than {FR}water. — FR on water |
| don't think so | I {H}don't {FR}think so. — FR on think |
| Yes they are | {H}Yes, they {FR}are — FR on are |
| Yes she is | {H}Yes, she {HF}is! — HF emphatic |
""",
)

# ---------------------------------------------------------------------------
# LEAF 24 = doc 18
# ---------------------------------------------------------------------------
write(
    24,
    f"""
negative sentences with not, never, no (adjective), nobody ®, nothing

#### Factual: knowledge

**2.5 stating whether one knows or does not know something or someone**  
I (don't) know (+ NP).

**2.6 enquiring whether one knows or does not know something or someone**  
Do(n't) you know (+ NP)?

#### Factual: modality

**2.7 expressing ability and inability**  
NP + can (not) …

**2.8 enquiring about ability and inability**  
Can (not) + NP …?

**2.9 expressing how (un)certain one is of something**  
**a** strong positive  
I'm sure (+ that clause). ®  
I'm certain (+ that clause). ®

**b** positive  
declarative sentence  
I know + that clause.

**c** intermediate  

> I {FR}think so.

I think + that clause.  

> I sup{FR}pose/be{FR}lieve so. ®

I suppose/believe + that clause. ®

**d** weak  
NP + may … ®  

> Per{H}haps. ®  
> I'm not {FR}sure (+ that clause). ®  
> I {LF}wonder. ®

**e** negative  
NP + cannot … ®  

> I {H}don't {LF}think so.

I don't think + that clause.

**2.10 enquiring how (un)certain others are of something**  

> {H}Are you ({D}quite) {LF}sure? ®

Are you (quite) sure + that clause? ®  

> {H}Do you {LF}think so? ®

Do you think + that clause? ®

**2.11 expressing one is (not) obliged to do something**  
I/We (don't) have to …

**2.12 enquiring whether one is obliged to do something**  
Do I/we have to …?

**2.13 giving permission**  
You can …  
You may …  
Yes.  

> Of {LF}course (you{D}may). ®  
> ({H}That's){D}all {LF}right.

**2.14 seeking permission**  
May I …?  
Can I …?  
Let me … ®  
Do you mind + if clause? ®

**2.15 stating that permission is withheld**  
(Please) don't (…).  
No.  
NP + must not … ®

#### Volitional

**2.16 expressing want, desire**  
I'd like … (e.g. a drink, to go now).  
I want … (e.g. a drink, to go now) (please).  
May I have + NP (please)?
""",
    catalog=f"""
| I think so | I {FR}think so. FR on think |
| suppose/believe | I sup{FR}pose/be{FR}lieve so. |
| not sure | I'm not {FR}sure |
| wonder | I {LF}wonder. |
| don't think so | I {H}don't {LF}think so. |
| Are you sure | {H}Are you ({D}quite) {LF}sure? |
| Of course you may | Of {LF}course (you{D}may). |
""",
)

# ---------------------------------------------------------------------------
# LEAF 25 = doc 19
# ---------------------------------------------------------------------------
write(
    25,
    f"""
**2.17 enquiring about want, desire**  
Would you like … (e.g. a drink, to go now)?  
Do you want … (e.g. a taxi, to walk)?  
What about … (e.g. a drink, going out)? ®

**2.18 expressing intention**  
NP + *be* going to …  
NP + will/'ll … ®

**2.19 enquiring about intention**  
Are you going to …?  
Will you …? ®

**2.20 expressing preference**  
I({H}d) prefer + NP.  
I({H}d) like + NP.  
I'd rather … (than …). ®  
I'd rather not (…). ®

#### Emotional

**2.21 expressing pleasure, liking**  
NP + *be* (very) nice.  
NP + *be* (very) pleasant. ®  
I like + NP (very much).  
I love … (e.g. books). ®

**2.22 expressing displeasure, dislike**  
NP + *be* not (very) nice.  
NP + *be* not (very) pleasant. ®  
I don't like + NP (very much).  
I hate … (e.g. cabbage, swimming). ®

**2.23 enquiring about pleasure, liking, displeasure, dislike**  
Do(n't) you like + NP?  
Would you like … (e.g. to go now)? ®

**2.24 expressing hope**  

> I {H}hope {LF}so.

I (do) hope + that clause. ®

**2.25 expressing satisfaction**  

> {D}This/{D}That is {H}very {LF}good/{LF}nice.

**2.26 expressing dissatisfaction**  

> I {H}don't {LF}like this/that.

**2.27 enquiring about satisfaction**  

> {H}Do you {LF}like this/that?  
> {H}Is {D}this {D}all {LF}right ({D}now)? ®

**2.28 expressing disappointment**  

> {H}What a {LF}pity!  
> {D}That's a ({H}great) {HF}pity! ®

**2.29 expressing gratitude**  

> {LF}Thank you ({H}very {LF}much).  
> That's {H}very {LF}kind of you. ®

#### Moral

**2.30 apologising**  

> I am ({H}very) {LF}sorry!  
> {H}Sorry!  
> I am {H}so {LF}sorry! ®

**2.31 granting forgiveness**  

> {H}That's {D}all {LF}right.  
> It's {H}all {D}right {LF}now. ®  
> It {H}doesn't {LF}matter (a{LF}t all). ®

**2.32 expressing approval**  

> {H}Good!  
> {D}That's {H}fine! ®

**2.33 expressing appreciation**  

> (It's) {H}very {LF}good/{LF}nice.

**2.34 expressing regret**  

> {H}What a {LF}pity!  
> It's a ({H}great) {LF}pity! ®  
> I'm (so/very) sorry if … ®

**2.35 expressing indifference**  

> It {D}doesn't {LF}matter.  
> I don't mind (+ if clause). ®

### 3 Getting things done (suasion)

**3.1 suggesting a course of action (including the speaker)**  
Let's …  
Shall we …? ®
""",
    catalog=f"""
| hope so | I {H}hope {LF}so. |
| satisfaction | {D}This/{D}That is {H}very {LF}good/{LF}nice. |
| What a pity | {H}What a {LF}pity! |
| Thank you | {LF}Thank you ({H}very {LF}much). |
| sorry | I am ({H}very) {LF}sorry! / {H}Sorry! |
| all right | {H}That's {D}all {LF}right. |
""",
)

# ---------------------------------------------------------------------------
# LEAF 26 = doc 20
# ---------------------------------------------------------------------------
write(
    26,
    f"""
We could … ®  
What about … (e.g. leaving now)? ®

**3.2 requesting others to do something**  
Please, … (e.g. come over here)  
…, please.  
Will/would/could you …? ®  
Would you mind …? ®

**3.3 inviting others to do something**  
Would you like to …?  
What about …? ®

**3.4 accepting an offer or invitation**  

> {H}Thank you.  
> {H}Yes, {LF}please.  
> That'll be {H}very {LF}nice. ®  
> {H}All {LF}right.

**3.5 declining an offer or invitation**  

> {H}No, {LF}thank you.

I'm afraid I cannot … ®

**3.6 enquiring whether an offer or invitation is accepted or declined**  
Will you … (do it, come, etc.)?

**3.7 advising others to do something**  
You should … ®  
Why don't you …? ®

**3.8 warning others to take care or to refrain from doing something**  

> Be {H}careful!  
> {H}Look {HF}out!  
> Don't …  
> Mind … (e.g. your head)! ®

**3.9 offering assistance**  
Can I … (e.g. help you)?

**3.10 requesting assistance**  
Can you … (e.g. help me), please?

### 4 Socialising

(See also Chapter 8 on sociocultural competence.)

**4.1 attracting attention**  

> Ex{H}cuse {LF}me!  
> Hal{H}lo!

**4.2 greeting people**  

> {H}Hal{LF}lo!  
> {H}Good {LF}morning/after{LF}noon/{LF}evening.

**4.3 when meeting people**  

> {H}Hal{LF}lo!  
> {H}How {LF}are you?  
> (I'm {H}fine, {LF}thank you,) {H}how are {LF}you?  
> {H}How do you {LF}do?  
> {H}How do you {LF}do?

**4.4 addressing somebody**  
first name  
Mr/Mrs/Miss + family name

**4.5 introducing somebody**  
This is …

**4.6 reacting to being introduced**  

> {H}Hal{LF}lo.  
> {H}How do you {LF}do?

**4.7 congratulating**  

> Con{H}gratu{LF}lations!

**4.8 proposing a toast**  

> {H}Cheers!  
> Here's to … ®

**4.9 taking leave**  

> {H}Good{LF}bye.  
> {H}Good {LF}night.  
> I'll {LF}see you (to{LF}morrow, {D}next {LF}week, etc.). ®

### 5 Structuring discourse

(See also Chapter 9.)

**5.1 opening**  
See the exponents of language functions 4.1, 4.2, 4.4.
""",
    catalog=f"""
| Yes please | {H}Yes, {LF}please. |
| No thank you | {H}No, {LF}thank you. |
| Look out | {H}Look {HF}out! |
| Excuse me | Ex{H}cuse {LF}me! |
| Hello greetings | {H}Hal{LF}lo! / {H}Good {LF}morning |
| How are you | {H}How {LF}are you? |
| Congratulations | Con{H}gratu{LF}lations! |
| Goodbye | {H}Good{LF}bye. / {H}Good {LF}night. |
""",
)

# ---------------------------------------------------------------------------
# LEAF 27 = doc 21
# ---------------------------------------------------------------------------
write(
    27,
    f"""
**5.2 hesitating, looking for words**  

> {D}Er …  
> {H}Just a {LF}moment.  
> {H}What's the {LF}word for it?

**5.3 correcting oneself**  

> {LF}No, …  
> {H}Sorry, …

**5.4 enumerating**  
… and … and …  
First …, then …, then …

**5.5 summing up**  
So …

**5.6 closing**  

> {D}Well, {H}good{LF}bye/{H}good {LF}night.  
> {H}Well, it's been {H}nice {LF}talking with you. ®  
> I'll {H}see you ({LF}later/{LF}soon/to{LF}morrow, etc.) ®

#### Telephone

**5.7 opening (on lifting the handset)**  
telephone number  
Oxford 785423  

> {H}Hal{LF}lo (this is …)

**5.8 asking for extension**  
I'd like to talk to …

**5.9 giving notice of a new call**  

> I'll {H}call a{H}gain ({LF}later/this after{LF}noon, etc.)

#### Letter

**5.10 opening**  
Dear …

**5.11 closing**  
Yours sincerely,  
Best wishes,  
Love from …

### 6 Communication repair

(See also Chapter 10.)

**6.1 signalling non-understanding**  

> {H}Sorry, | I {H}don't/{H}didn't under{LF}stand (that).  
> (I {D}beg your) {H}pardon? ®

**6.2 asking for overall repetition**  

> ({H}Sorry,) {H}can you {D}say that a{LF}gain, {D}please?  
> (I {D}beg your) {H}pardon? ®

**6.3 asking for partial repetition**  
({H}Sorry,) when/where/why/how/who …?

**6.4 asking for clarification**  

> ({H}Sorry,) {H}what is {LF}X?

**6.5 asking for confirmation of understanding**  

> {H}Did you say {LF}X?

**6.6 asking to spell something**  

> {H}Can you {LF}spell that, {D}please?

**6.7 asking to write something down**  

> {H}Can you {D}write that {LF}down for me, {D}please?

**6.8 expressing ignorance**  

> I {H}don't know {D}how to {LF}say it.

**6.9 appealing for assistance**  

> I {D}don't {H}know the {D}English {LF}word.  
> In [native language] we say …

**6.10 asking to slow down**  

> {H}Can you {D}speak {LF}slowly, {D}please?
""",
    catalog=f"""
| Just a moment | {H}Just a {LF}moment. |
| What's the word | {H}What's the {LF}word for it? |
| closing | {D}Well, {H}good{LF}bye |
| under stand | under{LF}stand |
| say again | a{LF}gain |
| spell/write/slowly | nucleus {LF} on spell/down/slowly |
""",
)

print("--- functions 22-27 done ---")
