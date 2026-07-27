# Vision QA output contract

The Vision QA agent is a **pure observer**. It compares:

1. Full-page PNG (`work/cefr-companion-2020/metadata/qa_snapshots/page_NNN.png`)
2. Markdown slice for that page
3. Rules in `extraction-invariants.md`

It returns **only** structured YAML. It must **never** suggest code, rewrite Markdown, or propose design.

---

## Schema

```yaml
status: pass | fail
failures:
  - page: <int>                    # PDF page number (1-based)
    element: callout | prose-block | table | figure | figure-caption | footnote | page-caption | other
    severity: critical | major | minor
    visual_observation: "<what the PNG / PDF layout shows>"
    md_observation: "<what the Markdown currently shows or lacks>"
    rule_violated: "<short-id-from-extraction-invariants>"
```

### Field rules

| Field | Rules |
|-------|--------|
| `status` | `pass` only if **no** failures. If any failure, `status` must be `fail`. |
| `failures` | Empty list `[]` when pass. One or more objects when fail. |
| `page` | Integer page under review (must match the snapshot page). |
| `element` | One of the enum values only — no new types. |
| `severity` | `critical` \| `major` \| `minor` per invariants severity guidance. |
| `visual_observation` | Factual description of the PDF page image. No fix instructions. |
| `md_observation` | Factual description of the MD slice. No proposed patches. |
| `rule_violated` | Short id from `extraction-invariants.md` (e.g. `callout-placement-inline-fullwidth-neighbors`). If none fit, use closest + honest note in observations; prefer existing ids. |

### Forbidden in the YAML body

- Code snippets meant as patches
- “Change X to Y in pipeline/…”
- Rewritten Markdown blocks as “the fix”
- Architecture proposals

Observations may quote short MD fragments **as evidence** (what is present), not as replacement content.

---

## Example: pass

```yaml
status: pass
failures: []
```

---

## Example: single failure

```yaml
status: fail
failures:
  - page: 41
    element: callout
    severity: major
    visual_observation: >
      Mid-page blue feature box sits between full-width prose paragraphs;
      no multi-column region immediately before or after the box.
    md_observation: >
      Callout blockquote appears only at end of body, after all prose and
      before footnotes; mid-flow position from the PDF is not reflected.
    rule_violated: callout-placement-inline-fullwidth-neighbors
```

---

## Example: multi-failure fail

```yaml
status: fail
failures:
  - page: 38
    element: figure
    severity: critical
    visual_observation: >
      Radar/profile chart occupies the upper figure area; surrounding body
      prose continues below without axis label lists under the chart.
    md_observation: >
      After the figure PNG, lines list reception/production scale names and
      axis fragments that are not body prose.
    rule_violated: no-figure-soup
  - page: 38
    element: table
    severity: major
    visual_observation: >
      Small level table is a real multi-column grid in the PDF.
    md_observation: >
      Table is emitted as a single prose paragraph; no markdown pipe table
      and no blank line after the db:id comment block.
    rule_violated: table-blank-after-header
  - page: 38
    element: prose-block
    severity: minor
    visual_observation: >
      Section heading 2.7 appears on its own line above the following paragraph.
    md_observation: >
      Heading text is still glued to the end of the previous paragraph on one line.
    rule_violated: prose-no-heading-glue
```

---

## Coding agent handling

- On `status: pass` → run adjacent + contract gates; write post-loop report; stop loop for that issue.
- On `status: fail` → fix only; re-run QA with **same** snapshot file; do not ask Vision for how to code.
- After **4** failed attempts → escalate to user with full context (see SKILL.md post-loop report).
