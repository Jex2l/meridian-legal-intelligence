from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas import AskRequest, AskResponse, CitationOut, DraftRequest, DraftResponse
from app.generation.answer import answer_question
from app.generation.citations import extract_and_validate_citations
from app.generation.draft import DRAFTING_CONFIDENCE_THRESHOLD, draft as run_draft
from app.models.models import User
from app.retrieval.search import SearchFilters

router = APIRouter(tags=["qa"])


def _citations_out(answer_text: str, retrieved) -> list[CitationOut]:
    validation = extract_and_validate_citations(answer_text, retrieved)
    return [
        CitationOut(
            index=c.index,
            chunk_id=c.chunk.chunk_id,
            document_id=c.chunk.document_id,
            document_filename=c.chunk.document_filename,
            section_heading=c.chunk.section_heading,
            page_number=c.chunk.page_number,
            text=c.chunk.text,
        )
        for c in validation.citations
    ]


@router.post("/ask", response_model=AskResponse)
def ask(
    req: AskRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AskResponse:
    filters = SearchFilters(jurisdiction=req.jurisdiction, document_id=req.document_id)
    # workspace_id is resolved from the authenticated user, never from the
    # request body -- the client cannot ask on behalf of another workspace.
    try:
        result = answer_question(db, req.question, current_user.workspace_id, k=req.k, filters=filters)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    citations = [] if (result.low_confidence or result.ungrounded_response_rejected) else _citations_out(
        result.answer_text, result.retrieved_chunks
    )
    return AskResponse(
        question=result.question,
        answer_text=result.answer_text,
        low_confidence=result.low_confidence,
        ungrounded_response_rejected=result.ungrounded_response_rejected,
        rejection_reason=result.rejection_reason,
        citations=citations,
    )


@router.post("/draft", response_model=DraftResponse)
def draft(
    req: DraftRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DraftResponse:
    filters = SearchFilters(jurisdiction=req.jurisdiction, document_id=req.document_id)
    try:
        result = run_draft(
            db, req.task, current_user.workspace_id, k=req.k, filters=filters,
            confidence_threshold=DRAFTING_CONFIDENCE_THRESHOLD,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    citations = [] if (result.low_confidence or result.ungrounded_response_rejected) else _citations_out(
        result.draft_text, result.retrieved_chunks
    )
    return DraftResponse(
        task=result.task,
        draft_text=result.draft_text,
        low_confidence=result.low_confidence,
        ungrounded_response_rejected=result.ungrounded_response_rejected,
        rejection_reason=result.rejection_reason,
        citations=citations,
    )
