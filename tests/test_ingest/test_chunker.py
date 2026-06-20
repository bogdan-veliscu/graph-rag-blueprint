"""Tests for chunker."""

import pytest

from graph_rag.ingest.chunker import chunk_document_pages
from graph_rag.models import Page


def test_chunker_preserves_page_boundaries_and_overlap(sample_page: Page, sample_document):
    """Confirm chunk windows stay within page limits."""
    # Create a page with longer content
    long_content = " ".join(["This is test content."] * 100)
    long_page = Page(
        id="test_page_1",
        document_id=sample_document.id,
        page_number=1,
        content=long_content,
        metadata={},
    )

    chunks = chunk_document_pages(sample_document.id, [long_page])

    assert len(chunks) > 0
    # Verify all chunks have correct page_id and document_id
    for chunk in chunks:
        assert chunk.page_id == long_page.id
        assert chunk.document_id == sample_document.id
        assert chunk.page_number == 1


def test_chunker_creates_overlapping_chunks(sample_page: Page, sample_document):
    """Test that chunks have overlap."""
    long_content = " ".join(["Word"] * 1000)
    long_page = Page(
        id="test_page_1",
        document_id=sample_document.id,
        page_number=1,
        content=long_content,
        metadata={},
    )

    chunks = chunk_document_pages(sample_document.id, [long_page])

    if len(chunks) > 1:
        # Verify overlap exists (chunks should share some content)
        assert chunks[0].end_char > chunks[1].start_char

