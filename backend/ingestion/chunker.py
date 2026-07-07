"""
ingestion/chunker.py — Split page texts into overlapping word-based chunks.
"""

from __future__ import annotations

import logging

from config import CHUNK_OVERLAP, CHUNK_SIZE

log = logging.getLogger(__name__)


def chunk_pages(
    pages: list[dict],
    doc_id: int,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Convert a list of page dicts into overlapping text chunks.

    Parameters
    ----------
    pages : list[dict]
        Output of ``pdf_parser.parse_pdf``.  Each dict must have
        ``"page"`` (int) and ``"text"`` (str) keys.
    doc_id : int
        Document identifier attached to every chunk.
    chunk_size : int
        Maximum number of words per chunk.
    overlap : int
        Number of words shared between consecutive chunks.

    Returns
    -------
    list[dict]
        Each element::

            {
                "text": "...",
                "doc_id": doc_id,
                "page": <first page that contributed>,
                "chunk_index": <0-based index>,
            }
    """
    # Flatten all pages into a single list of (word, page_num) tuples
    word_page: list[tuple[str, int]] = []
    for p in pages:
        words = p["text"].split()
        word_page.extend((w, p["page"]) for w in words)

    if not word_page:
        log.warning("No words extracted for doc %s", doc_id)
        return []

    chunks: list[dict] = []
    step = max(chunk_size - overlap, 1)
    idx = 0

    i = 0
    while i < len(word_page):
        window = word_page[i : i + chunk_size]
        text = " ".join(w for w, _ in window)
        # Attribute chunk to the first page in the window
        page_num = window[0][1]

        chunks.append(
            {
                "text": text,
                "doc_id": doc_id,
                "page": page_num,
                "chunk_index": idx,
            }
        )
        idx += 1
        i += step

    log.info("Created %d chunks for doc %s (chunk_size=%d, overlap=%d)",
             len(chunks), doc_id, chunk_size, overlap)
    return chunks
