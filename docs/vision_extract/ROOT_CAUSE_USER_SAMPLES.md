# Root cause — user random samples (2026-08-01)

## Samples flagged
2.2.3 wrong/there · 2.2.4.1 horrible · 2.2.5.2 will · 3.1.2 dance · 3.1.3 walk · 3.1.5 train · 4.2.1 Hallo · 5.4.1

## Why these were still wrong after “residual_risk = 0”

**Not a mystery. Not bad luck.**

1. **Coverage theater.** `line_zoom` / residual_risk=0 was achieved by generating line/strip PNGs and rewriting the coverage table — **not** by Vision-checking every glyph on every example against product MD. Reviewers even noted `_finalize_line_zoom.py` force-sets status. That is **status laundering**, not quality.

2. **Default ˈ for every PDF `'`.** Paper Capture uses one character for head / high fall / high rise. The pipeline defaulted to **head ˈ**. On many **nuclear** content words (wrong, horrible, will, train, walk, Hal…) the book has **high fall ˋ**. Random samples hit exactly that systematic error.

3. **Default ˎ for every PDF `,`.** Comma can be low fall **or** (when OCR confuses mid-dot) mid `·`. Hallo `Hal,lo` → we wrote `Halˎlo`; 10× PNG is **mid on lo** → `Hal·lo` with HF on Hal.

4. **No adversarial random sample gate.** Residual assertions only protect a **tiny gold set** (bedroom/train/Did/Please). Everything else could be wrong and still “PASS.”

## Per-item (10× PNG)

| Item | Was (MD) | PNG truth | Failure mode |
|------|----------|-----------|--------------|
| 2.2.3 | ˈwrong (ˎthere) | **ˋ**wrong (ˎthere) | nuclear ˈ not ˋ |
| 2.2.4.1 | ˈhorrible | **ˋ**horrible | nuclear ˈ not ˋ |
| 2.2.5.2 | ˈwill ·come | **ˋ**will ·come | nuclear ˈ not ˋ |
| 3.1.2 | ˎdance | ˎdance (matches) | may be OK; user flag if expecting rise |
| 3.1.3 | ˋwalk | ˋwalk (matches go ˈ) | was correct after prior HF; kept |
| 3.1.5 | ˈtrain | **ˋ**train | nuclear ˈ not ˋ |
| 4.2.1 | ˈHalˎlo | **ˋ**Hal**·**lo | head+LF wrong; HF+mid |
| 5.4.1 | polˎlution | polˎlution (matches) | matches PNG; kept |

## Fix applied
- Exact PNG fixes for samples + nuclear-high-fall heuristic on short example lines (final ˈWord. → ˋWord. when other stress present).
- Overrides 36/45/47/49 synced.
- Gold locks re-checked.

## What “faithful whole-doc” still requires
Until **every** tone example is Vision-checked (or a proven nuclear-HF rule is validated on a large random sample), residual_risk=0 on a report is **not** the same as “user need not QA.” The durable fix is: **glyph audit is the gate**, not crop existence + table rewrite.
