"""Async query orchestrator for parallel processing."""

import asyncio
import re
from typing import List

from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from src.graph_rag.models import AnswerResult
from src.graph_rag.query.answer_generator import AnswerGenerator
from src.graph_rag.query.entity_linker import EntityLinker
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

    async def process_query_async(self, question: str) -> AnswerResult:
        """Process a query asynchronously.

        Args:
            question: User question

        Returns:
            AnswerResult with answer and citations
        """
        # Parse query (synchronous)
        parsed_query = self.query_parser.parse(question)

        # Link entities (synchronous)
        linked_entities = self.entity_linker.link_entities(parsed_query.get("entities", []))

        # Retrieve chunks (synchronous)
        matches = self.retriever.retrieve(question)

        # Traverse graph (synchronous)
        augmented_matches = self.traverser.traverse(linked_entities, matches)

        # Rerank (synchronous)
        final_matches = self.reranker.rerank(augmented_matches)

        # Generate answer (async)
        result = await self._generate_answer_async(question, final_matches)

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
        tasks = [self.process_query_async(q) for q in questions]
        results = await asyncio.gather(*tasks)
        return results

