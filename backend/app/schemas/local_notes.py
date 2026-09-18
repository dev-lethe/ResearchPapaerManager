from pydantic import BaseModel


class LocalNoteResponse(BaseModel):
    root_path: str
    note_relative_path: str
    content: str
    exists: bool


class LocalNoteUpdateRequest(BaseModel):
    content: str
