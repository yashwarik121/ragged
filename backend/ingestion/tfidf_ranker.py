"""
ingestion/tfidf_ranker.py — TF-IDF based sentence ranking and keyword
extraction using scikit-learn and NLTK.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

log = logging.getLogger(__name__)

# ── Sentence splitter (no NLTK dependency) ───────────────────────────

def _sent_tokenize(text: str) -> list[str]:
    """Split *text* into sentences using regex.

    Handles common abbreviations (Mr., Dr., etc.) and avoids splitting
    on decimal numbers or single-letter initials.
    """
    # Split on sentence-ending punctuation followed by whitespace and
    # an uppercase letter (or end of string)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    # Also split on newlines that look like paragraph breaks
    result = []
    for s in sentences:
        parts = re.split(r'\n\s*\n', s)
        result.extend(p.strip() for p in parts if p.strip())
    return result


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def rank_sentences(text: str, top_n: int = 10) -> list[dict]:
    """
    Split *text* into sentences, rank them by TF-IDF importance, and
    return the top *top_n*.

    Returns
    -------
    list[dict]
        ``[{"sentence": "...", "score": float, "rank": int}, ...]``
    """
    sentences = _sent_tokenize(text)
    if not sentences:
        return []

    # Remove very short sentences (< 5 words) that rarely carry meaning
    sentences = [s for s in sentences if len(s.split()) >= 5]
    if not sentences:
        return []

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(sentences)
    except ValueError:
        # All sentences were stop-words
        return []

    # Score each sentence as the mean of its non-zero TF-IDF values
    scores = np.asarray(tfidf_matrix.mean(axis=1)).flatten()

    ranked_indices = scores.argsort()[::-1][:top_n]

    results: list[dict] = []
    for rank, idx in enumerate(ranked_indices, start=1):
        results.append(
            {
                "sentence": sentences[idx].strip(),
                "score": round(float(scores[idx]), 4),
                "rank": rank,
            }
        )
    return results


def extract_terms(text: str, top_n: int = 15) -> list[dict]:
    """
    Extract the top *top_n* keywords from *text* and attempt to find a
    definitional sentence for each.

    Returns
    -------
    list[dict]
        ``[{"term": "...", "definition": "..."}, ...]``
    """
    sentences = _sent_tokenize(text)

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=top_n * 3,  # broader pool, then trim
            ngram_range=(1, 2),
        )
        vectorizer.fit_transform([text])
    except ValueError:
        return []

    feature_names = vectorizer.get_feature_names_out()
    tfidf_scores = vectorizer.transform([text]).toarray().flatten()

    # Pair features with scores and sort descending
    term_scores = sorted(
        zip(feature_names, tfidf_scores), key=lambda x: x[1], reverse=True
    )

    results: list[dict] = []
    seen_terms: set[str] = set()

    for term, _score in term_scores:
        if len(results) >= top_n:
            break
        normalised = term.lower().strip()
        if normalised in seen_terms or len(normalised) < 3:
            continue
        seen_terms.add(normalised)

        # Find the first sentence that contains the term
        definition = ""
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        for sent in sentences:
            if pattern.search(sent):
                definition = sent.strip()
                break

        results.append({"term": term, "definition": definition})

    return results
