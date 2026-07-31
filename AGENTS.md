# Agent entrypoint

Before changing extraction, formatting, or rotated-table behavior:

1. Read **[`STATUS.md`](STATUS.md)** (single source of truth: done / open / runbook).
2. Read **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** if changing design or contracts.
3. For rotated tables, follow **[`work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md`](work/cefr-companion-2020/metadata/ROTATED_TABLES_AGENT_VISION.md)** (or the active job’s `work/<job-id>/metadata/`).

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

## Versioning + approval (mandatory process)

1. **Iterate freely** — pipeline overwrites live files in `output/<job-id>/`.
2. **After a successful write** of shippable output, regression runs automatically.
3. **If hard checks pass** → append-only snapshot `output/<job-id>/versions/00N/` (never overwrite prior versions).
4. Inspect versions when ready; mark one approved:
   `python -m pipeline.approve --job <id> --version 001`
5. **Production promotion** copies from the **approved version only** (see monorepo `docs/PROMOTION.md`).
6. **Do not** use top-level `staging/pending|approved` or competing `history/` folders.

| Goal | Command |
|------|---------|
| Run regression (+ auto-version on pass) | `python -m pipeline.regression --job cefr-companion-2020` |
| Regression only (no snapshot) | `python -m pipeline.regression --job cefr-companion-2020 --no-version` |
| List / approve version | `python -m pipeline.approve --job cefr-companion-2020 --list` · `--version 001` |

Hooks that auto-run regression + version after writing live output:

- `python -u run_production_extract.py --job <id>`
- `python iterate_format.py --job <id>` (use `--skip-regression` to bypass)
- `python run_pipeline.py --job <id> --step all|merge|figures|postprocess`

## Fast paths

| Goal | Command |
|------|---------|
| Format-only polish | `python iterate_format.py --job cefr-companion-2020` |
| Full rebuild | `python -u run_production_extract.py --job cefr-companion-2020` |
| Rotated PNG prep | `python prepare_rotated_for_grok.py --job cefr-companion-2020` |
| Adjacent gates | `python -m pipeline.adjacent_guard --job cefr-companion-2020` |
| Full regression suite | `python -m pipeline.regression --job cefr-companion-2020` |
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

## Deliverable / jobs

- Companion (active): `output/cefr-companion-2020/CEFR_Companion_Volume.md`
- Snapshots: `output/cefr-companion-2020/versions/00N/` · approval: `APPROVED.json`
- **Draft CEFR family jobs:** see [`STATUS.md` §1a](STATUS.md) (waystage / threshold / 2001 / descriptors xlsx / CN grid)
- Layout: `input|work|output/<job-id>/` + `profiles/` + `pipeline.job_context.load_job`
- CLI: **`--job <id>` required** (no silent default). Paths via `import pipeline.config as cfg`
- Non-PDF / non-markdown modes fail at `bootstrap_job` unless `--force-draft`; use `load_job` for inspection
