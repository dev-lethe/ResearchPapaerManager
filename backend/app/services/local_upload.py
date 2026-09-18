from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import BinaryIO

from app.services.local_files import resolve_papers_root

MAX_UPLOAD_SIZE_BYTES = 100 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def sanitize_filename(filename: str) -> str:
    safe_name = Path(filename).name.strip()
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)
    if not safe_name:
        safe_name = "uploaded.pdf"
    return safe_name


def ensure_pdf_filename(filename: str) -> str:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only .pdf files are allowed")
    return filename


def allocate_unique_path(root: Path, filename: str) -> Path:
    base = Path(filename).stem
    suffix = Path(filename).suffix

    candidate = root / filename
    if not candidate.exists():
        return candidate

    index = 1
    while True:
        candidate = root / f"{base}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def save_uploaded_pdf(
    file_obj: BinaryIO,
    original_filename: str,
    local_papers_path: str,
    *,
    storage_filename: str | None = None,
) -> tuple[Path, str, int, str]:
    ensure_pdf_filename(original_filename)
    root = resolve_papers_root(local_papers_path)
    root.mkdir(parents=True, exist_ok=True)

    if storage_filename:
        safe_name = ensure_pdf_filename(sanitize_filename(storage_filename))
        destination = root / safe_name
        if destination.exists():
            raise ValueError("Storage filename already exists")
    else:
        safe_name = sanitize_filename(original_filename)
        safe_name = ensure_pdf_filename(safe_name)
        destination = allocate_unique_path(root, safe_name)

    total_size = 0
    first_chunk = b""
    digest = hashlib.sha256()

    with destination.open("wb") as output:
        while True:
            chunk = file_obj.read(CHUNK_SIZE)
            if not chunk:
                break

            if not first_chunk:
                first_chunk = chunk[:8]

            total_size += len(chunk)
            if total_size > MAX_UPLOAD_SIZE_BYTES:
                output.close()
                destination.unlink(missing_ok=True)
                raise ValueError("File exceeds 100 MB size limit")

            digest.update(chunk)
            output.write(chunk)

    if total_size == 0:
        destination.unlink(missing_ok=True)
        raise ValueError("Empty file is not allowed")

    if not first_chunk.startswith(b"%PDF-"):
        destination.unlink(missing_ok=True)
        raise ValueError("File content is not a valid PDF")

    return destination, str(destination.relative_to(root)), total_size, digest.hexdigest()
