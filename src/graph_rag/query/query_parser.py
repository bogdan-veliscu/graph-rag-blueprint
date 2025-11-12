"""Query parser for extracting entities and keywords."""

import re
from typing import Any, Dict, List


class QueryParser:
    """Parse queries to extract entities and keywords."""

    def parse(self, query: str) -> Dict[str, Any]:
        """Parse a query string.

        Args:
            query: Query string

        Returns:
            Dictionary with 'entities', 'keywords', 'question_type'
        """
        # Extract potential entities (capitalized phrases)
        entities = self._extract_entities(query)

        # Extract keywords (non-stop words)
        keywords = self._extract_keywords(query)

        # Identify question type
        question_type = self._identify_question_type(query)

        return {
            "entities": entities,
            "keywords": keywords,
            "question_type": question_type,
            "original_query": query,
        }

    def _extract_entities(self, query: str) -> List[str]:
        """Extract potential entity mentions.

        Args:
            query: Query string

        Returns:
            List of entity strings
        """
        # Capitalized phrases
        entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", query)
        return list(set(entities))

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query.

        Args:
            query: Query string

        Returns:
            List of keywords
        """
        # Simple keyword extraction (remove stop words)
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "what",
            "who",
            "when",
            "where",
            "why",
            "how",
        }
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords

    def _identify_question_type(self, query: str) -> str:
        """Identify question type.

        Args:
            query: Query string

        Returns:
            Question type string
        """
        query_lower = query.lower()
        if query_lower.startswith("what"):
            return "what"
        elif query_lower.startswith("who"):
            return "who"
        elif query_lower.startswith("when"):
            return "when"
        elif query_lower.startswith("where"):
            return "where"
        elif query_lower.startswith("how"):
            return "how"
        else:
            return "general"

