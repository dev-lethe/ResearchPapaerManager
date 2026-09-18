import os
from unittest.mock import patch

import pytest

from app.schemas.local_metadata import LocalPaperMetadata
from app.services import local_search
from app.services.local_metadata import write_local_metadata
from app.services.local_notes import write_local_note


@pytest.fixture
def library(tmp_path):
    papers = tmp_path / "papers"
    notes = tmp_path / "notes"
    papers.mkdir()
    for index in range(5):
        name = f"{index}.pdf"
        pdf = papers / name
        pdf.write_bytes(b"%PDF-1.7\n")
        os.utime(pdf, (100 + index, 100 + index))
        write_local_metadata(str(notes), name, LocalPaperMetadata(
            title=f"Paper {index}", year=2024 if index % 2 == 0 else 2023,
            keywords=["Vision"],
        ))
        write_local_note(str(notes), name, f"# Memo {index}\nNeedle in notes")
    return str(papers), str(notes)


@pytest.mark.parametrize("query", [None, "", "   "])
def test_listing_reads_notes_only_for_requested_page(library, query):
    with patch.object(local_search, "read_local_note", wraps=local_search.read_local_note) as read_note:
        result = local_search.search_local_papers(*library, q=query, page=2, per_page=2)

    assert result.total == 5
    assert result.total_pages == 3
    assert [item.relative_path for item in result.items] == ["2.pdf", "1.pdf"]
    assert [call.args[1] for call in read_note.call_args_list] == ["2.pdf", "1.pdf"]
    assert result.items[0].note_preview == "# Memo 2\nNeedle in notes"


def test_full_text_search_includes_notes_and_filters_before_reading(library):
    with patch.object(local_search, "read_local_note", wraps=local_search.read_local_note) as read_note:
        result = local_search.search_local_papers(
            *library, q=" NEEDLE ", year=2024, keywords=["vision"], per_page=1,
        )

    assert result.total == 3
    assert result.items[0].relative_path == "4.pdf"
    assert result.items[0].note_preview == "# Memo 4\nNeedle in notes"
    assert [call.args[1] for call in read_note.call_args_list] == ["4.pdf", "2.pdf", "0.pdf"]


def test_empty_results_do_not_read_notes(library):
    with patch.object(local_search, "read_local_note", wraps=local_search.read_local_note) as read_note:
        result = local_search.search_local_papers(*library, year=1900, page=9)

    assert result.total == 0
    assert result.items == []
    assert result.page == result.total_pages == 1
    read_note.assert_not_called()


def test_out_of_range_page_keeps_last_page_preview(library):
    result = local_search.search_local_papers(*library, page=99, per_page=2)
    assert result.page == 3
    assert result.items[0].relative_path == "0.pdf"
    assert result.items[0].note_preview == "# Memo 0\nNeedle in notes"
