from pydantic import BaseModel, Field


class DoiMetadataRequest(BaseModel):
    doi: str


class DoiMetadataResponse(BaseModel):
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    affiliations: list[str] = Field(default_factory=list)
    year: int | None = None
    journal: str | None = None
    doi: str | None = None
    abstract: str | None = None
    publisher_url: str | None = None
    source: str = "crossref"
