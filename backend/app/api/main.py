import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import auth, documents, qa
from app.core.config import settings
from app.core.db import init_db

logger = logging.getLogger("lexrag")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    _warm_up_models()
    yield


def _warm_up_models() -> None:
    """Force-load the embedding and reranker models (sentence-transformers)
    during startup instead of lazily on a live request.

    Both are `@lru_cache`d singletons that download from HuggingFace and
    load into memory on first use (see app/retrieval/embedding.py and
    reranker.py). Left lazy, that cost lands on whichever user's request
    happens to be first -- on a free-tier host this took 47+ seconds in
    practice and blew past the platform's request-gateway timeout (502,
    even though the app was still working). Startup has a much more
    generous timeout (the deploy process waited minutes for a port to
    open), so paying the cost here means no live request ever has to.
    """
    try:
        from app.retrieval.embedding import embed_texts

        embed_texts(["warm-up"])

        # The reranker needs sentence_transformers, deliberately not
        # installed in production (see requirements-render.txt) when
        # ENABLE_RERANKER=false -- warming it up here would always fail
        # with ModuleNotFoundError in that configuration. Respect the same
        # flag that gates every other caller of this model (hybrid_search's
        # use_reranker default and app/generation/faithfulness.py's live
        # gate) instead of unconditionally trying.
        if settings.enable_reranker:
            from app.retrieval.reranker import rerank

            rerank("warm-up", ["warm-up"])

        logger.info("Models warmed up (reranker %s).", "included" if settings.enable_reranker else "skipped")
    except Exception:  # noqa: BLE001
        # Don't block startup on a warm-up failure (e.g. no network to
        # HuggingFace in some environment) -- the app will just pay the
        # lazy-load cost on first real request instead, same as before
        # this existed.
        logger.exception("Model warm-up failed; falling back to lazy load on first request.")


app = FastAPI(title="LexRAG API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(qa.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort safety net: any exception not already turned into an
    HTTPException by a route (DB connection drop, a bug, an unexpected
    third-party library error) gets logged with its full traceback
    server-side and returns a generic 500 to the client -- never a raw
    stack trace, which could leak internals (file paths, query shapes)."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
