"""Reranking combining semantic and graph scores."""

from typing import List

from src.graph_rag.config import config
from src.graph_rag.models import ChunkMatch


class Reranker:
    """Reranker combining semantic and graph scores."""

    def rerank(self, matches: List[ChunkMatch], top_k: int = None) -> List[ChunkMatch]:
        """Rerank matches using combined scores.

        Args:
            matches: List of ChunkMatch objects
            top_k: Number of results to return

        Returns:
            Reranked list of ChunkMatch objects
        """
        if top_k is None:
            top_k = config.rerank_top_k

        # Combine semantic and graph scores
        for match in matches:
            # Weighted combination: 70% semantic, 30% graph
            combined_score = 0.7 * match.semantic_score + 0.3 * match.graph_score
            match.score = combined_score

        # Sort by combined score
        sorted_matches = sorted(matches, key=lambda x: x.score, reverse=True)

        return sorted_matches[:top_k]

