import os

import pytest
import sqlalchemy

from app.core.db import init_db

pytestmark = pytest.mark.skipif(
    os.environ.get("LEXRAG_SKIP_DB_TESTS") == "1",
    reason="DB not available",
)


@pytest.fixture(autouse=True, scope="module")
def _ensure_db():
    try:
        init_db()
    except sqlalchemy.exc.OperationalError:
        pytest.skip("Postgres is not reachable; start it with `docker compose up -d`")
    yield


def test_warm_up_skips_reranker_when_disabled(monkeypatch):
    """Regression test: _warm_up_models() must not attempt to load the
    cross-encoder when ENABLE_RERANKER=false -- it isn't installed in that
    configuration (see requirements-render.txt) and the attempt would
    always fail with ModuleNotFoundError."""
    import app.api.main as main_module

    monkeypatch.setattr(main_module.settings, "enable_reranker", False)

    def exploding_rerank(*args, **kwargs):
        raise AssertionError("reranker must not be warmed up when enable_reranker is False")

    # Patch at the source module so main.py's lazy `from ... import rerank`
    # picks up the patched version.
    import app.retrieval.reranker as reranker_module

    monkeypatch.setattr(reranker_module, "rerank", exploding_rerank)

    main_module._warm_up_models()  # must not raise
