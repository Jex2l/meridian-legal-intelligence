import os

import pytest
import sqlalchemy

from app.core.db import init_db
from app.eval.metrics import (
    RetrievalEvalRow,
    citation_points_to_gold,
    faithfulness_score,
    mean_reciprocal_rank,
    retrieval_precision_at_k,
    retrieval_recall_at_k,
)
from app.eval.fixtures import GOLD_QA, GoldItem
from app.eval.seed import seed
from app.retrieval.search import SearchFilters, hybrid_search

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


@pytest.fixture
def db_session():
    from app.core.db import SessionLocal

    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


def test_gold_set_has_at_least_30_items():
    assert len(GOLD_QA) >= 30


def test_metric_helpers_on_toy_data():
    rows = [
        RetrievalEvalRow(gold_id="a", found_at_rank=1),
        RetrievalEvalRow(gold_id="b", found_at_rank=3),
        RetrievalEvalRow(gold_id="c", found_at_rank=None),
    ]
    assert retrieval_recall_at_k(rows) == pytest.approx(2 / 3)
    assert retrieval_precision_at_k(rows, k=5) == pytest.approx((1 / 5 + 1 / 5 + 0) / 3)
    assert mean_reciprocal_rank(rows) == pytest.approx((1 + 1 / 3 + 0) / 3)


def test_seeded_corpus_retrieval_recall_is_reasonable(db_session):
    """Integration smoke test: seed the demo corpus (idempotent) and check
    that hybrid search finds the gold passage for a sample of questions.
    Not the full 36-item eval (that's app/eval/run_eval.py); this just
    guards against the seed/retrieval wiring silently breaking."""
    ws = seed(db_session)

    sample = GOLD_QA[:5] + GOLD_QA[-3:]  # a few private + the public-corpus ones
    hits = 0
    for gold in sample:
        filters = SearchFilters(jurisdiction=gold.jurisdiction) if gold.jurisdiction else None
        results = hybrid_search(db_session, gold.question, ws.id, k=5, filters=filters)
        if any(c.document_filename == gold.gold_filename and gold.gold_text_substring in c.text for c in results):
            hits += 1
    assert hits / len(sample) >= 0.75


def test_citation_points_to_gold_true_and_false(db_session):
    ws = seed(db_session)
    gold = next(g for g in GOLD_QA if g.scope == "private")
    results = hybrid_search(db_session, gold.question, ws.id, k=5)
    gold_rank = next(i for i, c in enumerate(results, start=1) if gold.gold_text_substring in c.text)

    answer_citing_gold = f"This is supported by the relevant clause [{gold_rank}]."
    assert citation_points_to_gold(answer_citing_gold, results, gold) is True

    other_rank = 1 if gold_rank != 1 else 2
    answer_citing_other = f"This cites something else [{other_rank}]."
    assert citation_points_to_gold(answer_citing_other, results, gold) is False


def test_faithfulness_score_distinguishes_supported_vs_unsupported(db_session):
    ws = seed(db_session)
    gold = next(g for g in GOLD_QA if g.gold_filename == "master_services_agreement.docx" and "indemnif" in g.gold_text_substring.lower())
    results = hybrid_search(db_session, gold.question, ws.id, k=5)
    gold_rank = next(i for i, c in enumerate(results, start=1) if gold.gold_text_substring in c.text)

    supported = f"The Service Provider must indemnify the Client for third-party claims from its breach [{gold_rank}]."
    faithful, total = faithfulness_score(supported, results)
    assert total == 1
    assert faithful == 1

    unsupported = f"The moon is made of cheese according to this clause [{gold_rank}]."
    faithful, total = faithfulness_score(unsupported, results)
    assert total == 1
    assert faithful == 0
