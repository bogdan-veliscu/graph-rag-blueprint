"""Tests for parallel query processing."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from graph_rag.query.async_orchestrator import AsyncQueryOrchestrator
from graph_rag.utils.progress import ProgressTracker


@pytest.mark.asyncio
async def test_async_orchestrator_processes_queries():
    """Test that async orchestrator can process queries."""
    orchestrator = AsyncQueryOrchestrator()

    # Mock the async LLM client
    with patch.object(orchestrator, "async_llm_client") as mock_client:
        mock_client.generate = AsyncMock(return_value="Test answer [1]")

        # Mock graph operations
        orchestrator.graph.get_chunk = MagicMock(
            return_value={
                "id": "chunk1",
                "page_id": "page1",
                "document_id": "doc1",
                "page_number": 1,
                "text": "Test content",
                "source_file": "test.md",
            }
        )
        orchestrator.graph.get_document = MagicMock(return_value=None)
        orchestrator.graph.get_page = MagicMock(return_value=None)

        # Mock retriever
        orchestrator.retriever.retrieve = MagicMock(return_value=[])

        result = await orchestrator.process_query_async("Test question")

        assert result is not None
        assert "answer" in result.__dict__ or hasattr(result, "answer")


def test_progress_tracker_updates():
    """Test progress tracker updates correctly."""
    with ProgressTracker(10, desc="Test") as tracker:
        tracker.update(5)
        assert tracker.current == 5
        tracker.update(5)
        assert tracker.current == 10


def test_progress_tracker_without_tqdm():
    """Test progress tracker fallback when tqdm not available."""
    # Temporarily disable tqdm
    import graph_rag.utils.progress as progress_module

    original_available = progress_module.TQDM_AVAILABLE
    progress_module.TQDM_AVAILABLE = False

    try:
        with ProgressTracker(10, desc="Test") as tracker:
            tracker.update(5)
            assert tracker.current == 5
    finally:
        progress_module.TQDM_AVAILABLE = original_available

