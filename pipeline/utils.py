import re
from pathlib import Path

COMMON_WORDS = {
    "the", "and", "can", "for", "with", "understand", "language", "text", "information",
    "simple", "able", "their", "from", "that", "this", "have", "been", "which", "when",
    "about", "into", "through", "using", "other", "people", "different", "communicate",
    "interaction", "mediation", "production", "reception", "reading", "writing", "oral",
    "level", "descriptors", "competence", "activities", "strategies", "learner", "learning",
}


def slugify(text: str, prefix: str = "") -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    if prefix:
        return f"{prefix}_{text}" if text else prefix
    return text or "untitled"


def clean_running_headers(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^Page\s+\d+$", stripped, re.I):
            continue
        if re.match(r"^\d+\s+CEFR", stripped):
            continue
        if re.match(r"^CEFR.*Companion volume$", stripped, re.I):
            continue
        if re.match(r"^Companion volume$", stripped, re.I):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def english_word_score(text: str) -> float:
    words = re.findall(r"[A-Za-z]{3,}", text)
    if not words:
        return 0.0
    hits = sum(1 for w in words if w.lower() in COMMON_WORDS)
    return hits / len(words)


def is_gibberish(text: str, threshold: float = 0.08) -> bool:
    if len(text.strip()) < 40:
        return False
    score = english_word_score(text)
    reversed_hits = len(re.findall(r"[a-z]{4,}", text)) - sum(
        1 for w in re.findall(r"[a-z]{4,}", text) if w in COMMON_WORDS
    )
    if score < threshold and reversed_hits > 10:
        return True
    return score < 0.05


def escape_md_cell(value: str) -> str:
    if value is None:
        return ""
    value = str(value).replace("\n", " ").strip()
    value = value.replace("|", "\\|")
    return value


def table_to_markdown(rows: list[list]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    normalized = []
    for row in rows:
        padded = list(row) + [""] * (width - len(row))
        normalized.append([escape_md_cell(c) for c in padded])
    header = normalized[0]
    body = normalized[1:] if len(normalized) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def artifact_header(
    artifact_id: str,
    display_name: str,
    artifact_type: str,
    product_tiers: list[str],
    pages: str,
) -> str:
    tiers = ",".join(product_tiers)
    return (
        f"<!-- db:id={artifact_id} type={artifact_type} "
        f"product_tier={tiers} pages={pages} -->\n"
        f"### {display_name} | {artifact_id}\n"
    )


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path