# LexRAG

A legal research and drafting assistant MVP: upload documents, search a public
case-law slice, ask grounded questions with citations, and generate first
drafts. Built in phases; this file is updated as each phase lands.

**Not legal advice.** All output must be reviewed by a licensed attorney.

## Status: Phase 1 complete — scaffold, Docker Compose, ingestion pipeline

### What's built
- `docker-compose.yml`: a single Postgres instance (`pgvector/pgvector:pg16`)
  with data persisted to `./data/postgres` on this SSD. Postgres doubles as
  the metadata store, the BM25-ish full-text index (native `tsvector`, wired
  up in Phase 2), and the dense-vector store (via the `pgvector` extension) —
  one datastore instead of Postgres + Qdrant + OpenSearch, which keeps the
  MVP's cross-document joins and the access-control filter (below) inside a
  single SQL query instead of stitched across three systems. Revisit this if
  BM25 relevance turns out to need a real inverted-index engine.
- `backend/app/models/models.py`: data model —
  `Workspace` → `User` → `Document` → `Chunk`. Every `Document` and `Chunk`
  carries a `workspace_id` (nullable only for the public case-law corpus,
  which every workspace can read). This is deliberate: it means the Phase 6
  access-control filter is just `WHERE workspace_id = :ws OR workspace_id IS
  NULL`, applied inside the retrieval query itself, with no reworking of
  ingestion or the schema.
- `backend/app/ingestion/extract.py`: PDF text extraction via `pdfplumber`,
  DOCX via `python-docx`, OCR fallback via `pdf2image` + `pytesseract` when a
  PDF page yields too little text to be a real text layer.
- `backend/app/ingestion/chunking.py`: legal-aware chunking. Splits on
  recognized heading patterns (`ARTICLE I`, `SECTION 1.2`, `1.1 Foo`,
  `(a) Foo`, ALL-CAPS headings) and nests sub-clauses under their enclosing
  section via `parent_index`. Falls back to paragraph-grouping (~1200 chars)
  when no legal structure is detected (e.g. a plain memo).
- `backend/app/ingestion/pipeline.py`: orchestrates extract → chunk → persist,
  copies the source file into `data/uploads`, and enforces that uploaded
  documents always get a `workspace_id` + `owner_user_id` (the public corpus
  is the only path allowed to omit both).
- `backend/app/ingestion/cli.py`: CLI to bootstrap a workspace/user and ingest
  a file.
- Tests: `backend/tests/` — extraction (text + OCR-fallback path, OCR itself
  stubbed so tests don't need tesseract installed), chunking (heading
  detection, parent nesting, fallback), and pipeline/DB tests including one
  that asserts two workspaces' chunks never collide in a single query.

### How to run it

```bash
cd LexRAG
make up          # starts Postgres (pgvector) via Docker Compose
make venv        # creates backend/.venv and installs dependencies
make test        # runs the test suite against the live Postgres container
```

Ingest a document from the CLI:

```bash
cd backend && source .venv/bin/activate

python -m app.ingestion.cli init-workspace "Acme Law LLP" "alice@acme.law" "Alice Attorney"
# prints workspace_id=... user_id=...

python -m app.ingestion.cli <workspace_id> <user_id> /path/to/contract.pdf
# prints document_id=... status=ready chunks=N
```

Ingest into the public case-law corpus (no workspace):

```bash
python -m app.ingestion.cli --public /path/to/case.pdf
```

### Deviation from the suggested stack
Using Postgres + pgvector for both the vector index and the BM25-style
full-text search, instead of Qdrant/OpenSearch, to keep the MVP's retrieval
queries (and the per-workspace isolation filter) inside one engine. Can be
split out later if hybrid-search quality or scale demands a dedicated engine.

### Known limitations (Phase 1)
- No embeddings generated yet — `Chunk.embedding` exists in the schema but is
  populated starting Phase 2.
- No Alembic migrations yet; `init_db()` does `create_all`. Fine for an MVP,
  called out here so it isn't mistaken for an oversight.
- OCR requires `poppler` and `tesseract` system binaries, only exercised when
  a PDF page has too little extractable text.

### Next: Phase 2
Hybrid retrieval (BM25 + dense embeddings) with cross-encoder reranking, and
a CLI to query it.
