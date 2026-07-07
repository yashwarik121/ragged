"""
ingestion/ner_extractor.py — Named Entity Recognition with spaCy.

Entities are grouped into PERSON, ORG, DATE, GPE and a catch-all
CONCEPT bucket (NORP, EVENT, WORK_OF_ART, LAW).
"""

from __future__ import annotations

import logging
from typing import Optional

log = logging.getLogger(__name__)

# ── Lazy-loaded spaCy model ──────────────────────────────────────────
_nlp = None


def _get_nlp():
    """Load ``en_core_web_sm`` once and cache."""
    global _nlp
    if _nlp is not None:
        return _nlp
    try:
        import spacy

        _nlp = spacy.load("en_core_web_sm")
        log.info("spaCy model en_core_web_sm loaded.")
    except OSError:
        log.warning(
            "spaCy model 'en_core_web_sm' not found. "
            "Run: python -m spacy download en_core_web_sm"
        )
        raise
    return _nlp


# Mapping from spaCy labels to our simplified categories
_CONCEPT_LABELS = {"NORP", "EVENT", "WORK_OF_ART", "LAW"}
_TRACKED_LABELS = {"PERSON", "ORG", "DATE", "GPE"}


def extract_entities(text: str) -> dict[str, list[str]]:
    """
    Run NER on *text* and return deduplicated entities grouped by
    category.

    Returns
    -------
    dict
        ``{"PERSON": [...], "ORG": [...], "DATE": [...],
          "GPE": [...], "CONCEPT": [...]}``
    """
    nlp = _get_nlp()

    result: dict[str, set[str]] = {
        "PERSON": set(),
        "ORG": set(),
        "DATE": set(),
        "GPE": set(),
        "CONCEPT": set(),
    }

    # Process in chunks to avoid spaCy max-length issues
    max_len = 1_000_000
    for start in range(0, len(text), max_len):
        doc = nlp(text[start : start + max_len])
        for ent in doc.ents:
            label = ent.label_
            cleaned = ent.text.strip()
            if not cleaned:
                continue
            if label in _TRACKED_LABELS:
                result[label].add(cleaned)
            elif label in _CONCEPT_LABELS:
                result["CONCEPT"].add(cleaned)

    # Convert sets → sorted lists for deterministic output
    return {k: sorted(v) for k, v in result.items()}
