"""Run the eval suite and print a comparison table.

Usage:
    python -m app.eval.run_eval              # retrieval metrics only
    python -m app.eval.run_eval --generation  # also runs citation accuracy
                                               # and faithfulness (needs
                                               # ANTHROPIC_API_KEY)
"""

import argparse

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.eval.fixtures import GOLD_QA
from app.eval.metrics import (
    RetrievalEvalRow,
    citation_points_to_gold,
    faithfulness_score,
    mean_reciprocal_rank,
    retrieval_precision_at_k,
    retrieval_recall_at_k,
)
from app.eval.seed import seed
from app.retrieval.search import SearchFilters, hybrid_search

K = 5


def _is_gold_chunk(chunk, gold) -> bool:
    return chunk.document_filename == gold.gold_filename and gold.gold_text_substring in chunk.text


def _run_retrieval_config(session, workspace_id, use_reranker: bool, k: int) -> list[RetrievalEvalRow]:
    rows = []
    for gold in GOLD_QA:
        filters = SearchFilters(jurisdiction=gold.jurisdiction) if gold.jurisdiction else None
        results = hybrid_search(
            session, gold.question, workspace_id, k=k, filters=filters, use_reranker=use_reranker
        )
        rank = None
        for i, chunk in enumerate(results, start=1):
            if _is_gold_chunk(chunk, gold):
                rank = i
                break
        rows.append(RetrievalEvalRow(gold_id=gold.id, found_at_rank=rank))
    return rows


def _print_table(headers: list[str], data_rows: list[list[str]]) -> None:
    widths = [max(len(h), *(len(r[i]) for r in data_rows)) for i, h in enumerate(headers)]
    def fmt_row(row):
        return "  ".join(cell.ljust(w) for cell, w in zip(row, widths))
    print(fmt_row(headers))
    print(fmt_row(["-" * w for w in widths]))
    for row in data_rows:
        print(fmt_row(row))


def run_retrieval_comparison(session, workspace_id) -> None:
    configs = [("hybrid + rerank", True), ("hybrid, no rerank", False)]

    for k in (1, K):
        data_rows = []
        for name, use_reranker in configs:
            rows = _run_retrieval_config(session, workspace_id, use_reranker, k)
            recall = retrieval_recall_at_k(rows)
            precision = retrieval_precision_at_k(rows, k)
            mrr = mean_reciprocal_rank(rows)
            data_rows.append([name, f"{recall:.2f}", f"{precision:.3f}", f"{mrr:.2f}"])

        print(f"\nRetrieval metrics (k={k}, n={len(GOLD_QA)} gold Q/A pairs)")
        _print_table([f"config", f"recall@{k}", f"precision@{k}", "MRR"], data_rows)


def run_generation_eval(session, workspace_id) -> None:
    from app.generation.answer import answer_question

    citation_hits = 0
    faithful_total = 0
    cited_sentence_total = 0
    low_confidence_count = 0
    evaluated = 0

    for gold in GOLD_QA:
        filters = SearchFilters(jurisdiction=gold.jurisdiction) if gold.jurisdiction else None
        result = answer_question(session, gold.question, workspace_id, k=K, filters=filters)
        if result.low_confidence or result.ungrounded_response_rejected:
            low_confidence_count += 1
            continue
        evaluated += 1
        if citation_points_to_gold(result.answer_text, result.retrieved_chunks, gold):
            citation_hits += 1
        faithful, total = faithfulness_score(result.answer_text, result.retrieved_chunks)
        faithful_total += faithful
        cited_sentence_total += total

    print(f"\nGeneration metrics (n={len(GOLD_QA)} gold Q/A pairs, {evaluated} answered, "
          f"{low_confidence_count} fell back)")
    citation_accuracy = citation_hits / evaluated if evaluated else 0.0
    faithfulness = faithful_total / cited_sentence_total if cited_sentence_total else 0.0
    _print_table(
        ["metric", "value"],
        [
            ["citation accuracy (cites gold passage)", f"{citation_accuracy:.2f}"],
            ["faithfulness (cited sentences supported)", f"{faithfulness:.2f}"],
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="LexRAG eval harness")
    parser.add_argument("--generation", action="store_true", help="Also run citation accuracy + faithfulness")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as session:
        ws = seed(session)
        run_retrieval_comparison(session, ws.id)

        if args.generation:
            if not settings.anthropic_api_key:
                print("\n--generation requested but ANTHROPIC_API_KEY is not set; skipping.")
            else:
                run_generation_eval(session, ws.id)


if __name__ == "__main__":
    main()
