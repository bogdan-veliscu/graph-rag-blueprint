"""Main entry point for GraphRAG system."""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from graph_rag.config import config
from graph_rag.utils.progress import ProgressTracker

# Setup rich console and logging
console = Console()

# Configure logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)]
)
logger = logging.getLogger(__name__)


def ingest(document_paths: List[str]) -> None:
    """Ingest documents and build the knowledge graph.

    Args:
        document_paths: List of paths to document directories or files
    """
    from graph_rag.ingest.pipeline import ingest_documents

    console.print(Panel.fit(
        f"[bold cyan]GraphRAG Ingestion[/bold cyan]\n"
        f"Processing [bold]{len(document_paths)}[/bold] path(s)",
        border_style="cyan"
    ))
    ingest_documents(document_paths)
    console.print("[bold green]✓[/bold green] Ingestion complete")


def query(
    questions: List[str],
    output_path: Optional[str] = None,
    parallel: bool = True,
) -> List[str]:
    """Query the knowledge graph and generate answers.

    Args:
        questions: List of question strings
        output_path: Optional path to save results as JSON (defaults to "answers.json" in root)
        parallel: Whether to process queries in parallel (default: True)

    Returns:
        List of answer strings (formatted with citations)
    """
    # Ensure output_path defaults to answers.json in root directory
    if output_path is None:
        output_path = "answers.json"
    
    # Resolve to absolute path to ensure it's in project root
    output_path = Path(output_path).resolve()
    
    if parallel and len(questions) > 1:
        return _query_parallel(questions, str(output_path))
    else:
        return _query_sequential(questions, str(output_path))


def _query_parallel(questions: List[str], output_path: str) -> List[str]:
    """Process queries in parallel with progress tracking.

    Args:
        questions: List of question strings
        output_path: Path to save results as JSON (always provided)

    Returns:
        List of answer strings
    """
    import asyncio

    from graph_rag.config import config
    from graph_rag.query.async_orchestrator import AsyncQueryOrchestrator

    logger.info(f"Processing {len(questions)} questions in parallel")
    orchestrator = AsyncQueryOrchestrator()

    async def process_with_progress():
        results = []
        with ProgressTracker(len(questions), desc="Processing questions") as progress:
            # Process in batches to avoid overwhelming the system
            batch_size = config.query_batch_size
            for i in range(0, len(questions), batch_size):
                batch = questions[i : i + batch_size]
                batch_results = await orchestrator.process_queries_async(batch)
                results.extend(batch_results)  # Keep full AnswerResult objects
                progress.update(len(batch))
        return results

    results = asyncio.run(process_with_progress())

    # Extract answers and explainability
    answers = [r.answer for r in results]
    
    # Save to file - include explainability if enabled
    from graph_rag.config import config
    from graph_rag.query.explainability import format_explainability_human_readable
    
    output_data = []
    for result in results:
        item = {"answer": result.answer}
        if config.explainability_enabled and result.explainability:
            item["explainability"] = result.explainability
            # Add human-readable format for detailed level
            if config.explainability_level == "detailed":
                item["explainability_text"] = format_explainability_human_readable(result.explainability)
        output_data.append(item)
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path_obj, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    console.print(f"[bold green]✓[/bold green] Results saved to [cyan]{output_path}[/cyan]")

    # Print explainability summary if enabled
    if config.explainability_enabled and results and results[0].explainability:
        console.print("\n[bold cyan]Explainability Summary:[/bold cyan]")
        exp = results[0].explainability
        if "summary" in exp:
            summary = exp["summary"]
            console.print(f"  Entities detected: {summary.get('entities_detected', 0)}")
            console.print(f"  Entities linked: {summary.get('entities_linked', 0)}")
            console.print(f"  Chunks retrieved: {summary.get('chunks_retrieved', 0)}")
            console.print(f"  Chunks used: {summary.get('chunks_used', 0)}")
        if "timing" in exp:
            timing = exp["timing"]
            console.print(f"  Total time: {timing.get('total_time_seconds', 0):.3f}s")

    console.print("[bold green]✓[/bold green] Query processing complete")
    return answers


def _query_sequential(questions: List[str], output_path: str) -> List[str]:
    """Process queries sequentially.

    Args:
        questions: List of question strings
        output_path: Path to save results as JSON (always provided)

    Returns:
        List of answer strings
    """
    from graph_rag.query.orchestrator import QueryOrchestrator

    logger.info(f"Processing {len(questions)} questions sequentially")
    orchestrator = QueryOrchestrator()
    results = []

    with ProgressTracker(len(questions), desc="Processing questions") as progress:
        for question in questions:
            result = orchestrator.process_query(question)
            results.append(result)
            progress.update(1)

    # Extract answers
    answers = [r.answer for r in results]
    
    # Save to file - include explainability if enabled (note: sequential mode doesn't collect explainability yet)
    from graph_rag.config import config
    output_data = [{"answer": answer} for answer in answers]
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path_obj, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    console.print(f"[bold green]✓[/bold green] Results saved to [cyan]{output_path}[/cyan]")

    console.print("[bold green]✓[/bold green] Query processing complete")
    return answers


if __name__ == "__main__":
    if len(sys.argv) < 2:
        console.print(Panel.fit(
            "[bold cyan]GraphRAG System[/bold cyan]\n\n"
            "[bold]Usage:[/bold] python main.py <ingest|query> [args...]\n\n"
            "[bold]Examples:[/bold]\n"
            "  python main.py ingest data/source_data/\n"
            "  python main.py query 'What is Decree-Law No. 61?'\n"
            "  python main.py query --file data/sample_questions.json --output answers.json",
            border_style="cyan"
        ))
        sys.exit(1)

    command = sys.argv[1]

    if command == "ingest":
        paths = sys.argv[2:] if len(sys.argv) > 2 else ["data/source_data/"]
        ingest(paths)
    elif command == "query":
        import argparse

        parser = argparse.ArgumentParser(description="Query the knowledge graph")
        parser.add_argument(
            "questions",
            nargs="*",
            help="Question strings (or use --file to read from JSON)",
        )
        parser.add_argument(
            "--file",
            type=str,
            help="Path to JSON file with questions (format: [{'question': '...'}, ...])",
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Path to save results as JSON (default: answers.json)",
            default="answers.json",
        )
        parser.add_argument(
            "--no-parallel",
            action="store_true",
            help="Disable parallel processing",
        )

        args = parser.parse_args(sys.argv[2:])

        # Load questions
        if args.file:
            with open(args.file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    if isinstance(data[0], dict) and "question" in data[0]:
                        questions = [item["question"] for item in data]
                    else:
                        questions = data  # Assume list of strings
                else:
                    questions = [data]
        elif args.questions:
            questions = args.questions
        else:
            console.print("[bold red]✗[/bold red] Error: No questions provided. Use --file or provide questions as arguments.")
            sys.exit(1)

        # Get LLM provider info for display
        from graph_rag.config import config
        llm_info = []
        if config.llm_provider == "ollama":
            llm_info.append(f"Model: [bold]{config.ollama_model}[/bold]")
            llm_info.append(f"Endpoint: [bold]{config.ollama_base_url}[/bold]")
        elif config.llm_provider == "anthropic":
            llm_info.append(f"Provider: [bold]Anthropic[/bold]")
            llm_info.append(f"Endpoint: [bold]{config.anthropic_base_url}[/bold]")
        
        # Process queries
        panel_content = (
            f"[bold cyan]GraphRAG Query Processing[/bold cyan]\n"
            f"Processing [bold]{len(questions)}[/bold] question(s)\n"
            f"Mode: [bold]{'Parallel' if not args.no_parallel else 'Sequential'}[/bold]\n"
            f"{' | '.join(llm_info)}"
        )
        console.print(Panel.fit(panel_content, border_style="cyan"))
        answers = query(questions, output_path=args.output, parallel=not args.no_parallel)

        # Print summary table with per-question details
        summary_table = Table(title="Query Summary", show_header=True, header_style="bold cyan", show_lines=False)
        summary_table.add_column("No.", style="cyan", width=6, justify="right", no_wrap=True)
        summary_table.add_column("Question (first 100 chars)", style="yellow", min_width=40, max_width=60, overflow="fold")
        summary_table.add_column("Answer (first 200 chars)", style="green", min_width=50, max_width=80, overflow="fold")
        
        # Truncate function
        def truncate(text: str, max_len: int) -> str:
            """Truncate text to max_len characters, adding '...' if truncated."""
            if not text:
                return "(empty)"
            text_str = str(text).strip()
            if len(text_str) <= max_len:
                return text_str
            return text_str[:max_len - 3] + "..."
        
        # Add rows for each question-answer pair
        for i, (question, answer) in enumerate(zip(questions, answers), 1):
            question_truncated = truncate(question, 100)
            answer_truncated = truncate(answer, 200)
            summary_table.add_row(str(i), question_truncated, answer_truncated)
        
        # Add summary row
        summary_table.add_row("", "", "", style="dim")
        summary_table.add_row("Total", f"{len(questions)} questions processed", f"Saved to {args.output}", style="bold")
        console.print(summary_table)
    else:
        console.print(f"[bold red]✗[/bold red] Unknown command: [cyan]{command}[/cyan]")
        sys.exit(1)

