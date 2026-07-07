"""
extraction/cheatsheet_builder.py — Assemble a one-page cheat sheet
from NER data, TF-IDF insights, and raw chunks.
"""

from __future__ import annotations

import logging

from database import crud
from ingestion.ner_extractor import extract_entities
from ingestion.tfidf_ranker import extract_terms, rank_sentences

log = logging.getLogger(__name__)


def _collect_full_text(doc_id: int) -> str:
    """
    Reconstruct the full document text from stored chunks.

    Falls back to an empty string if no chunks are available yet (e.g.
    the reference data has evidence passages we can stitch together).
    """
    ref = crud.get_reference(doc_id)
    if ref and ref.get("evidence_passages"):
        return " ".join(
            p.get("text", "") for p in ref["evidence_passages"]
        )
    return ""


def build_cheatsheet(doc_id: int, full_text: str | None = None) -> dict:
    """
    Build and persist a cheat sheet for *doc_id*.

    Parameters
    ----------
    doc_id : int
        Primary-key of the document in the DB.
    full_text : str, optional
        Pre-assembled full text of the document.  When supplied the
        function skips the DB look-up (useful during initial ingestion).

    Returns
    -------
    dict
        Keys: ``abstract``, ``key_insights``, ``entities``,
        ``flashcards``, ``timeline``.
    """
    if full_text is None:
        full_text = _collect_full_text(doc_id)

    if not full_text.strip():
        log.warning("No text available for cheatsheet (doc %s)", doc_id)
        empty: dict = {
            "abstract": "",
            "key_insights": [],
            "entities": {},
            "flashcards": [],
            "timeline": [],
        }
        crud.save_cheatsheet(doc_id, empty)
        return empty

    # ── 1. Abstract — first 3 sentences ──────────────────────────────
    from ingestion.tfidf_ranker import _sent_tokenize

    sentences = _sent_tokenize(full_text)
    abstract = " ".join(sentences[:3]) if sentences else ""

    # ── 2. Key insights — top ranked sentences ───────────────────────
    key_insights = rank_sentences(full_text, top_n=10)

    # ── 3. Entities ──────────────────────────────────────────────────
    entities = extract_entities(full_text)

    # ── 4. Flashcards — terms + definitions ──────────────────────────
    flashcards = extract_terms(full_text, top_n=15)

    # ── 5. Timeline — all DATE entities ──────────────────────────────
    timeline = entities.get("DATE", [])

    cheatsheet = {
        "abstract": abstract,
        "key_insights": key_insights,
        "entities": entities,
        "flashcards": flashcards,
        "timeline": timeline,
    }

    crud.save_cheatsheet(doc_id, cheatsheet)
    log.info("Cheatsheet built for doc %s", doc_id)
    return cheatsheet
