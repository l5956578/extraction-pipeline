from pathlib import Path
import re
md_path = Path("output/cefr-companion-2020/CEFR_Companion_Volume.md")
md = md_path.read_text(encoding="utf-8")
md2, n = re.subn("\u201d([A-Za-z])", "\u201d \\1", md)
md_path.write_text(md2, encoding="utf-8")
print("fixed", n, "still", "\u201dthe" in md2)
