from __future__ import annotations

from collections import Counter

from app.schemas.local_metadata import LocalPaperMetadata
from app.schemas.local_search import (
    LocalPaperSearchItem,
    LocalPaperSearchResponse,
    LocalTagSummaryItem,
    LocalTagSummaryResponse,
)
from app.services.local_files import list_local_paper_files
from app.services.local_metadata import read_local_metadata
from app.services.local_notes import read_local_note


def _normalize_text(value: str) -> str:
    return value.strip().lower()


def _matches_filter(
    metadata: LocalPaperMetadata,
    *,
    status: str | None,
    year: int | None,
    conference: str | None,
    keyword: str | None,
    keywords: list[str] | None,
) -> bool:
    if status and metadata.status != status:
        return False

    if year is not None and metadata.year != year:
        return False

    if conference and _normalize_text(conference) not in _normalize_text(metadata.conference or ""):
        return False

    if keyword:
        target = _normalize_text(keyword)
        if all(target not in _normalize_text(item) for item in metadata.keywords):
            return False

    if keywords:
        normalized_tags = {_normalize_text(item) for item in metadata.keywords}
        for raw_keyword in keywords:
            expected = _normalize_text(raw_keyword)
            if not expected:
                continue
            if expected not in normalized_tags:
                return False

    return True


def _build_markdown_preview(note_content: str, max_lines: int = 20, max_chars: int = 2400) -> str:
    stripped = note_content.strip()
    if not stripped:
        return ""

    lines = stripped.splitlines()[:max_lines]
    preview = "\n".join(lines).strip()
    if len(preview) > max_chars:
        preview = preview[:max_chars].rstrip()
    return preview


def search_local_papers(
    papers_directory: str,
    notes_directory: str,
    *,
    q: str | None = None,
    status: str | None = None,
    year: int | None = None,
    conference: str | None = None,
    keyword: str | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    per_page: int = 50,
) -> LocalPaperSearchResponse:
    _, local_files = list_local_paper_files(papers_directory)

    query = _normalize_text(q or "")
    matched_items: list[LocalPaperSearchItem] = []
    for local_file in local_files:
        _, _, metadata = read_local_metadata(notes_directory, local_file.relative_path)
        if not _matches_filter(
            metadata,
            status=status,
            year=year,
            conference=conference,
            keyword=keyword,
            keywords=keywords,
        ):
            continue

        preview = ""
        if query:
            _, _, note_content, _ = read_local_note(notes_directory, local_file.relative_path)
            haystack = "\n".join([
                local_file.name,
                metadata.title or "",
                " ".join(metadata.authors),
                metadata.journal or "",
                metadata.doi or "",
                note_content,
                metadata.conference or "",
                " ".join(metadata.keywords),
            ]).lower()
            if query not in haystack:
                continue
            preview = _build_markdown_preview(note_content)

        matched_items.append(
            LocalPaperSearchItem(
                relative_path=local_file.relative_path,
                name=local_file.name,
                size_bytes=local_file.size_bytes,
                note_preview=preview,
                metadata=metadata,
            )
        )

    total = len(matched_items)
    safe_per_page = max(1, per_page)
    safe_page = max(1, page)
    total_pages = max(1, (total + safe_per_page - 1) // safe_per_page)
    if safe_page > total_pages:
        safe_page = total_pages

    start = (safe_page - 1) * safe_per_page
    end = start + safe_per_page
    items = matched_items[start:end]
    if not query:
        # Without a full-text query, only visible papers need their notes read.
        for item in items:
            _, _, note_content, _ = read_local_note(notes_directory, item.relative_path)
            item.note_preview = _build_markdown_preview(note_content)

    return LocalPaperSearchResponse(
        total=total,
        page=safe_page,
        per_page=safe_per_page,
        total_pages=total_pages,
        items=items,
    )


def summarize_local_tags(papers_directory: str, notes_directory: str) -> LocalTagSummaryResponse:
    _, local_files = list_local_paper_files(papers_directory)

    statuses = Counter()
    years = Counter()
    conferences = Counter()
    keywords = Counter()

    for local_file in local_files:
        _, _, metadata = read_local_metadata(notes_directory, local_file.relative_path)

        statuses[metadata.status] += 1
        if metadata.year is not None:
            years[str(metadata.year)] += 1
        if metadata.conference:
            conferences[metadata.conference.strip()] += 1
        for item in metadata.keywords:
            key = item.strip()
            if key:
                keywords[key] += 1

    def to_sorted_items(counter: Counter) -> list[LocalTagSummaryItem]:
        return [
            LocalTagSummaryItem(value=value, count=count)
            for value, count in sorted(counter.items(), key=lambda entry: (-entry[1], entry[0]))
        ]

    return LocalTagSummaryResponse(
        statuses=to_sorted_items(statuses),
        years=to_sorted_items(years),
        conferences=to_sorted_items(conferences),
        keywords=to_sorted_items(keywords),
    )
