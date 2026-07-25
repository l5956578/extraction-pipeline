import fitz

doc = fitz.open("CEFR Companion Volume_eng.pdf")

page = doc[33]
h = page.rect.height
print("page 34 h", h)
for b in page.get_text("dict")["blocks"]:
    if b.get("type") != 0:
        continue
    for line in b.get("lines", []):
        t = "".join(s["text"] for s in line["spans"]).strip()
        keys = (
            "Figure 2",
            "RECEPTION",
            "PRODUCTION",
            "INTERACTION",
            "MEDIATION",
            "As with many",
            "introduces the concept",
            "Chomskyan",
        )
        if any(k in t for k in keys):
            y = line["bbox"][1]
            print(f"y={y:.0f} ({y/h:.2f}) {t[:100]!r}")

print("drawings", len(page.get_drawings()))
ys = []
for d in page.get_drawings():
    r = d.get("rect")
    if r:
        ys.append((r.y0, r.y1, r.x0, r.x1))
for y0, y1, x0, x1 in sorted(ys)[:20]:
    print(
        "draw",
        round(y0, 1),
        round(y1, 1),
        f"frac y0={y0/h:.2f} y1={y1/h:.2f} x={x0:.0f}-{x1:.0f}",
    )

print("\n=== p36 top ===")
page = doc[35]
h = page.rect.height
for b in page.get_text("dict")["blocks"]:
    if b.get("type") != 0:
        continue
    for line in b.get("lines", []):
        t = "".join(s["text"] for s in line["spans"]).strip()
        if t and line["bbox"][1] < h * 0.55:
            y = line["bbox"][1]
            print(f"y={y:.0f} ({y/h:.2f}) {t[:100]!r}")

print("\n=== p32 Figure 1 area ===")
page = doc[31]
h = page.rect.height
for b in page.get_text("dict")["blocks"]:
    if b.get("type") != 0:
        continue
    for line in b.get("lines", []):
        t = "".join(s["text"] for s in line["spans"]).strip()
        if t and ("Figure 1" in t or "Savoir" in t or "overall approach" in t.lower() or "Linguistic" == t):
            y = line["bbox"][1]
            print(f"y={y:.0f} ({y/h:.2f}) {t[:100]!r}")

doc.close()
