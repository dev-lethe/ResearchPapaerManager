import pytest
from fastapi.testclient import TestClient

from app.api.v1 import router as api
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    papers = tmp_path / "papers"
    papers.mkdir()
    monkeypatch.setattr(api.settings, "local_papers_path", str(papers))
    monkeypatch.setattr(api.settings, "local_notes_path", str(tmp_path / "notes"))
    monkeypatch.setattr(api, "create_uploaded_paper", lambda **kwargs: None)
    monkeypatch.setattr(api, "find_duplicate_papers_by_hash", lambda **kwargs: [])
    monkeypatch.setattr(api, "find_duplicate_papers_by_doi", lambda **kwargs: [])
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize(("value", "expected"), [
    (" Alice, Bob , ", ["Alice", "Bob"]),
    ('["Alice, Jr.", " Bob "]', ["Alice, Jr.", "Bob"]),
    ("[]", []),
])
def test_upload_parses_authors_and_affiliations(client, value, expected):
    response = client.post("/api/v1/papers/upload",
        files={"file": ("paper.pdf", b"%PDF-1.7\n", "application/pdf")},
        data={"authors": value, "affiliations": value},
    )
    assert response.status_code == 200
    path = response.json()["relative_path"]
    metadata = client.get(f"/api/v1/papers/local-metadata/{path}").json()["metadata"]
    assert metadata["authors"] == expected
    assert metadata["affiliations"] == expected


def test_saved_note_response_matches_persisted_content(client, tmp_path):
    (tmp_path / "papers" / "paper.pdf").write_bytes(b"%PDF-1.7\n")
    content = "# 日本語メモ\n\n**Result**\n"
    url = "/api/v1/papers/local-notes/paper.pdf"
    response = client.put(url, json={"content": content})
    assert response.status_code == 200
    assert response.json()["content"] == content
    assert response.json()["exists"] is True
    assert client.get(url).json() == response.json()
    assert (tmp_path / "notes" / "paper.md").read_text() == content


def test_note_paths_cannot_escape_library(client, tmp_path):
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-1.7\n")
    (tmp_path / "papers" / "link.pdf").symlink_to(outside)
    for path in ["missing.pdf", "link.pdf", "%2E%2E%2Foutside.pdf"]:
        response = client.put(f"/api/v1/papers/local-notes/{path}", json={"content": "memo"})
        assert response.status_code == 404
    assert not (tmp_path / "notes").exists()
