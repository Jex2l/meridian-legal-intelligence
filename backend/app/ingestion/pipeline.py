import shutil
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion.chunking import chunk_document
from app.ingestion.extract import extract
from app.models.models import Chunk, Document, DocumentStatus, SourceType


class IngestionError(Exception):
    pass


def ingest_file(
    session: Session,
    *,
    src_path: Path,
    filename: str,
    workspace_id: uuid.UUID | None,
    owner_user_id: uuid.UUID | None,
    source_type: SourceType = SourceType.UPLOAD,
    jurisdiction: str | None = None,
    title: str | None = None,
) -> Document:
    """Extract, chunk, and persist a document. Public-corpus ingestion passes
    workspace_id=None/owner_user_id=None deliberately; every other caller
    must pass both so the row is attributable and filterable at query time.
    """
    if source_type == SourceType.UPLOAD and (workspace_id is None or owner_user_id is None):
        raise IngestionError("Uploaded documents must have a workspace_id and owner_user_id")

    suffix = src_path.suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise IngestionError(f"Unsupported file type: {suffix}")

    stored_name = f"{uuid.uuid4()}{suffix}"
    dest_path = settings.upload_path / stored_name
    shutil.copy(src_path, dest_path)

    document = Document(
        workspace_id=workspace_id,
        owner_user_id=owner_user_id,
        source_type=source_type.value,
        filename=filename,
        title=title,
        jurisdiction=jurisdiction,
        status=DocumentStatus.PROCESSING.value,
        storage_path=str(dest_path),
    )
    session.add(document)
    session.flush()

    try:
        extracted = extract(dest_path)
        raw_chunks = chunk_document(extracted)

        if not raw_chunks:
            raise IngestionError("No extractable text found in document")

        chunk_rows: list[Chunk] = []
        for raw in raw_chunks:
            chunk_rows.append(
                Chunk(
                    document_id=document.id,
                    workspace_id=workspace_id,
                    section_heading=raw.section_heading,
                    page_number=raw.page_number,
                    chunk_index=raw.chunk_index,
                    text=raw.text,
                )
            )
        session.add_all(chunk_rows)
        session.flush()

        # Wire up parent_chunk_id now that each chunk has a real id.
        for raw, row in zip(raw_chunks, chunk_rows):
            if raw.parent_index is not None:
                row.parent_chunk_id = chunk_rows[raw.parent_index].id

        document.status = DocumentStatus.READY.value
        session.commit()
        return document
    except Exception as exc:  # noqa: BLE001
        session.rollback()
        document.status = DocumentStatus.FAILED.value
        document.error = str(exc)
        session.add(document)
        session.commit()
        raise IngestionError(str(exc)) from exc
