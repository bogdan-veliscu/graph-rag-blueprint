"""FAISS-based entity resolution for deduplication."""

import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from graph_rag.config import config
from graph_rag.models import Entity

logger = logging.getLogger(__name__)


class FAISSEntityResolver:
    """Resolve entities using FAISS similarity search."""

    def __init__(self):
        """Initialize resolver with embedding model."""
        self.model = SentenceTransformer(config.embedding_model)
        self.threshold = config.entity_similarity_threshold
        self.batch_size = 10000  # Process entities in batches to avoid memory issues

    def resolve_entities(self, entities: List[Entity]) -> List[Entity]:
        """Resolve entities by merging duplicates.

        Args:
            entities: List of raw entities

        Returns:
            List of resolved (deduplicated) entities
        """
        if not entities:
            return []

        logger.info(f"Resolving {len(entities)} entities...")

        # Group entities by type for more efficient resolution
        entities_by_type = {}
        for entity in entities:
            entity_type = entity.entity_type
            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []
            entities_by_type[entity_type].append(entity)

        resolved_entities = []

        for entity_type, type_entities in entities_by_type.items():
            if len(type_entities) == 1:
                resolved_entities.append(type_entities[0])
                continue

            logger.debug(f"Resolving {len(type_entities)} entities of type {entity_type.value}")

            # Process in batches if too many entities
            if len(type_entities) > self.batch_size:
                resolved_entities.extend(self._resolve_batched(type_entities))
            else:
                resolved_entities.extend(self._resolve_single_batch(type_entities))

        logger.info(f"Resolved to {len(resolved_entities)} unique entities")
        return resolved_entities

    def _resolve_single_batch(self, type_entities: List[Entity]) -> List[Entity]:
        """Resolve a single batch of entities."""
        # Embed entity texts
        texts = [e.text for e in type_entities]
        embeddings = self.model.encode(texts, show_progress_bar=False, batch_size=512)

        # Build FAISS index
        import faiss

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype("float32"))

        # Find similar entities
        merged = set()
        resolved = []

        # Limit search to top-k similar entities (much faster than searching all)
        search_k = min(100, len(type_entities))  # Search top 100 most similar

        for i, entity in enumerate(type_entities):
            if i in merged:
                continue

            # Search for similar entities (limit to top-k)
            query_embedding = embeddings[i : i + 1].astype("float32")
            faiss.normalize_L2(query_embedding)
            distances, indices = index.search(query_embedding, search_k)

            # Find entities above threshold
            similar_indices = [
                idx
                for idx, dist in zip(indices[0], distances[0])
                if dist >= self.threshold and idx not in merged and idx != i
            ]

            # Use first entity as canonical
            canonical = entity

            # Merge similar entities
            for similar_idx in similar_indices:
                if similar_idx not in merged:
                    merged.add(similar_idx)
                    # Update canonical form if needed
                    similar_entity = type_entities[similar_idx]
                    if len(similar_entity.text) > len(canonical.canonical_form or ""):
                        canonical.canonical_form = similar_entity.text

            resolved.append(canonical)

        return resolved

    def _resolve_batched(self, type_entities: List[Entity]) -> List[Entity]:
        """Resolve entities in batches to avoid memory issues."""
        resolved = []
        total_batches = (len(type_entities) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(0, len(type_entities), self.batch_size):
            batch = type_entities[batch_idx : batch_idx + self.batch_size]
            logger.debug(
                f"Processing batch {batch_idx // self.batch_size + 1}/{total_batches} "
                f"({len(batch)} entities)"
            )
            batch_resolved = self._resolve_single_batch(batch)
            resolved.extend(batch_resolved)

        # Final pass: merge across batches using simple exact match
        # (This is a simplification - full cross-batch resolution would be more accurate but slower)
        seen_texts = {}
        final_resolved = []
        for entity in resolved:
            text_lower = entity.text.lower()
            if text_lower not in seen_texts:
                seen_texts[text_lower] = entity
                final_resolved.append(entity)
            else:
                # Merge with existing entity
                existing = seen_texts[text_lower]
                if len(entity.text) > len(existing.canonical_form or ""):
                    existing.canonical_form = entity.text

        return final_resolved

