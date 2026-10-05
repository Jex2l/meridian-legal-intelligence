"""CLI to query hybrid retrieval directly, and to backfill embeddings.

Usage:
    python -m app.retrieval.cli backfill
    python -m app.retrieval.cli query <workspace_id> "indemnification cap" [--k 5] [--no-rerank] [--jurisdiction NY]
"""

import argparse
import uuid

from app.core.db import SessionLocal, init_db
from app.retrieval.backfill import backfill_embeddings
from app.retrieval.search import SearchFilters, hybrid_search


def cmd_backfill(args: argparse.Namespace) -> None:
    init_db()
    with SessionLocal() as session:
        n = backfill_embeddings(session)
        print(f"embedded {n} chunks")


def cmd_query(args: argparse.Namespace) -> None:
    init_db()
    filters = SearchFilters(jurisdiction=args.jurisdiction)
    with SessionLocal() as session:
        results = hybrid_search(
            session,
            query=args.query,
            workspace_id=uuid.UUID(args.workspace_id),
            k=args.k,
            filters=filters,
            use_reranker=not args.no_rerank,
        )
        for i, r in enumerate(results, start=1):
            score = r.rerank_score if r.rerank_score is not None else r.fused_score
            heading = r.section_heading or "(no heading)"
            print(f"[{i}] score={score:.4f} doc={r.document_filename} section={heading} page={r.page_number}")
            print("    " + r.text[:200].replace("\n", " "))


def main() -> None:
    parser = argparse.ArgumentParser(description="LexRAG retrieval CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_backfill = sub.add_parser("backfill")
    p_backfill.set_defaults(func=cmd_backfill)

    p_query = sub.add_parser("query")
    p_query.add_argument("workspace_id")
    p_query.add_argument("query")
    p_query.add_argument("--k", type=int, default=5)
    p_query.add_argument("--no-rerank", action="store_true")
    p_query.add_argument("--jurisdiction", default=None)
    p_query.set_defaults(func=cmd_query)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
