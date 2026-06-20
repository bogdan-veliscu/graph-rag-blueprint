"""Explainability collection and formatting for query results."""

import time
from typing import Any, Dict, List, Optional

from graph_rag.config import config
from graph_rag.models import AnswerResult, ChunkMatch, Entity


class ExplainabilityCollector:
    """Collects explainability information during query processing."""

    def __init__(self):
        """Initialize explainability collector."""
        self.data: Dict[str, Any] = {}
        self.timings: Dict[str, float] = {}
        self.start_time: Optional[float] = None

    def start(self):
        """Start timing for the entire query."""
        self.start_time = time.time()
        self.data = {}
        self.timings = {}

    def record_step(self, step_name: str, data: Dict[str, Any]):
        """Record data for a processing step.

        Args:
            step_name: Name of the step (e.g., 'query_parsing', 'retrieval')
            data: Dictionary of data to record
        """
        if not config.explainability_enabled:
            return

        step_start = time.time()
        self.data[step_name] = data
        step_end = time.time()
        self.timings[step_name] = step_end - step_start

    def record_timing(self, step_name: str, duration: float):
        """Record timing for a step.

        Args:
            step_name: Name of the step
            duration: Duration in seconds
        """
        if not config.explainability_enabled:
            return
        self.timings[step_name] = duration

    def record_query_parsing(self, parsed_query: Dict[str, Any]):
        """Record query parsing results.

        Args:
            parsed_query: Parsed query dictionary
        """
        if not config.explainability_enabled or not config.explainability_include_entities:
            return

        self.record_step("query_parsing", {
            "entities_detected": parsed_query.get("entities", []),
            "query_type": parsed_query.get("query_type", "unknown"),
        })

    def record_entity_linking(
        self, query_entities: List[str], linked_entities: List[Entity]
    ):
        """Record entity linking results.

        Args:
            query_entities: Entities from query
            linked_entities: Linked entities from graph
        """
        if not config.explainability_enabled or not config.explainability_include_entities:
            return

        linked_info = []
        for entity in linked_entities:
            linked_info.append({
                "id": entity.id,
                "text": entity.text,
                "type": entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type),
                "canonical_form": entity.canonical_form,
            })

        self.record_step("entity_linking", {
            "query_entities": query_entities,
            "linked_entities": linked_info,
            "entities_found": len(linked_entities),
            "entities_searched": len(query_entities),
        })

    def record_retrieval(
        self,
        dense_matches: List[ChunkMatch],
        sparse_matches: List[ChunkMatch],
        fused_matches: List[ChunkMatch],
    ):
        """Record retrieval results.

        Args:
            dense_matches: Dense retrieval results
            sparse_matches: Sparse retrieval results
            fused_matches: Fused retrieval results
        """
        if not config.explainability_enabled or not config.explainability_include_retrieval:
            return

        def format_matches(matches: List[ChunkMatch], top_n: int = 5) -> List[Dict[str, Any]]:
            """Format matches for explainability."""
            formatted = []
            for match in matches[:top_n]:
                formatted.append({
                    "chunk_id": match.chunk_id,
                    "score": round(match.score, 4),
                    "semantic_score": round(match.semantic_score, 4) if hasattr(match, 'semantic_score') else None,
                })
            return formatted

        self.record_step("retrieval", {
            "dense_count": len(dense_matches),
            "sparse_count": len(sparse_matches),
            "fused_count": len(fused_matches),
            "top_dense_matches": format_matches(dense_matches) if config.explainability_level == "detailed" else None,
            "top_sparse_matches": format_matches(sparse_matches) if config.explainability_level == "detailed" else None,
            "top_fused_matches": format_matches(fused_matches),
        })

    def record_graph_traversal(
        self,
        linked_entities: List[Entity],
        retrieved_chunks: List[ChunkMatch],
        augmented_chunks: List[ChunkMatch],
    ):
        """Record graph traversal results.

        Args:
            linked_entities: Entities used for traversal
            retrieved_chunks: Chunks before traversal
            augmented_chunks: Chunks after traversal
        """
        if not config.explainability_enabled or not config.explainability_include_graph:
            return

        chunks_added = len(augmented_chunks) - len(retrieved_chunks)
        graph_scores = [m.graph_score for m in augmented_chunks if hasattr(m, 'graph_score') and m.graph_score > 0]

        self.record_step("graph_traversal", {
            "entities_used": [e.id for e in linked_entities],
            "chunks_before": len(retrieved_chunks),
            "chunks_after": len(augmented_chunks),
            "chunks_added": chunks_added,
            "avg_graph_score": round(sum(graph_scores) / len(graph_scores), 4) if graph_scores else 0.0,
            "max_graph_score": round(max(graph_scores), 4) if graph_scores else 0.0,
        })

    def record_reranking(
        self, before: List[ChunkMatch], after: List[ChunkMatch]
    ):
        """Record reranking results.

        Args:
            before: Chunks before reranking
            after: Chunks after reranking
        """
        if not config.explainability_enabled or not config.explainability_include_scores:
            return

        def format_top_matches(matches: List[ChunkMatch], top_n: int = 5) -> List[Dict[str, Any]]:
            """Format top matches for explainability."""
            formatted = []
            for match in matches[:top_n]:
                formatted.append({
                    "chunk_id": match.chunk_id,
                    "final_score": round(match.score, 4),
                    "semantic_score": round(match.semantic_score, 4) if hasattr(match, 'semantic_score') else None,
                    "graph_score": round(match.graph_score, 4) if hasattr(match, 'graph_score') else None,
                })
            return formatted

        self.record_step("reranking", {
            "chunks_before": len(before),
            "chunks_after": len(after),
            "top_matches": format_top_matches(after),
        })

    def record_answer_generation(
        self, question: str, chunks_used: List[str], citations: List[str]
    ):
        """Record answer generation results.

        Args:
            question: Original question
            chunks_used: Chunk IDs used in answer
            citations: Citation strings
        """
        if not config.explainability_enabled:
            return

        self.record_step("answer_generation", {
            "chunks_used_count": len(chunks_used),
            "citations_count": len(citations),
            "chunks_used": chunks_used if config.explainability_level == "detailed" else None,
        })

    def finalize(self) -> Dict[str, Any]:
        """Finalize explainability data and return formatted result.

        Returns:
            Dictionary with explainability information
        """
        if not config.explainability_enabled:
            return {}

        total_time = time.time() - self.start_time if self.start_time else 0.0

        explainability = {
            "enabled": True,
            "level": config.explainability_level,
        }

        # Add timing information
        if config.explainability_include_timing:
            explainability["timing"] = {
                "total_time_seconds": round(total_time, 4),
                "step_timings": {k: round(v, 4) for k, v in self.timings.items()},
            }

        # Add step data based on configuration
        if config.explainability_level == "minimal":
            # Minimal: just counts and summary
            explainability["summary"] = {
                "entities_detected": len(self.data.get("query_parsing", {}).get("entities_detected", [])),
                "entities_linked": self.data.get("entity_linking", {}).get("entities_found", 0),
                "chunks_retrieved": self.data.get("retrieval", {}).get("fused_count", 0),
                "chunks_used": self.data.get("answer_generation", {}).get("chunks_used_count", 0),
            }
        elif config.explainability_level == "standard":
            # Standard: include all configured components
            if config.explainability_include_entities:
                explainability["entities"] = {
                    "detected": self.data.get("query_parsing", {}).get("entities_detected", []),
                    "linked": self.data.get("entity_linking", {}).get("linked_entities", []),
                }
            if config.explainability_include_retrieval:
                retrieval_data = self.data.get("retrieval", {})
                explainability["retrieval"] = {
                    "dense_count": retrieval_data.get("dense_count", 0),
                    "sparse_count": retrieval_data.get("sparse_count", 0),
                    "fused_count": retrieval_data.get("fused_count", 0),
                    "top_matches": retrieval_data.get("top_fused_matches", []),
                }
            if config.explainability_include_graph:
                graph_data = self.data.get("graph_traversal", {})
                explainability["graph_traversal"] = {
                    "chunks_added": graph_data.get("chunks_added", 0),
                    "avg_graph_score": graph_data.get("avg_graph_score", 0.0),
                }
            if config.explainability_include_scores:
                rerank_data = self.data.get("reranking", {})
                explainability["reranking"] = {
                    "top_matches": rerank_data.get("top_matches", []),
                }
        else:  # detailed
            # Detailed: include everything
            explainability.update(self.data)

        return explainability


def format_explainability_human_readable(explainability: Dict[str, Any]) -> str:
    """Format explainability data as human-readable text.

    Args:
        explainability: Explainability dictionary

    Returns:
        Formatted string
    """
    if not explainability:
        return ""

    lines = ["\n--- Explainability ---"]

    # Timing
    if "timing" in explainability:
        timing = explainability["timing"]
        lines.append(f"\n⏱️  Total Time: {timing.get('total_time_seconds', 0):.3f}s")
        if "step_timings" in timing:
            lines.append("Step Timings:")
            for step, duration in timing["step_timings"].items():
                lines.append(f"  • {step}: {duration:.3f}s")

    # Summary (minimal level)
    if "summary" in explainability:
        summary = explainability["summary"]
        lines.append("\n📊 Summary:")
        lines.append(f"  • Entities detected: {summary.get('entities_detected', 0)}")
        lines.append(f"  • Entities linked: {summary.get('entities_linked', 0)}")
        lines.append(f"  • Chunks retrieved: {summary.get('chunks_retrieved', 0)}")
        lines.append(f"  • Chunks used: {summary.get('chunks_used', 0)}")

    # Entities
    if "entities" in explainability:
        entities = explainability["entities"]
        lines.append("\n🔗 Entities:")
        if entities.get("detected"):
            lines.append(f"  Detected: {', '.join(entities['detected'])}")
        if entities.get("linked"):
            linked = entities["linked"]
            lines.append(f"  Linked ({len(linked)}):")
            for entity in linked[:5]:  # Show top 5
                lines.append(f"    • {entity.get('text', 'N/A')} ({entity.get('type', 'N/A')})")

    # Retrieval
    if "retrieval" in explainability:
        retrieval = explainability["retrieval"]
        lines.append("\n🔍 Retrieval:")
        lines.append(f"  • Dense: {retrieval.get('dense_count', 0)} chunks")
        lines.append(f"  • Sparse: {retrieval.get('sparse_count', 0)} chunks")
        lines.append(f"  • Fused: {retrieval.get('fused_count', 0)} chunks")
        if retrieval.get("top_matches"):
            lines.append("  Top matches:")
            for match in retrieval["top_matches"][:3]:
                lines.append(f"    • Score: {match.get('score', 0):.4f}")

    # Graph Traversal
    if "graph_traversal" in explainability:
        graph = explainability["graph_traversal"]
        lines.append("\n🕸️  Graph Traversal:")
        lines.append(f"  • Chunks added: {graph.get('chunks_added', 0)}")
        lines.append(f"  • Avg graph score: {graph.get('avg_graph_score', 0):.4f}")

    # Reranking
    if "reranking" in explainability:
        rerank = explainability["reranking"]
        if rerank.get("top_matches"):
            lines.append("\n📈 Reranking:")
            lines.append("  Top matches:")
            for match in rerank["top_matches"][:3]:
                score = match.get("final_score", 0)
                semantic = match.get("semantic_score", 0)
                graph = match.get("graph_score", 0)
                lines.append(f"    • Final: {score:.4f} (semantic: {semantic:.4f}, graph: {graph:.4f})")

    lines.append("\n--- End Explainability ---\n")
    return "\n".join(lines)

