"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.graph_rag.models import Document, Page


@pytest.fixture
def sample_document_metadata() -> dict:
    """Sample document metadata."""
    return {
        "document_title": "Al-Kuwait Al-Youm Official Gazette - Issue 1733, Volume 71",
        "document_date": "2025-04-06",
        "document_id": "6-4-2025",
        "issue_number": 1733,
        "volume_number": 71,
        "document_type": "official_gazette",
        "language": ["ar", "en"],
        "authors": ["Amir of Kuwait"],
        "publisher": "Kuwait Today",
        "total_pages": 112,
    }


@pytest.fixture
def sample_page_metadata() -> dict:
    """Sample page metadata."""
    return {
        "page_number": 1,
        "page_title": "Contents of Issue 1733",
        "document_date": "2025-04-06",
        "issue_number": 1733,
        "volume_number": 71,
        "document_type": "official_gazette",
        "page_type": "index",
        "publisher": "Ministry of Information",
    }


@pytest.fixture
def sample_source_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a sample source file for testing."""
    content = """<document_metadata>
{
  "document_title": "Test Gazette - Issue 1",
  "document_date": "2025-01-01",
  "document_id": "test-1",
  "issue_number": 1,
  "volume_number": 1,
  "document_type": "official_gazette",
  "language": ["en"],
  "authors": ["Test Author"],
  "publisher": "Test Publisher",
  "total_pages": 2
}
</document_metadata>

<page_start>1</page_start>
<page_metadata>
{
  "page_number": 1,
  "page_title": "Test Page 1",
  "document_date": "2025-01-01",
  "issue_number": 1,
  "volume_number": 1,
  "document_type": "official_gazette",
  "page_type": "content",
  "publisher": "Test Publisher"
}
</page_metadata>
<header>Test Header</header>
This is test content for page 1.
<page_end>1</page_end>

<page_start>2</page_start>
<page_metadata>
{
  "page_number": 2,
  "page_title": "Test Page 2",
  "document_date": "2025-01-01",
  "issue_number": 1,
  "volume_number": 1,
  "document_type": "official_gazette",
  "page_type": "content",
  "publisher": "Test Publisher"
}
</page_metadata>
This is test content for page 2.
<page_end>2</page_end>
"""
    file_path = tmp_path / "test_source.md"
    file_path.write_text(content)
    yield file_path


@pytest.fixture
def sample_document(sample_document_metadata: dict) -> Document:
    """Sample document object."""
    return Document(
        id=sample_document_metadata["document_id"],
        filename="test-1",
        title=sample_document_metadata["document_title"],
        doc_type=sample_document_metadata["document_type"],
        metadata=sample_document_metadata,
    )


@pytest.fixture
def sample_page(sample_page_metadata: dict, sample_document: Document) -> Page:
    """Sample page object."""
    return Page(
        id=f"{sample_document.id}_page_1",
        document_id=sample_document.id,
        page_number=1,
        content="This is test content.",
        metadata=sample_page_metadata,
    )

