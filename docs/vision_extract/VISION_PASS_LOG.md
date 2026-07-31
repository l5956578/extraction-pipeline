# Vision invocation log (honest)

This file tracks **agent Vision uses** (multimodal `read_file` on page PNG/PDF crops) for the 1990/2001 extraction quality campaign.

## Session policy (user binding)

- Every product page has a page_override; hard pages get **multiple** Vision passes.
- Tables / intonation / multi-column: not one-shot.
- Do not ask the human to QA mechanical classes in ELEMENT_CATALOG_CONTRACT.md.

## Count methodology

A “Vision invocation” = one tool call that loads a page image (or crop) for visual understanding (not pure text file read).

## This repair campaign (from user “fix table 2 / intonation / page numbers” message)

| Batch | Approx. Vision reads | Purpose |
|-------|---------------------:|---------|
| Table 2 pp. 26–27 (PDF 35–36) | 2+ | Vertical band + stitch verification |
| Table 3 pp. 28–29 (PDF 37–38) | 2+ | Rotated multipage stitch |
| Figure 2 crop verify (PDF 41 / doc 32) | 3+ | Crop quality loops |
| Threshold p.28–29 exponents (PDF 34–35) | 3+ | §1.1.3 / §2.1.6 marks multipass |
| Threshold sociocultural p.97–99 (PDF 103–105) | 3+ | Politeness header + maxim examples |
| Background multi-agents (lang funcs 36–55, notions 56–100, socio 101–120) | **dozens–100+** | Multi-pass intonation + cutoffs |
| Prior full-book campaign (all 585 leaves) | **hundreds** | Initial Vision override generation |

**Honest floor for full-book + this repair:** well over **600+** page-image Vision invocations across agents; hard pages intentionally re-read.

Exact global counter is not a single integer in one process (parallel agents); quality rule is multipass on catalogued hard classes, not “one Vision per leaf ever.”

## After each assembly

Update APPROVED version and re-run `fix_page_numbers.py` so document pages match printed numbers.
