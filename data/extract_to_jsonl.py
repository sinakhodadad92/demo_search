#!/usr/bin/env python3
"""
extract_to_jsonl.py – v2.0 (2025-05)

Converts a folder of PDF files into JSON-Lines that can be bulk-indexed
into Elasticsearch for the 10-document search portal.

Key upgrades over v1.2
----------------------
• Truncates full_text to avoid ES highlight.max_analyzed_offset errors  
• Scrubs control characters so json.dumps never fails  
• Better fall-backs for missing title/authors  
• CLI flags: --max-chars  --min-title-words  
• SHA-1 checksum of the original PDF for provenance  
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import pathlib
import re
from typing import List, Optional, Tuple

logging.getLogger("pdfminer").setLevel(logging.ERROR)

from pdfminer.high_level import extract_text
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configurable heuristics & constants
# ---------------------------------------------------------------------------
TITLE_SKIP_PATTERNS = [
    r"^www\.", r"^http[s]?://", r"^forum[:\s]", r"^volume\s+\d+",
]
TITLE_RX = re.compile("|".join(TITLE_SKIP_PATTERNS), re.I)
ABSTRACT_MARKERS = ["abstract", "summary", "zusammenfassung"]

CTRL_RX = re.compile(r"[\x00-\x1F\x7F]")          # ASCII control chars

DEFAULT_MAX_CHARS = 50_000                        # ≈ 10k tokens
MIN_TITLE_WORDS    = 4


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def scrub(text: str) -> str:
    """Remove control chars that break JSON/ES."""
    return CTRL_RX.sub("", text)


def select_title(lines: List[str], min_words: int) -> str:
    """Pick first plausible title line."""
    for ln in lines:
        if TITLE_RX.match(ln):
            continue
        if len(ln.split()) >= min_words:
            return ln.strip()
    # fall-back
    return lines[0] if lines else ""


def parse_authors(lines: List[str], title_idx: int) -> List[str]:
    if title_idx + 1 >= len(lines):
        return []
    cand = lines[title_idx + 1]
    if TITLE_RX.match(cand):
        return []
    parts = re.split(r",| and ", cand)
    #   filter out URLs / long digit chunks
    return [
        p.strip() for p in parts
        if p.strip() and not re.search(r"\d{5,}", p) and "http" not in p.lower()
    ]


def extract_metadata(first_pg: str, min_title_words: int
                     ) -> Tuple[str, List[str], Optional[int]]:
    lines = [ln.strip() for ln in first_pg.splitlines() if ln.strip()]
    title  = select_title(lines, min_title_words)
    idx    = lines.index(title) if title in lines else 0
    authors = parse_authors(lines, idx)
    year_m  = re.search(r"(19|20)\d{2}", first_pg)
    year    = int(year_m.group()) if year_m else None
    return title, authors, year


def extract_abstract(first_pg: str) -> str:
    lowered = first_pg.lower()
    for m in ABSTRACT_MARKERS:
        pos = lowered.find(m)
        if pos != -1:
            after = first_pg[pos + len(m):]
            end   = after.find("\n\n")
            snippet = after[:end] if end != -1 else after
            lines = [ln.strip(": ").strip() for ln in snippet.splitlines()]
            return " ".join(lines).strip()
    return ""


def sha1_of_file(path: pathlib.Path, buf_sz: int = 131_072) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        while chunk := fh.read(buf_sz):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------
def process_pdf(path: pathlib.Path, max_chars: int, min_title_words: int) -> dict:
    try:
        full = extract_text(path)
        first = extract_text(path, page_numbers=[0])
    except Exception as e:          # corrupt PDF or password-protected
        logging.warning(f"✖  {path.name}: {e}")
        return {}

    title, authors, year = extract_metadata(first, min_title_words)
    abstract = extract_abstract(first)

    rec = {
        "id"      : path.stem,
        "sha1"    : sha1_of_file(path),
        "title"   : scrub(title)[:300],
        "authors" : authors[:10],
        "year"    : year,
        "abstract": scrub(abstract)[:5_000],
        "full_text": scrub(full)[:max_chars],
        "url"      : "",           # fill later if you host the PDFs
    }
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", required=True)
    ap.add_argument("--out",     required=True)
    ap.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                    help="truncate full_text to this many characters "
                         f"(default {DEFAULT_MAX_CHARS})")
    ap.add_argument("--min-title-words", type=int, default=MIN_TITLE_WORDS)
    args = ap.parse_args()

    pdf_dir  = pathlib.Path(args.pdf_dir)
    out_path = pathlib.Path(args.out)
    pdfs     = sorted(pdf_dir.glob("*.pdf"))

    with out_path.open("w", encoding="utf-8") as fh:
        for pdf in tqdm(pdfs, desc="Extracting"):
            rec = process_pdf(pdf, args.max_chars, args.min_title_words)
            if rec:                                  # skip if extraction failed
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"✔  Wrote {out_path} with {out_path.stat().st_size/1024:.1f} kB "
          f"({len(pdfs)} PDFs).")


if __name__ == "__main__":
    main()