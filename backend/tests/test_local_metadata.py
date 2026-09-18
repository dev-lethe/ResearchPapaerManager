import pytest

from app.services.local_metadata import read_local_metadata


@pytest.mark.parametrize("invalid_content", [None, "{", '{"authors": 1}'])
def test_default_metadata_is_not_shared_between_papers(tmp_path, invalid_content) -> None:
    if invalid_content is not None:
        (tmp_path / "first.meta.json").write_text(invalid_content, encoding="utf-8")

    _, _, first = read_local_metadata(str(tmp_path), "first.pdf")
    first.keywords.append("private keyword")

    _, _, second = read_local_metadata(str(tmp_path), "second.pdf")
    assert second.keywords == []
