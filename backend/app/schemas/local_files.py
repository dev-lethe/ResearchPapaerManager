from datetime import datetime

from pydantic import BaseModel


class LocalPaperFile(BaseModel):
    relative_path: str
    name: str
    size_bytes: int
    modified_at: datetime


class LocalPaperFileListResponse(BaseModel):
    root_path: str
    files: list[LocalPaperFile]
