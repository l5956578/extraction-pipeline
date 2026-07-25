# Rotated tables — agent vision procedure

**Status of which pages are done:** [`STATUS.md`](../STATUS.md) §6.  
**Architecture:** [`docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) §4.

---

## Authority

Coding-agent **multimodal vision** (read table PNG → write markdown) is the only production-quality extractor for rotated CEFR descriptor scales.

- Geometry / OCR: **fallback only** (incomplete / wrong structure).
- Chat/web Grok: **not** a pipeline step.

---

## Paths

| Role | Location |
|------|----------|
| PNG + JSON + handoff | `metadata/rotated_for_grok/page_{NNN}_{span_group_id}.*` |
| Manifest | `metadata/rotated_for_grok/manifest.json` |
| Vision output | `metadata/rotated_from_grok/page_{NNN}_{span_group_id}.md` |
| Module | `pipeline/extractors/rotated_grok_vision.py` |

---

## Agent checklist (quality bar — not a single skim)

The production standard is the **146–148** process: careful vision read → write → **re-read PNG against `.md`** → fix → optional third pass. Chat/web Grok single-pass failed; batch subagent first-pass alone is **not** enough without verify/fix.

1. `python prepare_rotated_for_grok.py` (if PNGs missing).
2. For each pending slug in the manifest:
   - Open `metadata/rotated_for_grok/{slug}.png` with vision.
   - Transcribe the scale table carefully.
   - Prefer PDF column headers when not receptive/productive.
   - Multi-row levels: blank `Level` cell on second row; descriptors joined with `<br>`.
   - Write **only** the table markdown to `metadata/rotated_from_grok/{slug}.md`.
   - **Re-open the same PNG and the `.md` side by side; fix every discrepancy before leaving the page.**
3. Prefer a second agent/pass whose job is **only** PNG vs `.md` audit (no speed shortcuts).
4. `python finalize_after_grok.py` or re-extract affected chunks + merge + `iterate_format.py`.

---

## Footnotes on rotated pages

Use geometry (`rotated_footnote_zone`), **not** vision.

---

## Coverage

**All 88** rotated inventory pages have vision markdown (including Appendix 5, 191–241).  
Manifest should show `pending: 0`. See STATUS §6.
