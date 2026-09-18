from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

from pydantic import ValidationError

from app.schemas.local_metadata import LocalPaperMetadata
from app.services.local_notes import resolve_notes_root


def build_metadata_relative_path_from_pdf(pdf_relative_path: str) -> Path:
    return Path(pdf_relative_path).with_suffix(".meta.json")


def resolve_metadata_file_path(notes_directory: str, pdf_relative_path: str) -> tuple[Path, Path]:
    root = resolve_notes_root(notes_directory).resolve()
    metadata_relative_path = build_metadata_relative_path_from_pdf(pdf_relative_path)
    metadata_path = (root / metadata_relative_path).resolve()

    try:
        metadata_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Invalid metadata path") from exc

    return root, metadata_path


def read_local_metadata(notes_directory: str, pdf_relative_path: str) -> tuple[Path, Path, LocalPaperMetadata]:
    root, metadata_path = resolve_metadata_file_path(notes_directory, pdf_relative_path)

    if not metadata_path.exists() or not metadata_path.is_file():
        return root, metadata_path, LocalPaperMetadata()

    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata = LocalPaperMetadata.model_validate(data)
        return root, metadata_path, metadata
    except (json.JSONDecodeError, ValidationError):
        return root, metadata_path, LocalPaperMetadata()


def write_local_metadata(
    notes_directory: str,
    pdf_relative_path: str,
    metadata: LocalPaperMetadata,
) -> tuple[Path, Path, LocalPaperMetadata]:
    root, metadata_path = resolve_metadata_file_path(notes_directory, pdf_relative_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    updated = metadata.model_copy(update={"updated_at": datetime.now(UTC)})
    metadata_path.write_text(
        updated.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return root, metadata_path, updated
