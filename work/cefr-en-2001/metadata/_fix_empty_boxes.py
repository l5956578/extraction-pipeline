"""Repair empty user-boxes in page_overrides from page OCR."""
from pathlib import Path
import re

ocr_dir = Path("work/cefr-en-2001/page_ocr")
out_dir = Path("work/cefr-en-2001/page_overrides")


def extract_boxes(ocr_text: str) -> list[list[str]]:
    """Return list of boxes; each box is a list of bullet strings."""
    lines = [ln.rstrip() for ln in ocr_text.splitlines()]
    boxes: list[list[str]] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        i += 1
        if not s.startswith("Users of the Framework may wish"):
            continue
        items: list[str] = []
        while i < len(lines):
            ns = lines[i].strip()
            i += 1
            if not ns:
                # allow blank; stop if next structural after blank+content ends
                continue
            if ns.startswith("Users of the Framework"):
                i -= 1
                break
            if re.match(r"^(4\.\d|5\.\d)", ns):
                i -= 1
                break
            if ns in ("C2", "C1", "B2", "B1", "A2", "A1"):
                i -= 1
                break
            if ns.isupper() and len(ns) > 8 and re.sub(r"[^A-Za-z]", "", ns).isupper():
                # scale title
                i -= 1
                break
            if ns in ("•", "·"):
                continue
            if ns.startswith("•") or ns.startswith("·"):
                items.append(ns.lstrip("•· ").strip())
            elif items:
                items[-1] = (items[-1] + " " + ns).strip()
            else:
                # might be first bullet without mark if OCR dropped it
                if ns[0].islower() or ns.startswith("to ") or ns.startswith("in ") or ns.startswith("which ") or ns.startswith("what ") or ns.startswith("how ") or ns.startswith("for "):
                    items.append(ns)
                else:
                    i -= 1
                    break
            # stop after we have items and hit something that looks like end
        boxes.append(items)
    return boxes


def render_box(items: list[str]) -> str:
    lines = [
        "> **Users of the Framework may wish to consider and where appropriate state:**",
        ">",
    ]
    for it in items:
        it = re.sub(r"\s+", " ", it).strip().rstrip(";")
        it = re.sub(r"(\w)-\s+(\w)", r"\1\2", it)
        # ligatures
        it = it.replace("ﬁ", "fi").replace("ﬂ", "fl")
        lines.append(f"> - *{it}*")
    return "\n".join(lines)


def main() -> None:
    fixed = 0
    for n in range(51, 141):
        md_path = out_dir / f"page_{n:03d}.md"
        if not md_path.exists():
            continue
        md = md_path.read_text(encoding="utf-8")
        if "Users of the Framework" not in md:
            continue
        # detect empty boxes: blockquote header with no bullets before next non-quote
        empty_pat = re.compile(
            r"> \*\*Users of the Framework may wish to consider and where appropriate state:\*\*\n>\n(?!(?:> -))",
        )
        if not empty_pat.search(md) and md.count("> -") >= md.count("Users of the Framework"):
            continue

        ocr = (ocr_dir / f"page_{n:03d}.txt").read_text(encoding="utf-8", errors="replace")
        boxes = extract_boxes(ocr)
        if not boxes or not any(boxes):
            print(f"{n}: no OCR boxes found")
            continue

        # replace empty box placeholders in order
        bi = 0

        def repl(_m: re.Match) -> str:
            nonlocal bi
            while bi < len(boxes) and not boxes[bi]:
                bi += 1
            if bi >= len(boxes):
                return _m.group(0)
            out = render_box(boxes[bi])
            bi += 1
            return out

        # Match empty or partial empty boxes
        new_md, nsub = re.subn(
            r"> \*\*Users of the Framework may wish to consider and where appropriate state:\*\*\n>(?:\n(?:>[^\n]*\n)*)?",
            repl,
            md,
            count=0,
        )
        # More careful: only replace blocks with zero bullets
        parts = re.split(
            r"(> \*\*Users of the Framework may wish to consider and where appropriate state:\*\*\n(?:>.*\n)*)",
            md,
        )
        bi = 0
        out_parts = []
        for part in parts:
            if part.startswith("> **Users of the Framework"):
                if "> -" not in part:
                    while bi < len(boxes) and not boxes[bi]:
                        bi += 1
                    if bi < len(boxes):
                        out_parts.append(render_box(boxes[bi]) + "\n")
                        bi += 1
                        fixed += 1
                        continue
                out_parts.append(part)
            else:
                out_parts.append(part)
        new_md = "".join(out_parts)
        if new_md != md:
            md_path.write_text(new_md, encoding="utf-8")
            print(f"fixed page {n}")
    print("done, fixed ops ~", fixed)


if __name__ == "__main__":
    main()
