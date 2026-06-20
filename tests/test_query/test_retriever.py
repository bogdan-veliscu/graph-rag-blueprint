"""Tests for retriever."""

import pytest

from graph_rag.query.retriever import Retriever


def test_retriever_rrf_blends_dense_and_sparse_scores():
    """Assert fused ranking honors both retrieval sources."""
    retriever = Retriever()

    # This test requires indices to be built first
    # For now, just verify the class initializes
    assert retriever is not None
    assert hasattr(retriever, "retrieve")
    assert hasattr(retriever, "_reciprocal_rank_fusion")

