from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Session:
    with SessionLocal() as session:
        yield session


def init_db() -> None:
    """Create extensions and all tables. Idempotent."""
    from sqlalchemy import text

    import app.models.models  # noqa: F401  ensures models are registered on Base

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    _ensure_search_indexes()
    _ensure_user_columns()


def _ensure_search_indexes() -> None:
    """Add the full-text (tsvector) column/index and the vector index.

    Not expressed as SQLAlchemy columns because a STORED generated column
    isn't part of the Column API; done as idempotent raw SQL instead of an
    Alembic migration, consistent with create_all() above (see README known
    limitations).
    """
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE chunks
                ADD COLUMN IF NOT EXISTS tsv tsvector
                GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chunks_tsv ON chunks USING GIN (tsv)"))
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS ix_chunks_embedding
                ON chunks USING hnsw (embedding vector_cosine_ops)
                """
            )
        )


def _ensure_user_columns() -> None:
    """Add the clickwrap-acceptance columns to an existing users table.
    Same idempotent-raw-SQL pattern as _ensure_search_indexes() -- see its
    docstring for why this isn't an Alembic migration."""
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_version VARCHAR(32)"))
