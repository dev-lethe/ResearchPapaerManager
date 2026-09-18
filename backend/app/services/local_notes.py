from __future__ import annotations

from pathlib import Path

from app.services.local_files import resolve_local_file_path


def resolve_notes_root(primary_directory: str) -> Path:
    candidates = [
        Path(primary_directory),
        Path("/workspace/Memo"),
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return Path(primary_directory)


def build_note_relative_path_from_pdf(pdf_relative_path: str) -> Path:
    pdf_path = Path(pdf_relative_path)
    # Keep directory structure and map the source filename to a markdown filename.
    return pdf_path.with_suffix(".md")


def resolve_note_file_path(notes_directory: str, pdf_relative_path: str) -> tuple[Path, Path]:
    root = resolve_notes_root(notes_directory).resolve()
    note_relative_path = build_note_relative_path_from_pdf(pdf_relative_path)
    note_path = (root / note_relative_path).resolve()

    try:
        note_path.relative_to(root)
    except ValueError as exc:
        raise ValueError("Invalid note path") from exc

    return root, note_path


def read_local_note(notes_directory: str, pdf_relative_path: str) -> tuple[Path, Path, str, bool]:
    root, note_path = resolve_note_file_path(notes_directory, pdf_relative_path)

    if not note_path.exists() or not note_path.is_file():
        return root, note_path, "", False

    content = note_path.read_text(encoding="utf-8")
    return root, note_path, content, True


def write_local_note(notes_directory: str, pdf_relative_path: str, content: str) -> tuple[Path, Path]:
    root, note_path = resolve_note_file_path(notes_directory, pdf_relative_path)
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(content, encoding="utf-8")
    return root, note_path


def ensure_note_template_if_missing(
    notes_directory: str,
    pdf_relative_path: str,
    paper_title: str | None = None,
) -> tuple[Path, Path, str]:
    root, note_path, content, exists = read_local_note(notes_directory, pdf_relative_path)
    if exists:
        return root, note_path, content

    title = " ".join((paper_title or "").split()) or Path(pdf_relative_path).stem
    template = f"# {title}\n"
    write_local_note(notes_directory, pdf_relative_path, template)
    return root, note_path, template


def pdf_exists_for_relative_path(papers_directory: str, pdf_relative_path: str) -> bool:
    return resolve_local_file_path(papers_directory, pdf_relative_path) is not None
