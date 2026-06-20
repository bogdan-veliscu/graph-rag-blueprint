"""Tests for answer generator."""

from unittest.mock import MagicMock, patch

import pytest

from graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from graph_rag.models import ChunkMatch
from graph_rag.query.answer_generator import AnswerGenerator


def test_answer_generator_formats_rich_citations():
    """Validate output uses metadata-driven Vancouver entries."""
    graph_adapter = MagicMock(spec=FalkorDBAdapter)

    # Mock document retrieval
    mock_document = MagicMock()
    mock_document.title = "Test Gazette"
    mock_document.metadata = {
        "document_title": "Test Gazette",
        "issue_number": 1,
        "volume_number": 1,
        "document_date": "2025-01-01",
        "publisher": "Test Publisher",
    }
    graph_adapter.get_document.return_value = mock_document

    # Mock page retrieval
    mock_page = MagicMock()
    mock_page.metadata = {"publisher": "Test Publisher", "page_number": 1}
    graph_adapter.get_page.return_value = mock_page

    # Mock chunk retrieval
    graph_adapter.get_chunk.return_value = {
        "id": "chunk1",
        "page_id": "page1",
        "document_id": "doc1",
        "page_number": 1,
        "text": "Test content",
        "source_file": "test-1",
    }

    generator = AnswerGenerator(graph_adapter)

    # Test citation formatting
    chunk_ids = ["chunk1"]
    references = generator._format_reference_list(chunk_ids)

    assert "Test Gazette" in references
    assert "Issue 1" in references
    assert "Volume 1" in references
    assert "2025-01-01" in references
    assert "p.1" in references


def test_format_reference_list_handles_missing_metadata():
    """Ensure graceful fallback when volume/publisher absent."""
    graph_adapter = MagicMock(spec=FalkorDBAdapter)

    # Mock document with missing fields
    mock_document = MagicMock()
    mock_document.title = "Test Gazette"
    mock_document.metadata = {
        "document_title": "Test Gazette",
        # Missing volume_number and publisher
    }
    graph_adapter.get_document.return_value = mock_document

    # Mock page
    mock_page = MagicMock()
    mock_page.metadata = {"page_number": 1}
    graph_adapter.get_page.return_value = mock_page

    # Mock chunk
    graph_adapter.get_chunk.return_value = {
        "id": "chunk1",
        "page_id": "page1",
        "document_id": "doc1",
        "page_number": 1,
        "text": "Test content",
        "source_file": "test-1",
    }

    generator = AnswerGenerator(graph_adapter)

    chunk_ids = ["chunk1"]
    references = generator._format_reference_list(chunk_ids)

    # Should still format citation without volume/publisher
    assert "Test Gazette" in references
    assert "p.1" in references

