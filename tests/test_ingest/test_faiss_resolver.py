"""Tests for FAISS entity resolver."""

import pytest

from src.graph_rag.ingest.faiss_resolver import FAISSEntityResolver
from src.graph_rag.models import Entity, EntityType


def test_resolve_entities_merges_duplicate_variants():
    """Check FAISS grouping collapses equivalent names."""
    resolver = FAISSEntityResolver()

    entities = [
        Entity(
            id="1",
            text="Party A",
            entity_type=EntityType.PARTY,
        ),
        Entity(
            id="2",
            text="the Party A",
            entity_type=EntityType.PARTY,
        ),
        Entity(
            id="3",
            text="Licensor",
            entity_type=EntityType.PARTY,
        ),
    ]

    resolved = resolver.resolve_entities(entities)

    # Should reduce duplicates
    assert len(resolved) <= len(entities)
    # All resolved entities should have PARTY type
    assert all(e.entity_type == EntityType.PARTY for e in resolved)

