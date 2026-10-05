import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.schemas import ChunkOut, DocumentDetailOut, DocumentOut
from app.ingestion.pipeline import IngestionError, ingest_file
from app.models.models import Document, User

router = APIRouter(prefix="/documents", tags=["documents"])

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25MB -- the ingestion pipeline (extract -> OCR ->
# chunk -> embed) runs synchronously inside this request; an unbounded upload could tie
# up a worker for minutes on a huge scanned PDF. Queue-based ingestion (see README
# roadmap) would remove this constraint.


def _workspace_or_public(user: User):
    return or_(Document.workspace_id == user.workspace_id, Document.workspace_id.is_(None))


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile,
    jurisdiction: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx files are supported")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        total = 0
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                tmp_path = Path(tmp.name)
                tmp.close()
                tmp_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024*1024)}MB limit")
            tmp.write(chunk)
        tmp_path = Path(tmp.name)

    try:
        document = ingest_file(
            db,
            src_path=tmp_path,
            filename=file.filename or f"upload{suffix}",
            workspace_id=current_user.workspace_id,
            owner_user_id=current_user.id,
            jurisdiction=jurisdiction,
        )
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return DocumentOut.model_validate(document, from_attributes=True)


@router.get("", response_model=list[DocumentOut])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Document]:
    rows = db.scalars(
        select(Document).where(_workspace_or_public(current_user)).order_by(Document.created_at.desc())
    ).all()
    return list(rows)


@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document(
    document_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DocumentDetailOut:
    document = db.scalar(
        select(Document).where(Document.id == document_id, _workspace_or_public(current_user))
    )
    if document is None:
        # Same 404 whether the document doesn't exist or belongs to another
        # workspace -- never confirm another workspace's document exists.
        raise HTTPException(status_code=404, detail="Document not found")

    chunks = sorted(document.chunks, key=lambda c: c.chunk_index)
    return DocumentDetailOut(
        **DocumentOut.model_validate(document, from_attributes=True).model_dump(),
        chunks=[ChunkOut.model_validate(c, from_attributes=True) for c in chunks],
    )
