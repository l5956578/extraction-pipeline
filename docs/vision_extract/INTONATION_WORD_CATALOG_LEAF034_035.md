# Word catalog — Threshold leaves 34–35 (doc pp. 28–29) — functions 1.x

**Date:** 2026-07-31  
**Method:** 8×–12× line crops + PDF text layer as *hint only*  
**Failure pattern fixed:** Paper Capture encodes **three high-family tones** as `'` and **two low-family tones** as `,`. Blind convert `'`→ˈ and `,`→ˎ is **wrong**. Shape + section context required.

| PDF glyph | Possible Unicode | Disambiguation |
|-----------|------------------|----------------|
| `'` above | `ˈ` head · `ˋ` high fall · `ˊ` high rise | vertical vs falling diagonal vs rising tick; section title |
| `,` below | `ˎ` low fall · `ˏ` low rise | falling vs rising stroke below |
| `"` / `v` above | `ˇ` fall-rise | |
| `.` mid | `·` secondary | |

---

## Leaf 34 / doc p.28

### 1.1.3
| Word | Mark | Why |
|------|------|-----|
| This | `ˈ` | vertical high upright |
| bedroom | `ˎ` | low fall below |
| animal | `ˇ` | v-mark above |
| there | `·` | mid |
| dog | `ˎ` | low fall |

```
ˈThis is the ˎbedroom.
The ˇanimal over ·there | is my ˎdog.
```

### 1.1.4
```
ˈHe is the ˎowner of the ·restaurant.
```

### 1.2.1
```
The ˈtrain has ˎleft.
```

### 1.2.2
```
He ·says the ˈshop is ˎshut.
```

### 1.3.1 contrastive stress  **(WAS WRONG: head ˈ on This/has)**
| Word | Mark | Why |
|------|------|-----|
| This | `ˋ` | **high fall diagonal above** (not vertical head) |
| bedroom | `·` | mid (contrast: not nucleus) |
| train | `·` | mid |
| has | `ˋ` | **high fall diagonal above** (contrastive nucleus) |
| left | `·` | mid |

```
ˋThis is the ·bedroom.
The ·train ˋhas ·left.
```

### 1.3.2–1.3.4
```
ˈNo it ˇisn’t.
Va·letta ˈisn’t in ˇItaly.
ˈYes you ˇdid.
```

---

## Leaf 35 / doc p.29

### 1.3.5
```
You ˇdid ·go to ·London.
```

### 1.4.1.1 interrogative (for confirmation)  **(WAS WRONG: ˈDid)**
| Word | Mark | Why |
|------|------|-----|
| Did | `ˊ` | **high-rising tick above** (yes/no interrogative) |
| see | `ˎ` | low fall below (glyph) |

```
ˊDid you ˎsee him?
```

### 1.4.1.2 high-rising declarative
```
You ˊsaw him?
```

### 1.4.1.3 statement + tag  **(PNG: both below-line marks = low fall)**
| Word | Mark | Why |
|------|------|-----|
| lost | `ˎ` | low fall below |
| match | `·` | mid |
| didn't | `ˎ` | low fall below — do **not** invent ˏ from section title |

```
They ˎlost the ·match, | ˎdidn't they?
```

### 1.4.2.1 wh questions (sample)
```
ˈWhen will the ·guests arˎrive?
ˈWhere is my ˎpurse?
ˈHow do you ·make an ˎomelette?
ˈHow ·far is it to ˎYork?
ˈWhy did you ·say ˎthat?
```

### 1.4.2.2 Please…  **(PNG: Please = upright head)**
| Word | Mark | Why |
|------|------|-----|
| Please | `ˈ` | high upright / head (not ˊ) |
| tell | `·` | mid |
| way | `·` | mid |
| station | `ˎ` | low fall nucleus |

```
ˈPlease can you ·tell me the ·way to the ˎstation?
```

### 1.5.1
```
ˎYes, | he ˎis.
ˎNo, | he ˎisn’t.
```

---

## Working rule (no legal novel)

1. **PNG glyph wins.** Section titles / App A prose never override a clear stroke on the crop.
2. PDF `'` / `,` are **hints only** — split head/HF/HR and LF/LR by shape on the crop.
3. **Re-Vision product MD vs crop** after write. Native convert is not a pass.
4. Full word catalog before multipass claim on a page.
5. **Section locks** — 1.1.3 / 1.2.1 / 1.3.1 share letter skeletons but different marks; never letter-skeleton-merge them into one form.
6. **Multi-iteration residual gate** before done (`full_md_vs_pdf_intonation.py`); must assert gold counts and ban bad residuals (including inventing `ˏ` on tags when PNG is low fall).
