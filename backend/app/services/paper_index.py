from __future__ import annotations

import uuid
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import func, select

from app.core.db import SessionLocal
from app.models.entities import Paper, ReadingStatus


@dataclass(frozen=True)
class PaperDuplicateEntry:
    paper_id: str
    pdf_path: str


@contextmanager
def db_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def find_duplicate_papers_by_hash(*, pdf_sha256: str) -> list[PaperDuplicateEntry]:
    with db_session() as session:
        statement = (
            select(Paper.id, Paper.pdf_path)
            .where(Paper.pdf_sha256 == pdf_sha256)
            .order_by(Paper.created_at.desc())
        )
        rows = session.execute(statement).all()
        return [PaperDuplicateEntry(paper_id=str(row.id), pdf_path=row.pdf_path) for row in rows]


def find_duplicate_papers_by_doi(*, normalized_doi: str | None) -> list[PaperDuplicateEntry]:
    if not normalized_doi:
        return []

    with db_session() as session:
        statement = (
            select(Paper.id, Paper.pdf_path)
            .where(func.lower(Paper.doi) == normalized_doi.lower())
            .order_by(Paper.created_at.desc())
        )
        rows = session.execute(statement).all()
        return [PaperDuplicateEntry(paper_id=str(row.id), pdf_path=row.pdf_path) for row in rows]


def create_uploaded_paper(
    *,
    paper_id: uuid.UUID,
    title: str,
    publication_year: int | None,
    journal: str | None,
    doi: str | None,
    publisher_url: str | None,
    pdf_path: str,
    pdf_original_name: str,
    pdf_sha256: str,
) -> None:
    with db_session() as session:
        paper = Paper(
            id=paper_id,
            title=title,
            publication_year=publication_year,
            journal=journal,
            doi=doi,
            publisher_url=publisher_url,
            pdf_path=pdf_path,
            pdf_original_name=pdf_original_name,
            pdf_sha256=pdf_sha256,
            reading_status=ReadingStatus.INBOX,
            rating=0,
        )
        session.add(paper)
