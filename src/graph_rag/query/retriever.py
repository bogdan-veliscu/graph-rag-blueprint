"""Hybrid retrieval: dense + sparse + RRF."""

import json
import pickle
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from src.graph_rag.config import config
from src.graph_rag.models import ChunkMatch
from src.graph_rag.utils.embeddings import embed_text


class Retriever:
    """Hybrid retriever combining dense and sparse search."""

    def __init__(self):
        """Initialize retriever with indices."""
        self.faiss_index = None
        self.bm25_index = None
        self.chunk_metadata = []
        self.chunk_id_to_index = {}

        self._load_indices()

    def _load_indices(self):
        """Load FAISS and BM25 indices."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Load FAISS index
        try:
            if config.embeddings_file.exists():
                self.faiss_index = faiss.read_index(str(config.embeddings_file))
                logger.info(f"Loaded FAISS index from {config.embeddings_file}")
            else:
                logger.warning(f"FAISS index not found at {config.embeddings_file}")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            self.faiss_index = None

        # Load BM25 index
        try:
            if config.bm25_file.exists():
                with open(config.bm25_file, "rb") as f:
                    self.bm25_index = pickle.load(f)
                logger.info(f"Loaded BM25 index from {config.bm25_file}")
            else:
                logger.warning(f"BM25 index not found at {config.bm25_file}")
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            self.bm25_index = None

        # Load chunk metadata
        try:
            if config.chunks_file.exists():
                with open(config.chunks_file, "r") as f:
                    self.chunk_metadata = json.load(f)
                self.chunk_id_to_index = {
                    chunk["id"]: i for i, chunk in enumerate(self.chunk_metadata)
                }
                logger.info(f"Loaded {len(self.chunk_metadata)} chunk metadata entries")
            else:
                logger.warning(f"Chunk metadata not found at {config.chunks_file}")
        except Exception as e:
            logger.error(f"Failed to load chunk metadata: {e}")
            self.chunk_metadata = []
            self.chunk_id_to_index = {}

    def retrieve(self, query: str, top_k: int = None) -> List[ChunkMatch]:
        """Retrieve chunks using hybrid retrieval.

        Args:
            query: Query string
            top_k: Number of results to return (defaults to config.rerank_top_k)

        Returns:
            List of ChunkMatch objects
        """
        import logging
        logger = logging.getLogger(__name__)
        
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        if top_k is None:
            top_k = config.rerank_top_k

        # Validate indices are loaded
        if not self.faiss_index and not self.bm25_index:
            logger.error("No retrieval indices available. Run ingestion first.")
            return []
        
        if not self.chunk_metadata:
            logger.error("No chunk metadata available. Run ingestion first.")
            return []

        # Dense retrieval
        try:
            dense_matches = self._dense_retrieve(query, config.dense_top_k)
        except Exception as e:
            logger.error(f"Dense retrieval failed: {e}")
            dense_matches = []

        # Sparse retrieval
        try:
            sparse_matches = self._sparse_retrieve(query, config.sparse_top_k)
        except Exception as e:
            logger.error(f"Sparse retrieval failed: {e}")
            sparse_matches = []

        # If both fail, return empty
        if not dense_matches and not sparse_matches:
            logger.warning("Both dense and sparse retrieval returned no results")
            return []

        # Reciprocal Rank Fusion
        try:
            fused_matches = self._reciprocal_rank_fusion(
                dense_matches, sparse_matches, top_k
            )
        except Exception as e:
            logger.error(f"Rank fusion failed: {e}")
            # Fallback: return dense matches if available, else sparse
            fused_matches = dense_matches[:top_k] if dense_matches else sparse_matches[:top_k]

        return fused_matches

    def _dense_retrieve(self, query: str, top_k: int) -> List[ChunkMatch]:
        """Dense retrieval using FAISS.

        Args:
            query: Query string
            top_k: Number of results

        Returns:
            List of ChunkMatch objects
        """
        if not self.faiss_index or not self.chunk_metadata:
            return []

        # Embed query
        query_embedding = np.array([embed_text(query)], dtype=np.float32)
        faiss.normalize_L2(query_embedding)

        # Search
        distances, indices = self.faiss_index.search(query_embedding, top_k)

        matches = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.chunk_metadata):
                chunk_data = self.chunk_metadata[idx]
                match = ChunkMatch(
                    chunk_id=chunk_data["id"],
                    score=float(distance),
                    semantic_score=float(distance),
                )
                matches.append(match)

        return matches

    def _sparse_retrieve(self, query: str, top_k: int) -> List[ChunkMatch]:
        """Sparse retrieval using BM25.

        Args:
            query: Query string
            top_k: Number of results

        Returns:
            List of ChunkMatch objects
        """
        if not self.bm25_index or not self.chunk_metadata:
            return []

        # Tokenize query
        query_tokens = query.lower().split()

        # Get scores
        scores = self.bm25_index.get_scores(query_tokens)

        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]

        matches = []
        for idx in top_indices:
            chunk_data = self.chunk_metadata[idx]
            match = ChunkMatch(
                chunk_id=chunk_data["id"],
                score=float(scores[idx]),
                semantic_score=0.0,  # BM25 doesn't have semantic score
            )
            matches.append(match)

        return matches

    def _reciprocal_rank_fusion(
        self,
        dense_matches: List[ChunkMatch],
        sparse_matches: List[ChunkMatch],
        top_k: int,
    ) -> List[ChunkMatch]:
        """Combine rankings using Reciprocal Rank Fusion.

        Args:
            dense_matches: Dense retrieval results
            sparse_matches: Sparse retrieval results
            top_k: Number of final results

        Returns:
            Fused ranking
        """
        # Build rank maps
        dense_ranks = {match.chunk_id: rank + 1 for rank, match in enumerate(dense_matches)}
        sparse_ranks = {
            match.chunk_id: rank + 1 for rank, match in enumerate(sparse_matches)
        }

        # Calculate RRF scores
        rrf_scores = defaultdict(float)
        k = config.fusion_k

        for chunk_id, rank in dense_ranks.items():
            rrf_scores[chunk_id] += 1.0 / (k + rank)

        for chunk_id, rank in sparse_ranks.items():
            rrf_scores[chunk_id] += 1.0 / (k + rank)

        # Combine semantic scores
        semantic_scores = {match.chunk_id: match.semantic_score for match in dense_matches}
        sparse_scores = {match.chunk_id: match.score for match in sparse_matches}

        # Create fused matches
        fused_matches = []
        for chunk_id, rrf_score in sorted(
            rrf_scores.items(), key=lambda x: x[1], reverse=True
        )[:top_k]:
            semantic_score = semantic_scores.get(chunk_id, 0.0)
            sparse_score = sparse_scores.get(chunk_id, 0.0)

            match = ChunkMatch(
                chunk_id=chunk_id,
                score=rrf_score,
                semantic_score=semantic_score,
            )
            fused_matches.append(match)

        return fused_matches

