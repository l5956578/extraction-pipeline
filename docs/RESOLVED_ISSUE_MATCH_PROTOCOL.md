# Resolved-issue match protocol

**Binding for every coding agent** when an extraction bug is reported (user log, chat, or extraction-qa-vision fail).

**Playbook (re-apply memory):** [`RESOLVED_EXTRACTION_ISSUES.md`](RESOLVED_EXTRACTION_ISSUES.md)  
**Open backlog SoT:** [`../STATUS.md`](../STATUS.md) — do not duplicate open work here.  
**Entrypoint:** [`../AGENTS.md`](../AGENTS.md)

---

## Hard rule

**Prefer action over questions.** Investigate first. Never use the user as memory or decision router for obvious re-applies. Ask **only** when the case is truly **AMBIGUOUS**.

---

## Control flow

```
New bug (user log | Vision YAML fail | chat)
  → INVESTIGATE (mandatory, before any ask)
  → OPEN docs/RESOLVED_EXTRACTION_ISSUES.md
  → MATCH candidates (Class / rule_ids / symptoms)
  → Verdict:
       CLEAR      → auto-apply Re-apply steps → re-QA if visual → gates → report
                    (do NOT ask)
       AMBIGUOUS  → ≤5-bullet comparison → ask once
       NOVEL      → implement → Vision QA if visual → gates → APPEND RIE entry
```

---

## Steps (mandatory order)

### 1. Parse the bug

Record:

- Page number(s) and element class (callout, figure, table, page chrome, footnote, id, …)
- Symptoms (what MD shows vs PDF / user description)
- Source: log name, Vision `rule_violated`, or chat

### 2. Investigate (before asking)

Do **all** that apply — do not skip to “what do you want me to do?”:

| Check | How |
|-------|-----|
| MD slice | Read page body from `output/CEFR_Companion_Volume.md` (markers at end of page; same slice rules as Vision skill / `adjacent_guard._page_body`) |
| Visual | If layout/chrome/placement: full-page snapshot `work/metadata/qa_snapshots/page_NNN.png` or PDF page |
| Inventory / RO | If placement or type wrong: page’s `reading_order` in the chunk inventory |
| Prior fix | Open the ledger; note matching RIE ids and which chunks/pages they already covered |

### 3. Match the ledger

Open [`RESOLVED_EXTRACTION_ISSUES.md`](RESOLVED_EXTRACTION_ISSUES.md):

1. Scan the **index** (Class / rule-id → RIE-id).
2. Read full candidate entries (Match criteria, Ambiguous if, Do not, Re-apply steps).
3. Compare **this** page/instance to **Chunks/pages verified** and Match criteria.

Use invariant **rule-ids** from  
`.grok/skills/extraction-qa-vision/references/extraction-invariants.md` when Vision YAML is present.

### 4. Decide CLEAR / AMBIGUOUS / NOVEL

| Verdict | When |
|---------|------|
| **CLEAR** | Same defect class / same `rule_violated` family; same fix surface; page matches **Match criteria**; no **Do not** triggered; re-apply does not require rewriting `rotated_from_grok` bodies unless the entry says alias-only. |
| **AMBIGUOUS** | Same symptom class but different multi-col vs full-width, different element type, fix would touch rotated vision bodies, two RIE entries conflict, or only a full-book rebuild path is documented when a chunk-local path might exist. |
| **NOVEL** | No credible ledger match. |

### 5. Act

| Verdict | Action |
|---------|--------|
| **CLEAR** | Run the entry’s **Re-apply steps** (prefer `python iterate_format.py` or single-chunk re-extract over full book). Do **not** invent a parallel one-off patch when the ledger path applies. |
| **AMBIGUOUS** | Present ≤5 bullets: prior fix, prior pages, current difference, proposed action, risk. Ask **once**. Do not dump the whole STATUS table. |
| **NOVEL** | Implement the smallest correct fix; respect C2-ADJ / replace semantics / contracts. |

### 6. Verify

After any MD or pipeline change:

```bash
python -m pipeline.adjacent_guard
python -m pipeline.contract_validators
```

If the defect is visual or the user directed Vision QA:

- Re-slice MD; re-run Vision critic (same full-page snapshot unless `--force` is justified).
- Do **not** skip user-named pages.

### 7. Report (visible investigation)

Always emit a short note (chat and/or Vision post-loop report):

```markdown
## Investigation
- Pages/elements: …
- MD/PDF check: …
- Ledger candidates: RIE-… / none
- Verdict: CLEAR | AMBIGUOUS | NOVEL
- Action taken: auto-applied RIE-… | asked user | novel fix …
```

Vision skill reports must also include:

- `Matched: RIE-xxx | none`
- `Action: auto-applied | asked user | novel`

### 8. Append on novel success

After a **NOVEL** fix is evidence-backed (gates green; Vision pass if visual):

1. Append a new `RIE-NNN` entry to `RESOLVED_EXTRACTION_ISSUES.md` using the template.
2. Update the top index table.
3. Only then claim done / update STATUS if status claims change.

---

## Anti-patterns (do not)

- Ask “should I apply the same fix as p.41?” when the case is **CLEAR**.
- Use the user as router for chunk numbers, file paths, or “did we already fix this?”.
- Claim full-book re-extract or **inventory rebuild alone** fixed a class without code proof (see **RIE-005** / `L07-ID-REBUILD`).
- Skip user-named Vision QA pages to “save time” while matching.
- Invent a second open-issue database parallel to `STATUS.md`.
- Wipe or bulk-rewrite `work/metadata/rotated_from_grok/*.md` (88 vision tables) unless an entry explicitly allows alias-only touch.
- Layer a second representation without replace semantics (C2-ADJ).

---

## Relationship to other docs

| Doc | Role |
|-----|------|
| `STATUS.md` | Open / partial / fixed **status** |
| `RESOLVED_EXTRACTION_ISSUES.md` | **Re-apply** playbook for fixed classes |
| `ADJACENT_ELEMENT_PROTECTION.md` | C2-ADJ package history (cross-link; do not fork) |
| `extraction-qa-vision` skill | Vision loop; coding agent runs this protocol **before each fix attempt** |
| `extraction-invariants.md` | Vocabulary for Class / `rule_violated` |
