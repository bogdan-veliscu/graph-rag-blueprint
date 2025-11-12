"""Async query orchestrator for parallel processing."""

import asyncio
import re
from typing import List

from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from src.graph_rag.models import AnswerResult
from src.graph_rag.query.answer_generator import AnswerGenerator
from src.graph_rag.query.entity_linker import EntityLinker
from src.graph_rag.query.explainability import ExplainabilityCollector
from src.graph_rag.query.graph_traversal import GraphTraverser
from src.graph_rag.query.query_parser import QueryParser
from src.graph_rag.query.reranker import Reranker
from src.graph_rag.query.retriever import Retriever
from src.graph_rag.utils.async_llm_client import AsyncLLMClient


class AsyncQueryOrchestrator:
    """Async orchestrator for parallel query processing."""

    def __init__(self, max_concurrent: int = None):
        """Initialize async query orchestrator.

        Args:
            max_concurrent: Maximum concurrent queries
        """
        self.graph = FalkorDBAdapter()
        self.retriever = Retriever()
        self.query_parser = QueryParser()
        self.entity_linker = EntityLinker(self.graph)
        self.traverser = GraphTraverser(self.graph)
        self.reranker = Reranker()
        self.async_llm_client = AsyncLLMClient(max_concurrent=max_concurrent)
        self.explainability_collector = ExplainabilityCollector()

    async def process_query_async(self, question: str) -> AnswerResult:
        """Process a query asynchronously.

        Args:
            question: User question

        Returns:
            AnswerResult with answer and citations
        """
        import logging
        import time
        logger = logging.getLogger(__name__)
        
        # Initialize explainability collector
        collector = ExplainabilityCollector()
        collector.start()
        
        try:
            # Parse query (synchronous)
            parse_start = time.time()
            parsed_query = self.query_parser.parse(question)
            collector.record_timing("query_parsing", time.time() - parse_start)
            collector.record_query_parsing(parsed_query)
        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            parsed_query = {"entities": []}

        try:
            # Link entities (synchronous)
            link_start = time.time()
            linked_entities = self.entity_linker.link_entities(parsed_query.get("entities", []))
            collector.record_timing("entity_linking", time.time() - link_start)
            collector.record_entity_linking(parsed_query.get("entities", []), linked_entities)
        except Exception as e:
            logger.error(f"Entity linking failed: {e}")
            linked_entities = []

        try:
            # Retrieve chunks (synchronous) - get dense/sparse separately for explainability
            retrieve_start = time.time()
            from src.graph_rag.config import config
            dense_matches = []
            sparse_matches = []
            if self.retriever.faiss_index and self.retriever.chunk_metadata:
                try:
                    dense_matches = self.retriever._dense_retrieve(question, config.dense_top_k)
                except Exception:
                    pass
            if self.retriever.bm25_index and self.retriever.chunk_metadata:
                try:
                    sparse_matches = self.retriever._sparse_retrieve(question, config.sparse_top_k)
                except Exception:
                    pass
            matches = self.retriever.retrieve(question)
            collector.record_timing("retrieval", time.time() - retrieve_start)
            collector.record_retrieval(dense_matches, sparse_matches, matches)
            if not matches:
                logger.warning("No chunks retrieved for query")
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            matches = []
            dense_matches = []
            sparse_matches = []

        try:
            # Traverse graph (synchronous)
            traverse_start = time.time()
            augmented_matches = self.traverser.traverse(linked_entities, matches)
            collector.record_timing("graph_traversal", time.time() - traverse_start)
            collector.record_graph_traversal(linked_entities, matches, augmented_matches)
        except Exception as e:
            logger.error(f"Graph traversal failed: {e}")
            augmented_matches = matches  # Fallback to original matches

        try:
            # Rerank (synchronous)
            rerank_start = time.time()
            final_matches = self.reranker.rerank(augmented_matches)
            collector.record_timing("reranking", time.time() - rerank_start)
            collector.record_reranking(augmented_matches, final_matches)
            if not final_matches:
                logger.warning("Reranking returned no matches")
                final_matches = augmented_matches[:10]  # Fallback to top 10
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            final_matches = augmented_matches[:10]  # Fallback to top 10

        try:
            # Generate answer (async)
            gen_start = time.time()
            result = await self._generate_answer_async(question, final_matches)
            collector.record_timing("answer_generation", time.time() - gen_start)
            collector.record_answer_generation(question, result.chunk_ids, result.citations)
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            # Return error message as answer
            result = AnswerResult(
                answer=f"I encountered an error generating an answer: {str(e)}. Please try again or rephrase your question.",
                citations=[],
                chunk_ids=[m.chunk_id for m in final_matches[:10]] if final_matches else [],
            )

        # Attach explainability data
        result.explainability = collector.finalize()

        return result

    async def _generate_answer_async(
        self, question: str, matches: List
    ) -> AnswerResult:
        """Generate answer asynchronously.

        Args:
            question: User question
            matches: Retrieved chunk matches

        Returns:
            AnswerResult
        """
        # Build context from chunks
        context_chunks = []
        chunk_ids = []
        for i, match in enumerate(matches[:10], 1):  # Top 10 chunks
            chunk_data = self.graph.get_chunk(match.chunk_id)
            if chunk_data:
                text = chunk_data.get("text", "")
                context_chunks.append(f"[{i}] {text}")
                chunk_ids.append(match.chunk_id)

        context = "\n\n".join(context_chunks)

        # Build prompt
        system_prompt = """You are a legal document assistant. Answer questions based ONLY on the provided context. 
CRITICAL RULES:
1. Use ONLY information from the provided context chunks
2. Cite sources using [1], [2], etc. inline
3. If information is not in the context, say "I cannot find this information in the provided documents"
4. Be precise and factual
5. Format citations as [1][2] inline in your answer"""

        user_prompt = f"""Context:
{context}

Question: {question}

Answer the question using ONLY the context above. Include inline citations like [1][2] for each claim."""

        # Generate answer (async)
        answer = await self.async_llm_client.generate(user_prompt, system_prompt)

        # Format citations (synchronous)
        # Extract citation numbers
        citation_numbers = re.findall(r"\[(\d+)\]", answer)
        unique_citations = sorted(set(int(n) for n in citation_numbers))

        # Format reference list using AnswerGenerator's method
        from src.graph_rag.query.answer_generator import AnswerGenerator

        generator = AnswerGenerator(self.graph)
        reference_list = generator._format_reference_list(
            [chunk_ids[i - 1] for i in unique_citations if i <= len(chunk_ids)]
        )

        # Format answer with citations appended
        formatted_answer = answer
        if reference_list:
            formatted_answer += f"\n\nReferences\n{reference_list}"

        return AnswerResult(
            answer=formatted_answer,
            citations=reference_list.split("\n") if reference_list else [],
            chunk_ids=chunk_ids,
        )

    async def process_queries_async(self, questions: List[str]) -> List[AnswerResult]:
        """Process multiple queries in parallel.

        Args:
            questions: List of questions

        Returns:
            List of AnswerResult objects
        """
        import logging
        logger = logging.getLogger(__name__)
        
        tasks = [self.process_query_async(q) for q in questions]
        # Use return_exceptions=True to prevent one failure from crashing all queries
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error AnswerResults
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query {i} failed: {result}")
                processed_results.append(
                    AnswerResult(
                        answer=f"I encountered an error processing this question: {str(result)}. Please try again or rephrase your question.",
                        citations=[],
                        chunk_ids=[],
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results

