"""
retrieval/hybrid_search.py — Reciprocal Rank Fusion (RRF) to combine
BM25 and vector search results.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


def rrf_fusion(
    bm25_results: list[dict],
    vector_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """
    Merge two ranked result lists using Reciprocal Rank Fusion.

    For every document the RRF score is::

        score = Σ  1 / (k + rank_i)

    where *rank_i* is the 1-based rank in each source list that
    contains the document.

    Parameters
    ----------
    bm25_results : list[dict]
        Results from BM25, already sorted by relevance (best first).
    vector_results : list[dict]
        Results from the vector store, already sorted by relevance.
    k : int
        Smoothing constant (default 60, per the original RRF paper).

    Returns
    -------
    list[dict]
        Merged results sorted by descending RRF score.  Each dict gets
        an extra ``"rrf_score"`` key.
    """
    scores: dict[str, float] = {}
    lookup: dict[str, dict] = {}

    def _key(item: dict) -> str:
        """Unique key for a chunk — use chunk_index + doc_id."""
        return f"{item.get('doc_id', 0)}_{item.get('chunk_index', 0)}"

    for rank, item in enumerate(bm25_results, start=1):
        key = _key(item)
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        lookup[key] = item

    for rank, item in enumerate(vector_results, start=1):
        key = _key(item)
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        if key not in lookup:
            lookup[key] = item

    # Sort by RRF score descending
    sorted_keys = sorted(scores, key=scores.__getitem__, reverse=True)

    merged: list[dict] = []
    for key in sorted_keys:
        entry = {**lookup[key], "rrf_score": round(scores[key], 6)}
        merged.append(entry)

    log.info(
        "RRF fusion: %d BM25 + %d vector → %d merged",
        len(bm25_results),
        len(vector_results),
        len(merged),
    )
    return merged
