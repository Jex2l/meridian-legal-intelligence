# LexRAG

A legal research and drafting assistant MVP: upload documents, search a public
case-law slice, ask grounded questions with citations, and generate first
drafts. Built in phases; this file is updated as each phase lands.

**Not legal advice.** All output must be reviewed by a licensed attorney.

**Status: MVP complete (Phases 1–7).** The build log below (one section per
phase) is kept as the detailed record of what was built, why, and what's
verified at each step. This top section is the map: architecture, how to
run everything, and where things stand overall.

## Architecture

```mermaid
flowchart LR
    subgraph Client
        UI["Next.js UI\nchat + source viewer"]
    end

    subgraph Backend [FastAPI backend]
        API["API routers\nauth / documents / ask / draft"]
        ING["Ingestion\nextract -> chunk -> embed"]
        RET["Hybrid retrieval\nBM25 + dense -> RRF -> rerank"]
        GEN["Generation\nprompt -> Claude -> validate citations"]
    end

    subgraph Data [Postgres + pgvector, on the mounted SSD]
        PG[("workspaces / users / documents / chunks\ntsvector + vector indexes")]
    end

    LLM[["Anthropic API\n(swappable LLMProvider)"]]

    UI -- "Bearer token" --> API
    API --> ING --> PG
    API --> RET --> PG
    API --> GEN
    GEN --> RET
    GEN --> LLM
    RET -. "workspace_id = :ws OR NULL\napplied inside the SQL" .-> PG
```

**The isolation guarantee, concretely:** `workspace_id` lives on every
`Document` and `Chunk` from ingestion onward. Both halves of hybrid
retrieval (`app/retrieval/search.py`) apply
`WHERE (workspace_id = :ws OR workspace_id IS NULL)` directly inside their
SQL — a chunk from another workspace is never fetched from Postgres, so it
can't leak into the LLM's context. The API layer resolves `:ws` from a
verified auth token, never from client input (see Phase 6's audit below).

## Quickstart

```bash
# 1. Postgres (pgvector), data persisted under ./data on this SSD
docker compose up -d

# 2. backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # add ANTHROPIC_API_KEY to use /ask and /draft
python -m pytest -q       # 32 tests, all against the live Postgres container
uvicorn app.api.main:app --reload --port 8000

# 3. frontend (separate terminal)
cd frontend
cp .env.local.example .env.local
npm install
npm run dev   # http://localhost:3000
```

Try it via CLI without the UI:

```bash
cd backend && source .venv/bin/activate
python -m app.ingestion.cli init-workspace "Acme Law LLP" "alice@acme.law" "Alice Attorney"
python -m app.ingestion.cli ingest <workspace_id> <user_id> /path/to/contract.pdf
python -m app.retrieval.cli query <workspace_id> "indemnification obligations"
python -m app.generation.cli ask <workspace_id> "What does the indemnification clause say?"
python -m app.eval.run_eval   # retrieval metrics; --generation adds citation accuracy/faithfulness
```

## Build log

## Phase 1: repo scaffold, Docker Compose, ingestion pipeline

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

## Phase 4: eval harness and baseline report

### What's built
- `backend/app/eval/fixtures.py`: a 36-item gold Q/A set (`GOLD_QA`) over a
  synthetic demo corpus — 6 private contracts (Master Services Agreement,
  Employment Agreement, Commercial Lease, Software License, Merger
  Agreement, Mutual NDA; 5 clauses each = 30 items) plus 2 public-corpus
  case summaries (3 holdings each = 6 items). **The corpus text is original
  boilerplate written for this project**, not real case law: CourtListener's
  API now requires an authenticated token this environment doesn't have
  (confirmed live — anonymous requests get `401`/`403`). `app/ingestion/
  courtlistener.py`-shaped real ingestion would plug into the same
  `ingest_file()` pipeline unchanged once a token is supplied; see Known
  Limitations.
- `backend/app/eval/seed.py`: idempotently ingests the fixture corpus into
  a `LexRAG Eval Demo` workspace (private docs) and the public corpus
  (case summaries) — safe to rerun, skips documents already ingested.
- `backend/app/eval/metrics.py`: `recall@k`, `precision@k`, MRR for
  retrieval; `citation_points_to_gold` (does at least one citation resolve
  to the actual gold passage, not just *a* valid one); `faithfulness_score`
  — splits a generated answer into cited sentences and scores each against
  its cited passage with the cross-encoder (reusing the Phase 2 reranker as
  a cheap entailment proxy, since it doesn't need an extra model or an LLM
  call).
- `backend/app/eval/run_eval.py`: seeds the corpus, runs retrieval at k=1
  and k=5 for "hybrid + rerank" vs. "hybrid, no rerank", and prints a
  comparison table. With `--generation` (needs `ANTHROPIC_API_KEY`), also
  runs citation-accuracy and faithfulness over real generated answers.
- Tests (`tests/test_eval.py`): gold-set size, metric-function correctness
  on toy data, a retrieval smoke test against the seeded corpus, and both
  branches (true/false) of `citation_points_to_gold` and
  `faithfulness_score` against real retrieved chunks.

### How to run it

```bash
cd backend && source .venv/bin/activate
python -m app.eval.run_eval              # retrieval metrics only
python -m app.eval.run_eval --generation # + citation accuracy/faithfulness (needs an API key)
```

### Baseline results (this demo corpus)

```
Retrieval metrics (k=1, n=36 gold Q/A pairs)
config             recall@1  precision@1  MRR
hybrid + rerank    0.94      0.944        0.94
hybrid, no rerank  0.94      0.944        0.94

Retrieval metrics (k=5, n=36 gold Q/A pairs)
config             recall@5  precision@5  MRR
hybrid + rerank    1.00      0.200        0.97
hybrid, no rerank  1.00      0.200        0.97
```

**Honest reading of this result:** reranking shows no lift here, and that's
a real finding, not a bug — on 36 well-separated clauses with little lexical
overlap, BM25+dense fusion alone already ranks the right chunk first almost
every time, so there's nothing for the reranker to fix. The 2/36 recall@1
misses are genuine retrieval failures worth inspecting. Reranking is
expected to matter more on a larger, noisier corpus with semantically
similar distractor clauses (e.g. many contracts' near-identical limitation-
of-liability clauses) — this harness is what you'd rerun against that
corpus to check.

### Known limitations (Phase 4)
- Public case law is synthetic, written for this project, not real
  CourtListener opinions — see above. A real `courtlistener.py` ingestion
  module (CourtListener REST v4, bearer token) is a small addition on top
  of the existing `ingest_file()` pipeline once a token is available, since
  the pipeline already accepts arbitrary text with `workspace_id=None` for
  the public corpus.
- Citation accuracy / faithfulness can't be reported in this environment
  (no `ANTHROPIC_API_KEY`) — the code path is implemented and unit-tested
  with `FakeProvider`-equivalent fixtures, just not run against a real
  model's output here.
- 36 items is enough to clear the "at least 30" bar but is still small;
  recall@5 saturating at 1.00 means k=5 isn't discriminating on this corpus
  size — the k=1 table is the more informative one here.

## Phase 5: FastAPI backend + Next.js UI

### What's built
- `backend/app/core/security.py`: minimal HMAC-signed token auth (email
  only, no password — an explicit MVP shortcut, documented as such). The
  reason it still matters for the isolation requirement: **every API
  endpoint resolves `workspace_id` from the verified token server-side**,
  never from the request body, so a client can't just assert "I'm workspace
  X" on a request.
- `backend/app/api/`: FastAPI app (`main.py`) with routers —
  `auth.py` (`/auth/signup`, `/auth/login`), `documents.py`
  (`/documents/upload`, `/documents`, `/documents/{id}` — all scoped to
  `current_user.workspace_id OR public`, with a 404 rather than 403 for a
  cross-workspace document so existence isn't leaked), and `qa.py`
  (`/ask`, `/draft`, wrapping `answer_question`/`draft` and turning a
  missing-API-key `RuntimeError` into a clean `503` instead of a stack
  trace).
- `frontend/`: Next.js (App Router, TypeScript, Tailwind). Split view —
  chat on the left (`Chat.tsx`, Ask/Draft mode toggle, a persistent "not
  legal advice" banner), source document viewer on the right
  (`SourceViewer.tsx`, renders all of a document's chunks with the cited
  one highlighted and scrolled into view). `CitedText.tsx` turns `[n]`
  markers in an answer into clickable buttons that jump the source viewer
  to that citation's passage. `AuthForm.tsx` handles signup/login;
  `Sidebar.tsx` handles document list + upload. Auth token stored in
  `localStorage` (`lib/session.ts`) with a thin typed API client
  (`lib/api.ts`).

### How to run it

```bash
# terminal 1
cd backend && source .venv/bin/activate
uvicorn app.api.main:app --reload --port 8000

# terminal 2
cd frontend && cp .env.local.example .env.local && npm install && npm run dev
```

Open `http://localhost:3000`, create a workspace, upload a `.pdf`/`.docx`,
and ask a question. Without `ANTHROPIC_API_KEY` set in `backend/.env`,
`/ask` and `/draft` will 503 with a clear message (verified live); an
unrelated question still returns the low-confidence fallback without
hitting that code path at all, same as the CLI.

### Verified live (via the browser)
Signup → document upload → sidebar listing → source viewer rendering all
chunks → low-confidence fallback in chat → clean 503 surfaced as an error
bubble instead of a crash. `npm run build` passes with no TypeScript
errors. Citation-click-to-highlight wasn't exercised against a *real*
generated answer (no API key here to produce one), but it's the same
`scrollIntoView` + highlight path already verified when selecting a
document from the sidebar.

### Known limitations (Phase 5)
- Auth is email-only with no password — fine for an MVP demo, not for
  anything real. Per-endpoint workspace resolution from the token is the
  part that actually matters for the isolation requirement; password auth
  is a separate, orthogonal concern to add later.
- No automated frontend tests (e.g. Playwright) — covered by live manual
  browser verification instead, given the time budget.
- The source viewer shows a document's chunks sequentially, not a rendered
  PDF/DOCX page — good enough to locate and read a cited passage, but not a
  pixel-accurate "document viewer."

## Phase 6: drafting mode + access-control audit

Drafting mode itself was built in Phase 3 (`app/generation/draft.py`) and
wired into the API/UI in Phase 5 — this phase verified it live and audited
isolation end-to-end rather than adding new product surface.

### Verified live
Switched the UI to Draft mode and sent "Rewrite the indemnification clause
to favor the buyer": against an empty workspace it correctly returned the
low-confidence fallback; after uploading the demo contract, retrieval found
the clause and the request reached the LLM call, surfacing the same clean
503 (no API key) as `/ask`. Confirms the confidence gate and the swappable-
provider error path both work identically for drafting as for Q&A.

### Access-control audit: every layer where isolation is enforced
1. **Ingestion** (`app/ingestion/pipeline.py`) — `ingest_file()` raises
   `IngestionError` if an uploaded document is missing `workspace_id` or
   `owner_user_id`; only the public-corpus path may omit them.
2. **Schema** (`app/models/models.py`) — `workspace_id` is denormalized onto
   `Chunk` itself (not just `Document`), so every retrieval query filters
   chunks directly without a join.
3. **Retrieval** (`app/retrieval/search.py`) — both the full-text and the
   vector query apply `WHERE (workspace_id = :ws OR workspace_id IS NULL)`
   inside their own SQL, so a chunk from another workspace is never fetched
   from Postgres, let alone reaches the LLM. This is the mechanism the
   original hard constraint asked for, built in Phase 2.
4. **Generation** (`app/generation/answer.py`, `draft.py`) — take
   `workspace_id` as a plain parameter; they never see a request object to
   trust, only what the caller (API or CLI) passes in.
5. **API** (`app/api/deps.py`, `app/api/routers/*.py`) — `workspace_id` is
   resolved from the HMAC-verified token (`current_user.workspace_id`),
   never read from the request body. `AskRequest`/`DraftRequest` have no
   `workspace_id` field at all, and Pydantic silently drops unknown JSON
   fields by default — so even a client that stuffs a `workspace_id` into
   the body has zero effect, which `test_spoofed_workspace_id_in_request_body_is_ignored`
   proves directly rather than assuming. Document endpoints return `404`
   (not `403`) for a cross-workspace document so the API never confirms
   another workspace's document even exists.
6. **Tests** — in addition to the retrieval-layer isolation test from Phase
   2, `tests/test_api.py` now has
   `test_cross_workspace_question_never_sees_other_workspaces_document`
   (Firm H, with zero documents, gets a low-confidence fallback to a
   question that *would* reach the LLM for Firm A, which owns the matching
   document) and the spoofed-body test above.

### Known limitations (Phase 6)
- This audit covers the paths that exist today (ask/draft/documents). Any
  new endpoint added later must resolve `workspace_id` from
  `current_user`, not from its request schema — there's no automated check
  enforcing that convention (e.g. a linter rule), just this documented
  pattern and the tests above as a regression guard.
- Auth itself (email-only, no password) remains the weakest link in the
  chain, as noted in Phase 5 — it determines *who* `current_user` is, which
  everything above then trusts.

## Phase 7: known limitations, roadmap

### Repo layout

```
LexRAG/
├── docker-compose.yml       # Postgres + pgvector, data on ./data (this SSD)
├── backend/
│   └── app/
│       ├── ingestion/       # extract (PDF/DOCX/OCR), chunk, pipeline, CLI
│       ├── retrieval/       # embeddings, reranker, hybrid search, CLI
│       ├── generation/      # provider, prompts, citations, answer, draft, CLI
│       ├── eval/            # fixtures, seed, metrics, run_eval
│       ├── api/             # FastAPI app, routers, schemas, auth
│       ├── core/            # config, db, security
│       └── models/          # SQLAlchemy models
│   └── tests/               # one file per package above, all against live Postgres
└── frontend/                # Next.js: chat + source viewer split view
```

### Known limitations, all in one place
Tech debt called out per-phase above, gathered here so nothing requires
reading the whole build log to find:

- **No Alembic migrations** — `init_db()` does `create_all` plus idempotent
  raw SQL for the generated `tsvector` column and the HNSW index (Phase 1,
  Phase 2). Fine for an MVP's single schema version; would need real
  migrations before a second schema change ships.
- **BM25 is approximated** via Postgres `ts_rank_cd` over `to_tsvector`,
  not a true BM25 implementation (Phase 2).
- **Public case law is synthetic**, written for this project — CourtListener
  now requires an authenticated API token this environment doesn't have,
  confirmed live (Phase 4). `ingest_file()` already accepts arbitrary text
  with `workspace_id=None`, so real ingestion is a small addition once a
  token exists, not a redesign.
- **No `ANTHROPIC_API_KEY` in this environment** — generation, drafting, and
  the eval harness's citation-accuracy/faithfulness metrics are fully
  implemented and unit-tested with a `FakeProvider`, but weren't run
  against a real model's output here (Phases 3–4). Every other piece
  (retrieval, confidence gating, citation validation, the UI, access
  control) was verified against the real pipeline.
- **Auth is email-only, no password** (Phase 5) — deliberately out of scope
  for an MVP demo; the part that matters for the hard isolation
  requirement (workspace resolved server-side from a verified token, not
  client input) is in place regardless, and audited in Phase 6.
- **No automated frontend tests** — covered by live manual browser
  verification at each UI-touching phase instead, given the time budget
  (Phase 5).
- **Eval set is 36 items** over a small synthetic corpus — clears the
  "at least 30" bar, but small enough that recall@5 saturates at 1.00 and
  the reranker shows no measurable lift (a real finding on this corpus, not
  a bug — see Phase 4's baseline results).

### Roadmap

**Near-term (fills the gaps above):**
1. Real CourtListener ingestion once an API token is available.
2. Run the eval harness with a real `ANTHROPIC_API_KEY` and record actual
   citation-accuracy/faithfulness numbers, not just the retrieval table.
3. Alembic migrations; replace email-only auth with real password/OAuth.
4. Scale the eval corpus (more documents, more distractor clauses) to get
   a reranker comparison that actually differentiates — the current one
   doesn't because the demo corpus is too clean.

**Further out:**
5. Document-level permissions beyond workspace-level (e.g. a document
   visible only to specific users within a workspace).
6. A real source-document viewer (rendered PDF/DOCX with highlight
   overlays) instead of the current sequential chunk list.
7. Streaming answers in the UI instead of waiting for the full response.
8. Multi-turn conversation context for follow-up questions.

### Moving to Kubernetes
Local dev is Docker Compose with one Postgres container; a production
deployment would look like:
- **Postgres** → a managed instance (RDS/Cloud SQL) or a StatefulSet with
  the `pgvector` extension, not a bare container — this is the one
  stateful piece and the most operationally sensitive given it's also the
  isolation boundary.
- **Backend** → a Deployment behind a Service, horizontally scalable since
  `app/api/main.py` is stateless (auth is a signed token, not a session
  store); embeddings/reranking model weights would move to an init
  container or a baked image layer to avoid a cold-start download per pod.
- **Frontend** → a separate Deployment (or a static export behind a CDN,
  since it's a standard Next.js app) pointed at the backend Service via
  `NEXT_PUBLIC_API_BASE_URL`.
- **Secrets** (`ANTHROPIC_API_KEY`, `SECRET_KEY`, DB credentials) → a
  Secret resource / external secrets manager, not `.env` files.
- **Ingestion** is currently synchronous inside the request (upload →
  extract → chunk → embed → respond); at real scale this would move to a
  queue (e.g. a Job or a worker Deployment consuming from SQS/Pub/Sub) so a
  large PDF upload doesn't hold an API pod and a request thread for the
  full OCR+embedding pipeline.
