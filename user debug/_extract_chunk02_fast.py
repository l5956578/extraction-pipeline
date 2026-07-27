"""Fast chunk_02 extract without full-book span registry (local smoke only).

Phase B: bootstrap a job before reading path attributes.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import fitz

from pipeline.bootstrap import bootstrap_job
import pipeline.config as cfg
from pipeline.extract_chunk import _ExtractContext, _el_fence, _extract_element


def main() -> None:
    bootstrap_job("cefr-companion-2020")
    inv = json.loads(
        (cfg.INVENTORIES_DIR / "chunk_02_inventory.json").read_text(encoding="utf-8")
    )
    doc = fitz.open(cfg.PDF_PATH)
    ctx = _ExtractContext({}, {})
    parts = [f"# chunk_02 (pages {inv['start_page']}-{inv['end_page']})\n"]
    t0 = time.time()
    for page_info in inv["pages"]:
        pn = page_info["page_number"]
        page = doc[pn - 1]
        print(f"page {pn}", flush=True)
        for el in page_info.get("reading_order") or []:
            block = _extract_element(el, page, pn, page_info, None, doc, ctx)
            if not block:
                continue
            etype = el.get("type") or "unknown"
            if etype not in ("footer", "span_continuation_skip"):
                eid = (
                    el.get("artifact_id")
                    or el.get("id")
                    or f"{etype}_p{pn:03d}_s{el.get('seq', 0)}"
                )
                block = _el_fence(etype, str(eid), pn, block)
            parts.append(block)
    doc.close()
    content = "\n".join(parts)
    cfg.RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = cfg.RAW_DIR / "chunk_02.md"
    out.write_text(content, encoding="utf-8")
    print(f"Extracted {out.name} ({len(content)} chars) in {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
