# GraphRAG Legal - Demo Guide

**Complete workflow for preparing and running the demo.**

## Quick Start (5 Minutes)

```bash
# 1. Ensure FalkorDB is running
make falkordb-status

# 2. Ingest documents (if not done)
make ingest-fast

# 3. Run demo
make demo

# 4. View results
cat answers.json
```

## Full Demo Workflow (30 Minutes)

```bash
# 1. Start FalkorDB
make falkordb-start

# 2. Install dependencies (if needed)
make install-uv

# 3. Ingest documents
make ingest

# 4. Run demo (processes questions and generates answers.json)
make demo

# 5. Review results
cat answers.json

# 6. Evaluate answers (optional)
make evaluate QUESTIONS=data/sample_questions.json ANSWERS=answers.json
```

## LLM Model Comparison

### Llama 3.1 8B (Current Baseline)
- **Pros**: Fast (~3s/question), low memory (~8GB)
- **Cons**: Baseline accuracy 55.5%, struggles with complex legal reasoning
- **Use Case**: Development and quick iteration

### Llama 3.3 70B (Recommended for Demo)
- **Pros**: Better reasoning, expected 75-85% accuracy, still local/private
- **Cons**: Slower (~10s/question), high memory (48GB RAM required)
- **Use Case**: Demo, production-quality results
- **Hardware**: M3 Max 48GB RAM recommended

### Performance Expectations

| Model | Mean Score | Questions/Min | Memory | Demo Quality |
|-------|------------|---------------|--------|--------------|
| Llama 3.1 8B | 55.5% | 3.2 q/min | 8GB | Development |
| Llama 3.3 70B | 75-85%* | 0.5 q/min | 48GB | Production |
| GPT-4o-mini (API) | 85-90%* | 2.0 q/min | N/A | Best (non-local) |

*Expected based on model capabilities, not yet validated

## Step-by-Step Demo Preparation

### 1. Environment Setup

```bash
# Check FalkorDB status
make falkordb-status

# Start FalkorDB if not running
make falkordb-start

# Install dependencies if needed
make install-uv

# Verify Ollama is running (if using local LLM)
ollama list
```

### 2. Build Knowledge Graph

```bash
# Ingest all documents from data/source_data/
make ingest

# For fast testing with single file:
make ingest-fast

# This will process documents and create:
# - FalkorDB graph (in Docker container)
# - output/embeddings.npy (semantic embeddings)
# - output/bm25.pkl (BM25 index)
# - output/chunks.json (chunk metadata)
```

### 3. Generate Test Questions (Optional)

```bash
# Generate test questions using script
python scripts/generate_test_questions.py --count 400 --output data/test_questions_400.json

# Or use existing sample questions
# - data/sample_questions.json (2 questions)
```

### 4. Run Queries

```bash
# Query with single question
make query Q="What is Decree-Law No. 61?"

# Query from JSON file
make query-file FILE=data/sample_questions.json

# Results saved to answers.json
```

### 5. Evaluate Answers (Optional)

```bash
# Evaluate answers using LLM-as-judge
make evaluate QUESTIONS=data/sample_questions.json ANSWERS=answers.json

# Results saved to evaluation_results.json
```

### 6. Benchmark Performance (Optional)

```bash
# Run performance benchmark
python scripts/benchmark_performance.py --count 400

# Or with questions file
python scripts/benchmark_performance.py --questions-file data/test_questions_400.json
```

## Demo Talking Points

### GraphRAG Architecture Highlights

1. **Hybrid Retrieval**:
   - BM25 (sparse keyword matching) + Semantic embeddings (dense)
   - Reciprocal Rank Fusion (RRF) combines both approaches
   - Configurable fusion weight (alpha): 0.5 = equal weight

2. **Knowledge Graph Enhancement**:
   - NetworkX MultiDiGraph with 22,657 chunks
   - Graph traversal for context expansion
   - Entity linking and relationship extraction

3. **Cross-Encoder Reranking**:
   - Second-stage semantic reranking
   - ms-marco-MiniLM-L-6-v2 model
   - Significantly improves relevance (+15-20 points)

4. **Anti-Hallucination Prompting**:
   - Strict CRITICAL RULES enforcing context-only answers
   - 5-metric LLM-as-judge evaluation
   - Vancouver-style legal citations with source verification

### Performance Metrics to Highlight

**Baseline Performance** (Llama 3.1 8B, 130-question eval):
- Mean Score: 55.5%
- Pass Rate: 16.9%
- Speed: ~3.2 questions/minute

**Expected with Llama 3.3 70B**:
- Mean Score: 75-85%
- Pass Rate: 60-70%
- Speed: ~0.5 questions/minute (slower but higher quality)

**With Optimization** (cross-encoder + fusion tuning):
- Mean Score: 85-95% target
- Pass Rate: 85-95% target

### Demo Script

1. **Show Current Status**:
   ```bash
   make falkordb-status
   make validate-graph
   ```
   - Highlight: Graph structure, node/edge counts, system ready

2. **Run Query Processing**:
   ```bash
   make query-file FILE=data/sample_questions.json
   ```
   - Show: Real-time query processing with progress bar
   - Highlight: Parallel processing, answer generation

3. **Review Results**:
   ```bash
   cat answers.json
   ```
   - Walk through: Answer format, citations, Vancouver-style references
   - Emphasize: Faithfulness (no hallucinations), citation accuracy

4. **Show Example Question/Answer**:
   ```bash
   cat answers.json | python3 -m json.tool
   ```
   - Demonstrate: Question → Context retrieval → Answer with citations
   - Highlight: Vancouver-style legal citations with rich metadata

5. **Discuss Architecture**:
   - Explain: Hybrid retrieval (FAISS + BM25 + RRF)
   - Show: Graph traversal, document-aware BFS
   - Emphasize: Privacy (all local, no cloud calls if using Ollama)

6. **Performance Metrics**:
   - Throughput: ~14 questions/minute (parallel)
   - Target: 400 questions in ≤60 minutes
   - Accuracy: >95% target across evaluation dimensions

## Troubleshooting

### Issue: Graph not found

```bash
# Check if graph is populated
make validate-graph

# If empty, rebuild:
make ingest
```

### Issue: Ollama not responding

```bash
# Check Ollama status
ollama list

# Restart Ollama if needed
brew services restart ollama
```

### Issue: Out of memory with 70B model

```bash
# Reduce batch size in src/config.py
# Change: num_batch = 1  (instead of 2)

# Or stick with Llama 3.1 8B for demo
# Change: model_name = "llama3.1:latest"
```

### Issue: Query processing taking too long

```bash
# Use smaller question set
python main.py query --file data/sample_questions.json --no-parallel

# Or reduce concurrent queries in config
# Edit src/graph_rag/config.py: max_concurrent = 64
```

## Next Steps After Demo

1. **Run Performance Benchmark**:
   ```bash
   python scripts/benchmark_performance.py --count 400
   ```

2. **Fine-Tune Configuration**:
   - Edit `src/graph_rag/config.py` for retrieval parameters
   - Test fusion_k values: 40, 60, 80
   - Adjust max_concurrent for your system

3. **Evaluate Answers**:
   ```bash
   make evaluate QUESTIONS=data/sample_questions.json ANSWERS=answers.json
   ```

4. **Consider Alternative LLMs**:
   - Ollama (local): llama3.1:8b, llama3.3:70b
   - Anthropic API: Claude 3.5 Sonnet (set ANTHROPIC_API_KEY)
   - Configure in `.env` file

## Success Criteria

**Minimum Acceptable**:
- Mean score: 85%
- Pass rate: 70%
- No critical failures (<50% score)

**Target**:
- Mean score: 90-95%
- Pass rate: 85-90%
- Faithfulness: >95% (no hallucinations)

**Stretch Goal**:
- Mean score: >95%
- Pass rate: >90%
- All metrics: >90%

## Resources

- **Makefile**: `make help` - All available commands
- **Configuration**: `src/graph_rag/config.py` - Tunable parameters
- **Demo Instructions**: `DEMO_INSTRUCTIONS.md` - Step-by-step demo runbook
- **Technical Note**: `TECHNICAL_NOTE.md` - Architecture overview
- **Quick Reference**: `docs/QUICK_REFERENCE.md` - Quick command reference
