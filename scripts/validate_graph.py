"""Validate graph structure after ingestion."""

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter

logging.basicConfig(level=logging.WARNING)  # Suppress INFO logs, only show errors
logger = logging.getLogger(__name__)
console = Console()


def validate_graph():
    """Validate graph structure."""
    console.print(Panel.fit(
        "[bold cyan]Graph Validation[/bold cyan]\n"
        "Checking graph structure and node/edge counts...",
        border_style="cyan"
    ))
    
    try:
        graph = FalkorDBAdapter()
        console.print("[green]✓[/green] Connected to FalkorDB")
    except Exception as e:
        console.print(f"[bold red]✗[/bold red] Failed to connect to FalkorDB: {e}")
        console.print("[yellow]Make sure FalkorDB is running:[/yellow] [cyan]make falkordb-start[/cyan]")
        return False

    # Create summary table
    summary_table = Table(title="Graph Summary", show_header=True, header_style="bold cyan")
    summary_table.add_column("Node/Edge Type", style="cyan", width=30)
    summary_table.add_column("Count", style="green", justify="right")
    summary_table.add_column("Status", style="yellow", width=15)

    total_nodes = 0
    total_edges = 0
    has_errors = False

    # Count nodes by type
    node_types = ["Document", "Page", "Chunk", "Entity"]
    console.print("\n[cyan]Counting nodes...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Querying nodes...", total=len(node_types))
        
        for node_type in node_types:
            try:
                query = f"MATCH (n:{node_type}) RETURN count(n) as count"
                results = graph.execute_query(query)
                count = results[0].get("count", 0) if results else 0
                total_nodes += count
                
                status = "[green]✓[/green]" if count > 0 else "[yellow]⚠[/yellow] Empty"
                summary_table.add_row(f"{node_type} nodes", f"{count:,}", status)
                progress.advance(task)
            except Exception as e:
                has_errors = True
                summary_table.add_row(f"{node_type} nodes", "[red]Error[/red]", f"[red]✗[/red] {str(e)[:30]}")
                progress.advance(task)

    # Count edges by type
    edge_types = [
        "DOCUMENT_HAS_PAGE",
        "PAGE_HAS_CHUNK",
        "PART_OF",
        "MENTIONS",
        "RELATED_TO",
        "DOCUMENT_PUBLISHED_BY",
        "PAGE_AUTHORED_BY",
    ]
    
    console.print("\n[cyan]Counting edges...[/cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Querying edges...", total=len(edge_types))
        
        for edge_type in edge_types:
            try:
                query = f"MATCH ()-[r:{edge_type}]->() RETURN count(r) as count"
                results = graph.execute_query(query)
                count = results[0].get("count", 0) if results else 0
                total_edges += count
                
                status = "[green]✓[/green]" if count > 0 else "[yellow]⚠[/yellow] Empty"
                summary_table.add_row(f"{edge_type} edges", f"{count:,}", status)
                progress.advance(task)
            except Exception as e:
                has_errors = True
                summary_table.add_row(f"{edge_type} edges", "[red]Error[/red]", f"[red]✗[/red] {str(e)[:30]}")
                progress.advance(task)

    # Add totals row
    summary_table.add_section()
    summary_table.add_row(
        "[bold]Total Nodes[/bold]",
        f"[bold green]{total_nodes:,}[/bold green]",
        "[green]✓[/green]" if total_nodes > 0 else "[red]✗[/red]"
    )
    summary_table.add_row(
        "[bold]Total Edges[/bold]",
        f"[bold green]{total_edges:,}[/bold green]",
        "[green]✓[/green]" if total_edges > 0 else "[red]✗[/red]"
    )

    console.print("\n")
    console.print(summary_table)

    # Validation checks
    console.print("\n[cyan]Validation Checks:[/cyan]")
    
    checks_passed = True
    
    if total_nodes == 0:
        console.print("[bold red]✗[/bold red] [red]No nodes found in graph![/red]")
        console.print("[yellow]   → Run ingestion first: [cyan]make ingest-fast[/cyan][/yellow]")
        checks_passed = False
    else:
        console.print(f"[bold green]✓[/bold green] Found {total_nodes:,} nodes")
    
    if total_edges == 0:
        console.print("[bold red]✗[/bold red] [red]No edges found in graph![/red]")
        console.print("[yellow]   → Run ingestion first: [cyan]make ingest-fast[/cyan][/yellow]")
        checks_passed = False
    else:
        console.print(f"[bold green]✓[/bold green] Found {total_edges:,} edges")
    
    # Check for expected minimums
    if total_nodes > 0:
        try:
            doc_query = "MATCH (n:Document) RETURN count(n) as count"
            doc_results = graph.execute_query(doc_query)
            doc_count = doc_results[0].get("count", 0) if doc_results else 0
            
            if doc_count == 0:
                console.print("[yellow]⚠[/yellow] [yellow]No Document nodes found[/yellow]")
            else:
                console.print(f"[bold green]✓[/bold green] Found {doc_count:,} document(s)")
        except Exception:
            pass

    # Final status
    console.print("\n")
    if checks_passed and not has_errors:
        console.print(Panel.fit(
            "[bold green]✓ Graph Validation Passed[/bold green]\n"
            f"Graph contains {total_nodes:,} nodes and {total_edges:,} edges",
            border_style="green"
        ))
        return True
    else:
        console.print(Panel.fit(
            "[bold red]✗ Graph Validation Failed[/bold red]\n"
            "Check errors above and ensure ingestion completed successfully",
            border_style="red"
        ))
        return False


if __name__ == "__main__":
    success = validate_graph()
    sys.exit(0 if success else 1)
