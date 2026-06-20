"""Main ingestion pipeline."""

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any

import numpy as np
from rank_bm25 import BM25Okapi
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from graph_rag.config import config
from graph_rag.graph.falkordb_adapter import FalkorDBAdapter
from graph_rag.ingest.chunker import chunk_document_pages
from graph_rag.ingest.entity_extractor import extract_entities_from_text
from graph_rag.ingest.faiss_resolver import FAISSEntityResolver
from graph_rag.ingest.graph_builder import GraphBuilder
from graph_rag.ingest.relation_extractor import extract_relations
from graph_rag.ingest.source_converter import convert_source_to_document_nodes
from graph_rag.ingest.source_parser import parse_source_data
from graph_rag.models import Document, Page, Chunk, Entity

logger = logging.getLogger(__name__)
console = Console()


async def _process_file_async(
    file_path: Path,
    semaphore: asyncio.Semaphore,
) -> Tuple[str, Dict[str, Any], List[Exception]]:
    """Process a single file asynchronously.
    
    Args:
        file_path: Path to file to process
        semaphore: Semaphore to limit concurrency
        
    Returns:
        Tuple of (filename, result_dict, errors_list)
        result_dict contains: document, pages, chunks, entities, chunk_entities
    """
    async with semaphore:
        # Run CPU-bound operations in thread pool
        loop = asyncio.get_event_loop()
        try:
            # Parse document (I/O bound - file reading)
            parsed = await loop.run_in_executor(None, parse_source_data, file_path)
            
            # Convert to models (CPU bound)
            document, pages = await loop.run_in_executor(
                None, convert_source_to_document_nodes, parsed
            )
            
            # Process pages and chunks (CPU bound)
            all_chunks = []
            all_entities = []
            all_chunk_entities = []
            
            for page in pages:
                # Chunk page
                chunks = await loop.run_in_executor(
                    None, chunk_document_pages, document.id, [page]
                )
                all_chunks.extend(chunks)
                
                # Extract entities from chunks
                for chunk in chunks:
                    entities = await loop.run_in_executor(
                        None, extract_entities_from_text, chunk.text, chunk.id
                    )
                    all_entities.extend(entities)
                    
                    chunk_entity_ids = [e.id for e in entities]
                    all_chunk_entities.append({
                        "id": chunk.id,
                        "entity_ids": chunk_entity_ids
                    })
            
            return (
                file_path.name,
                {
                    "document": document,
                    "pages": pages,
                    "chunks": all_chunks,
                    "entities": all_entities,
                    "chunk_entities": all_chunk_entities,
                },
                []
            )
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)
            return (file_path.name, {}, [e])


def ingest_documents(document_paths: List[str]) -> None:
    """Ingest documents and build knowledge graph.

    Args:
        document_paths: List of paths to document directories or files
    """
    # Validate FalkorDB connection first
    logger.info(f"Connecting to FalkorDB at {config.falkordb_host}:{config.falkordb_port}...")
    try:
        graph_adapter = FalkorDBAdapter()
        # Test connection with simple query
        graph_adapter.execute_query("RETURN 1")
        logger.info(f"✅ Connected to FalkorDB successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to FalkorDB: {e}")
        logger.error(f"   Host: {config.falkordb_host}, Port: {config.falkordb_port}")
        logger.error("   Run: make falkordb-start")
        logger.error("   Or set FALKORDB_PORT environment variable if using custom port")
        raise ConnectionError(
            f"FalkorDB not available at {config.falkordb_host}:{config.falkordb_port}. "
            f"Run 'make falkordb-start' or set FALKORDB_PORT environment variable."
        ) from e

    graph_builder = GraphBuilder(graph_adapter)
    entity_resolver = FAISSEntityResolver()

    all_chunks = []
    all_entities = []
    all_chunk_entities = []
    successful_files = []
    failed_files = []

    # Collect all files first to show progress
    all_files = []
    for doc_path_str in document_paths:
        doc_path = Path(doc_path_str)
        if doc_path.is_file():
            all_files.append(doc_path)
        elif doc_path.is_dir():
            all_files.extend(doc_path.glob("*.md"))
        else:
            logger.warning(f"Path not found: {doc_path}")
            continue

    total_files = len(all_files)
    console.print(f"[cyan]Found {total_files} files to process[/cyan]")
    
    # Determine concurrency level
    if config.ingestion_workers > 0:
        max_workers = config.ingestion_workers
    else:
        import os
        max_workers = min(os.cpu_count() or 4, 8)
    console.print(f"[cyan]Using {max_workers} parallel workers[/cyan]\n")

    # Process files asynchronously with progress bar
    async def process_all_files():
        semaphore = asyncio.Semaphore(max_workers)
        results = []
        
        # Create wrapper to update progress
        async def process_with_progress(file_path: Path):
            filename, file_data, errors = await _process_file_async(file_path, semaphore)
            return filename, file_data, errors
        
        # Create tasks for all files
        tasks = [
            process_with_progress(file_path)
            for file_path in all_files
        ]
        
        # Process with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Processing files...", total=total_files)
            
            # Process files as they complete
            for coro in asyncio.as_completed(tasks):
                try:
                    filename, file_data, errors = await coro
                    if errors:
                        failed_files.append((filename, str(errors[0])))
                    elif file_data:
                        results.append(file_data)
                        successful_files.append(filename)
                    else:
                        failed_files.append((filename, "No data returned"))
                except Exception as e:
                    failed_files.append(("unknown", str(e)))
                finally:
                    progress.advance(task)
        
        return results
    
    # Run async processing
    file_results = asyncio.run(process_all_files())
    
    # Extract data from results and add to graph sequentially with progress
    console.print("\n[cyan]Adding data to graph...[/cyan]")
    
    # First, collect all data to calculate totals
    total_documents = len(file_results)
    total_pages = sum(len(fd["pages"]) for fd in file_results)
    total_chunks = sum(len(fd["chunks"]) for fd in file_results)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        # Task 1: Add documents, pages, and chunks
        graph_task = progress.add_task(
            "[cyan]Adding documents/pages/chunks to graph...",
            total=total_documents + total_pages + total_chunks
        )
        
        for file_data in file_results:
            document = file_data["document"]
            pages = file_data["pages"]
            chunks = file_data["chunks"]
            entities = file_data["entities"]
            chunk_entities = file_data["chunk_entities"]
            
            # Add document node
            graph_builder.add_document_node(document)
            progress.advance(graph_task)
            
            # Add pages to graph
            for page in pages:
                graph_builder.add_page_node(page)
                progress.advance(graph_task)
            
            # Add chunks to graph (this includes embedding generation)
            for chunk in chunks:
                graph_builder.add_chunk_node(chunk)
                progress.advance(graph_task)
            
            # Collect entities and chunk-entity relationships
            all_chunks.extend(chunks)
            all_entities.extend(entities)
            all_chunk_entities.extend(chunk_entities)

        # Resolve entities (show spinner for large sets)
        if len(all_entities) > 10000:
            entity_resolve_task = progress.add_task(
                f"[cyan]Resolving {len(all_entities):,} entities (batched, this may take a while)...",
                total=None  # Unknown total for batched processing
            )
        
        resolved_entities = entity_resolver.resolve_entities(all_entities)
        
        if len(all_entities) > 10000:
            progress.remove_task(entity_resolve_task)
        
        console.print(f"[green]✓[/green] Resolved to {len(resolved_entities):,} unique entities")

        # Filter entities (remove noisy types)
        filtered_entities = [
            e
            for e in resolved_entities
            if e.entity_type.value
            not in ["LEGAL_TERM", "DATE", "AMOUNT"]  # Filter noisy types
        ]
        console.print(f"[green]✓[/green] Filtered to {len(filtered_entities)} entities")

        # Add entity nodes with progress
        if filtered_entities:
            entity_task = progress.add_task(
                "[cyan]Adding entity nodes...",
                total=len(filtered_entities)
            )
            for entity in filtered_entities:
                graph_builder.add_entity_node(entity)
                progress.advance(entity_task)

        # Update chunk-entity relationships with resolved entity IDs
        entity_id_map = {e.id: e.id for e in filtered_entities}
        
        # Collect all mention edges for batch creation
        mention_edges = []
        for chunk_entity_data in all_chunk_entities:
            chunk_id = chunk_entity_data["id"]
            entity_ids = chunk_entity_data["entity_ids"]
            for entity_id in entity_ids:
                if entity_id in entity_id_map:
                    resolved_id = entity_id_map[entity_id]
                    mention_edges.append((chunk_id, resolved_id))
        
        total_mentions = len(mention_edges)
        if total_mentions > 0:
            mentions_task = progress.add_task(
                "[cyan]Adding mention edges (batched)...",
                total=total_mentions
            )
            # Process in batches with progress updates
            # Reduced batch size to avoid connection timeouts
            batch_size = 50  # Smaller batches for reliability
            for batch_start in range(0, total_mentions, batch_size):
                batch = mention_edges[batch_start : batch_start + batch_size]
                # Update progress before processing batch
                progress.update(mentions_task, completed=batch_start)
                # Process batch
                graph_builder.add_mentions_edges_batch(batch, batch_size=batch_size)
                # Update progress after processing batch
                progress.update(mentions_task, completed=min(batch_start + len(batch), total_mentions))

        # Extract relationships
        console.print(f"\n[cyan]Extracting relationships...[/cyan]")
        relationships = extract_relations(all_chunk_entities, filtered_entities)
        console.print(f"[green]✓[/green] Extracted {len(relationships)} relationships")

        # Add relationship edges with batch processing
        if relationships:
            rel_task = progress.add_task(
                "[cyan]Adding relationship edges (batched)...",
                total=len(relationships)
            )
            # Process in batches with progress updates
            # Reduced batch size to avoid connection timeouts
            batch_size = 50  # Smaller batches for reliability
            for batch_start in range(0, len(relationships), batch_size):
                batch = relationships[batch_start : batch_start + batch_size]
                # Update progress before processing batch
                progress.update(rel_task, completed=batch_start)
                # Process batch
                graph_builder.add_relationships_batch(batch, batch_size=batch_size)
                # Update progress after processing batch
                progress.update(rel_task, completed=min(batch_start + len(batch), len(relationships)))

    # Build FAISS index
    console.print(f"\n[cyan]Building FAISS index...[/cyan]")
    embeddings = []
    chunk_ids = []
    for chunk in all_chunks:
        if chunk.embedding:
            embeddings.append(chunk.embedding)
            chunk_ids.append(chunk.id)

    if embeddings:
        embeddings_array = np.array(embeddings, dtype=np.float32)
        import faiss

        dimension = embeddings_array.shape[1]
        index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embeddings_array)
        index.add(embeddings_array)
        faiss.write_index(index, str(config.embeddings_file))
        console.print(f"[green]✓[/green] FAISS index built with {len(embeddings)} embeddings")

    # Build BM25 index
    console.print(f"[cyan]Building BM25 index...[/cyan]")
    if not all_chunks:
        logger.warning("No chunks to index. Skipping BM25 index creation.")
        logger.warning("This usually means no documents were successfully ingested.")
        logger.warning("Check logs above for parsing errors (missing metadata tags, malformed JSON, etc.)")
        # Create empty BM25 index with at least one empty document to avoid division by zero
        import pickle
        bm25 = BM25Okapi([[""]])
        with open(config.bm25_file, "wb") as f:
            pickle.dump(bm25, f)
    else:
        chunk_texts = [chunk.text for chunk in all_chunks]
        tokenized_texts = [text.lower().split() for text in chunk_texts]
        bm25 = BM25Okapi(tokenized_texts)

        # Save BM25 index and chunk metadata
        import pickle

        with open(config.bm25_file, "wb") as f:
            pickle.dump(bm25, f)
        console.print(f"[green]✓[/green] BM25 index built with {len(all_chunks)} chunks")

    console.print(f"[cyan]Saving chunk metadata...[/cyan]")
    chunk_metadata = [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "page_id": chunk.page_id,
            "page_number": chunk.page_number,
            "text": chunk.text,
            "source_file": chunk.source_file,
        }
        for chunk in all_chunks
    ]
    with open(config.chunks_file, "w") as f:
        json.dump(chunk_metadata, f, indent=2)
    console.print(f"[green]✓[/green] Saved {len(chunk_metadata)} chunk metadata entries")

    # Summary with rich formatting
    summary_table = Table(title="Ingestion Summary", show_header=True, header_style="bold cyan")
    summary_table.add_column("Metric", style="cyan", width=30)
    summary_table.add_column("Value", style="green", justify="right")
    
    summary_table.add_row("Successfully processed", f"[bold green]{len(successful_files)}[/bold green] files")
    summary_table.add_row("Failed", f"[bold red]{len(failed_files)}[/bold red] files" if failed_files else "[bold green]0[/bold green] files")
    summary_table.add_row("Total chunks", f"[bold]{len(all_chunks)}[/bold]")
    summary_table.add_row("Total entities", f"[bold]{len(filtered_entities)}[/bold]")
    summary_table.add_row("Total relationships", f"[bold]{len(relationships)}[/bold]")
    
    console.print("\n")
    console.print(summary_table)
    
    if failed_files:
        failed_panel_content = "\n".join([
            f"[red]•[/red] [bold]{filename}[/bold]: {error[:80]}..."
            for filename, error in failed_files[:10]
        ])
        if len(failed_files) > 10:
            failed_panel_content += f"\n[dim]... and {len(failed_files) - 10} more failures[/dim]"
        
        console.print(Panel(
            failed_panel_content,
            title="[bold red]Failed Files[/bold red]",
            border_style="red"
        ))
    
    logger.info("Ingestion complete!")

