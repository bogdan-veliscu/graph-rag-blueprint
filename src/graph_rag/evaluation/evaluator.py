"""LLM-as-judge evaluator for answer quality assessment."""

import json
import logging
from typing import Dict, List, Optional

from graph_rag.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class Evaluator:
    """Evaluates answers using LLM-as-judge across multiple dimensions."""

    def __init__(self):
        """Initialize evaluator."""
        self.llm_client = LLMClient()

    def evaluate(
        self,
        questions: List[str],
        answers: List[str],
        ground_truth: Optional[List[str]] = None,
    ) -> Dict:
        """Evaluate answers using LLM-as-judge.

        Args:
            questions: List of question strings
            answers: List of answer strings (same length as questions)
            ground_truth: Optional list of ground truth answers

        Returns:
            Dictionary with overall score and per-dimension scores:
            {
                "overall_score": 0.95,
                "faithfulness": 0.96,
                "relevance": 0.94,
                "completeness": 0.95,
                "clarity": 0.95,
                "per_question": [...]
            }
        """
        if len(questions) != len(answers):
            raise ValueError("Questions and answers must have same length")

        logger.info(f"Evaluating {len(questions)} question-answer pairs")

        # Evaluate each question-answer pair
        per_question_scores = []
        dimension_scores = {
            "faithfulness": [],
            "relevance": [],
            "completeness": [],
            "clarity": [],
        }

        for i, (question, answer) in enumerate(zip(questions, answers)):
            logger.info(f"Evaluating question {i+1}/{len(questions)}")
            scores = self._evaluate_single(question, answer, ground_truth[i] if ground_truth else None)
            per_question_scores.append(scores)

            # Aggregate dimension scores
            for dimension in dimension_scores.keys():
                dimension_scores[dimension].append(scores[dimension])

        # Calculate overall scores
        overall_scores = {}
        for dimension, scores_list in dimension_scores.items():
            overall_scores[dimension] = sum(scores_list) / len(scores_list) if scores_list else 0.0

        # Overall score is average of all dimensions
        overall_score = sum(overall_scores.values()) / len(overall_scores) if overall_scores else 0.0

        result = {
            "overall_score": overall_score,
            **overall_scores,
            "per_question": per_question_scores,
            "total_questions": len(questions),
        }

        logger.info(f"Evaluation complete. Overall score: {overall_score:.2%}")
        logger.info(f"Faithfulness: {overall_scores['faithfulness']:.2%}")
        logger.info(f"Relevance: {overall_scores['relevance']:.2%}")
        logger.info(f"Completeness: {overall_scores['completeness']:.2%}")
        logger.info(f"Clarity: {overall_scores['clarity']:.2%}")

        return result

    def _evaluate_single(
        self, question: str, answer: str, ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """Evaluate a single question-answer pair.

        Args:
            question: Question string
            answer: Answer string
            ground_truth: Optional ground truth answer

        Returns:
            Dictionary with scores for each dimension (0.0 to 1.0)
        """
        prompt = self._build_evaluation_prompt(question, answer, ground_truth)
        response = self.llm_client.generate(prompt, max_tokens=200, temperature=0.0)

        # Parse JSON response
        try:
            # Extract JSON from response (may have markdown code blocks)
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            scores = json.loads(response_text)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse evaluation response: {e}. Using default scores.")
            # Default to neutral scores if parsing fails
            scores = {
                "faithfulness": 0.5,
                "relevance": 0.5,
                "completeness": 0.5,
                "clarity": 0.5,
            }

        # Ensure all dimensions are present and in [0, 1] range
        for dimension in ["faithfulness", "relevance", "completeness", "clarity"]:
            if dimension not in scores:
                scores[dimension] = 0.5
            scores[dimension] = max(0.0, min(1.0, float(scores[dimension])))

        return scores

    def _build_evaluation_prompt(
        self, question: str, answer: str, ground_truth: Optional[str] = None
    ) -> str:
        """Build evaluation prompt for LLM-as-judge.

        Args:
            question: Question string
            answer: Answer string
            ground_truth: Optional ground truth answer

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert evaluator assessing the quality of an answer to a legal question.

Question: {question}

Answer to evaluate:
{answer}
"""

        if ground_truth:
            prompt += f"""
Ground truth reference (for comparison):
{ground_truth}
"""

        prompt += """
Evaluate the answer across four dimensions on a scale of 0.0 to 1.0:

1. **Faithfulness** (0.0-1.0): Is the answer grounded in the cited sources? Are there any hallucinations or unsupported claims?
   - 1.0: All claims are supported by citations, no hallucinations
   - 0.5: Some claims supported, some unsupported
   - 0.0: Major hallucinations or no citations

2. **Relevance** (0.0-1.0): Does the answer address the question's intent?
   - 1.0: Directly and completely addresses the question
   - 0.5: Partially relevant but misses key aspects
   - 0.0: Not relevant to the question

3. **Completeness** (0.0-1.0): Does the answer cover all key legal points?
   - 1.0: Comprehensive coverage of all important points
   - 0.5: Covers main points but misses some details
   - 0.0: Incomplete or missing key information

4. **Clarity** (0.0-1.0): Is the answer well-structured and legally coherent?
   - 1.0: Clear, well-structured, legally coherent
   - 0.5: Generally clear but could be better organized
   - 0.0: Unclear or poorly structured

Respond with a JSON object containing scores for each dimension:
{
  "faithfulness": 0.95,
  "relevance": 0.94,
  "completeness": 0.93,
  "clarity": 0.96
}
"""

        return prompt

