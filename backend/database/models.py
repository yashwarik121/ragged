"""
database/models.py — SQLAlchemy ORM models for the ragged backend.

Tables are created automatically on import so that downstream code
never has to worry about migration.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DATABASE_URL

# ── Engine & session factory ─────────────────────────────────────────
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ── Models ───────────────────────────────────────────────────────────

class Document(Base):
    """Uploaded PDF metadata."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False)
    total_pages = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    upload_time = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    status = Column(String(64), default="PROCESSING")


class CheatsheetData(Base):
    """One-page cheat sheet artefact for a document."""

    __tablename__ = "cheatsheet_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    abstract = Column(Text, default="")
    key_insights = Column(Text, default="[]")       # JSON string
    entities = Column(Text, default="{}")            # JSON string
    flashcards = Column(Text, default="[]")          # JSON string
    timeline = Column(Text, default="[]")            # JSON string


class ReferenceData(Base):
    """Evidence / reference artefact for a document."""

    __tablename__ = "reference_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    claims = Column(Text, default="[]")              # JSON string
    statistics = Column(Text, default="[]")          # JSON string
    evidence_passages = Column(Text, default="[]")   # JSON string
    citation_index = Column(Text, default="{}")      # JSON string


class ReportData(Base):
    """LLM-generated opinion report for a document."""

    __tablename__ = "report_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    executive_brief = Column(Text, default="")
    critical_analysis = Column(Text, default="{}")   # JSON string
    so_what = Column(Text, default="")
    dissenting_opinion = Column(Text, default="")
    confidence_score = Column(Float, default=0.0)
    passages_used = Column(Text, default="[]")       # JSON string


# ── Create tables ────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)
