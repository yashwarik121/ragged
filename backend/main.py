"""
main.py — FastAPI application for the ragged document intelligence engine.

Endpoints
---------
GET  /                  Health check
GET  /documents         List all uploaded documents
POST /upload            Upload & ingest a PDF
GET  /cheatsheet/{id}   Build / return cheat sheet
GET  /reference/{id}    Build / return reference document
POST /report            Generate LLM opinion report
GET  /export/{id}/pdf   Download styled PDF report
"""

from __future__ import annotations

import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# ── Ensure the backend directory is on sys.path so relative imports
#    resolve correctly when running with ``uvicorn main:app``.
_BACKEND_DIR = str(Path(__file__).resolve().parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import UPLOAD_DIR
from database import crud

# ── Logging setup ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
log = logging.getLogger("ragged")

# ── FastAPI app ──────────────────────────────────────────────────────
app = FastAPI(
    title="ragged",
    description="Document Intelligence Engine",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared singletons (lazy-initialised) ─────────────────────────────
_vector_store = None
_bm25_store = None
_embedder = None


def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        from retrieval.vector_store import VectorStore

        _vector_store = VectorStore()
    return _vector_store


def _get_bm25_store():
    global _bm25_store
    if _bm25_store is None:
        from retrieval.bm25_store import BM25Store

        _bm25_store = BM25Store()
    return _bm25_store


def _get_embedder():
    global _embedder
    if _embedder is None:
        from ingestion.embedder import Embedder

        _embedder = Embedder()
    return _embedder


# ── Pydantic request models ─────────────────────────────────────────

class ReportRequest(BaseModel):
    doc_id: int


# ──────────────────────────────────────────────────────────────────────
# Ingestion pipeline (runs synchronously or in background)
# ──────────────────────────────────────────────────────────────────────

def _run_ingestion(doc_id: int, file_path: str) -> None:
    """Full ingestion: parse → chunk → embed → index → NER → TF-IDF."""
    try:
        log.info("⏳ Ingestion started for doc %s", doc_id)

        # 1. Parse PDF
        from ingestion.pdf_parser import parse_pdf

        pages = parse_pdf(file_path)
        total_pages = len(pages)

        # 2. Chunk
        from ingestion.chunker import chunk_pages

        chunks = chunk_pages(pages, doc_id)
        total_chunks = len(chunks)

        if total_chunks == 0:
            crud.update_document_status(
                doc_id, "FAILED", total_pages=total_pages, total_chunks=0
            )
            log.warning("No chunks produced for doc %s — empty PDF?", doc_id)
            return

        # 3. Embed
        embedder = _get_embedder()
        texts = [c["text"] for c in chunks]
        embeddings = embedder.embed(texts)

        # 4. ChromaDB
        vs = _get_vector_store()
        vs.add_documents(doc_id, chunks, embeddings)

        # 5. BM25
        bm25 = _get_bm25_store()
        bm25.build_index(doc_id, chunks)

        # 6. Wire stores into ollama_report for later use
        from generation.ollama_report import set_stores

        set_stores(vs, bm25)

        # 7. Build full text for NER + TF-IDF
        full_text = " ".join(p["text"] for p in pages)

        # 8. Reference (claims, stats, evidence)
        from extraction.reference_builder import build_reference

        build_reference(doc_id, chunks)

        # 9. Cheatsheet
        from extraction.cheatsheet_builder import build_cheatsheet

        build_cheatsheet(doc_id, full_text=full_text)

        # 10. Update status
        crud.update_document_status(
            doc_id,
            "READY",
            total_pages=total_pages,
            total_chunks=total_chunks,
        )
        log.info(
            "✅ Ingestion complete for doc %s — %d pages, %d chunks",
            doc_id, total_pages, total_chunks,
        )

    except Exception:
        log.exception("Ingestion failed for doc %s", doc_id)
        crud.update_document_status(doc_id, "FAILED")


# ──────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────

@app.get("/")
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok", "app": "ragged"}


@app.get("/documents")
async def list_documents():
    """Return all documents in the database."""
    try:
        docs = crud.get_all_documents()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "total_pages": d.total_pages,
                "total_chunks": d.total_chunks,
                "upload_time": d.upload_time.isoformat() if d.upload_time else None,
                "status": d.status,
            }
            for d in docs
        ]
    except Exception as exc:
        log.exception("Error listing documents")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, persist it to disk, and kick off the full ingestion
    pipeline synchronously.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save file to disk
    safe_name = file.filename.replace(" ", "_")
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        log.exception("Failed to save uploaded file")
        raise HTTPException(status_code=500, detail=f"File save error: {exc}")

    # Create DB record
    doc = crud.create_document(filename=safe_name)

    # Run ingestion synchronously (simpler for initial version)
    _run_ingestion(doc.id, file_path)

    # Return updated doc
    updated = crud.get_document(doc.id)
    return {
        "id": updated.id,
        "filename": updated.filename,
        "total_pages": updated.total_pages,
        "total_chunks": updated.total_chunks,
        "upload_time": updated.upload_time.isoformat() if updated.upload_time else None,
        "status": updated.status,
    }


@app.get("/cheatsheet/{doc_id}")
async def get_cheatsheet(doc_id: int):
    """Build (or return cached) cheat sheet for a document."""
    doc = crud.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    # Check cache
    existing = crud.get_cheatsheet(doc_id)
    if existing:
        return existing

    # Build fresh
    try:
        from extraction.cheatsheet_builder import build_cheatsheet

        result = build_cheatsheet(doc_id)
        return result
    except Exception as exc:
        log.exception("Cheatsheet build failed for doc %s", doc_id)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/reference/{doc_id}")
async def get_reference(doc_id: int):
    """Build (or return cached) reference document."""
    doc = crud.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    existing = crud.get_reference(doc_id)
    if existing:
        return existing

    try:
        from extraction.reference_builder import build_reference

        result = build_reference(doc_id)
        return result
    except Exception as exc:
        log.exception("Reference build failed for doc %s", doc_id)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/report")
async def generate_report(req: ReportRequest):
    """Generate an LLM opinion report via Ollama."""
    doc = crud.get_document(req.doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {req.doc_id} not found")

    try:
        # Ensure stores are wired
        from generation.ollama_report import generate_report as gen, set_stores

        set_stores(_get_vector_store(), _get_bm25_store())
        result = gen(req.doc_id)

        if "error" in result and result["error"] == f"Document {req.doc_id} not found":
            raise HTTPException(status_code=404, detail=result["error"])

        return result
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Report generation failed for doc %s", req.doc_id)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/export/{doc_id}/pdf")
async def export_pdf(doc_id: int):
    """Generate a styled PDF and stream it as a download."""
    doc = crud.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

    try:
        from export.pdf_builder import build_pdf

        pdf_path = build_pdf(doc_id)
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=os.path.basename(pdf_path),
        )
    except Exception as exc:
        log.exception("PDF export failed for doc %s", doc_id)
        raise HTTPException(status_code=500, detail=str(exc))


# ──────────────────────────────────────────────────────────────────────
# Run with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
