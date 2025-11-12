"""Performance benchmark script to validate 400 questions can be processed in ≤60 minutes."""

import json
import logging
import time
from pathlib import Path
from typing import List

import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn

from main import query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


def generate_test_questions(count: int = 400) -> List[str]:
    """Generate test questions for benchmarking.
    
    Args:
        count: Number of questions to generate
        
    Returns:
        List of question strings
    """
    # Template questions that can be varied
    templates = [
        "What is the maximum duration of a commercial lease?",
        "What is the filing fee for an appeal in civil court?",
        "What are the requirements for a valid contract?",
        "What is the statute of limitations for breach of contract?",
        "What are the penalties for non-compliance?",
        "What is the procedure for filing a lawsuit?",
        "What are the rights of tenants?",
        "What is the process for obtaining a license?",
        "What are the tax obligations for businesses?",
        "What is the legal framework for employment?",
        "What are the regulations for environmental protection?",
        "What is the procedure for dispute resolution?",
        "What are the requirements for data protection?",
        "What is the legal status of intellectual property?",
        "What are the rules for international trade?",
    ]
    
    questions = []
    for i in range(count):
        # Cycle through templates and add variation
        template = templates[i % len(templates)]
        if i > len(templates):
            # Add variation to make questions unique
            questions.append(f"{template} (Question {i+1})")
        else:
            questions.append(template)
    
    return questions


def benchmark_performance(
    question_count: int = 400,
    questions_file: str = None,
    output_file: str = "benchmark_results.json",
) -> dict:
    """Run performance benchmark.
    
    Args:
        question_count: Number of questions to process (if questions_file not provided)
        questions_file: Optional path to JSON file with questions
        output_file: Path to save benchmark results
        
    Returns:
        Dictionary with benchmark results
    """
    console.print(Panel.fit(
        f"[bold cyan]Performance Benchmark[/bold cyan]\n"
        f"Target: Process {question_count} questions in ≤60 minutes",
        border_style="cyan"
    ))
    
    # Load or generate questions
    if questions_file and Path(questions_file).exists():
        console.print(f"[cyan]Loading questions from {questions_file}[/cyan]")
        with open(questions_file, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                if isinstance(data[0], dict) and "question" in data[0]:
                    questions = [item["question"] for item in data]
                else:
                    questions = data
            else:
                questions = [data]
        question_count = len(questions)
    else:
        console.print(f"[cyan]Generating {question_count} test questions[/cyan]")
        questions = generate_test_questions(question_count)
    
    console.print(f"[green]✓[/green] Loaded {len(questions)} questions\n")
    
    # Run benchmark
    start_time = time.time()
    console.print("[cyan]Starting query processing...[/cyan]\n")
    
    try:
        answers = query(questions, output_path="benchmark_answers.json", parallel=True)
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        elapsed_minutes = elapsed_time / 60
        questions_per_minute = len(questions) / elapsed_minutes if elapsed_minutes > 0 else 0
        
        # Calculate statistics
        target_time_minutes = 60
        time_under_target = elapsed_minutes <= target_time_minutes
        time_margin = target_time_minutes - elapsed_minutes
        
        results = {
            "question_count": len(questions),
            "elapsed_time_seconds": elapsed_time,
            "elapsed_time_minutes": elapsed_minutes,
            "questions_per_minute": questions_per_minute,
            "target_time_minutes": target_time_minutes,
            "time_under_target": time_under_target,
            "time_margin_minutes": time_margin,
            "answers_generated": len(answers),
            "success": time_under_target,
        }
        
        # Display results
        console.print("\n")
        results_table = Table(title="Benchmark Results", show_header=True, header_style="bold cyan")
        results_table.add_column("Metric", style="cyan", width=30)
        results_table.add_column("Value", style="green", justify="right")
        results_table.add_column("Status", style="yellow", width=15)
        
        results_table.add_row(
            "Questions Processed",
            str(results["question_count"]),
            "[green]✓[/green]" if results["answers_generated"] == results["question_count"] else "[red]✗[/red]"
        )
        results_table.add_row(
            "Elapsed Time",
            f"{results['elapsed_time_minutes']:.2f} minutes",
            "[green]✓[/green]" if time_under_target else "[red]✗[/red]"
        )
        results_table.add_row(
            "Target Time",
            f"{target_time_minutes} minutes",
            ""
        )
        results_table.add_row(
            "Time Margin",
            f"{time_margin:.2f} minutes",
            "[green]✓[/green]" if time_margin > 0 else "[red]✗[/red]"
        )
        results_table.add_row(
            "Throughput",
            f"{questions_per_minute:.2f} questions/minute",
            "[green]✓[/green]" if questions_per_minute >= (question_count / 60) else "[yellow]⚠[/yellow]"
        )
        results_table.add_row(
            "Status",
            "[bold green]PASS[/bold green]" if time_under_target else "[bold red]FAIL[/bold red]",
            "[green]✓[/green]" if time_under_target else "[red]✗[/red]"
        )
        
        console.print(results_table)
        
        # Save results
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]✓[/green] Benchmark results saved to [cyan]{output_file}[/cyan]")
        
        # Final verdict
        if time_under_target:
            console.print(Panel.fit(
                f"[bold green]✓ Benchmark PASSED[/bold green]\n"
                f"Processed {question_count} questions in {elapsed_minutes:.2f} minutes\n"
                f"({time_margin:.2f} minutes under target)",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                f"[bold red]✗ Benchmark FAILED[/bold red]\n"
                f"Processed {question_count} questions in {elapsed_minutes:.2f} minutes\n"
                f"({abs(time_margin):.2f} minutes over target)\n\n"
                f"[yellow]Recommendations:[/yellow]\n"
                f"- Increase max_concurrent in config\n"
                f"- Optimize batch_size\n"
                f"- Check LLM response times",
                border_style="red"
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        console.print(f"[bold red]✗[/bold red] Benchmark failed with error: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance benchmark for query processing")
    parser.add_argument(
        "--count",
        type=int,
        default=400,
        help="Number of questions to process (default: 400)"
    )
    parser.add_argument(
        "--questions-file",
        type=str,
        help="Path to JSON file with questions (overrides --count)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Path to save benchmark results (default: benchmark_results.json)"
    )
    
    args = parser.parse_args()
    
    benchmark_performance(
        question_count=args.count,
        questions_file=args.questions_file,
        output_file=args.output,
    )

