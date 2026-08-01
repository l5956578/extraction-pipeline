# Intonation-bearing pages — high-precision multipass required

**Protocol:** `INTONATION_NOTATION.md` multipass + word catalog (see `INTONATION_WORD_CATALOG_LEAF034.md` as gold template).  
**PDF leaf → document page:** Threshold/Waystage `doc = pdf − 6` (Arabic p.1 = PDF leaf 7).  
**Per-page pass counts:** [`INTONATION_PASS_INVENTORY.md`](INTONATION_PASS_INVENTORY.md) (Threshold + Waystage).

Do **not** limit work to Chapter 5. Chapters with exponent **examples** that carry nuclear/secondary marks:

---

## Threshold 1990

| Doc pages | PDF leaves | Chapter / section |
|-----------|------------|-------------------|
| **27–47** | 33–53 | **5** Language functions (exponents) |
| **48–58** | 54–64 | **6** General notions (marked examples) |
| **59–81** | 65–87 | **7** Specific notions (examples + lists) |
| **82–87** | 88–93 | **8** Verbal exchange patterns (dialogues) |
| **94–102** | 100–108 | **11** Sociocultural (politeness exponents) |
| **103–106** | 109–112 | **12** Compensation strategies (exponents) |
| **115–124** | 121–130 | **Appendix A** Pronunciation & intonation (legend + uses) |

Optional verify (often false positives from apostrophes): grammar appendix ~128–156.

**Primary continuous band for swarm:** PDF **34–64**, **66–90**, **104–112**, **124–130**.

---

## Waystage 1990

| Doc pages | PDF leaves | Chapter / section |
|-----------|------------|-------------------|
| **15–21** | 21–27 | **3** Language functions |
| **22–29** | 28–35 | **4** General notions |
| **30–41** | 36–47 | **5** Themes and specific notions |
| **46–49** | 52–55 | **8** Sociocultural (if marked) |
| **50–55** | 56–61 | **9** Verbal exchange patterns |
| **56–59** | 62–65 | **10** Compensation |
| **68–74** | 74–80 | **Appendix A** Pronunciation & intonation |

**Primary continuous band for swarm:** PDF **22–35**, **38–47**, **56–65**, **77–80**.

---

## CEFR EN 2001

No van Ek five-tone exponent system — **out of scope** for this pass.

---

## Done criteria (per page)

1. Zoom Vision of every example line  
2. Word-level mark catalog before MD write  
3. Re-Vision MD vs crop  
4. No ASCII `'` as tone; no `ˌ` for low fall; `·` vs `ˎ` distinguished  

---

## Status (v006 — 2026-07-31) — **COMPLETE**

| Book | Band coverage | Method | Product |
|------|---------------|--------|---------|
| **Threshold** | Ch 5–8, 11–12, App A (PDF 34–64, 66–90, 104–112, 124–130) | PDF native convert + Vision multipass overrides (line-merge) + gold lock | `versions/006` |
| **Waystage** | Ch 3–5, 9–10, App A (PDF 22–35, 38–47, 56–65, 77–80) | Image PDF Vision multipass (38 pages) + OCR→Unicode | `versions/006` |
| **CEFR 2001** | — | out of scope | prior |

**Vision subagents finished:** THR 34–45, 46–56, 57–75, 34–64, 66–90, 104–130; Waystage full primary.

**Run pipeline:** `full_intonation_pass.py` → `convert_md_ocr_marks.py` → `merge_override_tones_into_md.py` (protected skeletons) → `restore_gold_113_134.py` → `force_contrastive_and_midword.py` → `audit_intonation_md.py`.

**Do not** whole-page restitch overrides over product without audit. **Do not** letter-skeleton-merge protected pairs (bedroom/train/isn’t/did). **Do not** double-run `fix_page_numbers.py` (idempotent).  
