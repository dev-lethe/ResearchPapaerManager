import uuid

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models.entities import Paper
from app.services import paper_index


def test_upload_index_commits_without_fetching_unused_record(monkeypatch):
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def add_now(connection, _):
        connection.create_function("now", 0, lambda: "2026-01-01 00:00:00")

    Paper.__table__.create(engine)
    monkeypatch.setattr(paper_index, "SessionLocal", sessionmaker(bind=engine))
    statements = []

    @event.listens_for(engine, "before_cursor_execute")
    def record_query(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    paper_id = uuid.uuid4()
    try:
        paper_index.create_uploaded_paper(
            paper_id=paper_id, title="Paper", publication_year=2024, journal=None,
            doi="10.1234/example", publisher_url=None, pdf_path=f"{paper_id}.pdf",
            pdf_original_name="paper.pdf", pdf_sha256="a" * 64,
        )
        assert not any(statement.lstrip().upper().startswith("SELECT") for statement in statements)
        duplicates = paper_index.find_duplicate_papers_by_hash(pdf_sha256="a" * 64)
        assert [item.paper_id for item in duplicates] == [str(paper_id)]
        assert paper_index.find_duplicate_papers_by_doi(normalized_doi="10.1234/EXAMPLE") == duplicates
    finally:
        engine.dispose()
