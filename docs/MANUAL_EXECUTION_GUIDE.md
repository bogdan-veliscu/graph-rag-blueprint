# Manual Execution Guide - GraphRAG Optimization

This guide shows you how to manually run the long-running optimization tasks in a separate tmux session.

## Current State

**Baseline Evaluation Complete**:
- 130-question sample analyzed
- Mean score: 55.5%
- Pass rate: 16.9%
- Full findings: `docs/BASELINE_FINDINGS.md`

**Scripts Ready**:
- ✅ `scripts/quick_optimize.py` - Quick 50-question validation (~15min)
- ✅ `scripts/optimize_retrieval.py` - Full 400-question optimization (~6-8 hours)
- ✅ `scripts/analyze_baseline.py` - Results analysis

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

## Step 2: Option A - Quick Validation (Recommended First)

Run a 50-question test to validate cross-encoder gains before committing to full run:

```bash
cd /Users/bogdan/work/freelance/graph-rag-legal

# Run quick validation (2 experiments, 50 questions each, ~30 minutes total)
uv run python scripts/quick_optimize.py \
    --graph output/graph.pkl \
    --questions data/questions_400_v2.json \
    --sample-size 50 \
    --output-dir output/quick_test

# You can detach with Ctrl+b d and it will keep running
```

**Expected Output**:
```
======================================================================
QUICK VALIDATION SUMMARY
======================================================================
Baseline (from 130-question eval): 55.5%

Cross-Encoder Enabled (α=0.5)            : 70.5% (+15.0 points)
Cross-Encoder + Fusion α=0.7             : 78.2% (+22.7 points)

🏆 Best Quick Test: Cross-Encoder + Fusion α=0.7
   Score: 78.2%

✅ VALIDATION SUCCESSFUL
   Cross-encoder showed expected +15-20 point gain
   Safe to proceed with full 400-question optimization
```

**Decision Criteria**:
- **≥70%** → ✅ Proceed with full optimization
- **65-70%** → ⚠️ Partial success, may need additional work
- **<65%** → ❌ Investigate retrieval issues

## Step 3: Option B - Full Optimization (If Validation Successful)

Run full 400-question optimization across 4 configurations (~6-8 hours):

```bash
cd /Users/bogdan/work/freelance/graph-rag-legal

# Run full optimization (4 experiments × 400 questions × ~18s each)
uv run python scripts/optimize_retrieval.py \
    --graph output/graph.pkl \
    --questions data/questions_400_v2.json \
    --output-dir output/optimization

# Detach with Ctrl+b d - this will take several hours
```

**Expected Output**:
```
======================================================================
OPTIMIZATION RESULTS SUMMARY
======================================================================
Configuration                         Mean Score    Q/min Duration
----------------------------------------------------------------------
Baseline (α=0.5, CE=off)                   55.5%    3.24     2.1h
Cross-Encoder (α=0.5, CE=on)              70.2%    2.98     2.2h
Fusion α=0.7 + CE                         82.5%    2.95     2.3h
Fusion α=0.3 + CE                         75.8%    3.01     2.2h

======================================================================
🏆 BEST CONFIGURATION: Fusion α=0.7 + CE
   Mean Score: 82.5%
   Results: output/optimization/fusion_0.7_ce.json
======================================================================
```

## Step 4: Monitor Progress

### From Outside Tmux
```bash
# List tmux sessions
tmux ls

# Peek at session without attaching
tmux capture-pane -t graphrag -p | tail -20

# Check output files
ls -lh output/quick_test/
ls -lh output/optimization/
```

### From Inside Tmux
```bash
# Attach to running session
tmux attach -t graphrag

# View in real-time (Ctrl+C to stop following)
tail -f output/quick_test/cross_encoder.txt
```

## Step 5: Analyze Results

After benchmark completes:

```bash
# Analyze quick validation results
cat output/quick_test/validation_summary.json

# Analyze full optimization results (if run)
uv run python scripts/analyze_baseline.py \
    --results output/optimization/fusion_0.7_ce.json
```

## Alternative: Run in Background with nohup

If you don't want to use tmux:

```bash
# Quick validation
nohup uv run python scripts/quick_optimize.py \
    --graph output/graph.pkl \
    --questions data/questions_400_v2.json \
    --sample-size 50 \
    --output-dir output/quick_test \
    > output/quick_test.log 2>&1 &

# Get process ID
echo $!

# Monitor log
tail -f output/quick_test.log

# Kill if needed
kill <process-id>
```

## Recommended Workflow

1. **Start tmux session**: `tmux new -s graphrag`
2. **Run quick validation**: ~30 minutes, validates approach
3. **Detach**: `Ctrl+b d` (keeps running)
4. **Check results**: After 30min, check `output/quick_test/validation_summary.json`
5. **If successful**: Run full optimization in same tmux session
6. **Final analysis**: Review results and select best configuration

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
# Check for Python benchmark processes
ps aux | grep "run_benchmark.py"

# Kill if needed
pkill -f "run_benchmark.py"
```

## Next Steps After Optimization

1. **Review Results**: Check `output/optimization/optimization_summary.json`
2. **Select Best Config**: Highest mean score
3. **Update Config**: Update `src/config.py` with best parameters
4. **Final Validation**: Run one more 100-question test to confirm
5. **Documentation**: Update docs with final results

## Expected Timeline

| Task | Duration | Output |
|------|----------|--------|
| Quick Validation | 30 min | validation_summary.json |
| Full Optimization | 6-8 hours | optimization_summary.json |
| Analysis | 10 min | Comprehensive report |
| **Total** | **7-9 hours** | **Final optimized config** |

## Success Criteria

- **Minimum**: 85% mean score
- **Target**: 90-95% mean score
- **Stretch**: >95% mean score

Current baseline is 55.5%, so we need +30-40 percentage points improvement.
