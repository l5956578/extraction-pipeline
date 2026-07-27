"""Split PDF into span-safe chunks."""

from __future__ import annotations

import json
from pathlib import Path

import fitz

import pipeline.config as cfg
from pipeline.span_detector import SpanGroup, detect_spans

def _protected_ranges(groups: list[SpanGroup]) -> list[tuple[int, int]]:
    protected = []
    for g in groups:
        if g.span_type in ("continuation", "section_block"):
            protected.append((g.start_page, g.end_page))
        elif g.span_type == "series" and (g.end_page - g.start_page + 1) >= 10:
            protected.append((g.start_page, g.end_page))
    return sorted(protected)

def _inside_protected(page: int, protected: list[tuple[int, int]]) -> tuple[int, int] | None:
    for s, e in protected:
        if s <= page <= e:
            return (s, e)
    return None

def compute_chunk_ranges(total_pages: int, groups: list[SpanGroup]) -> list[tuple[int, int]]:
    protected = _protected_ranges(groups)
    chunks: list[tuple[int, int]] = []
    pos = 1

    while pos <= total_pages:
        ideal_end = min(pos + cfg.TARGET_CHUNK_SIZE - 1, total_pages)

        # Extend ideal_end if it would split a protected range
        for s, e in protected:
            if s <= ideal_end < e:
                ideal_end = e
                break

        # Don't start inside protected range
        for s, e in protected:
            if s < pos <= e:
                pos = e + 1
                ideal_end = min(pos + cfg.TARGET_CHUNK_SIZE - 1, total_pages)
                for s2, e2 in protected:
                    if s2 <= ideal_end < e2:
                        ideal_end = e2
                        break
                break

        end = ideal_end
        if end < pos:
            end = pos
        chunks.append((pos, end))
        pos = end + 1

    return chunks

def write_chunks(ranges: list[tuple[int, int]]) -> list[dict]:
    cfg.CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    src = fitz.open(cfg.PDF_PATH)
    manifest = []

    for idx, (start, end) in enumerate(ranges, start=1):
        chunk_id = f"chunk_{idx:02d}"
        out_path = cfg.CHUNKS_DIR / f"{chunk_id}_pages_{start:03d}-{end:03d}.pdf"
        dst = fitz.open()
        dst.insert_pdf(src, from_page=start - 1, to_page=end - 1)
        dst.save(out_path)
        dst.close()
        manifest.append(
            {
                "chunk_id": chunk_id,
                "start_page": start,
                "end_page": end,
                "path": str(out_path),
            }
        )
        print(f"Created {out_path.name} ({end - start + 1} pages)")

    src.close()
    meta_path = cfg.METADATA_DIR / "chunks.json"
    meta_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

def run_chunking() -> list[dict]:
    groups = detect_spans()
    save_path = cfg.METADATA_DIR / "spanning_tables.json"
    save_path.write_text(
        json.dumps([g.__dict__ for g in groups], indent=2), encoding="utf-8"
    )
    doc = fitz.open(cfg.PDF_PATH)
    total = doc.page_count
    doc.close()
    ranges = compute_chunk_ranges(total, groups)
    return write_chunks(ranges)

if __name__ == "__main__":
    from pipeline.bootstrap import parse_and_load_job

    parse_and_load_job(description="Chunk PDF for extraction")
    run_chunking()