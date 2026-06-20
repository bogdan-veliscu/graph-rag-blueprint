# GraphRAG Legal System

A high-accuracy GraphRAG (Graph-based Retrieval-Augmented Generation) system for legal document question-answering.

## Status

This is a public blueprint/proof repo for experimenting with legal-document
GraphRAG: structured legal source parsing, knowledge graph construction,
hybrid retrieval, explainable citations, and LLM-as-judge evaluation. It is
intended for local experimentation and adaptation, not as a hosted SaaS
product.

## Features

- **Rich Metadata Parsing**: Extracts document titles, dates, issue numbers, authors, publishers from XML-tagged markdown files
- **Knowledge Graph Construction**: Builds a FalkorDB graph with documents, pages, chunks, and entities
- **Hybrid Retrieval**: Combines dense (FAISS), sparse (BM25), and graph traversal for optimal accuracy
- **Vancouver-Style Citations**: Generates answers with properly formatted citations using rich metadata
- **Multilingual Support**: Parses `<orig>` tags for Arabic/English content

## Sample Data Boundary

The demo expects legal source documents under `data/source_data/` and smaller
fast-path examples under `data/fast_data/`. Treat these as sample/demo corpus
inputs for local experimentation. For real usage, replace them with documents
you are authorized to process and review the extracted metadata before relying
on answers or citations.

## Quick Start

### Prerequisites

- Python 3.12+
- Docker (for FalkorDB)
- Ollama or Anthropic API key (for LLM)

### Installation

**Option 1: Using uv (Recommended)**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
make install-uv
# Or: uv sync

# Download spaCy model
python -m spacy download en_core_web_sm

# Start FalkorDB
make falkordb-start

# Check FalkorDB port (may be 6379 or 6380)
make falkordb-status

# If FalkorDB is on port 6380, set environment variable:
export FALKORDB_PORT=6380

# (Optional) Start Ollama for local LLM
ollama pull llama3.1:8b
export LLM_PROVIDER=ollama
```

**Option 2: Using pip**
```bash
# Install dependencies
make install
# Or: pip install -e .

# Download spaCy model
python -m spacy download en_core_web_sm

# Start FalkorDB
make falkordb-start

# (Optional) Start Ollama for local LLM
ollama pull llama3.1:8b
export LLM_PROVIDER=ollama
```

### Usage

#### Using Makefile (Recommended)

```bash
# Install dependencies
make install

# Ingest documents
make ingest

# Query with a single question
make query Q="What is Decree-Law No. 61 of 2025 about?"

# Query from JSON file
make query-file FILE=data/sample_questions.json

# Run complete demo (ingest + process ~400 questions)
make demo

# Run tests
make test

# Run fast tests that do not require FalkorDB, Docker, or LLM credentials
make test-fast

# Evaluate answers (LLM-as-judge)
make evaluate QUESTIONS=data/questions.json ANSWERS=answers.json

# Manage FalkorDB
make falkordb-start    # Start FalkorDB container
make falkordb-stop     # Stop FalkorDB container
make falkordb-status    # Check FalkorDB status
make falkordb-restart   # Restart FalkorDB container
make falkordb-logs      # Show FalkorDB logs
```

#### Using Python Directly

```bash
# Ingest documents
python main.py ingest data/source_data/

# Query with a single question
python main.py query "What is Decree-Law No. 61 of 2025 about?"

# Query from JSON file
python main.py query --file data/sample_questions.json --output answers.json

# Run demo script
python scripts/run_demo.py
```

## Architecture

```
Ingestion: Parse → Chunk → Extract → Resolve → Relate → Build Graph
Query: Parse → Link → Retrieve → Traverse → Rerank → Generate
```

### Key Components

- **Source Parser**: Parses markdown files with XML tags, extracts metadata
- **Chunker**: Splits documents into semantic chunks (512 tokens, 128 overlap)
- **Entity Extractor**: Hybrid regex + spaCy NER extraction
- **FAISS Resolver**: Deduplicates entities using cosine similarity
- **Graph Builder**: Constructs FalkorDB knowledge graph
- **Retriever**: Hybrid dense + sparse + RRF retrieval
- **Graph Traverser**: Document-aware BFS + Personalized PageRank
- **Answer Generator**: LLM-based answer generation with citations

## Citation Format

The system generates **Vancouver-style citations** using rich metadata extracted from documents:

### Example Citation

**Before** (filename-based):
```
[1] 6-4-2025_en.md. p.1.
```

**After** (rich metadata):
```
[1] Al-Kuwait Al-Youm Official Gazette - Issue 1733, Volume 71 (2025-04-06). p.1. Ministry of Information.
```

### Citation Components

Citations include the following metadata fields:
- **Document title**: Full title from `document_metadata.document_title`
- **Issue number**: Gazette issue number (e.g., "Issue 1733")
- **Volume number**: Publication volume (e.g., "Volume 71")
- **Publication date**: ISO 8601 date format (e.g., "2025-04-06")
- **Page number**: Page reference (e.g., "p.1")
- **Publisher**: Publisher name (with `<orig>` tags stripped for readability)

### How Citations Work

1. **Metadata Extraction**: During ingestion, document and page metadata are parsed from XML tags (`<document_metadata>`, `<page_metadata>`)
2. **Graph Storage**: Metadata is stored in FalkorDB graph nodes (Document and Page nodes)
3. **Citation Generation**: When generating answers, `AnswerGenerator._format_reference_list()` retrieves Document and Page nodes from the graph
4. **Formatting**: Citations are formatted using the retrieved metadata, with graceful fallback to filename if metadata is unavailable

### Multilingual Support

The system handles multilingual content via `<orig>` tags:
- Publisher names like `"Kuwait Today <orig>الكويت اليوم</orig>"` are parsed
- Citations display only the primary language text (e.g., "Kuwait Today")
- Original language text is preserved in graph metadata for future use

## Configuration

See `src/graph_rag/config.py` for all configuration options. Key settings:

- `chunk_size`: 512 tokens
- `chunk_overlap`: 128 tokens
- `dense_top_k`: 50 chunks
- `sparse_top_k`: 50 chunks
- `rerank_top_k`: 10 chunks for generation

## Demo Workflow

For the live demo with ~400 questions:

```bash
# 1. Start FalkorDB
docker run -d -p 6379:6379 falkordb/falkordb:latest

# 2. Run complete demo (ingests + processes questions)
make demo

# Or use the demo script directly
python scripts/run_demo.py --questions data/sample_questions.json --answers answers.json
```

The demo script will:
- Ingest documents from `data/source_data/`
- Load questions from JSON file
- Process all questions in parallel with progress tracking
- Save answers to `answers.json`
- Report timing metrics (questions/minute, total time)

## Parallel Processing

The system processes queries in parallel by default. Configure concurrency:

```bash
export MAX_CONCURRENT=64  # Max concurrent LLM requests
export QUERY_BATCH_SIZE=10  # Batch size for processing
```

## Testing

```bash
# Run all tests
make test
# or
pytest

# Run fast tests
make test-fast

# Run specific test suite
pytest tests/test_ingest/
pytest tests/test_query/

# Run with coverage
pytest --cov=src --cov-report=html
```

## Project Structure

```
src/graph_rag/
├── ingest/          # Ingestion pipeline
├── query/           # Query pipeline
├── graph/           # Graph database adapter
├── utils/           # Utilities (LLM, embeddings)
├── models.py        # Data models
└── config.py        # Configuration

tests/
├── test_ingest/     # Ingestion tests
└── test_query/      # Query tests

scripts/
└── validate_graph.py  # Graph validation script
```

## License

MIT
