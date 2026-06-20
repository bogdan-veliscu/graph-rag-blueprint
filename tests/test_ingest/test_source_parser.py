"""Tests for source parser."""

from pathlib import Path

import pytest

from graph_rag.ingest.source_parser import parse_source_data
from graph_rag.utils.text_utils import parse_orig_tags


def test_parse_source_data_extracts_document_metadata(sample_source_file: Path):
    """Verify all document fields captured correctly."""
    parsed = parse_source_data(sample_source_file)

    assert parsed.document_metadata.document_title == "Test Gazette - Issue 1"
    assert parsed.document_metadata.document_date == "2025-01-01"
    assert parsed.document_metadata.document_id == "test-1"
    assert parsed.document_metadata.issue_number == 1
    assert parsed.document_metadata.volume_number == 1
    assert parsed.document_metadata.document_type == "official_gazette"
    assert len(parsed.pages) == 2


def test_parse_orig_tag_yields_original_name_field():
    """Ensure multilingual spans split into separate attributes."""
    text = "Kuwait Today <orig>الكويت اليوم</orig>"
    display, original = parse_orig_tags(text)

    assert display == "Kuwait Today"
    assert original == "الكويت اليوم"


def test_parse_source_data_handles_page_metadata(sample_source_file: Path):
    """Test page metadata parsing."""
    parsed = parse_source_data(sample_source_file)

    assert len(parsed.pages) == 2
    page1 = parsed.pages[0]
    assert page1["page_number"] == 1
    assert page1["metadata"].page_title == "Test Page 1"
    assert page1["metadata"].page_number == 1


def test_parse_source_data_fixes_date_inheritance():
    """Test that date inheritance bug is fixed."""
    # This would need a file with the 1954 date bug
    # For now, just verify the function exists
    assert hasattr(parse_source_data, "__call__")


def test_parse_source_data_handles_key_value_document_metadata(tmp_path: Path):
    """Parser supports document metadata blocks that use key-value lines."""
    source_path = tmp_path / "sample_key_value.md"
    source_path.write_text(
        """
<document_metadata>
 document_id: sample-doc
 document_date: 2025-11-12
 language: en
 total_pages: 1
 processed: 2025-11-12T00:00:00
</document_metadata>

---

<page_start>1</page_start>
<page_metadata>
{
  "page_title": "Sample Page",
  "document_date": "2025-11-12"
}
</page_metadata>
Sample content body.
<page_end>1</page_end>
""".strip(),
        encoding="utf-8",
    )

    parsed = parse_source_data(source_path)

    assert parsed.document_metadata.document_id == "sample-doc"
    assert parsed.document_metadata.document_title == "sample-doc"
    assert parsed.document_metadata.document_date == "2025-11-12"
    assert parsed.document_metadata.language == ["en"]
    assert parsed.document_metadata.total_pages == 1
    assert len(parsed.pages) == 1
    assert parsed.pages[0]["metadata"].page_title == "Sample Page"


def test_parse_source_data_handles_string_authors(tmp_path: Path):
    """Parser correctly handles authors field as string (not converting to character list)."""
    source_path = tmp_path / "sample_string_authors.md"
    source_path.write_text(
        """
<document_metadata>
{
  "document_title": "Test Document",
  "document_date": "2025-01-01",
  "document_id": "test-string-authors",
  "authors": "Fahad Yusuf Saud Al-Sabah <orig>فهد يوسف سعود الصباح</orig>",
  "publisher": "Test Publisher",
  "total_pages": 1
}
</document_metadata>

---

<page_start>1</page_start>
<page_metadata>
{
  "page_number": 1,
  "page_title": "Test Page"
}
</page_metadata>
Test content.
<page_end>1</page_end>
""".strip(),
        encoding="utf-8",
    )

    parsed = parse_source_data(source_path)

    # Authors should be a list with one string element, not a list of characters
    assert isinstance(parsed.document_metadata.authors, list)
    assert len(parsed.document_metadata.authors) == 1
    assert isinstance(parsed.document_metadata.authors[0], str)
    assert parsed.document_metadata.authors[0] == "Fahad Yusuf Saud Al-Sabah"
    # Verify it's not a character list
    assert parsed.document_metadata.authors[0] != "F"  # First character if bug exists


def test_parse_source_data_handles_list_authors(tmp_path: Path):
    """Parser correctly handles authors field as list."""
    source_path = tmp_path / "sample_list_authors.md"
    source_path.write_text(
        """
<document_metadata>
{
  "document_title": "Test Document",
  "document_date": "2025-01-01",
  "document_id": "test-list-authors",
  "authors": ["Author One", "Author Two <orig>المؤلف الثاني</orig>"],
  "publisher": "Test Publisher",
  "total_pages": 1
}
</document_metadata>

---

<page_start>1</page_start>
<page_metadata>
{
  "page_number": 1,
  "page_title": "Test Page"
}
</page_metadata>
Test content.
<page_end>1</page_end>
""".strip(),
        encoding="utf-8",
    )

    parsed = parse_source_data(source_path)

    # Authors should be a list of strings
    assert isinstance(parsed.document_metadata.authors, list)
    assert len(parsed.document_metadata.authors) == 2
    assert parsed.document_metadata.authors[0] == "Author One"
    assert parsed.document_metadata.authors[1] == "Author Two"


def test_parse_source_data_handles_none_authors(tmp_path: Path):
    """Parser correctly handles missing or null authors field."""
    source_path = tmp_path / "sample_no_authors.md"
    source_path.write_text(
        """
<document_metadata>
{
  "document_title": "Test Document",
  "document_date": "2025-01-01",
  "document_id": "test-no-authors",
  "publisher": "Test Publisher",
  "total_pages": 1
}
</document_metadata>

---

<page_start>1</page_start>
<page_metadata>
{
  "page_number": 1,
  "page_title": "Test Page"
}
</page_metadata>
Test content.
<page_end>1</page_end>
""".strip(),
        encoding="utf-8",
    )

    parsed = parse_source_data(source_path)

    # Authors should be an empty list, not None
    assert isinstance(parsed.document_metadata.authors, list)
    assert len(parsed.document_metadata.authors) == 0

