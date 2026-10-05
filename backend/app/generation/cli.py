"""CLI for grounded Q&A and drafting.

Usage:
    python -m app.generation.cli ask <workspace_id> "question"
    python -m app.generation.cli draft <workspace_id> "rewrite the indemnity clause to favor the buyer"
"""

import argparse
import sys
import uuid

from app.core.db import SessionLocal, init_db
from app.generation.answer import answer_question
from app.generation.draft import draft as run_draft


def _print_sources(chunks):
    print("\nSources:")
    for i, c in enumerate(chunks, start=1):
        heading = c.section_heading or "(no heading)"
        print(f"  [{i}] {c.document_filename} - {heading} (page {c.page_number})")


def cmd_ask(args: argparse.Namespace) -> None:
    init_db()
    with SessionLocal() as session:
        try:
            result = answer_question(session, args.question, uuid.UUID(args.workspace_id), k=args.k)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(result.answer_text)
        if not result.low_confidence and not result.ungrounded_response_rejected:
            _print_sources(result.retrieved_chunks)
        if result.ungrounded_response_rejected:
            print("\n[blocked: model cited a passage outside the retrieved set]")


def cmd_draft(args: argparse.Namespace) -> None:
    init_db()
    with SessionLocal() as session:
        try:
            result = run_draft(session, args.task, uuid.UUID(args.workspace_id), k=args.k)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
        print(result.draft_text)
        if not result.low_confidence and not result.ungrounded_response_rejected:
            _print_sources(result.retrieved_chunks)
        if result.ungrounded_response_rejected:
            print("\n[blocked: model cited a passage outside the retrieved set]")


def main() -> None:
    parser = argparse.ArgumentParser(description="LexRAG generation CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("workspace_id")
    p_ask.add_argument("question")
    p_ask.add_argument("--k", type=int, default=5)
    p_ask.set_defaults(func=cmd_ask)

    p_draft = sub.add_parser("draft")
    p_draft.add_argument("workspace_id")
    p_draft.add_argument("task")
    p_draft.add_argument("--k", type=int, default=6)
    p_draft.set_defaults(func=cmd_draft)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
