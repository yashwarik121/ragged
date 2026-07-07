"""
extraction/reference_builder.py — Extract claims, statistics, and
evidence passages from document chunks.
"""

from __future__ import annotations

import logging
import re

from database import crud

log = logging.getLogger(__name__)

# ── Claim detection ──────────────────────────────────────────────────
_CLAIM_MARKERS = [
    "studies show",
    "research indicates",
    "data shows",
    "findings reveal",
    "evidence suggests",
    "results suggest",
    "according to",
]

_CLAIM_PATTERN = re.compile(
    "|".join(re.escape(m) for m in _CLAIM_MARKERS), re.IGNORECASE
)

# ── Statistics detection ─────────────────────────────────────────────
_STAT_PATTERN = re.compile(
    r"""
    (?:                       # match sentences containing:
        \d+(?:\.\d+)?%        #   percentages  (42%, 3.5%)
      | \$\d                  #   dollar amounts
      | \d{1,3}(?:,\d{3})+   #   large numbers (1,000  100,000)
      | \d+(?:\.\d+)?\s*(?:million|billion|trillion|thousand)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _sent_tokenize(text: str) -> list[str]:
    """Split text into sentences using regex."""
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    result = []
    for s in sentences:
        parts = re.split(r'\n\s*\n', s)
        result.extend(p.strip() for p in parts if p.strip())
    return result


def build_reference(doc_id: int, chunks: list[dict] | None = None) -> dict:
    """
    Build and persist a reference document for *doc_id*.

    Parameters
    ----------
    doc_id : int
        Document primary key.
    chunks : list[dict], optional
        Pre-computed chunks (each with ``text`` and ``page`` keys).
        If not provided, tries to load evidence passages from the DB.

    Returns
    -------
    dict
        Keys: ``claims``, ``statistics``, ``evidence_passages``,
        ``citation_index``.
    """
    # Resolve chunks
    if chunks is None:
        existing = crud.get_reference(doc_id)
        if existing and existing.get("evidence_passages"):
            chunks = existing["evidence_passages"]
        else:
            chunks = []

    if not chunks:
        log.warning("No chunks available for reference (doc %s)", doc_id)
        empty: dict = {
            "claims": [],
            "statistics": [],
            "evidence_passages": [],
            "citation_index": {},
        }
        crud.save_reference(doc_id, empty)
        return empty

    # Sort chunks by page so the output is in reading order
    sorted_chunks = sorted(chunks, key=lambda c: (c.get("page", 0), c.get("chunk_index", 0)))

    claims: list[dict] = []
    statistics: list[dict] = []
    evidence_passages: list[dict] = []
    citation_index: dict[str, list[int]] = {}  # marker → list of pages

    for chunk in sorted_chunks:
        text = chunk.get("text", "")
        page = chunk.get("page", 0)

        # Evidence passages (every chunk is an evidence passage)
        evidence_passages.append(
            {
                "text": text,
                "page": page,
                "chunk_index": chunk.get("chunk_index", 0),
            }
        )

        sentences = _sent_tokenize(text)

        for sent in sentences:
            # Claims
            match = _CLAIM_PATTERN.search(sent)
            if match:
                marker = match.group(0).lower()
                claims.append(
                    {"sentence": sent.strip(), "marker": marker, "page": page}
                )
                citation_index.setdefault(marker, [])
                if page not in citation_index[marker]:
                    citation_index[marker].append(page)

            # Statistics
            if _STAT_PATTERN.search(sent):
                statistics.append({"sentence": sent.strip(), "page": page})

    reference = {
        "claims": claims,
        "statistics": statistics,
        "evidence_passages": evidence_passages,
        "citation_index": citation_index,
    }

    crud.save_reference(doc_id, reference)
    log.info(
        "Reference built for doc %s — %d claims, %d stats, %d passages",
        doc_id, len(claims), len(statistics), len(evidence_passages),
    )
    return reference
