"""Graph traversal for document-aware BFS and PageRank."""

from collections import deque
from typing import Dict, List, Set

from src.graph_rag.config import config
from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from src.graph_rag.models import ChunkMatch, Entity, NodeType


class GraphTraverser:
    """Graph traversal for augmenting retrieval results."""

    def __init__(self, graph_adapter: FalkorDBAdapter):
        """Initialize graph traverser.

        Args:
            graph_adapter: FalkorDB adapter instance
        """
        self.graph = graph_adapter

    def traverse(
        self,
        linked_entities: List[Entity],
        retrieved_chunks: List[ChunkMatch],
    ) -> List[ChunkMatch]:
        """Traverse graph to find related chunks.

        Args:
            linked_entities: Entities linked from query
            retrieved_chunks: Initial retrieval results

        Returns:
            Augmented list of ChunkMatch objects
        """
        if not linked_entities:
            return retrieved_chunks

        # Document-aware BFS
        bfs_chunks = self._document_aware_bfs(linked_entities, retrieved_chunks)

        # Personalized PageRank
        ppr_chunks = self._personalized_pagerank(linked_entities, retrieved_chunks)

        # Merge results
        chunk_scores = {match.chunk_id: match.score for match in retrieved_chunks}
        chunk_graph_scores = {match.chunk_id: match.graph_score for match in retrieved_chunks}

        # Add BFS chunks
        for chunk_id in bfs_chunks:
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = 0.0
            chunk_graph_scores[chunk_id] = chunk_graph_scores.get(chunk_id, 0.0) + 0.3

        # Add PageRank chunks
        for chunk_id, score in ppr_chunks.items():
            if chunk_id not in chunk_scores:
                chunk_scores[chunk_id] = 0.0
            chunk_graph_scores[chunk_id] = chunk_graph_scores.get(chunk_id, 0.0) + score

        # Create augmented matches
        augmented_matches = []
        for chunk_id, score in chunk_scores.items():
            match = ChunkMatch(
                chunk_id=chunk_id,
                score=score,
                graph_score=chunk_graph_scores.get(chunk_id, 0.0),
            )
            augmented_matches.append(match)

        return augmented_matches

    def _document_aware_bfs(
        self, linked_entities: List[Entity], retrieved_chunks: List[ChunkMatch]
    ) -> Set[str]:
        """Document-aware BFS traversal.

        Args:
            linked_entities: Starting entities
            retrieved_chunks: Retrieved chunks to get document IDs from

        Returns:
            Set of chunk IDs found via BFS
        """
        # Get document IDs from retrieved chunks
        document_ids = set()
        for match in retrieved_chunks:
            chunk_data = self.graph.get_chunk(match.chunk_id)
            if chunk_data:
                doc_id = chunk_data.get("document_id")
                if doc_id:
                    document_ids.add(doc_id)

        # If no document IDs found, return empty set
        if not document_ids:
            return set()

        found_chunks = set()
        visited_entities = set()

        # BFS from each linked entity
        for entity in linked_entities:
            queue = deque([(entity.id, 0)])  # (entity_id, hop_count)
            visited = {entity.id}

            while queue:
                current_entity_id, hops = queue.popleft()

                if hops >= config.max_hops:
                    continue

                # Find chunks mentioning this entity
                if document_ids:
                    doc_ids_str = "', '".join(document_ids)
                    query = f"""
                    MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {{id: '{current_entity_id}'}})
                    MATCH (c)-[:PART_OF]->(d:Document)
                    WHERE d.id IN ['{doc_ids_str}']
                    RETURN c.id as chunk_id
                    LIMIT 10
                    """
                else:
                    query = f"""
                    MATCH (c:Chunk)-[:MENTIONS]->(e:Entity {{id: '{current_entity_id}'}})
                    RETURN c.id as chunk_id
                    LIMIT 10
                    """
                results = self.graph.execute_query(query)
                for result in results:
                    chunk_id = result.get("chunk_id")
                    if chunk_id:
                        found_chunks.add(chunk_id)

                # Find related entities (within same document)
                if document_ids:
                    doc_ids_str = "', '".join(document_ids)
                    query = f"""
                    MATCH (e1:Entity {{id: '{current_entity_id}'}})-[:RELATED_TO]-(e2:Entity)
                    MATCH (c:Chunk)-[:MENTIONS]->(e2)
                    MATCH (c)-[:PART_OF]->(d:Document)
                    WHERE d.id IN ['{doc_ids_str}']
                    RETURN DISTINCT e2.id as entity_id, c.id as chunk_id
                    LIMIT 20
                    """
                else:
                    query = f"""
                    MATCH (e1:Entity {{id: '{current_entity_id}'}})-[:RELATED_TO]-(e2:Entity)
                    MATCH (c:Chunk)-[:MENTIONS]->(e2)
                    RETURN DISTINCT e2.id as entity_id, c.id as chunk_id
                    LIMIT 20
                    """
                results = self.graph.execute_query(query)
                for result in results:
                    entity_id = result.get("entity_id")
                    chunk_id = result.get("chunk_id")
                    if entity_id and entity_id not in visited:
                        visited.add(entity_id)
                        queue.append((entity_id, hops + 1))
                    if chunk_id:
                        found_chunks.add(chunk_id)

        return found_chunks

    def _personalized_pagerank(
        self, linked_entities: List[Entity], retrieved_chunks: List[ChunkMatch]
    ) -> Dict[str, float]:
        """Personalized PageRank starting from linked entities.

        Args:
            linked_entities: Starting entities
            retrieved_chunks: Retrieved chunks

        Returns:
            Dictionary mapping chunk_id to PageRank score
        """
        # Simplified PageRank: use entity-chunk relationships
        entity_ids = [e.id for e in linked_entities]
        chunk_scores = {}

        # Get chunks connected to linked entities
        for entity_id in entity_ids:
            query = f"""
            MATCH (e:Entity {{id: '{entity_id}'}})<-[:MENTIONS]-(c:Chunk)
            RETURN c.id as chunk_id
            LIMIT 50
            """
            results = self.graph.execute_query(query)
            for result in results:
                chunk_id = result.get("chunk_id")
                if chunk_id:
                    chunk_scores[chunk_id] = chunk_scores.get(chunk_id, 0.0) + 1.0

        # Normalize scores
        max_score = max(chunk_scores.values()) if chunk_scores else 1.0
        if max_score > 0:
            chunk_scores = {
                chunk_id: score / max_score for chunk_id, score in chunk_scores.items()
            }

        return chunk_scores

