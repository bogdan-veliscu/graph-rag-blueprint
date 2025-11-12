"""Script to evaluate answers using LLM-as-judge."""

import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph_rag.evaluation.evaluator import Evaluator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def evaluate_answers(
    questions_file: str,
    answers_file: str,
    ground_truth_file: Optional[str] = None,
    output_file: str = "evaluation_results.json",
):
    """Evaluate answers against questions.

    Args:
        questions_file: Path to JSON file with questions
        answers_file: Path to JSON file with answers
        ground_truth_file: Optional path to ground truth answers
        output_file: Path to save evaluation results
    """
    # Load questions
    with open(questions_file, "r") as f:
        questions_data = json.load(f)
        if isinstance(questions_data, list):
            if isinstance(questions_data[0], dict) and "question" in questions_data[0]:
                questions = [item["question"] for item in questions_data]
            else:
                questions = questions_data
        else:
            questions = [questions_data]

    # Load answers
    with open(answers_file, "r") as f:
        answers_data = json.load(f)
        if isinstance(answers_data, list):
            if isinstance(answers_data[0], dict) and "answer" in answers_data[0]:
                answers = [item["answer"] for item in answers_data]
            else:
                answers = answers_data
        else:
            answers = [answers_data]

    # Load ground truth if provided
    ground_truth = None
    if ground_truth_file and Path(ground_truth_file).exists():
        with open(ground_truth_file, "r") as f:
            ground_truth_data = json.load(f)
            if isinstance(ground_truth_data, list):
                if isinstance(ground_truth_data[0], dict) and "answer" in ground_truth_data[0]:
                    ground_truth = [item["answer"] for item in ground_truth_data]
                else:
                    ground_truth = ground_truth_data
            else:
                ground_truth = [ground_truth_data]

    if len(questions) != len(answers):
        logger.error(f"Mismatch: {len(questions)} questions but {len(answers)} answers")
        sys.exit(1)

    logger.info(f"Evaluating {len(questions)} question-answer pairs")

    # Evaluate
    evaluator = Evaluator()
    results = evaluator.evaluate(questions, answers, ground_truth)

    # Save results
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Evaluation results saved to {output_file}")
    logger.info(f"Overall score: {results['overall_score']:.2%}")
    logger.info(f"Passing threshold: >95% ({'>95%' if results['overall_score'] > 0.95 else 'FAILED'})")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate answers using LLM-as-judge")
    parser.add_argument(
        "--questions",
        type=str,
        required=True,
        help="Path to questions JSON file",
    )
    parser.add_argument(
        "--answers",
        type=str,
        required=True,
        help="Path to answers JSON file",
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default=None,
        help="Optional path to ground truth answers JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation_results.json",
        help="Path to save evaluation results",
    )

    args = parser.parse_args()

    evaluate_answers(
        questions_file=args.questions,
        answers_file=args.answers,
        ground_truth_file=args.ground_truth,
        output_file=args.output,
    )

