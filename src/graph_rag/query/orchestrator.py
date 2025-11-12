"""Query orchestrator coordinating retrieval, traversal, reranking, and generation."""

import logging
from typing import Any, Dict, List, Optional

from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from src.graph_rag.models import AnswerResult, Entity
from src.graph_rag.query.answer_generator import AnswerGenerator
from src.graph_rag.query.entity_linker import EntityLinker
from src.graph_rag.query.graph_traversal import GraphTraverser
from src.graph_rag.query.query_parser import QueryParser
from src.graph_rag.query.reranker import Reranker
from src.graph_rag.query.retriever import Retriever

logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """Orchestrates the query pipeline."""

    def __init__(self):
        """Initialize query orchestrator."""
        try:
            self.graph = FalkorDBAdapter()
            # Validate graph connection
            self._validate_graph_connection()
        except Exception as e:
            logger.error(f"Failed to initialize graph adapter: {e}")
            raise
        
        try:
            self.retriever = Retriever()
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise
        
        self.query_parser = QueryParser()
        self.entity_linker = EntityLinker(self.graph)
        self.traverser = GraphTraverser(self.graph)
        self.reranker = Reranker()
        self.answer_generator = AnswerGenerator(self.graph)

    def _validate_graph_connection(self):
        """Validate that graph is accessible and populated."""
        try:
            # Try a simple query to verify connection
            result = self.graph.execute_query("MATCH (n:Document) RETURN count(n) as count LIMIT 1")
            if result:
                doc_count = result[0].get("count", 0)
                if doc_count == 0:
                    logger.warning("Graph is empty. Run ingestion first.")
        except Exception as e:
            logger.warning(f"Graph validation query failed: {e}. Continuing anyway.")

    def process_query(self, question: str) -> AnswerResult:
        """Process a query end-to-end.

        Args:
            question: User question

        Returns:
            AnswerResult with answer and citations
        """
        if not question or not question.strip():
            logger.warning("Empty question provided")
            return AnswerResult(
                answer="I cannot process an empty question. Please provide a valid question.",
                citations=[],
                chunk_ids=[],
            )

        try:
            # Parse query
            parsed_query: Dict[str, Any] = self.query_parser.parse(question)
        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            return AnswerResult(
                answer=f"I encountered an error parsing your question: {str(e)}",
                citations=[],
                chunk_ids=[],
            )

        try:
            # Link entities
            linked_entities = self.entity_linker.link_entities(parsed_query.get("entities", []))
        except Exception as e:
            logger.error(f"Entity linking failed: {e}")
            linked_entities = []

        try:
            # Retrieve chunks
            matches = self.retriever.retrieve(question)
            if not matches:
                logger.warning("No chunks retrieved for query")
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            matches = []

        try:
            # Traverse graph
            augmented_matches = self.traverser.traverse(linked_entities, matches)
        except Exception as e:
            logger.error(f"Graph traversal failed: {e}")
            augmented_matches = matches  # Fallback to original matches

        try:
            # Rerank
            final_matches = self.reranker.rerank(augmented_matches)
            if not final_matches:
                logger.warning("Reranking returned no matches")
                final_matches = augmented_matches[:10]  # Fallback to top 10
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            final_matches = augmented_matches[:10]  # Fallback to top 10

        try:
            # Generate answer
            result = self.answer_generator.generate_answer(question, final_matches)
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            # Return error message as answer
            result = AnswerResult(
                answer=f"I encountered an error generating an answer: {str(e)}. Please try again or rephrase your question.",
                citations=[],
                chunk_ids=[m.chunk_id for m in final_matches[:10]] if final_matches else [],
            )

        return result

