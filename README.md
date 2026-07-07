# RAGGED

### Drop the doc. Get the brain.

RAGGED is a document intelligence engine. Drop PDFs in, get three outputs:

1. **THE CHEAT SHEET** — Pure extraction. Key terms, top sentences, entities, timeline, abstract.
2. **THE REFERENCE DOC** — Claims with citations, statistics, evidence passages. All cited to page.
3. **THE OPINION REPORT** — Local LLM reads your doc and writes an executive brief, critical analysis, and actionable takeaways.

No API keys. No subscriptions. No cloud. Runs on your machine.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| PDF Parsing | PyMuPDF |
| NER | spaCy (en_core_web_sm) |
| Sentence Ranking | NLTK + TF-IDF (scikit-learn) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | ChromaDB (local, persisted to disk) |
| Sparse Search | rank-bm25 |
| Result Fusion | Reciprocal Rank Fusion (RRF) |
| Reranking | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| LLM | Ollama (llama3 or mistral) — local, no API |
| PDF Export | ReportLab |
| Backend | FastAPI |
| Frontend | React + Vite |
| Database | SQLite (via SQLAlchemy) |

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Ollama** (for the Opinion Report feature)

---

## Ollama Setup

The Opinion Report uses a local LLM via Ollama. Install and configure it:

```bash
# 1. Install Ollama
# Windows: Download from https://ollama.ai/download
# macOS:   brew install ollama
# Linux:   curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull a model (choose one)
ollama pull llama3
# or for a lighter model:
ollama pull mistral

# 3. Start Ollama server
ollama serve
# Ollama runs at http://localhost:11434
```

> **Note:** The Cheat Sheet and Reference Doc work without Ollama. Only the Opinion Report requires it. If Ollama is not running, the report endpoint will return a graceful fallback message.

---

## Quick Start

### Backend

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start the backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/documents` | List all uploaded documents |
| `POST` | `/upload` | Upload a PDF and run full ingestion |
| `GET` | `/cheatsheet/{doc_id}` | Get/build cheat sheet |
| `GET` | `/reference/{doc_id}` | Get/build reference document |
| `POST` | `/report` | Generate LLM opinion report (body: `{"doc_id": 1}`) |
| `GET` | `/export/{doc_id}/pdf` | Download styled PDF report |

---

## How It Works

### Ingestion Pipeline (on upload)

```
PDF → PyMuPDF (text + page numbers)
    → Chunker (400 tokens, 50 overlap)
    → sentence-transformers (dense embeddings)
    → ChromaDB (vector store)
    → BM25 (sparse index)
    → spaCy NER (entities)
    → TF-IDF (key sentences + terms)
    → SQLite (metadata)
```

### Retrieval (for Opinion Report)

```
Query → BM25 search + Vector search
      → RRF Fusion
      → Cross-encoder reranking
      → Top 15 passages → Ollama
```

---

## Project Structure

```
ragged/
├── backend/
│   ├── main.py                     # FastAPI app + all endpoints
│   ├── config.py                   # Configuration constants
│   ├── requirements.txt            # Python dependencies
│   ├── database/
│   │   ├── models.py               # SQLAlchemy models
│   │   └── crud.py                 # CRUD operations
│   ├── ingestion/
│   │   ├── pdf_parser.py           # PyMuPDF text extraction
│   │   ├── chunker.py              # 400-token chunking
│   │   ├── embedder.py             # sentence-transformers embeddings
│   │   ├── ner_extractor.py        # spaCy NER
│   │   └── tfidf_ranker.py         # TF-IDF ranking
│   ├── retrieval/
│   │   ├── vector_store.py         # ChromaDB operations
│   │   ├── bm25_store.py           # BM25 index
│   │   ├── hybrid_search.py        # RRF fusion
│   │   └── reranker.py             # Cross-encoder reranking
│   ├── extraction/
│   │   ├── cheatsheet_builder.py   # Cheat sheet assembly
│   │   └── reference_builder.py    # Reference doc compilation
│   ├── generation/
│   │   └── ollama_report.py        # Ollama LLM + confidence scoring
│   └── export/
│       └── pdf_builder.py          # ReportLab PDF export
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── index.css               # Brutalist design system
        ├── App.jsx                 # Router + theme management
        ├── components/
        │   ├── TextScramble.jsx    # Text scramble animation
        │   ├── Navigation.jsx      # Fixed top nav bar
        │   ├── UploadZone.jsx      # Drag-drop + progress overlay
        │   ├── Flashcard.jsx       # Key terms display
        │   ├── EntityCloud.jsx     # Categorized entity tags
        │   ├── Timeline.jsx        # Vertical timeline
        │   ├── CitationBlock.jsx   # Citation with hover tooltip
        │   ├── ConfidenceMeter.jsx # Animated score display
        │   └── ExportButton.jsx    # PDF download button
        └── pages/
            ├── Home.jsx            # Upload + document library
            ├── CheatSheet.jsx      # Extraction dashboard
            ├── Reference.jsx       # Citations + evidence
            └── Report.jsx          # LLM opinion analysis
```

---

## First Run Notes

- **Model downloads**: On first run, `sentence-transformers`, `cross-encoder`, and `spaCy` will download their models (~500MB total). This happens automatically.
- **NLTK data**: The `punkt_tab` tokenizer is downloaded automatically on first use.
- **Database**: `brief.db` (SQLite) is created automatically in the backend directory.
- **Storage**: Uploaded PDFs are saved to `backend/uploads/`, ChromaDB data to `backend/chroma_db/`.

---

## License

MIT
