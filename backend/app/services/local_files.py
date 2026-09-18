from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path

from app.schemas.local_files import LocalPaperFile


def resolve_papers_root(primary_directory: str) -> Path:
    candidates = [
        Path(primary_directory),
        Path("/workspace/Paper"),
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return Path(primary_directory)


def list_local_paper_files(directory: str) -> tuple[Path, list[LocalPaperFile]]:
    root = resolve_papers_root(directory)
    if not root.exists() or not root.is_dir():
        return root, []

    files: list[LocalPaperFile] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".pdf":
            continue

        stat = path.stat()
        files.append(
            LocalPaperFile(
                relative_path=str(path.relative_to(root)),
                name=path.name,
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime, UTC),
            )
        )

    return root, sorted(files, key=lambda item: item.modified_at, reverse=True)


def resolve_local_file_path(directory: str, relative_path: str) -> tuple[Path, Path] | None:
    root = resolve_papers_root(directory).resolve()
    candidate = (root / relative_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        return None

    if not candidate.exists() or not candidate.is_file():
        return None

    return root, candidate
