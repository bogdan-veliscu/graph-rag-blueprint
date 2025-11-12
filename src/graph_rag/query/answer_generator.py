"""Answer generation with LLM and citation formatting."""

import re
from typing import List

from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from src.graph_rag.models import AnswerResult, ChunkMatch
from src.graph_rag.utils.llm_client import LLMClient
from src.graph_rag.utils.text_utils import strip_orig_tags


class AnswerGenerator:
    """Generate answers with citations."""

    def __init__(self, graph_adapter: FalkorDBAdapter):
        """Initialize answer generator.

        Args:
            graph_adapter: FalkorDB adapter for metadata retrieval
        """
        self.graph = graph_adapter
        self.llm_client = LLMClient()

    def generate_answer(
        self, question: str, matches: List[ChunkMatch]
    ) -> AnswerResult:
        """Generate answer from question and retrieved chunks.

        Args:
            question: User question
            matches: Retrieved chunk matches

        Returns:
            AnswerResult with answer and citations
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

        # Generate answer
        answer = self.llm_client.generate(user_prompt, system_prompt)

        # Extract citation numbers from answer
        citation_numbers = re.findall(r"\[(\d+)\]", answer)
        unique_citations = sorted(set(int(n) for n in citation_numbers))

        # Format reference list
        reference_list = self._format_reference_list(
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

    def _format_reference_list(self, chunk_ids: List[str]) -> str:
        """Format reference list with rich metadata.

        Args:
            chunk_ids: List of chunk IDs to cite

        Returns:
            Formatted reference list string
        """
        references = []
        seen_docs = set()

        for i, chunk_id in enumerate(chunk_ids, 1):
            chunk_data = self.graph.get_chunk(chunk_id)
            if not chunk_data:
                # Fallback to chunk ID
                references.append(f"{i}. {chunk_id}")
                continue

            # Get page and document metadata
            page_id = chunk_data.get("page_id")
            document_id = chunk_data.get("document_id")
            page_number = chunk_data.get("page_number", "?")

            citation_parts = []

            if document_id and document_id not in seen_docs:
                seen_docs.add(document_id)
                document = self.graph.get_document(document_id)
                if document:
                    # Format citation with rich metadata
                    title = document.title or document.metadata.get("document_title", "")
                    issue_number = document.metadata.get("issue_number")
                    volume_number = document.metadata.get("volume_number")
                    document_date = document.metadata.get("document_date", "")

                    citation = title
                    if issue_number:
                        citation += f" - Issue {issue_number}"
                    if volume_number:
                        citation += f", Volume {volume_number}"
                    if document_date:
                        citation += f" ({document_date})"
                    citation += f". p.{page_number}."

                    # Get publisher from page or document
                    publisher = None
                    if page_id:
                        page = self.graph.get_page(page_id)
                        if page:
                            publisher = page.metadata.get("publisher")
                    if not publisher:
                        publisher = document.metadata.get("publisher")

                    if publisher:
                        # Strip <orig> tags for citation
                        publisher_text = strip_orig_tags(publisher)
                        citation += f" {publisher_text}."

                    citation_parts.append(citation)
                else:
                    # Fallback to filename
                    source_file = chunk_data.get("source_file", chunk_id)
                    citation_parts.append(f"{source_file}. p.{page_number}.")
            else:
                # Same document, just page number
                citation_parts.append(f"p.{page_number}.")

            if citation_parts:
                references.append(f"{i}. {' '.join(citation_parts)}")
            else:
                # Final fallback
                source_file = chunk_data.get("source_file", chunk_id)
                references.append(f"{i}. {source_file}. p.{page_number}.")

        return "\n".join(references)

