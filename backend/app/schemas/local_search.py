from pydantic import BaseModel

from app.schemas.local_metadata import LocalPaperMetadata


class LocalPaperSearchItem(BaseModel):
    relative_path: str
    name: str
    size_bytes: int
    note_preview: str
    metadata: LocalPaperMetadata


class LocalPaperSearchResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    items: list[LocalPaperSearchItem]


class LocalTagSummaryItem(BaseModel):
    value: str
    count: int


class LocalTagSummaryResponse(BaseModel):
    statuses: list[LocalTagSummaryItem]
    years: list[LocalTagSummaryItem]
    conferences: list[LocalTagSummaryItem]
    keywords: list[LocalTagSummaryItem]
