import mimetypes
import uuid
from json import JSONDecodeError, loads

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.doi_metadata import DoiMetadataRequest, DoiMetadataResponse
from app.schemas.local_files import LocalPaperFileListResponse
from app.schemas.local_metadata import LocalPaperMetadata, LocalPaperMetadataResponse
from app.schemas.local_notes import LocalNoteResponse, LocalNoteUpdateRequest
from app.schemas.local_search import LocalPaperSearchResponse, LocalTagSummaryResponse
from app.schemas.local_upload import LocalUploadResponse
from app.services.local_files import list_local_paper_files, resolve_local_file_path
from app.services.local_auto_metadata import infer_upload_metadata, normalize_doi, resolve_doi_metadata
from app.services.local_metadata import read_local_metadata, write_local_metadata
from app.services.paper_index import create_uploaded_paper, find_duplicate_papers_by_doi, find_duplicate_papers_by_hash
from app.services.local_notes import (
    ensure_note_template_if_missing,
    pdf_exists_for_relative_path,
    write_local_note,
)
from app.services.local_search import search_local_papers, summarize_local_tags
from app.services.local_upload import save_uploaded_pdf

router = APIRouter()


def _parse_form_list(value: str | None) -> list[str]:
    source = (value or "").strip()
    if not source:
        return []
    if source.startswith("["):
        try:
            raw = loads(source)
            if isinstance(raw, list):
                return [text for item in raw if (text := str(item).strip())]
        except JSONDecodeError:
            pass
    return [text for item in source.split(",") if (text := item.strip())]


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/metadata/doi", response_model=DoiMetadataResponse)
def post_metadata_by_doi(payload: DoiMetadataRequest) -> DoiMetadataResponse:
    normalized = normalize_doi(payload.doi)
    if not normalized:
        raise HTTPException(status_code=400, detail="DOI is required")

    resolved = resolve_doi_metadata(normalized, settings.crossref_mailto)
    if not resolved:
        raise HTTPException(status_code=404, detail="DOI metadata not found")

    return DoiMetadataResponse(**resolved)


@router.post("/papers/upload", response_model=LocalUploadResponse)
def upload_local_pdf(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    doi: str | None = Form(default=None),
    year: int | None = Form(default=None),
    conference: str | None = Form(default=None),
    journal: str | None = Form(default=None),
    volume: str | None = Form(default=None),
    month: str | None = Form(default=None),
    number: str | None = Form(default=None),
    pages: str | None = Form(default=None),
    authors: str | None = Form(default=None),
    affiliations: str | None = Form(default=None),
    abstract: str | None = Form(default=None),
    publisher_url: str | None = Form(default=None),
    project_page: str | None = Form(default=None),
    keywords: str | None = Form(default=None),
) -> LocalUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Unsupported content type")

    paper_id = uuid.uuid4()
    storage_filename = f"{paper_id}.pdf"

    try:
        _, relative_path, size_bytes, pdf_sha256 = save_uploaded_pdf(
            file.file,
            file.filename,
            settings.local_papers_path,
            storage_filename=storage_filename,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    venue = (conference or "").strip() or (journal or "").strip() or None
    inferred_metadata = infer_upload_metadata(
        file_name=file.filename,
        title=title,
        doi=doi,
        year=year,
        venue=venue,
        crossref_mailto=settings.crossref_mailto,
        authors=_parse_form_list(authors),
        affiliations=_parse_form_list(affiliations),
        abstract=abstract,
        publisher_url=publisher_url,
        journal=journal,
        volume=volume,
        month=month,
        number=number,
        pages=pages,
        project_page=project_page,
        keywords=[item.strip() for item in (keywords or "").split(",") if item.strip()],
    )

    duplicate_pdf_entries = find_duplicate_papers_by_hash(pdf_sha256=pdf_sha256)
    normalized_doi = normalize_doi(inferred_metadata.doi)
    duplicate_doi_entries = find_duplicate_papers_by_doi(normalized_doi=normalized_doi)

    create_uploaded_paper(
        paper_id=paper_id,
        title=inferred_metadata.title or file.filename,
        publication_year=inferred_metadata.year,
        journal=inferred_metadata.journal or inferred_metadata.conference,
        doi=normalized_doi,
        publisher_url=inferred_metadata.publisher_url,
        pdf_path=relative_path,
        pdf_original_name=file.filename,
        pdf_sha256=pdf_sha256,
    )

    write_local_metadata(settings.local_notes_path, relative_path, inferred_metadata)

    return LocalUploadResponse(
        paper_id=str(paper_id),
        relative_path=relative_path,
        file_name=file.filename,
        size_bytes=size_bytes,
        pdf_sha256=pdf_sha256,
        inferred_metadata=inferred_metadata,
        duplicate_pdf_relative_paths=[item.pdf_path for item in duplicate_pdf_entries],
        duplicate_doi_relative_paths=[item.pdf_path for item in duplicate_doi_entries],
        duplicate_pdf_paper_ids=[item.paper_id for item in duplicate_pdf_entries],
        duplicate_doi_paper_ids=[item.paper_id for item in duplicate_doi_entries],
        requires_manual_doi=not bool((inferred_metadata.doi or "").strip()),
    )


@router.get("/papers/local-files", response_model=LocalPaperFileListResponse)
def get_local_paper_files() -> LocalPaperFileListResponse:
    root_path, files = list_local_paper_files(settings.local_papers_path)
    return LocalPaperFileListResponse(root_path=str(root_path), files=files)


@router.get("/papers/local-files/content/{relative_path:path}")
def get_local_paper_file_content(relative_path: str) -> FileResponse:
    resolved = resolve_local_file_path(settings.local_papers_path, relative_path)
    if resolved is None:
        raise HTTPException(status_code=404, detail="File not found")

    _, file_path = resolved
    media_type, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(
        path=file_path,
        media_type=media_type or "application/octet-stream",
        filename=file_path.name,
        headers={"Content-Disposition": f'inline; filename="{file_path.name}"'},
    )


@router.get("/papers/local-notes/{relative_path:path}", response_model=LocalNoteResponse)
def get_local_note(relative_path: str) -> LocalNoteResponse:
    if not pdf_exists_for_relative_path(settings.local_papers_path, relative_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    _, _, metadata = read_local_metadata(settings.local_notes_path, relative_path)
    root, note_path, content = ensure_note_template_if_missing(
        settings.local_notes_path,
        relative_path,
        metadata.title,
    )
    return LocalNoteResponse(
        root_path=str(root),
        note_relative_path=str(note_path.relative_to(root)),
        content=content,
        exists=note_path.exists(),
    )


@router.put("/papers/local-notes/{relative_path:path}", response_model=LocalNoteResponse)
def put_local_note(relative_path: str, payload: LocalNoteUpdateRequest) -> LocalNoteResponse:
    if not pdf_exists_for_relative_path(settings.local_papers_path, relative_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    root, note_path = write_local_note(settings.local_notes_path, relative_path, payload.content)

    return LocalNoteResponse(
        root_path=str(root),
        note_relative_path=str(note_path.relative_to(root)),
        content=payload.content,
        exists=True,
    )


@router.get("/papers/local-metadata/{relative_path:path}", response_model=LocalPaperMetadataResponse)
def get_local_metadata(relative_path: str) -> LocalPaperMetadataResponse:
    if not pdf_exists_for_relative_path(settings.local_papers_path, relative_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    root, metadata_path, metadata = read_local_metadata(settings.local_notes_path, relative_path)
    return LocalPaperMetadataResponse(
        root_path=str(root),
        metadata_relative_path=str(metadata_path.relative_to(root)),
        relative_path=relative_path,
        metadata=metadata,
    )


@router.put("/papers/local-metadata/{relative_path:path}", response_model=LocalPaperMetadataResponse)
def put_local_metadata(relative_path: str, payload: LocalPaperMetadata) -> LocalPaperMetadataResponse:
    if not pdf_exists_for_relative_path(settings.local_papers_path, relative_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    root, metadata_path, metadata = write_local_metadata(settings.local_notes_path, relative_path, payload)
    return LocalPaperMetadataResponse(
        root_path=str(root),
        metadata_relative_path=str(metadata_path.relative_to(root)),
        relative_path=relative_path,
        metadata=metadata,
    )


@router.get("/papers/local-search", response_model=LocalPaperSearchResponse)
def get_local_search(
    q: str | None = None,
    status: str | None = Query(default=None, pattern="^(INBOX|TO_READ|READING|READ)$"),
    year: int | None = None,
    conference: str | None = None,
    keyword: str | None = None,
    keywords: str | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
) -> LocalPaperSearchResponse:
    parsed_keywords = [item.strip() for item in (keywords or "").split(",") if item.strip()] or None

    return search_local_papers(
        settings.local_papers_path,
        settings.local_notes_path,
        q=q,
        status=status,
        year=year,
        conference=conference,
        keyword=keyword,
        keywords=parsed_keywords,
        page=page,
        per_page=per_page,
    )


@router.get("/tags/local-summary", response_model=LocalTagSummaryResponse)
def get_local_tag_summary() -> LocalTagSummaryResponse:
    return summarize_local_tags(settings.local_papers_path, settings.local_notes_path)
