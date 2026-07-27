#!/usr/bin/env python3
"""Render a full PDF page to work/cefr-companion-2020/metadata/qa_snapshots/page_NNN.png for Vision QA.

Hard rules:
  - Full page only (never crop).
  - Reuse existing valid PNG unless --force.
  - Scale locked to pipeline.config.RENDER_SCALE (default 2.0).
  - Only intended for pages with an open extraction bug (caller discipline).

Usage (from workspace root):
  python .grok/skills/extraction-qa-vision/scripts/render_page_png.py --page 41
  python .grok/skills/extraction-qa-vision/scripts/render_page_png.py --page 41 --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Minimum bytes for a plausible full-page PNG at ~2x (reject empty/truncated).
_MIN_PNG_BYTES = 1024
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _project_root() -> Path:
    """Walk up from this script to find workspace root (has PDF or pipeline/)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pipeline" / "config.py").exists():
            return parent
        if (parent / "CEFR Companion Volume_eng.pdf").exists() and (
            parent / "AGENTS.md"
        ).exists():
            return parent
    # Fallback: skill is at .grok/skills/extraction-qa-vision/scripts/
    return here.parents[4]


def _resolve_pdf(root: Path) -> Path:
    try:
        sys.path.insert(0, str(root))
        from pipeline.config import PDF_PATH  # type: ignore

        if PDF_PATH.exists():
            return Path(PDF_PATH)
    except Exception:
        pass
    candidate = root / "CEFR Companion Volume_eng.pdf"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"PDF not found. Expected pipeline.config.PDF_PATH or {candidate}"
    )


def _default_scale(root: Path) -> float:
    """Project RENDER_SCALE when importable; else 2.0."""
    try:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from pipeline.config import RENDER_SCALE  # type: ignore

        return float(RENDER_SCALE)
    except Exception:
        return 2.0


def _png_is_reusable(path: Path) -> bool:
    """True if path is a non-trivial PNG (reject empty/corrupt for reuse)."""
    try:
        if not path.is_file():
            return False
        size = path.stat().st_size
        if size < _MIN_PNG_BYTES:
            return False
        with path.open("rb") as f:
            magic = f.read(8)
        return magic == _PNG_MAGIC
    except OSError:
        return False


def render_page(
    page: int,
    out_dir: Path,
    *,
    force: bool = False,
    scale: float | None = None,
    pdf_path: Path | None = None,
) -> Path:
    """Render full page `page` (1-based) to page_NNN.png. Reuse if valid."""
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page}")

    root = _project_root()
    pdf_path = pdf_path or _resolve_pdf(root)
    if scale is None:
        scale = _default_scale(root)
    out_dir = out_dir if out_dir.is_absolute() else (root / out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"page_{page:03d}.png"

    if out_path.exists() and not force:
        if _png_is_reusable(out_path):
            rel = _rel(root, out_path)
            print(f"exists (reuse): {rel}")
            print(str(rel).replace("\\", "/"))
            return out_path
        print(
            f"invalid snapshot (re-render): { _rel(root, out_path) } "
            f"(missing PNG header or size < {_MIN_PNG_BYTES} bytes)",
            file=sys.stderr,
        )

    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    try:
        if page > doc.page_count:
            raise ValueError(
                f"page {page} out of range (PDF has {doc.page_count} pages)"
            )
        # PyMuPDF is 0-based
        pg = doc.load_page(page - 1)
        mat = fitz.Matrix(scale, scale)
        # Full page — no clip
        pix = pg.get_pixmap(matrix=mat, alpha=False)
        pix.save(str(out_path))
    finally:
        doc.close()

    if not _png_is_reusable(out_path):
        raise RuntimeError(
            f"render produced unusable file: {out_path} "
            f"(size={out_path.stat().st_size if out_path.exists() else 0})"
        )

    rel = _rel(root, out_path)
    print(f"wrote: {rel}")
    print(str(rel).replace("\\", "/"))
    return out_path


def _rel(root: Path, path: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Render full PDF page PNG for extraction Vision QA (no crop). "
            "Scale is project RENDER_SCALE (locked); use --force to replace an existing file."
        )
    )
    parser.add_argument(
        "--page",
        type=int,
        required=True,
        help="1-based PDF page number",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if a valid page_NNN.png already exists",
    )
    # Default under active job metadata (config auto-loads cefr-companion-2020)
    try:
        sys.path.insert(0, str(_project_root()))
        from pipeline.config import METADATA_DIR
        _default_out = str(METADATA_DIR / "qa_snapshots")
    except Exception:
        _default_out = "work/cefr-companion-2020/metadata/qa_snapshots"
    parser.add_argument(
        "--out-dir",
        type=str,
        default=_default_out,
        help="Output directory (default: work/<job>/metadata/qa_snapshots)",
    )
    # Advanced only: not for routine use. Changing scale breaks snapshot determinism;
    # always pair with --force and treat prior QA on that page as void.
    parser.add_argument(
        "--scale",
        type=float,
        default=None,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args(argv)

    try:
        render_page(
            args.page,
            Path(args.out_dir),
            force=args.force,
            scale=args.scale,
        )
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
