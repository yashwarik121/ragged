"""
ingestion/embedder.py — Singleton sentence-transformer embedder.

The model is loaded lazily on first use so that the FastAPI server can
start even if the model files haven't been downloaded yet.
"""

from __future__ import annotations

import logging
from typing import Optional

from config import EMBEDDING_MODEL

log = logging.getLogger(__name__)


class Embedder:
    """Thread-safe singleton wrapper around a SentenceTransformer model."""

    _instance: Optional["Embedder"] = None
    _model = None

    def __new__(cls) -> "Embedder":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ── lazy loader ──────────────────────────────────────────────────
    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            log.info("Loading embedding model: %s", EMBEDDING_MODEL)
            self._model = SentenceTransformer(EMBEDDING_MODEL)
            log.info("Embedding model loaded successfully.")
        except Exception:
            log.exception("Could not load embedding model '%s'", EMBEDDING_MODEL)
            raise

    # ── public API ───────────────────────────────────────────────────
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts and return a list of float vectors."""
        self._load()
        vectors = self._model.encode(texts, show_progress_bar=False)
        return [v.tolist() for v in vectors]

    def embed_single(self, text: str) -> list[float]:
        """Embed a single string."""
        return self.embed([text])[0]
