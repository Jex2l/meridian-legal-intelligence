"""CLI for ingesting a document and for bootstrapping a workspace/user.

Usage:
    python -m app.ingestion.cli init-workspace "Acme Law" "alice@acme.law" "Alice"
    python -m app.ingestion.cli ingest <workspace_id> <user_id> /path/to/file.pdf
"""

import argparse
import sys
import uuid
from pathlib import Path

from app.core.db import SessionLocal, init_db
from app.ingestion.pipeline import ingest_file
from app.models.models import SourceType, User, Workspace


def cmd_init_workspace(args: argparse.Namespace) -> None:
    init_db()
    with SessionLocal() as session:
        ws = Workspace(name=args.workspace_name)
        session.add(ws)
        session.flush()
        user = User(workspace_id=ws.id, email=args.email, name=args.user_name)
        session.add(user)
        session.commit()
        print(f"workspace_id={ws.id}")
        print(f"user_id={user.id}")


def cmd_ingest(args: argparse.Namespace) -> None:
    init_db()
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with SessionLocal() as session:
        source_type = SourceType.PUBLIC_CORPUS if args.public else SourceType.UPLOAD
        workspace_id = None if args.public else uuid.UUID(args.workspace_id)
        owner_user_id = None if args.public else uuid.UUID(args.user_id)

        document = ingest_file(
            session,
            src_path=path,
            filename=path.name,
            workspace_id=workspace_id,
            owner_user_id=owner_user_id,
            source_type=source_type,
            jurisdiction=args.jurisdiction,
        )
        print(f"document_id={document.id} status={document.status} chunks={len(document.chunks)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LexRAG ingestion CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-workspace")
    p_init.add_argument("workspace_name")
    p_init.add_argument("email")
    p_init.add_argument("user_name")
    p_init.set_defaults(func=cmd_init_workspace)

    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("workspace_id", nargs="?", default="")
    p_ingest.add_argument("user_id", nargs="?", default="")
    p_ingest.add_argument("path")
    p_ingest.add_argument("--public", action="store_true", help="Ingest into the public case-law corpus")
    p_ingest.add_argument("--jurisdiction", default=None)
    p_ingest.set_defaults(func=cmd_ingest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
