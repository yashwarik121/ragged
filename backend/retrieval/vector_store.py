"""
retrieval/vector_store.py — ChromaDB-backed vector store.

One collection per document (``doc_<id>``).  Uses cosine similarity
by default.
"""

from __future__ import annotations

import logging

import chromadb

from config import CHROMA_DIR

log = logging.getLogger(__name__)


class VectorStore:
    """Persistent vector store powered by ChromaDB."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(path=CHROMA_DIR)
        log.info("ChromaDB client initialised at %s", CHROMA_DIR)

    # ── helpers ──────────────────────────────────────────────────────
    def _collection_name(self, doc_id: int) -> str:
        return f"doc_{doc_id}"

    def _get_or_create(self, doc_id: int):
        return self._client.get_or_create_collection(
            name=self._collection_name(doc_id),
            metadata={"hnsw:space": "cosine"},
        )

    # ── public API ───────────────────────────────────────────────────

    def add_documents(
        self,
        doc_id: int,
        chunks: list[dict],
        embeddings: list[list[float]],
    ) -> None:
        """
        Insert *chunks* with their *embeddings* into the collection for
        *doc_id*.

        Each chunk dict must have ``text``, ``page``, and
        ``chunk_index`` keys.
        """
        col = self._get_or_create(doc_id)

        ids = [f"{doc_id}_{c['chunk_index']}" for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {"doc_id": doc_id, "page": c["page"], "chunk_index": c["chunk_index"]}
            for c in chunks
        ]

        # ChromaDB has a batch limit; split into safe batches
        batch_size = 5000
        for start in range(0, len(ids), batch_size):
            end = start + batch_size
            col.add(
                ids=ids[start:end],
                embeddings=embeddings[start:end],
                documents=documents[start:end],
                metadatas=metadatas[start:end],
            )

        log.info("Added %d vectors to collection doc_%s", len(ids), doc_id)

    def query(
        self,
        query_embedding: list[float],
        doc_id: int,
        top_k: int = 20,
    ) -> list[dict]:
        """
        Retrieve the *top_k* most similar chunks from *doc_id*'s
        collection.

        Returns
        -------
        list[dict]
            Each dict: ``{"text": ..., "page": ..., "chunk_index": ...,
            "score": ...}``
        """
        col = self._get_or_create(doc_id)

        if col.count() == 0:
            return []

        results = col.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, col.count()),
            include=["documents", "metadatas", "distances"],
        )

        out: list[dict] = []
        for i in range(len(results["ids"][0])):
            out.append(
                {
                    "text": results["documents"][0][i],
                    "page": results["metadatas"][0][i].get("page", 0),
                    "chunk_index": results["metadatas"][0][i].get("chunk_index", 0),
                    "score": 1.0 - results["distances"][0][i],  # cosine → similarity
                }
            )
        return out
