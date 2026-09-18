from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ReadingStatus = Literal["INBOX", "TO_READ", "READING", "READ"]


class LocalPaperMetadata(BaseModel):
    status: ReadingStatus = "INBOX"
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    year: int | None = None
    conference: str | None = None
    journal: str | None = None
    volume: str | None = None
    month: str | None = None
    number: str | None = None
    pages: str | None = None
    doi: str | None = None
    abstract: str | None = None
    publisher_url: str | None = None
    project_page: str | None = None
    keywords: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None


class LocalPaperMetadataResponse(BaseModel):
    root_path: str
    metadata_relative_path: str
    relative_path: str
    metadata: LocalPaperMetadata
