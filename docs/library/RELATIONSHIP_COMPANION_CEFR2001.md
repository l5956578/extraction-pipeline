# Relationship map — Companion 2020 ↔ CEFR 2001

**Goal:** Answer student/coach questions using the **right book**, and build greps/DB queries that do not collapse distinct content.

Legend:
- **C→2** Companion supplies context that makes 2001 usable / modern
- **2-primary** CEFR 2001 remains the fuller or unique source
- **C-primary** Companion is the operational source (2001 thin, outdated, or silent)
- **Both** Need both layers (philosophy in one, scales in the other)

---

## 1. High-level relationship

| Dimension | CEFR 2001 | Companion 2020 |
|-----------|-----------|----------------|
| Role | Foundational metalanguage + full descriptive scheme + policy/curriculum/assessment chapters | **Update/extension** of illustrative descriptors + modern practice chapters |
| Levels | Defines A1–C2 system | Uses same system; adds Pre-A1 detail, profiles, salient features |
| Mediation | Concept present; limited operationalization | **Full scale system** + strategies + domain examples |
| Online | Not as contemporary mode | **Online conversation + goal-oriented online** scales |
| Phonology | Older phonological control treatment | **Redesigned** phonology / qualitative spoken grid |
| Signing | Minimal | **Full signing competences** chapter + project story |
| Plurilingual/pluricultural | Defined; lightly scaled | **Operational scales** + validation survey |
| Descriptor wording | Original (often “native speaker”) | App 7 documents **substantive wording changes** |

Companion constantly says, in effect: “Keep reading 2001 for X; here is the updated Y.”

---

## 2. Chapter correspondence (practical)

| Need | Prefer first | Then |
|------|--------------|------|
| What is CEFR for? Policy aims, criteria | **2001 Ch 1** | Companion Ch 1–2 framing |
| Action-oriented approach, social agent | **2001 Ch 2** (full) | Companion 2.1–2.2 (practitioner recap) |
| How to *read* a scale | **2001 3.7–3.8** | Companion 2.8–2.9 |
| Branching / plus levels | **2001 3.5** | Companion uses + levels throughout |
| Domains / situations / themes inventory | **2001 Ch 4** (especially 4.1.1) | Companion App 5 *examples* for online/mediation only |
| Reception / production / interaction **can-dos** | Companion Ch 3 (current) | 2001 Ch 4 scales for historical compare; App 7 for wording |
| Mediation **teaching & can-dos** | **Companion Ch 3.4 + App 5** | 2001 only for concept origin |
| Online interaction | **Companion only** | — |
| Plurilingual/pluricultural **can-dos** | **Companion Ch 4** | 2001 Ch 1.3 / 6.1.3 for philosophy |
| Linguistic/sociolinguistic/pragmatic competence can-dos | Companion Ch 5 (current) | 2001 Ch 5 + **App 7** if comparing editions |
| Phonology assessment | **Companion Ch 5 + App 3** | Not 2001 as-is |
| Signing | **Companion Ch 6** | — |
| Curriculum diversification | **2001 Ch 8** + Beacco guides (linked from Companion) | Companion Ch 2.3 / Ch 4 |
| Tasks in teaching | **2001 Ch 7** | Companion assumes task literacy |
| Assessment types / classical theory | **2001 Ch 9** | Companion grids Apps 2–4; later Manual 2009 |
| Self-assessment grid (modern) | **Companion App 2** | 2001 grid is ancestor |
| “What changed since 2001?” | **Companion Ch 1.1 Table 2 + App 7** | — |
| Validation / how new descriptors were built | **Companion App 6** | 2001 appendices for original research |

---

## 3. Companion-as-brilliant-context-for-2001 (C→2)

These Companion passages make 2001 safer and clearer for students/coaches:

1. **Action-oriented recap (2.1–2.2)** — Compresses 2001 Ch 2/7 into coach language without deleting 2001 depth.
2. **Descriptive scheme Figure 1 (2.4)** — Visual “where everything sits”; use before diving into 2001 Ch 4–5.
3. **Profiles (2.7)** — Teaches that a single global level is often wrong; illuminates 2001 branching (3.5).
4. **Mediation framing (2.5, 3.4 prose)** — Shows what 2001 only sketched; prevents misreading 2001 “mediation” as only interpreting.
5. **App 1 salient features** — Narrative level portraits that make 2001 level labels human.
6. **App 7 strike/add** — Required decoder when a quote from 2001 still says “native speaker” but product MD uses inclusive wording.
7. **App 5 domains** — Concrete Personal/Public/Occupational/Educational situations implementing **2001 §4.1.1**.
8. **Pointers to CoE guides** (curriculum, Manual, FREPA) — Operationalize 2001 Ch 8–9 era aims with later instruments.

---

## 4. CEFR 2001 primary / distinct (do not collapse into Companion)

1. **Full action-oriented model detail (Ch 2)** — Competences × activities × domains × tasks; Companion assumes it.
2. **How to read/use scales (3.7–3.9)** — Still the classical literacy chapter.
3. **Ch 4 depth** — Themes, situations, text types, strategy taxonomies beyond the can-do lines.
4. **Ch 6 teaching options** — Method neutrality expanded; Companion is not a methods book.
5. **Ch 7 tasks** — Difficulty factors, real-life vs pedagogic tasks.
6. **Ch 8 curriculum diversification** — Structural curriculum thinking.
7. **Ch 9 assessment typology** — Broader than Companion’s grids.
8. **Original scale wordings** — Needed for exam history / research; always pair with App 7 if using *as current pedagogy*.
9. **Appendices on original empirical work / ALTE** — Provenance of the 2001 descriptor set.

---

## 5. Grep / future-DB conventions

| Query type | Strategy |
|------------|----------|
| “Can-do for B1 interaction” | Companion Ch 3 scales by `db:id` first |
| “What is mediation?” | Companion 2.5 + 3.4 intro prose, then scales |
| “Domain: occupational online” | Companion App 5 goal-oriented / online tables |
| “What does A2 ‘feel like’?” | Companion App 1, then 2001 3.6 / global scale |
| “Design a task at B1” | 2001 Ch 7 + domain 4.1 + Companion can-do |
| “Is this 2001 wording still current?” | Companion App 7 + current scale in Ch 3/5 |
| “Plurilingual classroom” | Companion Ch 4 scales + 2001 1.3 / 8 |
| “Phonology criteria” | Companion only (App 3 / Ch 5) |

**Anti-pattern:** Answering mediation/online/phonology/signing from 2001 alone.  
**Anti-pattern:** Ignoring 2001 Ch 4 domains when building situations (App 5 is only a slice).  
**Anti-pattern:** Mixing editions of a descriptor without App 7.

---

## 6. Explicit cross-reference hotspots (Companion → 2001)

Companion cites **CEFR 2001** ~100+ times. Highest-value targets for linking in DB later:

| Companion focus | Typical 2001 anchors |
|-----------------|----------------------|
| Aims / metalanguage | §§1.1–1.5, 1.4 |
| Action-oriented / tasks | Ch 2, Ch 7 |
| Levels / plus / reading scales | Ch 3 (esp. 3.5–3.8) |
| Domains for App 5 | **§4.1.1** |
| Competences | Ch 5 |
| Plurilingual philosophy | §1.3, §6.1.3.x |
| Curriculum | Ch 8 (+ external guides) |
| Assessment | Ch 9 |

---

## 7. Student-facing explanation (short)

> CEFR 2001 is the **constitution**: how we think about language learning, levels, and the big map.  
> Companion 2020 is the **current statute book of can-dos** for modern classrooms (mediation, online, inclusive wording, signing), plus a translator’s note (App 7) for what changed.  
> Good coaching uses **both**: 2001 for deep design; Companion for today’s descriptors.
