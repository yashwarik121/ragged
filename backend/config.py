"""
config.py — Central configuration constants for the ragged backend.

Directories are created automatically on import so that the rest of
the application can assume they exist.
"""

import os
from pathlib import Path

# ── Directories ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = str(BASE_DIR / "uploads")
CHROMA_DIR = str(BASE_DIR / "chroma_db")
EXPORT_DIR = str(BASE_DIR / "exports")

# ── Database ─────────────────────────────────────────────────────────
DATABASE_URL = f"sqlite:///{BASE_DIR / 'brief.db'}"

# ── Ollama ───────────────────────────────────────────────────────────
OLLAMA_URL = "http://localhost:11434"

# ── ML Models ────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# ── Chunking ─────────────────────────────────────────────────────────
CHUNK_SIZE = 400       # words per chunk
CHUNK_OVERLAP = 50     # word overlap between consecutive chunks

# ── Ensure required directories exist on import ──────────────────────
for _dir in (UPLOAD_DIR, CHROMA_DIR, EXPORT_DIR):
    os.makedirs(_dir, exist_ok=True)
