"""
generation/ollama_report.py — Generate an LLM opinion report via Ollama,
with confidence scoring against source passages.
"""

from __future__ import annotations

import json
import logging
import re

import requests

from config import OLLAMA_URL
from database import crud
from ingestion.embedder import Embedder
from retrieval.bm25_store import BM25Store
from retrieval.hybrid_search import rrf_fusion
from retrieval.reranker import Reranker
from retrieval.vector_store import VectorStore

log = logging.getLogger(__name__)

# ── Shared singletons (initialised lazily by main.py) ────────────────
_vector_store: VectorStore | None = None
_bm25_store: BM25Store | None = None


def set_stores(vs: VectorStore, bm25: BM25Store) -> None:
    """Allow main.py to inject the shared store instances."""
    global _vector_store, _bm25_store
    _vector_store = vs
    _bm25_store = bm25


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _build_query(doc_id: int) -> str:
    """Derive a broad query from the cheatsheet abstract or filename."""
    cs = crud.get_cheatsheet(doc_id)
    if cs and cs.get("abstract"):
        # Use the abstract as a pseudo-query
        return cs["abstract"][:500]
    doc = crud.get_document(doc_id)
    if doc:
        return f"Key topics and findings in {doc.filename}"
    return "Main themes and key findings of this document"


def _retrieve_passages(doc_id: int, query: str, top_k: int = 15) -> list[dict]:
    """Hybrid search + rerank → top passages."""
    embedder = Embedder()
    query_emb = embedder.embed_single(query)

    # Vector search
    vs = _vector_store or VectorStore()
    vector_results = vs.query(query_emb, doc_id, top_k=20)

    # BM25 search
    bm25 = _bm25_store or BM25Store()
    bm25_results = bm25.query(doc_id, query, top_k=20)

    # Fuse
    fused = rrf_fusion(bm25_results, vector_results)

    # Rerank
    try:
        reranker = Reranker()
        return reranker.rerank(query, fused, top_k=top_k)
    except Exception:
        log.warning("Reranker unavailable — returning RRF results directly")
        return fused[:top_k]


def _call_ollama(system_prompt: str, user_prompt: str) -> str | None:
    """
    Call the Ollama API and return the generated text.

    Tries ``tinyllama`` first, then ``llama3``, falls back to ``mistral``.
    Returns ``None`` on any failure.
    """
    for model in ("tinyllama", "llama3", "mistral"):
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "stream": False,
                },
                timeout=180,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("response", "")
            log.warning(
                "Ollama returned %s for model '%s'", resp.status_code, model
            )
        except requests.ConnectionError:
            log.warning("Ollama not reachable at %s (model=%s)", OLLAMA_URL, model)
        except Exception:
            log.exception("Unexpected error calling Ollama (model=%s)", model)

    return None


def _parse_report(raw: str) -> dict:
    """
    Best-effort extraction of structured sections from LLM output.

    Expected sections:
    1. Executive Brief
    2. Critical Analysis
    3. So What
    4. Dissenting Opinion
    """
    sections = {
        "executive_brief": "",
        "critical_analysis": {},
        "so_what": "",
        "dissenting_opinion": "",
    }

    # Try to split on numbered headers or markdown headers
    patterns = [
        (r"(?:1[\.\)]\s*)?(?:executive\s*brief)[:\s]*", "executive_brief"),
        (r"(?:2[\.\)]\s*)?(?:critical\s*analysis)[:\s]*", "critical_analysis"),
        (r"(?:3[\.\)]\s*)?(?:so\s*what)[:\s]*", "so_what"),
        (r"(?:4[\.\)]\s*)?(?:dissenting\s*opinion|counterpoint)[:\s]*", "dissenting_opinion"),
    ]

    # Find section boundaries
    boundaries: list[tuple[int, str]] = []
    for pat, key in patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            boundaries.append((m.end(), key))

    boundaries.sort(key=lambda x: x[0])

    if boundaries:
        for i, (start, key) in enumerate(boundaries):
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(raw)
            # Walk backwards to chop off the next header line
            text_block = raw[start:end].strip()
            # Remove trailing header pattern
            for pat, _ in patterns:
                text_block = re.split(pat, text_block, flags=re.IGNORECASE)[0].strip()
            if key == "critical_analysis":
                sections[key] = {"text": text_block}
            else:
                sections[key] = text_block
    else:
        # Couldn't parse — dump everything into executive_brief
        sections["executive_brief"] = raw.strip()

    return sections


def _compute_confidence(report_text: str, passages: list[dict]) -> float:
    """
    Simple confidence score: what fraction of report sentences can be
    traced back to at least one source passage (via keyword overlap).
    """
    try:
        from ingestion.tfidf_ranker import _sent_tokenize
        report_sentences = _sent_tokenize(report_text)
    except Exception:
        report_sentences = [s.strip() for s in report_text.split(".") if s.strip()]

    if not report_sentences:
        return 0.0

    passage_texts = " ".join(p.get("text", "") for p in passages).lower()
    matched = 0

    for sent in report_sentences:
        # Extract significant words (>= 4 chars) from the sentence
        words = [w.lower() for w in sent.split() if len(w) >= 4]
        if not words:
            continue
        # If >= 40% of significant words appear in source passages
        hits = sum(1 for w in words if w in passage_texts)
        if hits / len(words) >= 0.4:
            matched += 1

    return round(matched / len(report_sentences), 2)


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────

def generate_report(doc_id: int) -> dict:
    """
    Generate an LLM-powered opinion report for *doc_id*.

    Returns
    -------
    dict
        Keys: ``executive_brief``, ``critical_analysis``, ``so_what``,
        ``dissenting_opinion``, ``confidence_score``, ``passages_used``.
        On failure the dict contains an ``"error"`` key instead.
    """
    doc = crud.get_document(doc_id)
    if doc is None:
        return {"error": f"Document {doc_id} not found"}

    # 1. Retrieve passages
    query = _build_query(doc_id)
    passages = _retrieve_passages(doc_id, query)

    if not passages:
        return {"error": "No passages retrieved — has the document been ingested?"}

    # 2. Build prompt
    context = "\n\n".join(
        f"[Page {p.get('page', '?')}] {p['text']}" for p in passages
    )

    system_prompt = (
        "You are a sharp, critical research analyst. You write like a "
        "senior editor at a serious publication. Direct, precise, no filler."
    )
    user_prompt = (
        "Given these passages from a document, write:\n"
        "1. Executive Brief — summarise the document in exactly 3 sentences.\n"
        "2. Critical Analysis — identify strengths and weaknesses.\n"
        "3. So What — explain why this matters in the real world.\n"
        "4. Dissenting Opinion — present one credible counterargument.\n\n"
        f"PASSAGES:\n{context}"
    )

    # 3. Call Ollama
    raw = _call_ollama(system_prompt, user_prompt)

    if raw is None:
        fallback = {
            "executive_brief": (
                "Ollama is not running or no model is available. "
                "Please start Ollama and pull llama3 or mistral."
            ),
            "critical_analysis": {"text": "Report generation failed — LLM unavailable."},
            "so_what": "Unable to generate analysis without an LLM backend.",
            "dissenting_opinion": "",
            "confidence_score": 0.0,
            "passages_used": [{"text": p["text"], "page": p.get("page", 0)} for p in passages],
            "error": "Ollama unavailable",
        }
        crud.save_report(doc_id, fallback)
        return fallback

    # 4. Parse structured response
    report = _parse_report(raw)

    # 5. Confidence scoring
    full_report_text = " ".join(
        str(v) if isinstance(v, str) else str(v)
        for v in report.values()
    )
    report["confidence_score"] = _compute_confidence(full_report_text, passages)
    report["passages_used"] = [
        {"text": p["text"], "page": p.get("page", 0)} for p in passages
    ]

    # 6. Persist
    crud.save_report(doc_id, report)
    log.info(
        "Report generated for doc %s (confidence=%.2f)",
        doc_id,
        report["confidence_score"],
    )
    return report
