"""Entity linker for matching query entities to graph entities."""

from typing import List, Optional

from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from src.graph_rag.models import Entity, NodeType


class EntityLinker:
    """Link query entities to graph entities."""

    def __init__(self, graph_adapter: FalkorDBAdapter):
        """Initialize entity linker.

        Args:
            graph_adapter: FalkorDB adapter instance
        """
        self.graph = graph_adapter

    def link_entities(self, query_entities: List[str]) -> List[Entity]:
        """Link query entities to graph entities.

        Args:
            query_entities: List of entity strings from query

        Returns:
            List of linked Entity objects
        """
        linked_entities = []

        for query_entity in query_entities:
            # Fuzzy match to graph entities
            matched_entity = self._fuzzy_match(query_entity)
            if matched_entity:
                linked_entities.append(matched_entity)

        return linked_entities

    def _fuzzy_match(self, query_text: str) -> Optional[Entity]:
        """Fuzzy match query text to graph entity.

        Args:
            query_text: Query entity text

        Returns:
            Matched Entity or None
        """
        # Simple substring matching (can be improved with Levenshtein)
        query_lower = query_text.lower()

        # Search for entities with similar text
        cypher_query = f"""
        MATCH (e:Entity)
        WHERE toLower(e.text) CONTAINS '{query_lower}'
           OR toLower(e.canonical_form) CONTAINS '{query_lower}'
        RETURN e
        LIMIT 1
        """
        results = self.graph.execute_query(cypher_query)

        if results:
            entity_data = results[0]
            return Entity(
                id=entity_data.get("id", ""),
                text=entity_data.get("text", ""),
                entity_type=entity_data.get("entity_type", ""),
                canonical_form=entity_data.get("canonical_form"),
                original_name=entity_data.get("original_name"),
            )

        return None

