# Manual Execution Guide - GraphRAG System

This guide shows you how to manually run long-running tasks and manage the system.

## Available Scripts

**Core Scripts**:
- ✅ `scripts/benchmark_performance.py` - Performance benchmark for 400 questions
- ✅ `scripts/generate_test_questions.py` - Generate test questions for benchmarking
- ✅ `scripts/evaluate.py` - Evaluate answers using LLM-as-judge
- ✅ `scripts/run_demo.py` - Run complete demo (ingest + query)
- ✅ `scripts/validate_graph.py` - Validate graph structure

## Current System State

**Ingestion**: Optimized with batch processing
- Entity resolution: Batched FAISS (10K entities per batch)
- Edge creation: Batched Cypher queries (1000 edges per batch)
- File processing: Parallel async (up to 8 workers)

**Query Processing**: Parallel with progress tracking
- Default: 128 concurrent queries
- Batch size: 10 questions per batch
- Target: 400 questions in ≤60 minutes

## Step 1: Create Tmux Session

```bash
# Create a new tmux session named "graphrag"
tmux new -s graphrag

# Or attach to existing session
tmux attach -t graphrag
```

### Tmux Quick Reference
- `Ctrl+b d` - Detach from session (keeps running)
- `Ctrl+b c` - Create new window
- `Ctrl+b n` - Next window
- `Ctrl+b p` - Previous window
- `Ctrl+b ,` - Rename window
- `tmux ls` - List sessions
- `tmux kill-session -t graphrag` - Kill session

## Step 2: Run Performance Benchmark

Run performance benchmark to validate 400 questions can be processed in ≤60 minutes:

```bash
cd /Users/bogdan/work/freelance/graph-rag-blueprint

# Generate test questions (if needed)
python scripts/generate_test_questions.py --count 400 --output data/test_questions_400.json

# Run benchmark
python scripts/benchmark_performance.py --questions-file data/test_questions_400.json

# You can detach with Ctrl+b d and it will keep running
```

**Expected Output**:
```
======================================================================
Benchmark Results
======================================================================
Questions Processed: 400
Elapsed Time: 28.5 minutes
Target Time: 60 minutes
Time Margin: 31.5 minutes
Throughput: 14.04 questions/minute
Status: PASS
======================================================================
```

**Success Criteria**:
- **≤60 minutes** → ✅ Meets objective requirement
- **>60 minutes** → ⚠️ Need to optimize (reduce max_concurrent, check LLM response times)

## Step 3: Run Full Demo

Run complete demo workflow (ingest + query processing):

```bash
cd /Users/bogdan/work/freelance/graph-rag-blueprint

# Run demo (ingests if needed, then processes questions)
python scripts/run_demo.py

# Or skip ingestion if graph already exists
python scripts/run_demo.py --skip-ingest

# Detach with Ctrl+b d - this will take 30-60 minutes
```

## Step 4: Monitor Progress

### From Outside Tmux
```bash
# List tmux sessions
tmux ls

# Peek at session without attaching
tmux capture-pane -t graphrag -p | tail -20

# Check output files
ls -lh answers.json
ls -lh benchmark_results.json
ls -lh evaluation_results.json
```

### From Inside Tmux
```bash
# Attach to running session
tmux attach -t graphrag

# View progress in real-time
# Progress bars are shown automatically during execution
```

## Step 5: Analyze Results

After benchmark completes:

```bash
# View benchmark results
cat benchmark_results.json | python3 -m json.tool

# View answers
cat answers.json | python3 -m json.tool

# Evaluate answers (if evaluation was run)
cat evaluation_results.json | python3 -m json.tool
```

## Alternative: Run in Background with nohup

If you don't want to use tmux:

```bash
# Run benchmark in background
nohup python scripts/benchmark_performance.py \
    --count 400 \
    > benchmark.log 2>&1 &

# Get process ID
echo $!

# Monitor log
tail -f benchmark.log

# Kill if needed
kill <process-id>
```

## Recommended Workflow

1. **Start tmux session**: `tmux new -s graphrag`
2. **Run benchmark**: ~30-60 minutes, validates performance
3. **Detach**: `Ctrl+b d` (keeps running)
4. **Check results**: After completion, check `benchmark_results.json`
5. **If successful**: Run full demo or process questions
6. **Final analysis**: Review answers and evaluation results

## Troubleshooting

### Tmux session lost
```bash
# List all sessions
tmux ls

# Attach to specific session
tmux attach -t graphrag
```

### Process stuck
```bash
# From within tmux
Ctrl+C  # Stop current process

# Or kill the session
tmux kill-session -t graphrag
```

### Check if still running
```bash
# Check for Python processes
ps aux | grep "benchmark_performance.py"
ps aux | grep "run_demo.py"

# Kill if needed
pkill -f "benchmark_performance.py"
pkill -f "run_demo.py"
```

## Next Steps After Benchmarking

1. **Review Results**: Check `benchmark_results.json`
2. **Verify Performance**: Ensure ≤60 minutes for 400 questions
3. **Optimize if Needed**: Adjust `max_concurrent` or `query_batch_size` in config
4. **Run Evaluation**: Evaluate answers for quality metrics
5. **Documentation**: Update docs with performance results

## Expected Timeline

| Task | Duration | Output |
|------|----------|--------|
| Generate Questions | 1 min | test_questions_400.json |
| Performance Benchmark | 30-60 min | benchmark_results.json |
| Full Demo | 30-60 min | answers.json |
| Evaluation | 10-20 min | evaluation_results.json |
| **Total** | **1-2 hours** | **Complete results** |

## Success Criteria

- **Performance**: ≤60 minutes for 400 questions
- **Accuracy**: >95% target across evaluation dimensions
- **Throughput**: ≥6.67 questions/minute
