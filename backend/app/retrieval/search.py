"""Hybrid retrieval: BM25-ish full-text search + dense embeddings, fused with
Reciprocal Rank Fusion, then optionally reranked by a cross-encoder.

The workspace/public filter is applied INSIDE both SQL queries' WHERE
clauses (not as a post-filter on results), so a chunk belonging to another
workspace is never fetched from the database in the first place -- it can't
leak into the candidate set, let alone reach the LLM.
"""

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.retrieval.embedding import embed_query
from app.retrieval.reranker import rerank as cross_encoder_rerank

RRF_K = 60


@dataclass
class SearchFilters:
    jurisdiction: str | None = None
    document_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID | None
    text: str
    section_heading: str | None
    page_number: int | None
    document_filename: str
    bm25_rank: int | None = None
    dense_rank: int | None = None
    fused_score: float = 0.0
    rerank_score: float | None = None


def _filter_clause(filters: SearchFilters | None, params: dict) -> str:
    clauses = []
    if filters:
        if filters.jurisdiction:
            # Case-insensitive: a client passing "new york" vs. "New York"
            # should not silently get zero results from a strict `=` match.
            clauses.append("d.jurisdiction ILIKE :jurisdiction")
            params["jurisdiction"] = filters.jurisdiction
        if filters.document_id:
            clauses.append("c.document_id = :document_id")
            params["document_id"] = str(filters.document_id)
        if filters.date_from:
            clauses.append("d.doc_date >= :date_from")
            params["date_from"] = filters.date_from
        if filters.date_to:
            clauses.append("d.doc_date <= :date_to")
            params["date_to"] = filters.date_to
    return ("AND " + " AND ".join(clauses)) if clauses else ""


def _bm25_candidates(
    session: Session, query: str, workspace_id: uuid.UUID, filters: SearchFilters | None, limit: int
) -> list[RetrievedChunk]:
    params: dict = {"ws": str(workspace_id), "q": query, "limit": limit}
    extra = _filter_clause(filters, params)
    sql = text(
        f"""
        SELECT c.id, c.document_id, c.workspace_id, c.text, c.section_heading,
               c.page_number, d.filename
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE (c.workspace_id = :ws OR c.workspace_id IS NULL)
          AND c.tsv @@ plainto_tsquery('english', :q)
          {extra}
        ORDER BY ts_rank_cd(c.tsv, plainto_tsquery('english', :q)) DESC
        LIMIT :limit
        """
    )
    rows = session.execute(sql, params).fetchall()
    return [
        RetrievedChunk(
            chunk_id=r[0], document_id=r[1], workspace_id=r[2], text=r[3],
            section_heading=r[4], page_number=r[5], document_filename=r[6],
        )
        for r in rows
    ]


def _dense_candidates(
    session: Session, query_vector: list[float], workspace_id: uuid.UUID, filters: SearchFilters | None, limit: int
) -> list[RetrievedChunk]:
    vec_literal = "[" + ",".join(str(x) for x in query_vector) + "]"
    params: dict = {"ws": str(workspace_id), "qvec": vec_literal, "limit": limit}
    extra = _filter_clause(filters, params)
    sql = text(
        f"""
        SELECT c.id, c.document_id, c.workspace_id, c.text, c.section_heading,
               c.page_number, d.filename
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE (c.workspace_id = :ws OR c.workspace_id IS NULL)
          AND c.embedding IS NOT NULL
          {extra}
        ORDER BY c.embedding <=> CAST(:qvec AS vector)
        LIMIT :limit
        """
    )
    rows = session.execute(sql, params).fetchall()
    return [
        RetrievedChunk(
            chunk_id=r[0], document_id=r[1], workspace_id=r[2], text=r[3],
            section_heading=r[4], page_number=r[5], document_filename=r[6],
        )
        for r in rows
    ]


def hybrid_search(
    session: Session,
    query: str,
    workspace_id: uuid.UUID,
    k: int = 5,
    candidate_k: int = 30,
    filters: SearchFilters | None = None,
    use_reranker: bool | None = None,
) -> list[RetrievedChunk]:
    # None (the implicit default for answer_question()/draft()'s callers)
    # defers to settings.enable_reranker; CLI/eval callers pass an explicit
    # True/False and are unaffected.
    if use_reranker is None:
        use_reranker = settings.enable_reranker

    bm25_results = _bm25_candidates(session, query, workspace_id, filters, candidate_k)
    query_vector = embed_query(query)
    dense_results = _dense_candidates(session, query_vector, workspace_id, filters, candidate_k)

    merged: dict[uuid.UUID, RetrievedChunk] = {}
    for rank, chunk in enumerate(bm25_results, start=1):
        merged[chunk.chunk_id] = chunk
        chunk.bm25_rank = rank
    for rank, chunk in enumerate(dense_results, start=1):
        if chunk.chunk_id in merged:
            merged[chunk.chunk_id].dense_rank = rank
        else:
            chunk.dense_rank = rank
            merged[chunk.chunk_id] = chunk

    for chunk in merged.values():
        score = 0.0
        if chunk.bm25_rank is not None:
            score += 1.0 / (RRF_K + chunk.bm25_rank)
        if chunk.dense_rank is not None:
            score += 1.0 / (RRF_K + chunk.dense_rank)
        chunk.fused_score = score

    fused = sorted(merged.values(), key=lambda c: c.fused_score, reverse=True)[:candidate_k]

    if not use_reranker or not fused:
        return fused[:k]

    scores = cross_encoder_rerank(query, [c.text for c in fused])
    for chunk, score in zip(fused, scores):
        chunk.rerank_score = score
    fused.sort(key=lambda c: c.rerank_score, reverse=True)
    return fused[:k]
