"""Embed any chunks that don't yet have a vector. Called after ingestion
(or standalone) since embedding is a separate, swappable step from
extraction/chunking.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Chunk
from app.retrieval.embedding import embed_texts

BATCH_SIZE = 64


def backfill_embeddings(session: Session) -> int:
    total = 0
    while True:
        pending = session.scalars(select(Chunk).where(Chunk.embedding.is_(None)).limit(BATCH_SIZE)).all()
        if not pending:
            break
        vectors = embed_texts([c.text for c in pending])
        for chunk, vector in zip(pending, vectors):
            chunk.embedding = vector
        session.commit()
        total += len(pending)
    return total
