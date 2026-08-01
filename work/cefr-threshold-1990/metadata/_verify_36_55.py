from pathlib import Path
import re

base = Path(__file__).resolve().parents[1] / "page_overrides"
good = 0
issues = []
for n in range(36, 56):
    p = base / f"page_{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    doc = n - 6
    if f"leaf {n}" not in t and f"page {n}" not in t:
        issues.append(f"{n}: missing leaf/page in header")
    if "\u02CC" in t:
        issues.append(f"{n}: has U+02CC low vertical")
    if "multipass" not in t.lower() and "vision:" not in t.lower():
        issues.append(f"{n}: no vision header")
    # ASCII apostrophe used as tone: space/'Word or >'Word
    suspicious = re.findall(r"[ >\n]('[A-Za-z]{2,})", t)
    # filter contractions that start mid-word handled separately
    suspicious = [s for s in suspicious if not re.match(r"'[st]|'re|'ve|'ll|'d|'m", s)]
    if suspicious:
        issues.append(f"{n}: suspicious ASCII-as-tone: {suspicious[:8]}")
    marks = {
        k: t.count(c)
        for k, c in [
            ("ˈ", "\u02C8"),
            ("ˎ", "\u02CE"),
            ("ˋ", "\u02CB"),
            ("ˏ", "\u02CF"),
            ("ˊ", "\u02CA"),
            ("ˇ", "\u02C7"),
            ("·", "\u00B7"),
        ]
    }
    print(f"page_{n:03d} doc_p={doc} marks={marks}")
    good += 1

print("pages_rewritten", good)
print("issues:")
for i in issues:
    print(" ", i)

print("\n=== 2.1.6 samples (p035–p036) ===")
for n in (35, 36):
    t = (base / f"page_{n:03d}.md").read_text(encoding="utf-8")
    for line in t.splitlines():
        if "2.1.6" in line or (
            n == 36 and any(x in line for x in ("think", "Certainly", "course", "Yes", "believe", "believe"))
        ):
            if any(x in line for x in ("2.1.6", "think", "Certainly", "course", "Yes", "believe", "so.", "do.")):
                print(f"p{n}: {line}")
