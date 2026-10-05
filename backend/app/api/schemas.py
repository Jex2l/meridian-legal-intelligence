import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


class SignupRequest(BaseModel):
    workspace_name: str
    email: str
    name: str


class LoginRequest(BaseModel):
    email: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    email: str


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    title: str | None
    jurisdiction: str | None
    doc_date: date | None
    status: str
    source_type: str
    created_at: datetime


class ChunkOut(BaseModel):
    id: uuid.UUID
    section_heading: str | None
    page_number: int | None
    chunk_index: int
    text: str


class DocumentDetailOut(DocumentOut):
    chunks: list[ChunkOut]


class CitationOut(BaseModel):
    index: int
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str
    section_heading: str | None
    page_number: int | None
    text: str


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=5, ge=1, le=20)
    jurisdiction: str | None = None
    document_id: uuid.UUID | None = None

    @field_validator("question")
    @classmethod
    def _question_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be blank")
        return v


class AskResponse(BaseModel):
    question: str
    answer_text: str
    low_confidence: bool
    ungrounded_response_rejected: bool
    rejection_reason: str | None = None
    citations: list[CitationOut]


class DraftRequest(BaseModel):
    task: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=6, ge=1, le=20)
    jurisdiction: str | None = None
    document_id: uuid.UUID | None = None

    @field_validator("task")
    @classmethod
    def _task_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("task must not be blank")
        return v


class DraftResponse(BaseModel):
    task: str
    draft_text: str
    low_confidence: bool
    ungrounded_response_rejected: bool
    rejection_reason: str | None = None
    citations: list[CitationOut]
