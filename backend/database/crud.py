"""
database/crud.py — CRUD helpers for the ragged backend.

Every public function opens its own session so callers don't need to
manage transactions.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from database.models import (
    CheatsheetData,
    Document,
    ReferenceData,
    ReportData,
    SessionLocal,
)

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Document CRUD
# ──────────────────────────────────────────────────────────────────────

def create_document(filename: str, total_pages: int = 0, total_chunks: int = 0) -> Document:
    """Insert a new document row and return it (detached from session)."""
    db = SessionLocal()
    try:
        doc = Document(
            filename=filename,
            total_pages=total_pages,
            total_chunks=total_chunks,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_document(doc_id: int) -> Optional[Document]:
    """Fetch a single document by primary key."""
    db = SessionLocal()
    try:
        return db.query(Document).filter(Document.id == doc_id).first()
    finally:
        db.close()


def get_all_documents() -> list[Document]:
    """Return every document row ordered by upload time (newest first)."""
    db = SessionLocal()
    try:
        return (
            db.query(Document)
            .order_by(Document.upload_time.desc())
            .all()
        )
    finally:
        db.close()


def update_document_status(doc_id: int, status: str, **kwargs: Any) -> None:
    """Update a document's status and optional extra columns."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc is None:
            log.warning("update_document_status: doc %s not found", doc_id)
            return
        doc.status = status
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────────
# Cheatsheet CRUD
# ──────────────────────────────────────────────────────────────────────

def save_cheatsheet(doc_id: int, data: dict) -> CheatsheetData:
    """Upsert cheatsheet data for *doc_id*."""
    db = SessionLocal()
    try:
        existing = db.query(CheatsheetData).filter(
            CheatsheetData.doc_id == doc_id
        ).first()

        payload = {
            "abstract": data.get("abstract", ""),
            "key_insights": json.dumps(data.get("key_insights", [])),
            "entities": json.dumps(data.get("entities", {})),
            "flashcards": json.dumps(data.get("flashcards", [])),
            "timeline": json.dumps(data.get("timeline", [])),
        }

        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            return existing

        cs = CheatsheetData(doc_id=doc_id, **payload)
        db.add(cs)
        db.commit()
        db.refresh(cs)
        return cs
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_cheatsheet(doc_id: int) -> Optional[dict]:
    """Return cheatsheet dict or *None*."""
    db = SessionLocal()
    try:
        row = db.query(CheatsheetData).filter(
            CheatsheetData.doc_id == doc_id
        ).first()
        if row is None:
            return None
        return {
            "doc_id": row.doc_id,
            "abstract": row.abstract,
            "key_insights": json.loads(row.key_insights),
            "entities": json.loads(row.entities),
            "flashcards": json.loads(row.flashcards),
            "timeline": json.loads(row.timeline),
        }
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────────
# Reference CRUD
# ──────────────────────────────────────────────────────────────────────

def save_reference(doc_id: int, data: dict) -> ReferenceData:
    """Upsert reference data for *doc_id*."""
    db = SessionLocal()
    try:
        existing = db.query(ReferenceData).filter(
            ReferenceData.doc_id == doc_id
        ).first()

        payload = {
            "claims": json.dumps(data.get("claims", [])),
            "statistics": json.dumps(data.get("statistics", [])),
            "evidence_passages": json.dumps(data.get("evidence_passages", [])),
            "citation_index": json.dumps(data.get("citation_index", {})),
        }

        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            return existing

        ref = ReferenceData(doc_id=doc_id, **payload)
        db.add(ref)
        db.commit()
        db.refresh(ref)
        return ref
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_reference(doc_id: int) -> Optional[dict]:
    """Return reference dict or *None*."""
    db = SessionLocal()
    try:
        row = db.query(ReferenceData).filter(
            ReferenceData.doc_id == doc_id
        ).first()
        if row is None:
            return None
        return {
            "doc_id": row.doc_id,
            "claims": json.loads(row.claims),
            "statistics": json.loads(row.statistics),
            "evidence_passages": json.loads(row.evidence_passages),
            "citation_index": json.loads(row.citation_index),
        }
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────────
# Report CRUD
# ──────────────────────────────────────────────────────────────────────

def save_report(doc_id: int, data: dict) -> ReportData:
    """Upsert report data for *doc_id*."""
    db = SessionLocal()
    try:
        existing = db.query(ReportData).filter(
            ReportData.doc_id == doc_id
        ).first()

        payload = {
            "executive_brief": data.get("executive_brief", ""),
            "critical_analysis": json.dumps(data.get("critical_analysis", {})),
            "so_what": data.get("so_what", ""),
            "dissenting_opinion": data.get("dissenting_opinion", ""),
            "confidence_score": data.get("confidence_score", 0.0),
            "passages_used": json.dumps(data.get("passages_used", [])),
        }

        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            return existing

        rpt = ReportData(doc_id=doc_id, **payload)
        db.add(rpt)
        db.commit()
        db.refresh(rpt)
        return rpt
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_report(doc_id: int) -> Optional[dict]:
    """Return report dict or *None*."""
    db = SessionLocal()
    try:
        row = db.query(ReportData).filter(
            ReportData.doc_id == doc_id
        ).first()
        if row is None:
            return None
        return {
            "doc_id": row.doc_id,
            "executive_brief": row.executive_brief,
            "critical_analysis": json.loads(row.critical_analysis),
            "so_what": row.so_what,
            "dissenting_opinion": row.dissenting_opinion,
            "confidence_score": row.confidence_score,
            "passages_used": json.loads(row.passages_used),
        }
    finally:
        db.close()
