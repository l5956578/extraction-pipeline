Rotated table agent vision handoff
==================================

AGENT VISION EXTRACTION (rotated tables only — user is out of the loop)
=======================================================================
You (coding agent with vision) are the sole authoritative extractor for rotated
descriptor-scale tables. Do **not** ask the user to upload PNGs to chat/web Grok.

For each pending slug in work/metadata/rotated_for_grok/manifest.json:

  1. Open work/metadata/rotated_for_grok/{slug}.png with vision.
  2. Transcribe every descriptor into markdown:
       | Level | Receptive | Productive |
     Blank Level on second row when PDF has a horizontal rule (B2/B1 multi-row).
     Join descriptors in a cell with <br>.
  3. Write work/metadata/rotated_from_grok/{slug}.md (table only).
  4. After a span is complete (or for a production run with geometry fallback):
       python finalize_after_grok.py

Chat/web Grok is NOT a pipeline step.

Commands
--------
  python prepare_rotated_for_grok.py
  python finalize_after_grok.py

Pending agent .md: 51
Ready: 37
Manifest: D:\y\lang-platform\pipelines\extraction-pipeline\work\metadata\rotated_for_grok\manifest.json
Output dir: D:\y\lang-platform\pipelines\extraction-pipeline\work\metadata\rotated_from_grok
