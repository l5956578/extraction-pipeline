"""Post-process drafted page_overrides: unglue long headers, table spacing."""
from pathlib import Path
import re

p = Path("work/cefr-en-2001/page_overrides")
SKIP = {74, 80, 100}  # already vision-fixed carefully
# Also skip hand-crafted early pages
fixed = 0

for f in sorted(p.glob("page_*.md")):
    n = int(f.stem.split("_")[1])
    if n < 74 or n > 140:
        continue
    if n in SKIP:
        continue
    t = f.read_text(encoding="utf-8")
    orig = t

    def split_long_header(m: re.Match) -> str:
        hashes, num, rest = m.group(1), m.group(2), m.group(3).strip()
        words = rest.split()
        if len(words) > 10:
            return f"{hashes} {num}\n\n{rest}"
        return m.group(0)

    t = re.sub(
        r"^(#{3,4})\s+(\d+(?:\.\d+)+)\s+(.+)$",
        split_long_header,
        t,
        flags=re.M,
    )
    t = t.replace("`", "'")
    t = re.sub(r"([^\n])\n(\| Level \|)", r"\1\n\n\2", t)
    t = re.sub(r"(\*\*[A-Z][^*]+\*\*)\n(\| Level \|)", r"\1\n\n\2", t)
    # de-hyphenate residual mid-word breaks
    t = re.sub(r"(\w)-\s+(\w)", r"\1\2", t)

    if t != orig:
        f.write_text(t, encoding="utf-8")
        fixed += 1

print("fixed files", fixed)

rng = [f for f in p.glob("page_*.md") if 51 <= int(f.stem.split("_")[1]) <= 140]
print("overrides 51-140:", len(rng))
missing = [i for i in range(51, 141) if not (p / f"page_{i:03d}.md").exists()]
print("missing:", missing)

bad = []
for i in range(51, 141):
    t = (p / f"page_{i:03d}.md").read_text(encoding="utf-8")
    if "<!-- vision:" not in t:
        bad.append((i, "no vision"))
    elif len(t) < 150:
        bad.append((i, f"thin:{len(t)}"))
print("quality flags:", bad)
