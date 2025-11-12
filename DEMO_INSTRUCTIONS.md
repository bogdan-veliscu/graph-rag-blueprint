# Demo Instructions - GraphRAG Legal System

## Overview

This document provides step-by-step instructions for running the live demo of the GraphRAG legal document question-answering system.

## Prerequisites

### Required Software

1. **Python 3.12+**
   ```bash
   python3 --version  # Should be 3.12 or higher
   ```

2. **Docker** (for FalkorDB)
   ```bash
   docker --version
   ```

3. **Ollama** (for local LLM) OR **Anthropic API Key** (for cloud LLM)
   ```bash
   # For Ollama (local):
   ollama --version
   
   # For Anthropic (cloud):
   # Set ANTHROPIC_API_KEY environment variable
   ```

### System Requirements

- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 20GB free space
- **CPU**: Multi-core recommended for parallel processing

## Setup Instructions

### Step 1: Install Dependencies

**Option A: Using uv (Recommended)**
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
make install-uv
# Or: uv sync
```

**Option B: Using pip**
```bash
make install
# Or: pip install -e .
```

### Step 2: Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### Step 3: Start FalkorDB

```bash
# Start FalkorDB container
make falkordb-start

# Verify FalkorDB is running
make falkordb-status

# If FalkorDB is on port 6380 (not default 6379), set environment variable:
export FALKORDB_PORT=6380
```

### Step 4: Configure LLM Provider

**Option A: Ollama (Local)**
```bash
# Start Ollama (if not running)
ollama serve

# Pull required model
ollama pull llama3.1:8b

# Set environment variable
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=llama3.1:8b
export OLLAMA_BASE_URL=http://localhost:11434
```

**Option B: Anthropic (Cloud)**
```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=your-api-key-here
export ANTHROPIC_BASE_URL=https://api.anthropic.com/v1/messages
```

### Step 5: Verify Setup

```bash
# Check that all components are accessible
python -c "from src.graph_rag.graph.falkordb_adapter import FalkorDBAdapter; FalkorDBAdapter()"
python -c "from src.graph_rag.query.retriever import Retriever; Retriever()"
```

## Demo Workflow

### Phase 1: Ingestion (One-time, before demo)

**Ingest documents from source data:**

```bash
# Ingest all documents
make ingest

# Or ingest specific directory/file
python main.py ingest data/source_data/

# For fast testing with single file
make ingest-fast
```

**Expected Output:**
- Graph nodes created (Documents, Pages, Chunks, Entities)
- FAISS index built (`output/embeddings.npy`)
- BM25 index built (`output/bm25.pkl`)
- Chunk metadata saved (`output/chunks.json`)

**Verification:**
```bash
# Validate graph structure
make validate-graph
# Or: python scripts/validate_graph.py
```

### Phase 2: Query Processing (During Demo)

**Receive questions file:**

The demo will receive a JSON file with ~400 questions in this format:
```json
[
  {"question": "What is the maximum duration of a commercial lease?"},
  {"question": "What is the filing fee for an appeal in civil court?"},
  ...
]
```

**Process questions:**

```bash
# Process questions and generate answers.json
python main.py query --file questions.json --output answers.json

# Or using the query() function directly:
python -c "
from main import query
import json

with open('questions.json') as f:
    data = json.load(f)
    questions = [q['question'] for q in data]

answers = query(questions, output_path='answers.json', parallel=True)
"
```

**Expected Output:**

1. **Console Output:**
   - Progress bar showing query processing
   - Summary table with metrics
   - Confirmation that `answers.json` was created

2. **answers.json File:**
   ```json
   [
     {
       "answer": "The maximum duration of a commercial lease is 15 years [1].\n\nReferences\n1. Al-Kuwait Al-Youm Official Gazette - Issue 1733, Volume 71 (2025-04-06). p.42. Ministry of Information."
     },
     ...
   ]
   ```

**Performance Target:**
- Process ~400 questions in ≤60 minutes
- Progress indicator shows real-time status

### Phase 3: Verification

**Check output format:**

```bash
# Verify answers.json exists and has correct format
python -c "
import json
with open('answers.json') as f:
    data = json.load(f)
    print(f'Total answers: {len(data)}')
    print(f'Format check: {all(\"answer\" in item for item in data)}')
    print(f'First answer preview: {data[0][\"answer\"][:100]}...')
"
```

**Expected Results:**
- `answers.json` contains array of objects
- Each object has `"answer"` key
- Answers include Vancouver-style citations
- All questions processed successfully

## Troubleshooting

### Issue: FalkorDB Connection Error

**Symptoms:**
```
Connection refused: localhost:6379
```

**Solutions:**
1. Check if FalkorDB is running: `make falkordb-status`
2. Verify port: `docker ps | grep falkordb`
3. If running on port 6380: `export FALKORDB_PORT=6380`
4. Restart FalkorDB: `make falkordb-restart`

### Issue: No Retrieval Indices

**Symptoms:**
```
No retrieval indices available. Run ingestion first.
```

**Solutions:**
1. Run ingestion: `make ingest`
2. Verify indices exist:
   ```bash
   ls -lh output/embeddings.npy output/bm25.pkl output/chunks.json
   ```
3. If missing, re-run ingestion

### Issue: LLM Timeout

**Symptoms:**
```
TimeoutError: Ollama request timed out after 3 attempts
```

**Solutions:**
1. Check LLM is running: `ollama list` or verify API key
2. Increase timeout in config (if needed)
3. Check system resources (CPU/RAM)
4. Reduce `max_concurrent` in config for slower systems

### Issue: Empty Graph

**Symptoms:**
```
Graph is empty. Run ingestion first.
```

**Solutions:**
1. Verify ingestion completed successfully
2. Check graph: `make validate-graph`
3. Re-run ingestion if needed

### Issue: Performance Issues

**Symptoms:**
- Processing takes >60 minutes for 400 questions

**Solutions:**
1. Check `max_concurrent` setting (default: 128)
2. Reduce `query_batch_size` if memory constrained
3. Verify LLM response times
4. Check system resources (CPU/RAM)

## Demo Script

**Quick demo script:**

```bash
#!/bin/bash
# demo.sh - Complete demo workflow

set -e

echo "=== GraphRAG Demo ==="
echo ""

# Step 1: Verify prerequisites
echo "Step 1: Verifying prerequisites..."
python3 --version
docker ps > /dev/null
echo "✓ Prerequisites OK"
echo ""

# Step 2: Start services
echo "Step 2: Starting services..."
make falkordb-start
sleep 5
echo "✓ FalkorDB started"
echo ""

# Step 3: Ingest documents (if not already done)
if [ ! -f "output/chunks.json" ]; then
    echo "Step 3: Ingesting documents..."
    make ingest-fast  # Use fast ingestion for demo
    echo "✓ Ingestion complete"
else
    echo "Step 3: Using existing graph (skipping ingestion)"
fi
echo ""

# Step 4: Process questions
echo "Step 4: Processing questions..."
if [ -f "questions.json" ]; then
    python main.py query --file questions.json --output answers.json
    echo "✓ Query processing complete"
else
    echo "⚠ questions.json not found. Using sample questions..."
    python main.py query --file data/sample_questions.json --output answers.json
fi
echo ""

# Step 5: Verify results
echo "Step 5: Verifying results..."
if [ -f "answers.json" ]; then
    python -c "
import json
with open('answers.json') as f:
    data = json.load(f)
    print(f'✓ Generated {len(data)} answers')
    print(f'✓ Format valid: {all(\"answer\" in item for item in data)}')
    "
else
    echo "✗ answers.json not found"
    exit 1
fi
echo ""

echo "=== Demo Complete ==="
```

## Performance Benchmarking

**Run performance benchmark:**

```bash
# Generate 400 test questions
python scripts/generate_test_questions.py --count 400 --output data/test_questions_400.json

# Run benchmark
python scripts/benchmark_performance.py --questions-file data/test_questions_400.json

# Or use custom count
python scripts/benchmark_performance.py --count 400
```

**Expected Results:**
- Processes 400 questions in ≤60 minutes
- Throughput: ≥6.67 questions/minute
- All questions answered successfully

## Architecture Explanation Points

During the demo, be prepared to explain:

1. **Knowledge Graph Construction:**
   - Documents → Pages → Chunks hierarchy
   - Entity extraction and resolution
   - Relationship extraction (co-occurrence)

2. **Graph Traversal:**
   - Document-aware BFS (prevents cross-document contamination)
   - Personalized PageRank for entity relationships
   - Multi-hop reasoning (max_hops=2)

3. **Hybrid Retrieval:**
   - Dense retrieval (FAISS semantic embeddings)
   - Sparse retrieval (BM25 keyword matching)
   - Reciprocal Rank Fusion (RRF) combining both

4. **Answer Generation:**
   - LLM with anti-hallucination prompts
   - Vancouver-style citation formatting
   - Rich metadata extraction (titles, dates, issue numbers)

## Quick Reference

**Common Commands:**
```bash
# Ingestion
make ingest                    # Ingest all documents
make ingest-fast              # Fast test with single file

# Querying
make query Q="Your question"  # Single question
make query-file FILE=questions.json  # From file

# Validation
make validate-graph           # Check graph structure
make test                     # Run tests

# Services
make falkordb-start           # Start FalkorDB
make falkordb-stop            # Stop FalkorDB
make falkordb-status          # Check status
```

## Support

For issues during demo:
1. Check logs for error messages
2. Verify all services are running
3. Check system resources
4. Review troubleshooting section above

