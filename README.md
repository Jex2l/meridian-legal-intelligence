# LexRAG

A legal research and drafting assistant MVP: upload documents, search a public
case-law slice, ask grounded questions with citations, and generate first
drafts. Built in phases; this file is updated as each phase lands.

**Not legal advice.** All output must be reviewed by a licensed attorney.

## Status: Phase 3 complete — grounded generation, citations, drafting mode

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

## Phase 2: hybrid retrieval, reranking, query CLI

### What's built
- `backend/app/core/db.py`: `_ensure_search_indexes()` adds a `tsv` generated
  column (`to_tsvector('english', text)`, `STORED`) with a GIN index for
  full-text search, and an HNSW cosine index on `chunks.embedding` for dense
  search. Raw idempotent SQL rather than Alembic, same tradeoff as Phase 1.
- `backend/app/retrieval/embedding.py`: dense embeddings via
  `sentence-transformers/all-MiniLM-L6-v2` (384-dim, matches the schema).
- `backend/app/retrieval/reranker.py`: cross-encoder reranking via
  `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- `backend/app/retrieval/search.py`: `hybrid_search()` — runs a full-text
  query and a dense-vector query **separately**, each with
  `WHERE (workspace_id = :ws OR workspace_id IS NULL)` baked directly into
  its SQL, then fuses the two ranked lists with Reciprocal Rank Fusion (RRF),
  then reranks the fused shortlist with the cross-encoder. Metadata filters
  (`jurisdiction`, `document_id`, date range) are appended to both queries'
  `WHERE` clauses too — never applied after the fact. This is the mechanism
  that satisfies the "isolation enforced inside the search query" constraint:
  a chunk from another workspace is never fetched from Postgres in the first
  place.
- `backend/app/retrieval/backfill.py`: embeds any chunk with `embedding IS
  NULL` in batches; called automatically at the end of `ingest_file()`
  (`embed=True` by default) and also runnable standalone.
- `backend/app/retrieval/cli.py`: query CLI and a manual `backfill` command.
- Tests: `backend/tests/test_search.py` — retrieval relevance, cross-encoder
  reranking, metadata-filter enforcement, and (most importantly) a test that
  ingests an "indemnification" clause into workspace A only and a scoped
  query from workspace B never returns it, even though public-corpus
  (`workspace_id IS NULL`) chunks remain visible from both.
- `backend/tests/conftest.py` now truncates the chunks/documents/users/
  workspaces tables before every test, since `ingest_file()` commits
  internally and a bare `session.rollback()` can't undo that — without this,
  repeated local test runs silently accumulate rows in the dev database.

### How to run it

```bash
cd backend && source .venv/bin/activate

# embed any chunks ingested before Phase 2 existed
python -m app.retrieval.cli backfill

# query
python -m app.retrieval.cli query <workspace_id> "indemnification obligations" --k 3
python -m app.retrieval.cli query <workspace_id> "indemnification obligations" --k 3 --no-rerank
python -m app.retrieval.cli query <workspace_id> "query" --jurisdiction "New York"
```

### Known limitations (Phase 2)
- BM25-style ranking uses Postgres `ts_rank_cd` over `to_tsvector`, not a
  true BM25 implementation — a reasonable MVP approximation, revisit if
  lexical-match quality matters more as the corpus grows.
- RRF fusion weights BM25 and dense retrieval equally; no tuning yet.
- No eval numbers yet for recall@k / precision / reranker lift — that's
  Phase 4.

## Phase 3: grounded generation, citation validation, drafting mode

### What's built
- `backend/app/generation/provider.py`: `LLMProvider` interface so the model
  can be swapped. `AnthropicProvider` calls Claude via the `anthropic` SDK;
  `FakeProvider` is a deterministic stand-in used by tests (no network/API
  key needed to test the pipeline logic itself).
- `backend/app/generation/prompts.py`: system/user prompts that require
  every claim to carry a `[n]` citation marker and instruct the model to
  answer exactly `"I couldn't find support for this."` when the passages
  don't support an answer. A separate drafting prompt asks for a draft plus
  a cited "Reasoning" section.
- `backend/app/generation/citations.py`: parses `[n]` markers out of the
  model's response and validates each one resolves to an actually-retrieved
  chunk. This is the enforcement mechanism for "never invent a citation" —
  it's a check against the retrieved set, not a trust in the prompt.
- `backend/app/generation/confidence.py`: low-confidence gate based on the
  top reranked chunk's cross-encoder score. If retrieval confidence is low,
  the fallback message is returned **without calling the LLM at all** (saves
  cost and avoids giving the model a chance to make something up from weak
  context). Q&A uses a stricter threshold (`0.0`) than drafting (`-8.0`),
  because the cross-encoder is trained on question-style queries and scores
  an imperative drafting instruction lower than an equivalent question even
  against a genuinely relevant passage — confirmed empirically in
  `tests/test_generation.py`.
- `backend/app/generation/answer.py` / `draft.py`: orchestrate retrieve →
  prompt → generate → validate citations → reject if any citation is
  invented (falls back to the same "couldn't find support" message rather
  than returning a partially-trustworthy answer).
- `backend/app/generation/cli.py`: `ask` and `draft` subcommands.
- Tests (`tests/test_generation.py`, using `FakeProvider`): a valid-citation
  answer is accepted; an invented citation (`[99]` when at most 5 passages
  were retrieved) is rejected and replaced with the fallback; an unrelated
  question never reaches the LLM at all (asserted via a provider that raises
  if called); drafting produces a cited draft + reasoning section.

### How to run it

```bash
cd backend && source .venv/bin/activate
# add a real key to backend/.env (ANTHROPIC_API_KEY=...) to actually call Claude

python -m app.generation.cli ask <workspace_id> "What does the indemnification clause say?"
python -m app.generation.cli draft <workspace_id> "Rewrite the indemnity clause to favor the buyer"
```

Without an API key configured, both commands fail with a clear
`ANTHROPIC_API_KEY is not set` error rather than a stack trace — verified by
running `ask` against this repo's own demo contract.

### Known limitations (Phase 3)
- The confidence thresholds are tuned by hand against this small demo
  corpus, not against the eval set yet — Phase 4 should revisit them with
  real recall/precision numbers.
- Citation validation checks that a cited passage number exists; it does
  not yet verify the specific sentence is actually supported by that
  passage's text (a stronger "faithfulness" check) — that's the Phase 4 eval
  harness's job, run offline, not an online gate.

### Next: Phase 4
Eval harness: a 30+ question/answer gold set, recall@k/precision, citation
accuracy, and a faithfulness check, with a script that prints a comparison
table.
