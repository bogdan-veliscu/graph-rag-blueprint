# GraphRAG Legal - Demo Guide

**Complete workflow for preparing and running the demo.**

## Quick Start (5 Minutes)

```bash
# 1. Ensure you have the graph built
make status

# 2. Run quick demo with 7 questions
make demo-quick

# 3. View results
cat output/eval_7_report.txt
```

## Full Demo Workflow (30 Minutes)

```bash
# 1. Setup Llama 3.3 70B (one-time, ~40GB download)
make setup-llm-demo

# 2. Update model in src/config.py
# Change: model_name = "llama3.3:70b-instruct-q4_K_M"

# 3. Run full demo
make demo

# 4. Review results
cat output/eval_7_report.txt   # Quick validation (7 questions)
cat output/eval_70_report.txt  # Comprehensive test (70 questions)
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
# Check current status
make status

# Install dependencies if needed
make install-dev

# Verify Ollama is running
ollama list
```

### 2. Build Knowledge Graph (if not done)

```bash
# Build from all documents in data/source_data/
make build-full

# This will process ~70 documents and create:
# - output/graph.pkl (knowledge graph)
# - output/embeddings.npy (semantic embeddings)
# - output/bm25.pkl (BM25 index)
```

### 3. Generate Test Questions

```bash
# Generate 7-question quick test
make generate-questions-7

# Generate 70-question comprehensive test
make generate-questions-70

# Questions are saved to:
# - data/questions_7.json
# - data/questions_70.json
```

### 4. Run Evaluation

```bash
# Quick evaluation (7 questions, ~2 minutes)
make evaluate-7

# Comprehensive evaluation (70 questions, ~20 minutes)
make evaluate-70

# Results saved to:
# - output/eval_7.json (detailed scores)
# - output/eval_7_report.txt (human-readable summary)
# - output/eval_70.json
# - output/eval_70_report.txt
```

### 5. Benchmark Ingestion (Optional)

```bash
# Benchmark document processing performance
make benchmark-ingestion

# Results saved to:
# - output/benchmarks/ingestion_benchmark.json
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
   make status
   ```
   - Highlight: X documents processed, graph built, test sets ready

2. **Run Quick Evaluation**:
   ```bash
   make evaluate-7
   ```
   - Show: Real-time evaluation on 7 questions (~2 minutes)
   - Highlight: Detailed scores, citations, answer quality

3. **Review Results**:
   ```bash
   cat output/eval_7_report.txt
   ```
   - Walk through: Mean score, pass rate, metric breakdown
   - Emphasize: Faithfulness (no hallucinations), citation accuracy

4. **Show Example Question/Answer**:
   ```bash
   cat output/eval_7.json | jq '.results[0]'
   ```
   - Demonstrate: Question → Context retrieval → Answer with citations
   - Highlight: Vancouver-style legal citations

5. **Discuss Architecture**:
   - Explain: Hybrid retrieval (BM25 + embeddings)
   - Show: Graph enhancement, cross-encoder reranking
   - Emphasize: Privacy (all local, no cloud calls)

6. **Performance Comparison**:
   - Current: Llama 3.1 8B baseline
   - Demo: Llama 3.3 70B upgrade
   - Future: Optimization roadmap (fusion tuning)

## Troubleshooting

### Issue: Questions generation fails

```bash
# Check if graph exists
ls -lh output/graph.pkl

# If not, rebuild:
make build-full
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

### Issue: Evaluation taking too long

```bash
# Use 7-question test instead of 70
make evaluate-7

# Or sample from existing questions
head -n 10 data/questions_70.json > data/questions_10.json
```

## Next Steps After Demo

1. **Optimize Retrieval Parameters**:
   ```bash
   make quick-optimize  # 50-question validation
   make full-optimize   # 400-question full optimization
   ```

2. **Fine-Tune Fusion Weight**:
   - Test alpha values: 0.3, 0.5, 0.7
   - Optimize for semantic vs keyword balance

3. **Validate on Full 400-Question Set**:
   ```bash
   make benchmark
   ```

4. **Consider Alternative LLMs**:
   - GPT-4o-mini (API): Best quality, requires API key
   - Claude 3.5 Haiku (API): Fast, accurate, good citations
   - Llama 3.3 70B (local): Good balance of quality and privacy

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
- **Configuration**: `src/config.py` - Tunable parameters
- **Manual Execution**: `docs/MANUAL_EXECUTION_GUIDE.md` - Tmux workflows
- **Baseline Findings**: `docs/BASELINE_FINDINGS.md` - Analysis and insights
- **Completion Summary**: `docs/COMPLETION_SUMMARY.md` - Project status
