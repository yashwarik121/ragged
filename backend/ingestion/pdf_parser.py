"""
ingestion/pdf_parser.py — Extract text from PDF files page-by-page
using PyMuPDF (fitz).
"""

from __future__ import annotations

import logging
from pathlib import Path

import fitz  # PyMuPDF

log = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> list[dict]:
    """
    Open *file_path* with PyMuPDF and return a list of page dicts.

    Each dict has the shape::

        {"page": <1-based page number>, "text": "<extracted text>"}

    Pages whose text is empty after stripping are still included so
    page numbering stays consistent.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages: list[dict] = []

    try:
        doc = fitz.open(str(path))
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text") or ""
            pages.append({"page": page_num + 1, "text": text})
        doc.close()
    except Exception:
        log.exception("Failed to parse PDF: %s", file_path)
        raise

    log.info("Parsed %d pages from %s", len(pages), path.name)
    return pages
