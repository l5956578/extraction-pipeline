# Intonation pass inventory — Threshold & Waystage 1990

**Generated:** 2026-07-31  
**Purpose:** Per-page list of quality passes applied for intonation (and full-book Vision baseline).  
**Related:** `INTONATION_PAGE_INDEX.md`, `VISION_PASS_LOG.md`, `EXTRACTION_STATUS_1990_2001.md`  

## What counts as a “pass”

| Pass type | Meaning |
|-----------|---------|
| **full-book Vision (v004)** | Initial Vision page_override for every PDF leaf |
| **native PDF mark convert** | Threshold Paper-Capture text layer → Unicode tones (mechanical) |
| **Vision MP: …** | Dedicated high-precision intonation multipass (zoom/word-catalog rewrite) |
| **word-catalog file** | Per-leaf catalog under `intonation_hires/catalogs/` |
| **hi-res crop multipass** | 4× full + L/R + bands prepared for Vision |
| **product MD tone merge/OCR convert** | Product MD mark repair (not freehand invent) |
| **gold force-restore** | Section-aware lock for 1.1.3–1.3.4 (LF vs contrastive) |

**Note:** Parallel agents rewrote some leaves more than once. Counts include **distinct documented campaigns** that targeted that leaf (not every intermediate crop tool call). Re-Vision *within* a campaign is folded into that campaign’s single Vision MP line.

**Document page formula:** `doc = PDF leaf − 6` (Arabic p.1 = leaf 7).

---

## Threshold 1990

**Product:** `output/cefr-threshold-1990/Threshold_1990.md` (APPROVED v006)  
**Overrides:** `work/cefr-threshold-1990/page_overrides/`

### Summary by band

| Band | PDF leaves | Doc pages | Typical passes/page |
|------|------------|-----------|---------------------:|
| Ch.5 Language functions | 34–53 | 28–47 | 5–6 |
| Ch.6 General notions | 54–64 | 48–58 | 5–6 |
| Ch.7 Specific notions | 66–87 | 60–81 | 4–5 |
| Ch.8 Verbal exchange | 88–90 | 82–84 | 4 |
| Ch.11 Sociocultural | 104–108 | 98–102 | 4 |
| Ch.12 Compensation | 109–112 | 103–106 | 4 |
| Appendix A | 124–130 | 118–124 | 4 |
| Grammar appendix (secondary) | 134–162 | 128–156 | 2–3 |
| Full book (non-intonation pages) | other | — | 1 (full-book Vision only) |

### Per-page detail (intonation-targeted leaves)

| PDF leaf | Doc p. | Chapter / band | Passes (total) | Pass breakdown | Unicode tones (product page) | Class |
|---------:|-------:|----------------|---------------:|----------------|-----------------------------:|-------|
| 14 | 8 | front/intro (hit) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 5 | full-book / secondary |
| 19 | 13 | front/intro (hit) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 13 | full-book / secondary |
| 34 | 28 | 5 Language functions | **7** | full-book Vision (v004); native PDF mark convert; gold force-restore product MD; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; Vision MP: leaf-34 gold catalog/restore; product MD tone merge/OCR convert | 29 | GOLD template page |
| 35 | 29 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 75 | multipass |
| 36 | 30 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 92 | multipass |
| 37 | 31 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 81 | multipass |
| 38 | 32 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 73 | multipass |
| 39 | 33 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 75 | multipass |
| 40 | 34 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 88 | multipass |
| 41 | 35 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 87 | multipass |
| 42 | 36 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 106 | multipass |
| 43 | 37 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 97 | multipass |
| 44 | 38 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 95 | multipass |
| 45 | 39 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 34–45; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 85 | multipass |
| 46 | 40 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 84 | multipass |
| 47 | 41 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 84 | multipass |
| 48 | 42 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 77 | multipass |
| 49 | 43 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 80 | multipass |
| 50 | 44 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 77 | multipass |
| 51 | 45 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 66 | multipass |
| 52 | 46 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 79 | multipass |
| 53 | 47 | 5 Language functions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 11 | multipass |
| 54 | 48 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 3 | multipass |
| 55 | 49 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 63 | multipass |
| 56 | 50 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 46–56; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 60 | multipass |
| 57 | 51 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 61 | multipass |
| 58 | 52 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 86 | multipass |
| 59 | 53 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 65 | multipass |
| 60 | 54 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 25 | multipass |
| 61 | 55 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 45 | multipass |
| 62 | 56 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 75 | multipass |
| 63 | 57 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 52 | multipass |
| 64 | 58 | 6 General notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch5–6 34–64; product MD tone merge/OCR convert | 31 | multipass |
| 65 | 59 | 7 Specific notions | **3** | full-book Vision (v004); Vision MP: gold 57–75 (scan); product MD tone merge/OCR convert | 0 | multipass |
| 66 | 60 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 20 | multipass |
| 67 | 61 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 8 | multipass |
| 68 | 62 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 20 | multipass |
| 69 | 63 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 39 | multipass |
| 70 | 64 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 25 | multipass |
| 71 | 65 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 26 | multipass |
| 72 | 66 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 15 | multipass |
| 73 | 67 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 35 | multipass |
| 74 | 68 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 42 | multipass |
| 75 | 69 | 7 Specific notions | **5** | full-book Vision (v004); native PDF mark convert; Vision MP: gold 57–75; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 33 | multipass |
| 76 | 70 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 71 | multipass |
| 77 | 71 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 70 | multipass |
| 78 | 72 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 73 | multipass |
| 79 | 73 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 8 | multipass |
| 80 | 74 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 54 | multipass |
| 81 | 75 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 78 | multipass |
| 82 | 76 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 51 | multipass |
| 83 | 77 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 12 | multipass |
| 84 | 78 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 58 | multipass |
| 85 | 79 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 35 | multipass |
| 86 | 80 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 20 | multipass |
| 87 | 81 | 7 Specific notions | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 9 | multipass |
| 88 | 82 | 8 Verbal exchange | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 38 | multipass |
| 89 | 83 | 8 Verbal exchange | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 7 | multipass |
| 90 | 84 | 8 Verbal exchange | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: ch7–8 66–90; product MD tone merge/OCR convert | 0 | multipass |
| 91 | 85 | 8 Verbal exchange | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 92 | 86 | 8 Verbal exchange | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 93 | 87 | 8 Verbal exchange | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 94 | 88 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 95 | 89 | misc hit | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 28 | multipass |
| 96 | 90 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 2 | multipass |
| 97 | 91 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 98 | 92 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 99 | 93 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 100 | 94 | 11 Sociocultural | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 101 | 95 | 11 Sociocultural | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 102 | 96 | 11 Sociocultural | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 103 | 97 | 11 Sociocultural | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 104 | 98 | 11 Sociocultural | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 45 | multipass |
| 105 | 99 | 11 Sociocultural | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 71 | multipass |
| 106 | 100 | 11 Sociocultural | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 71 | multipass |
| 107 | 101 | 11 Sociocultural | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 77 | multipass |
| 108 | 102 | 11 Sociocultural | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 46 | multipass |
| 109 | 103 | 12 Compensation | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 0 | multipass |
| 110 | 104 | 12 Compensation | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 0 | multipass |
| 111 | 105 | 12 Compensation | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 27 | multipass |
| 112 | 106 | 12 Compensation | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 32 | multipass |
| 113 | 107 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 114 | 108 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 115 | 109 | misc hit | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 15 | multipass |
| 116 | 110 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 117 | 111 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 118 | 112 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 119 | 113 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 120 | 114 | other | **2** | full-book Vision (v004); product MD tone merge/OCR convert | 0 | multipass |
| 124 | 118 | Appendix A | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 24 | multipass |
| 125 | 119 | Appendix A | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 67 | multipass |
| 126 | 120 | Appendix A | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 56 | multipass |
| 127 | 121 | Appendix A | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 57 | multipass |
| 128 | 122 | Appendix A | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 62 | multipass |
| 129 | 123 | Appendix A | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 28 | multipass |
| 130 | 124 | Appendix A | **4** | full-book Vision (v004); native PDF mark convert; Vision MP: socio+AppA 104–130; product MD tone merge/OCR convert | 19 | multipass |
| 134 | 128 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 7 | full-book / secondary |
| 135 | 129 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 19 | full-book / secondary |
| 136 | 130 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 18 | full-book / secondary |
| 137 | 131 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 0 | full-book / secondary |
| 138 | 132 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 3 | full-book / secondary |
| 139 | 133 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 0 | full-book / secondary |
| 140 | 134 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 0 | full-book / secondary |
| 141 | 135 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 0 | full-book / secondary |
| 142 | 136 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 15 | full-book / secondary |
| 143 | 137 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 32 | full-book / secondary |
| 144 | 138 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 22 | full-book / secondary |
| 145 | 139 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 19 | full-book / secondary |
| 146 | 140 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 16 | full-book / secondary |
| 147 | 141 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 16 | full-book / secondary |
| 148 | 142 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 27 | full-book / secondary |
| 149 | 143 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 25 | full-book / secondary |
| 150 | 144 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 26 | full-book / secondary |
| 151 | 145 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 13 | full-book / secondary |
| 152 | 146 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 27 | full-book / secondary |
| 153 | 147 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 8 | full-book / secondary |
| 154 | 148 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 20 | full-book / secondary |
| 155 | 149 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 20 | full-book / secondary |
| 156 | 150 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 20 | full-book / secondary |
| 157 | 151 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 21 | full-book / secondary |
| 158 | 152 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 16 | full-book / secondary |
| 159 | 153 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 21 | full-book / secondary |
| 160 | 154 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 15 | full-book / secondary |
| 161 | 155 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 23 | full-book / secondary |
| 162 | 156 | grammar appendix (secondary) | **3** | full-book Vision (v004); native PDF mark convert; product MD tone merge/OCR convert | 9 | full-book / secondary |

**Threshold intonation-targeted leaves listed:** 125  
**Sum of pass-counts (listed leaves):** 471  
**Full book also has 1× full-book Vision on remaining leaves** (192 total overrides).

---

## Waystage 1990

**Product:** `output/cefr-waystage-1990/Waystage_1990.md` (APPROVED v006)  
**Overrides:** `work/cefr-waystage-1990/page_overrides/`  
**Note:** Image PDF (no text layer) — no native PDF convert pass.

### Summary by band

| Band | PDF leaves | Doc pages | Typical passes/page |
|------|------------|-----------|---------------------:|
| Ch.3 Language functions | 22–27 | 16–21 | 5–6 |
| Ch.4 General notions | 28–35 | 22–29 | 5 |
| Ch.5 Themes / specific notions | 38–47 | 32–41 | 5 |
| Ch.9 Verbal exchange | 56–61 | 50–55 | 5 |
| Ch.10 Compensation | 62–65 | 56–59 | 5 |
| Appendix A | 77–80 | 71–74 | 5 |
| Grammar appendix (secondary) | 82–100 | 76–94 | 2 |
| Full book (other pages) | other | — | 1 (full-book Vision only) |

### Per-page detail (intonation-targeted leaves)

| PDF leaf | Doc p. | Chapter / band | Passes (total) | Pass breakdown | Unicode tones (product page) | Class |
|---------:|-------:|----------------|---------------:|----------------|-----------------------------:|-------|
| 22 | 16 | 3 Language functions | **6** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix; gold force-restore contrastive bedroom | 31 | primary multipass |
| 23 | 17 | 3 Language functions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 85 | primary multipass |
| 24 | 18 | 3 Language functions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 18 | primary multipass |
| 25 | 19 | 3 Language functions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 54 | primary multipass |
| 26 | 20 | 3 Language functions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 50 | primary multipass |
| 27 | 21 | 3 Language functions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 62 | primary multipass |
| 28 | 22 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 3 | primary multipass |
| 29 | 23 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 39 | primary multipass |
| 30 | 24 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 43 | primary multipass |
| 31 | 25 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 40 | primary multipass |
| 32 | 26 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 32 | primary multipass |
| 33 | 27 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 35 | primary multipass |
| 34 | 28 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 43 | primary multipass |
| 35 | 29 | 4 General notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 33 | primary multipass |
| 38 | 32 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 10 | primary multipass |
| 39 | 33 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 16 | primary multipass |
| 40 | 34 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 21 | primary multipass |
| 41 | 35 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 14 | primary multipass |
| 42 | 36 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 43 | primary multipass |
| 43 | 37 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 27 | primary multipass |
| 44 | 38 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 19 | primary multipass |
| 45 | 39 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 13 | primary multipass |
| 46 | 40 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 17 | primary multipass |
| 47 | 41 | 5 Themes / specific notions | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 9 | primary multipass |
| 52 | 46 | 8 Sociocultural | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 0 | secondary/residual |
| 53 | 47 | 8 Sociocultural | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 0 | secondary/residual |
| 54 | 48 | 8 Sociocultural | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 0 | secondary/residual |
| 55 | 49 | 8 Sociocultural | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 0 | secondary/residual |
| 56 | 50 | 9 Verbal exchange | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 20 | primary multipass |
| 57 | 51 | 9 Verbal exchange | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 4 | primary multipass |
| 58 | 52 | 9 Verbal exchange | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 59 | 53 | 9 Verbal exchange | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 60 | 54 | 9 Verbal exchange | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 61 | 55 | 9 Verbal exchange | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 62 | 56 | 10 Compensation | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 63 | 57 | 10 Compensation | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 64 | 58 | 10 Compensation | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 24 | primary multipass |
| 65 | 59 | 10 Compensation | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 27 | primary multipass |
| 77 | 71 | Appendix A | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 118 | primary multipass |
| 78 | 72 | Appendix A | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 79 | 73 | Appendix A | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 80 | 74 | Appendix A | **5** | full-book Vision (v004); Vision MP: Waystage primary bands; word-catalog file written; hi-res crop multipass (4x/bands); product MD OCR mark convert + gold fix | 0 | primary multipass |
| 82 | 76 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 60 | secondary/residual |
| 83 | 77 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 20 | secondary/residual |
| 84 | 78 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 16 | secondary/residual |
| 85 | 79 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 0 | secondary/residual |
| 86 | 80 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 0 | secondary/residual |
| 87 | 81 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 16 | secondary/residual |
| 88 | 82 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 10 | secondary/residual |
| 89 | 83 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 67 | secondary/residual |
| 90 | 84 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 72 | secondary/residual |
| 91 | 85 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 93 | secondary/residual |
| 92 | 86 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 66 | secondary/residual |
| 93 | 87 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 69 | secondary/residual |
| 94 | 88 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 72 | secondary/residual |
| 95 | 89 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 59 | secondary/residual |
| 96 | 90 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 57 | secondary/residual |
| 97 | 91 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 57 | secondary/residual |
| 98 | 92 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 88 | secondary/residual |
| 99 | 93 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 89 | secondary/residual |
| 100 | 94 | grammar appendix (secondary) | **2** | full-book Vision (v004); product MD OCR mark convert (residual) | 55 | secondary/residual |

**Waystage intonation-targeted leaves listed:** 61  
**Sum of pass-counts (listed leaves):** 237  
**Full book also has 1× full-book Vision on remaining leaves** (120 total overrides).

---

## Pass-count histogram (listed leaves only)

### Threshold
- **2 passes:** 19 pages
- **3 passes:** 34 pages
- **4 passes:** 31 pages
- **5 passes:** 40 pages
- **7 passes:** 1 pages

### Waystage
- **2 passes:** 23 pages
- **5 passes:** 37 pages
- **6 passes:** 1 pages

## Highest-effort pages (by pass total)

### Threshold (top)
- leaf **34** (doc p.28): **7** passes — 5 Language functions
- leaf **35** (doc p.29): **5** passes — 5 Language functions
- leaf **36** (doc p.30): **5** passes — 5 Language functions
- leaf **37** (doc p.31): **5** passes — 5 Language functions
- leaf **38** (doc p.32): **5** passes — 5 Language functions
- leaf **39** (doc p.33): **5** passes — 5 Language functions
- leaf **40** (doc p.34): **5** passes — 5 Language functions
- leaf **41** (doc p.35): **5** passes — 5 Language functions
- leaf **42** (doc p.36): **5** passes — 5 Language functions
- leaf **43** (doc p.37): **5** passes — 5 Language functions
- leaf **44** (doc p.38): **5** passes — 5 Language functions
- leaf **45** (doc p.39): **5** passes — 5 Language functions
- leaf **46** (doc p.40): **5** passes — 5 Language functions
- leaf **47** (doc p.41): **5** passes — 5 Language functions
- leaf **48** (doc p.42): **5** passes — 5 Language functions

### Waystage (top)
- leaf **22** (doc p.16): **6** passes — 3 Language functions
- leaf **23** (doc p.17): **5** passes — 3 Language functions
- leaf **24** (doc p.18): **5** passes — 3 Language functions
- leaf **25** (doc p.19): **5** passes — 3 Language functions
- leaf **26** (doc p.20): **5** passes — 3 Language functions
- leaf **27** (doc p.21): **5** passes — 3 Language functions
- leaf **28** (doc p.22): **5** passes — 4 General notions
- leaf **29** (doc p.23): **5** passes — 4 General notions
- leaf **30** (doc p.24): **5** passes — 4 General notions
- leaf **31** (doc p.25): **5** passes — 4 General notions
- leaf **32** (doc p.26): **5** passes — 4 General notions
- leaf **33** (doc p.27): **5** passes — 4 General notions
- leaf **34** (doc p.28): **5** passes — 4 General notions
- leaf **35** (doc p.29): **5** passes — 4 General notions
- leaf **38** (doc p.32): **5** passes — 5 Themes / specific notions

---

## Campaign map (source of Vision MP lines)

| Campaign | Book | Leaves | Agent / method |
|----------|------|--------|----------------|
| Full-book Vision v004 | both | all | prior full-book override generation |
| Native PDF convert | Threshold | primary+secondary | `full_intonation_pass.py` |
| Gold multipass 34–45 | Threshold | 34–45 | subagent gold Vision |
| Gold multipass 46–56 | Threshold | 46–56 | subagent gold Vision |
| Gold multipass 57–75 | Threshold | 57–75 | subagent gold Vision |
| Ch5–6 multipass 34–64 | Threshold | 34–64 | subagent Vision |
| Ch7–8 multipass 66–90 | Threshold | 66–90 | subagent Vision |
| Socio+AppA 104–130 | Threshold | 104–112, 124–130 | subagent Vision |
| Leaf-34 gold catalog | Threshold | 34 | `INTONATION_WORD_CATALOG_LEAF034.md` + restore |
| Waystage primary multipass | Waystage | 22–35, 38–47, 56–65, 77–80 | subagent Vision (38 pages) |
| OCR→Unicode product | Waystage (+THR residual) | product MD | `convert_md_ocr_marks.py` |

*End of inventory.*
