"""
retrieval/bm25_store.py — In-memory BM25 index (one per document).
"""

from __future__ import annotations

import logging

from rank_bm25 import BM25Okapi

log = logging.getLogger(__name__)


class BM25Store:
    """Maintains per-document BM25 indices in memory."""

    def __init__(self) -> None:
        # doc_id → {"bm25": BM25Okapi, "chunks": list[dict]}
        self._indices: dict[int, dict] = {}

    def build_index(self, doc_id: int, chunks: list[dict]) -> None:
        """
        Build a BM25 index from *chunks* for the given *doc_id*.

        Each chunk dict must have a ``"text"`` key.
        """
        tokenised = [c["text"].lower().split() for c in chunks]
        bm25 = BM25Okapi(tokenised)
        self._indices[doc_id] = {"bm25": bm25, "chunks": chunks}
        log.info("BM25 index built for doc %s (%d chunks)", doc_id, len(chunks))

    def query(
        self, doc_id: int, query_text: str, top_k: int = 20
    ) -> list[dict]:
        """
        Retrieve the *top_k* most relevant chunks for *query_text*.

        Returns
        -------
        list[dict]
            Each dict has the original chunk keys plus a ``"bm25_score"``
            field.
        """
        if doc_id not in self._indices:
            log.warning("BM25 index for doc %s not found", doc_id)
            return []

        entry = self._indices[doc_id]
        bm25: BM25Okapi = entry["bm25"]
        chunks: list[dict] = entry["chunks"]

        tokens = query_text.lower().split()
        scores = bm25.get_scores(tokens)

        # Pair each chunk with its score and sort descending
        scored = sorted(
            zip(chunks, scores), key=lambda x: x[1], reverse=True
        )

        results: list[dict] = []
        for chunk, score in scored[:top_k]:
            results.append({**chunk, "bm25_score": float(score)})

        return results
