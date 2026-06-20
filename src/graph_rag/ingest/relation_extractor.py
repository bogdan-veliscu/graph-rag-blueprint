"""Relation extraction from entity co-occurrence."""

from collections import defaultdict
from typing import Dict, List

from graph_rag.models import Entity, Relationship, EdgeType


def extract_relations(
    chunks: List[Dict], entities: List[Entity]
) -> List[Relationship]:
    """Extract relationships via co-occurrence model.

    Args:
        chunks: List of chunk dictionaries with entity mentions
        entities: List of resolved entities

    Returns:
        List of Relationship objects
    """
    # Build entity index
    entity_map = {e.id: e for e in entities}

    # Track co-occurrences
    cooccurrence: Dict[tuple[str, str], int] = defaultdict(int)
    entity_chunks: Dict[str, set] = defaultdict(set)

    # Count co-occurrences within chunks
    for chunk in chunks:
        chunk_entity_ids = chunk.get("entity_ids", [])
        chunk_id = chunk.get("id", "")

        for entity_id in chunk_entity_ids:
            entity_chunks[entity_id].add(chunk_id)

        # Count pairwise co-occurrences
        for i, entity_id1 in enumerate(chunk_entity_ids):
            for entity_id2 in chunk_entity_ids[i + 1 :]:
                if entity_id1 != entity_id2:
                    pair = tuple(sorted([entity_id1, entity_id2]))
                    cooccurrence[pair] += 1

    # Create relationships
    relationships = []

    for (entity_id1, entity_id2), count in cooccurrence.items():
        if entity_id1 in entity_map and entity_id2 in entity_map:
            # Calculate weight based on co-occurrence count and shared chunks
            shared_chunks = len(
                entity_chunks[entity_id1].intersection(entity_chunks[entity_id2])
            )
            weight = count + shared_chunks * 0.5

            relationship = Relationship(
                source_id=entity_id1,
                target_id=entity_id2,
                edge_type=EdgeType.RELATED_TO,
                weight=weight,
                metadata={"cooccurrence_count": count, "shared_chunks": shared_chunks},
            )
            relationships.append(relationship)

    return relationships

