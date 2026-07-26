# Agent entrypoint

Before changing extraction, formatting, or rotated-table behavior:

1. Read **[`STATUS.md`](STATUS.md)** (single source of truth: done / open / runbook).
2. Read **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** if changing design or contracts.
3. For rotated tables, follow **[`work/metadata/ROTATED_TABLES_AGENT_VISION.md`](work/metadata/ROTATED_TABLES_AGENT_VISION.md)**.

Do **not** treat `docs/archive/**` as current requirements.

## Logging user feedback

The user is not required to speak in “bug tickets.” When they write logs, chat notes, or screenshots:

- **Log everything** they give you (product intent, process, validation expectations, design direction, frustration about regressions, agent-in-the-loop requests — not only code defects).
- Do **not** ignore or discard content because it is non-technical or does not fit a bug template.
- Put defects in the issue catalog; put requirements/policy/design in **STATUS §5a (User voice)** and the matching “User voice” section of `docs/ISSUES_CHAPTER2_DIAGNOSIS.md` (or successor logs).
- See **STATUS.md → Standing rule — log everything the user writes**.

## Adjacent-element protection (mandatory)

**C2-ADJ:** Fixing one element must not trash neighbors (log 04: garbage under PNG, glued `Page **N**`, dropped next header, duplicate titles).

**Plan + status log (expected vs coded vs remains):**  
[`docs/ADJACENT_ELEMENT_PROTECTION.md`](docs/ADJACENT_ELEMENT_PROTECTION.md)  
**Full approved plan:** [`docs/plans/2026-07-17_adjacent_element_protection_plan.md`](docs/plans/2026-07-17_adjacent_element_protection_plan.md)

Before claiming a figure/callout/table/footnote fix:

1. Run `python -m pipeline.adjacent_guard` (or full `python -m pipeline.contract_validators`).
2. Manually check **before and after** the changed element on that page (and page ±1).
3. Prefer **replace** semantics: correct representation **replaces** the old one; do not layer PNG on top of leftover figure-as-prose.
4. Design notes: `docs/CONTRACTS.md` § exclusive regions / replace semantics.

## Fast paths

| Goal | Command |
|------|---------|
| Format-only polish | `python iterate_format.py` |
| Full rebuild | `python -u run_production_extract.py` (after inventory/vision as needed) |
| Rotated PNG prep | `python prepare_rotated_for_grok.py` |
| Adjacent gates | `python -m pipeline.adjacent_guard` |
| Extraction visual QA loop | Load skill `/extraction-qa-vision` (`.grok/skills/extraction-qa-vision/`) |
| Match prior extraction fix | Read [`docs/RESOLVED_EXTRACTION_ISSUES.md`](docs/RESOLVED_EXTRACTION_ISSUES.md) + [`docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md`](docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md) |

## Vision QA — when the user points at a log

If the user files `user debug/log*.md` (or chat) **and** asks for Vision QA / the extraction-qa-vision skill:

- **Every page they name is mandatory** for baseline full-page snapshot + Vision pass/fail.
- **Do not skip, cancel, or “P3 later”** a named page. Prioritize only *after* all named pages have baseline YAML.
- Inventory rebuild is **not** a substitute for fixing id/title bugs (garbled slugs often **survive** rebuild — fix emit/`title_fix`/alias, do not claim rebuild alone).
- Page running headers/footers are in scope (full-page PNG must be compared to MD chrome).

## Resolved-issue matching (mandatory)

When an extraction bug is reported (user log, chat, or Vision fail):

1. **Investigate first** (MD slice + PDF/snapshot as needed) — **before** asking the user anything.
2. Open **[`docs/RESOLVED_EXTRACTION_ISSUES.md`](docs/RESOLVED_EXTRACTION_ISSUES.md)** and follow **[`docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md`](docs/RESOLVED_ISSUE_MATCH_PROTOCOL.md)**.
3. **CLEAR** match → **auto-apply** the documented re-apply steps; report what you did; **do not ask**.
4. **AMBIGUOUS** only → short comparison (≤5 bullets) and ask once.
5. **NOVEL** → implement the fix, then **append** a new RIE entry before claiming done.

Hard rule: **prefer action over questions.** The user is not the agent’s memory or decision router.

| Doc | Role |
|-----|------|
| `STATUS.md` | Open / partial / fixed **status** |
| `docs/RESOLVED_EXTRACTION_ISSUES.md` | **Re-apply** playbook for known-good fixes |

## Deliverable

`output/CEFR_Companion_Volume.md`
