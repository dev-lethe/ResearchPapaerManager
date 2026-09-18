from pydantic import BaseModel, Field

from app.schemas.local_metadata import LocalPaperMetadata


class LocalUploadResponse(BaseModel):
    paper_id: str
    relative_path: str
    file_name: str
    size_bytes: int
    pdf_sha256: str
    inferred_metadata: LocalPaperMetadata
    duplicate_pdf_relative_paths: list[str] = Field(default_factory=list)
    duplicate_doi_relative_paths: list[str] = Field(default_factory=list)
    duplicate_pdf_paper_ids: list[str] = Field(default_factory=list)
    duplicate_doi_paper_ids: list[str] = Field(default_factory=list)
    requires_manual_doi: bool = False
