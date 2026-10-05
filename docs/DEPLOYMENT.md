# Deploying to production, for free

This is the handoff checklist for the parts I can't do for you: creating
accounts on hosting platforms. Account creation and logging in with a
password are things I won't do on your behalf regardless of cost — so
everything below that says "you" is a step only you can take. Everything
I could prepare in code ahead of this (the Groq provider, CORS config,
`render.yaml`) is already committed to `main`.

**Honest scope of "free":** every service below has a real free tier with
no credit card required at signup (as of when this was written — verify
current terms yourself, they change). The tradeoffs are real too: a
512MB-RAM free web service, a database that may pause after inactivity,
and a backend that cold-starts after 15 minutes idle. This is a solid free
demo deployment, not a production SLA.

## 1. Database — Supabase

1. Go to [supabase.com](https://supabase.com), sign up, and create a new
   project (pick any region close to you; free tier).
2. In the project dashboard, go to **Database → Extensions**, search for
   `vector`, and enable it (this is `pgvector`, already assumed by this
   project's schema).
3. Go to **Project Settings → Database → Connection string**, choose the
   **URI** / "Transaction pooler" format, and copy it. It looks like:
   ```
   postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-xxxx.pooler.supabase.com:6543/postgres
   ```
4. This project's `DATABASE_URL` needs the `postgresql+psycopg://` scheme
   (SQLAlchemy driver prefix) instead of bare `postgresql://`. Rewrite the
   copied string's scheme accordingly — e.g.:
   ```
   postgresql+psycopg://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-xxxx.pooler.supabase.com:6543/postgres
   ```
5. Send me this connection string (or set it directly as `DATABASE_URL` in
   Render's dashboard in step 4 below) — I'll use it to confirm the schema
   initializes correctly (`init_db()` runs automatically on backend
   startup and is idempotent).

**Free tier limits to know:** Supabase free projects pause after 7 days of
no API activity (a visit to the dashboard or an API call un-pauses it,
with a short delay) and cap storage/bandwidth — fine for a demo, not for
real traffic.

## 2. LLM — Groq

1. Go to [console.groq.com](https://console.groq.com), sign up (free, no
   card).
2. Go to **API Keys → Create API Key**, name it (e.g. `meridian-prod`),
   and copy the key — it's shown once.
3. Send me the key to set as `GROQ_API_KEY` in Render (step 4), or set it
   there yourself.

**Free tier limits to know:** Groq's free tier has generous but real rate
limits (requests/tokens per minute) that reset over time — fine for a
demo's traffic, will throttle under real load.

## 3. Embeddings — HuggingFace (needed before Render)

Render's free tier is 512MB RAM, which — confirmed by actually deploying
and hitting it — is not enough to load the embedding + reranker models
locally via `sentence-transformers`/`torch`, even with a CPU-only torch
build. So production calls HuggingFace's hosted embedding API instead of
loading a model in-process, and runs without the cross-encoder reranker
(hybrid search falls back to its RRF fused score — see
`app/retrieval/search.py`).

1. Go to [huggingface.co](https://huggingface.co), sign up (free, no card).
2. Go to **Settings → Access Tokens → Create new token**. Choose the
   **"Fine-grained"** type, give it a name, and enable the
   **"Make calls to Inference Providers"** permission (sometimes shown as
   "Inference" under serverless). Copy the token (starts with `hf_`).

## 4. Backend API — Render

1. Go to [render.com](https://render.com) and sign up (GitHub login is
   easiest, since the repo is already on your GitHub).
2. **New + → Blueprint**, connect the `meridian-legal-intelligence` repo.
   Render will detect `render.yaml` at the repo root and propose a
   `meridian-legal-backend` web service on the free plan, with
   `EMBEDDING_PROVIDER=huggingface_api` and `ENABLE_RERANKER=false`
   already set from the blueprint. Confirm it.
   - If you'd rather configure manually instead of via Blueprint: **New +
     → Web Service**, connect the repo, set **Root Directory** to
     `backend`, **Build Command** to `pip install -r requirements-render.txt`
     (not plain `requirements.txt` — that one includes the heavy ML
     libraries this deployment deliberately avoids), **Start Command** to
     `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`, plan **Free**.
3. In the service's **Environment** tab, add:
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the Supabase connection string from step 1 (with `postgresql+psycopg://`) |
   | `GROQ_API_KEY` | the key from step 2 |
   | `HF_API_TOKEN` | the token from step 3 |
   | `SECRET_KEY` | a long random string — generate one with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"` and never reuse the repo's dev default |
   | `CORS_ALLOWED_ORIGINS` | leave as `http://localhost:3000` for now — you'll update this in step 6 once Vercel gives you real URLs |
   | `UPLOAD_DIR` | `/tmp/uploads` (see Known Limitations below) |
   - If you deployed manually instead of via Blueprint, also add
     `EMBEDDING_PROVIDER=huggingface_api` and `ENABLE_RERANKER=false` here
     (the Blueprint path sets these automatically from `render.yaml`).
4. Deploy. Once live, Render gives you a URL like
   `https://meridian-legal-backend.onrender.com`. Check
   `https://<that-url>/health` returns `{"status":"ok"}`.

**Free tier limits to know:** the service spins down after 15 minutes idle
and takes 30–60s to wake up on the next request. RAM should no longer be
the blocker it was during initial setup, since the backend doesn't load
any ML model in-process in this configuration — but it's still a 512MB
instance, so keep that in mind if you add other memory-hungry features
later.

## 5. Client portal + marketing site — Vercel

Deploy **two** separate Vercel projects from the same repo (one per app):

1. Go to [vercel.com](https://vercel.com), sign up (GitHub login easiest).
2. **Add New → Project**, import `meridian-legal-intelligence`.
   - **Root Directory:** `frontend`
   - Framework preset: Next.js (auto-detected)
   - Add environment variables:
     | Key | Value |
     |---|---|
     | `NEXT_PUBLIC_API_BASE_URL` | your Render backend URL from step 4 |
     | `NEXT_PUBLIC_MARKETING_URL` | the website's Vercel URL (you'll get this in the next sub-step — come back and set it after) |
   - Deploy. Note the resulting URL, e.g. `https://meridian-legal-portal.vercel.app`.
3. **Add New → Project** again, same repo:
   - **Root Directory:** `website`
   - Add environment variable:
     | Key | Value |
     |---|---|
     | `NEXT_PUBLIC_APP_URL` | the `frontend` project's Vercel URL from the previous sub-step |
   - Deploy. Note this URL too, e.g. `https://meridian-legal-site.vercel.app`.
4. Go back to the `frontend` project's env vars and set
   `NEXT_PUBLIC_MARKETING_URL` to this `website` URL, then redeploy
   (Vercel → Deployments → ⋯ → Redeploy) so it picks up the new value.

## 6. Close the loop — CORS

Back in Render (step 4), set `CORS_ALLOWED_ORIGINS` to your real `frontend`
Vercel URL (comma-separate if you later add a custom domain), e.g.:

```
CORS_ALLOWED_ORIGINS=https://meridian-legal-portal.vercel.app
```

Redeploy the backend. Now visit your `website` URL, click "Client Login",
sign up, upload a document, and ask a question — that's the full stack
live.

## Known limitations of this specific free deployment

- **Uploaded file originals don't persist.** Render's free tier disk is
  ephemeral — it's wiped on every redeploy/restart. This project already
  separates "the original file" (stored on disk, used only during
  ingestion) from "the extracted text and chunks" (stored in Postgres,
  used for every query) — so **search and Q&A keep working** after a
  restart, but the original uploaded PDF/DOCX itself is gone, and
  re-downloading the source file isn't possible. For a real deployment,
  point `UPLOAD_DIR` at persistent object storage (S3, Supabase Storage)
  instead — not built here, flagged as a gap.
- **No OCR in this deployment.** Render's native Python runtime doesn't
  have `poppler`/`tesseract` installed, and the free tier doesn't support
  a custom Dockerfile with `apt-get`. Scanned PDFs needing OCR will fail
  to ingest; text-layer PDFs and DOCX files are unaffected.
- **Cold starts.** The first request after 15 minutes of inactivity takes
  30–60 seconds while Render wakes the service back up.
- **No cross-encoder reranking in production.** `ENABLE_RERANKER=false`
  means retrieval relies on the RRF-fused BM25+dense score alone, not the
  reranked order — confirmed via the eval harness to still work (see
  `docs/BUILD_LOG.md`), just with somewhat lower precision than the fully
  reranked local-dev configuration. There's no remote reranking API wired
  up here; if you need reranking in production, the realistic options are
  upgrading off the free Render plan to fit the local model, or building a
  remote reranker integration (not done in this repo).
- **Embeddings depend on HuggingFace's Inference API being up and within
  its free rate limits.** If HF has an outage or you hit a rate limit,
  ingestion and retrieval will fail with a clear error (not a crash) until
  it recovers.
- **Demo auth is still demo auth.** Nothing about this deployment adds
  password authentication — see the existing Known Limitations in the
  main [README](../README.md).
