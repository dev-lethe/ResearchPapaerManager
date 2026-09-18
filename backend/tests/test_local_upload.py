import hashlib
from io import BytesIO

import pytest

from app.services import local_upload


def test_original_extension_is_checked_with_uuid_storage_name(tmp_path) -> None:
    with pytest.raises(ValueError, match="Only .pdf files are allowed"):
        local_upload.save_uploaded_pdf(
            BytesIO(b"%PDF-1.7\n"), "paper.txt", str(tmp_path), storage_filename="uuid.pdf"
        )
    assert list(tmp_path.iterdir()) == []


def test_pdf_upload_preserves_content_and_hash(tmp_path) -> None:
    content = b"%PDF-1.7\nexample"
    path, relative_path, size, digest = local_upload.save_uploaded_pdf(
        BytesIO(content), "paper.PDF", str(tmp_path), storage_filename="uuid.pdf"
    )
    assert path.read_bytes() == content
    assert relative_path == "uuid.pdf"
    assert size == len(content)
    assert digest == hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize("content", [b"", b"not a PDF", b"%PDF-1.7\n" + b"x" * 32])
def test_rejected_upload_does_not_leave_a_file(tmp_path, monkeypatch, content) -> None:
    monkeypatch.setattr(local_upload, "MAX_UPLOAD_SIZE_BYTES", 32)
    with pytest.raises(ValueError):
        local_upload.save_uploaded_pdf(
            BytesIO(content), "paper.pdf", str(tmp_path), storage_filename="uuid.pdf"
        )
    assert list(tmp_path.iterdir()) == []
