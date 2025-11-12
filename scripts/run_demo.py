"""Demo script for processing ~400 questions."""

import json
import logging
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ingest, query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_demo(
    questions_file: str = "data/sample_questions.json",
    answers_file: str = "answers.json",
    ingest_paths: list = None,
    skip_ingest: bool = False,
):
    """Run the complete demo workflow.

    Args:
        questions_file: Path to questions JSON file
        answers_file: Path to save answers JSON file
        ingest_paths: List of paths to ingest (defaults to data/source_data/)
        skip_ingest: Skip ingestion if graph already exists
    """
    start_time = time.time()

    # Step 1: Ingest documents
    if not skip_ingest:
        logger.info("=" * 60)
        logger.info("STEP 1: Ingesting documents")
        logger.info("=" * 60)
        ingest_start = time.time()
        if ingest_paths is None:
            ingest_paths = ["data/source_data/"]
        ingest(ingest_paths)
        ingest_time = time.time() - ingest_start
        logger.info(f"Ingestion completed in {ingest_time:.2f} seconds")
    else:
        logger.info("Skipping ingestion (graph already exists)")

    # Step 2: Load questions
    logger.info("=" * 60)
    logger.info("STEP 2: Loading questions")
    logger.info("=" * 60)
    questions_path = Path(questions_file)
    if not questions_path.exists():
        logger.error(f"Questions file not found: {questions_file}")
        sys.exit(1)

    with open(questions_path, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        if isinstance(data[0], dict) and "question" in data[0]:
            questions = [item["question"] for item in data]
        else:
            questions = data  # Assume list of strings
    else:
        questions = [data]

    logger.info(f"Loaded {len(questions)} questions from {questions_file}")

    # Step 3: Process queries
    logger.info("=" * 60)
    logger.info("STEP 3: Processing queries")
    logger.info("=" * 60)
    query_start = time.time()
    answers = query(questions, output_path=answers_file, parallel=True)
    query_time = time.time() - query_start

    # Step 4: Report results
    logger.info("=" * 60)
    logger.info("STEP 4: Results Summary")
    logger.info("=" * 60)
    total_time = time.time() - start_time
    questions_per_minute = len(questions) / (query_time / 60) if query_time > 0 else 0

    logger.info(f"Total questions processed: {len(questions)}")
    logger.info(f"Query processing time: {query_time:.2f} seconds ({query_time/60:.2f} minutes)")
    logger.info(f"Questions per minute: {questions_per_minute:.2f}")
    logger.info(f"Total time (including ingestion): {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    logger.info(f"Answers saved to: {answers_file}")

    # Validate timing requirements
    if query_time > 3600:  # 60 minutes
        logger.warning(f"⚠️  Query processing exceeded 60 minutes: {query_time/60:.2f} minutes")
    else:
        logger.info(f"✅ Query processing completed within 60 minutes: {query_time/60:.2f} minutes")

    return answers


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run GraphRAG demo")
    parser.add_argument(
        "--questions",
        type=str,
        default="data/sample_questions.json",
        help="Path to questions JSON file",
    )
    parser.add_argument(
        "--answers",
        type=str,
        default="answers.json",
        help="Path to save answers JSON file",
    )
    parser.add_argument(
        "--ingest-paths",
        nargs="+",
        default=None,
        help="Paths to ingest (defaults to data/source_data/)",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip ingestion if graph already exists",
    )

    args = parser.parse_args()

    run_demo(
        questions_file=args.questions,
        answers_file=args.answers,
        ingest_paths=args.ingest_paths,
        skip_ingest=args.skip_ingest,
    )

