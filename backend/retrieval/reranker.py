"""
retrieval/reranker.py — Cross-encoder reranker (singleton).

Uses ``cross-encoder/ms-marco-MiniLM-L-6-v2`` to rescore passages
against a query, then returns the top-k reranked results.
"""

from __future__ import annotations

import logging
from typing import Optional

from config import RERANKER_MODEL

log = logging.getLogger(__name__)


class Reranker:
    """Singleton cross-encoder reranker."""

    _instance: Optional["Reranker"] = None
    _model = None

    def __new__(cls) -> "Reranker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── lazy loader ──────────────────────────────────────────────────
    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder

            log.info("Loading reranker model: %s", RERANKER_MODEL)
            self._model = CrossEncoder(RERANKER_MODEL)
            log.info("Reranker model loaded successfully.")
        except Exception:
            log.exception("Could not load reranker model '%s'", RERANKER_MODEL)
            raise

    # ── public API ───────────────────────────────────────────────────
    def rerank(
        self, query: str, passages: list[dict], top_k: int = 15
    ) -> list[dict]:
        """
        Rerank *passages* against *query* using the cross-encoder.

        Each passage dict must have a ``"text"`` key.  A
        ``"rerank_score"`` key is added to every returned dict.

        Returns the top *top_k* passages sorted by rerank score
        (descending).
        """
        if not passages:
            return []

        self._load()

        pairs = [(query, p["text"]) for p in passages]
        scores = self._model.predict(pairs)

        for passage, score in zip(passages, scores):
            passage["rerank_score"] = float(score)

        reranked = sorted(passages, key=lambda p: p["rerank_score"], reverse=True)
        return reranked[:top_k]
