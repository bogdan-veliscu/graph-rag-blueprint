# Ingestion Pipeline - Quick Reference Guide

## The Problem
Standard ingestion takes **90-120 minutes** for 400 documents because **Stage 4: Entity Resolution** consumes **95% of time**.

```
Why Entity Resolution is Slow:
  • O(n²) pairwise comparisons: 70K entities = 2.45 billion comparisons
  • Embedding computation: 70K embeddings at ~0.1-0.5s each
  • Similarity matrix: O(n²) memory = 37GB for 70K entities
  • Connected components: Expensive DFS traversal
```

---

## The Solution: fast_ingest.py

**Instead of:** Parse → Chunk → Extract → **Resolve** → Relationships → Graph (95 min)

**Do:** Parse → Chunk → Graph (1.5 min) ✓

**Speedup: 75x faster** (95 min → 1.5 min)

### What You Get
✓ Document-based chunks with embeddings  
✓ Full BM25 sparse retrieval index  
✓ Document structure (Articles → Sections → Clauses)  
✓ Semantic search working perfectly  

### What You Lose
✗ Entity deduplication (Party A vs. Licensor)  
✗ Entity nodes in graph  
✗ Entity mentions tracking  
✗ Direct entity-entity relationships  

---

## When to Use What

| Use Case | Approach |
|----------|----------|
| "Find documents about X" | fast_ingest (1.5 min) ✓ |
| "What is similar to Y?" | fast_ingest (1.5 min) ✓ |
| "Extract all parties" | standard pipeline (95 min) |
| "Relationship between Party A and B?" | standard pipeline (95 min) |
| "Get me answer + entity context" | hybrid (1.5 min + on-demand) |

---

## The Hybrid Approach (To Be Implemented)

**Best of both worlds:**

```
1. Start: fast_ingest (1.5 min) → chunks + BM25 ready immediately
2. Query comes in: Retrieve chunks (instant)
3. If query needs entities → Extract entities from retrieved chunks
4. Resolve ONLY those entities (100s, not 70K!)
5. Return enhanced answer with entity context
```

**Benefits:**
- Fast ingestion (1.5 min)
- Query-time entity resolution (only when needed)
- Small entity set (10-100, not 70K)
- Entity resolution time: 0.1-1 sec per query instead of 95 min upfront

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [1] Parse          [2] Chunk       [3] Extract    [4] BOTTLENECK│
│  ─────────────────  ──────────────  ──────────────  ─────────────│
│  15s               30s             45s             5400s !!!      │
│                                                                   │
│  [5] Relationships  [6] Build Graph                              │
│  ──────────────────  ─────────────────                           │
│  5s                60s                                           │
│                                                                   │
│  Total: 5555s (92 minutes)                                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

fast_ingest skips [3] [4] [5] entirely!
```

---

## Graph Structure Comparison

### Standard Pipeline Graph
```
Nodes: ~71,000
  • 1 document node
  • ~2,000 chunk nodes
  • ~69,000 entity nodes

Edges: ~150,000+
  • PART_OF: chunk → document (2,000)
  • MENTIONS: chunk → entity (70,000)
  • RELATED_TO: entity ↔ entity (78,000+)
```

### fast_ingest Graph
```
Nodes: ~2,000
  • 1 document node
  • ~2,000 chunk nodes
  • 0 entity nodes

Edges: ~2,000
  • PART_OF: chunk → document (2,000)
  • MENTIONS: (none - no entities)
  • RELATED_TO: (none - no entities)
```

### Hybrid Graph (Proposed)
```
Phase 1: Same as fast_ingest
Phase 2: Add entities on demand when queried
```

---

## Entity Resolution Details

### The Algorithm

```python
resolve_entities(raw_entities):
    # 1. Group by type (PARTY, DATE, AMOUNT, etc.)
    groups = group_by_type(raw_entities)
    
    # 2. For each group, compute embeddings
    for group in groups:
        embeddings = embed(group.texts)
        
        # 3. Build O(n²) similarity matrix
        for i, j in all_pairs(group):
            sim[i][j] = 0.7 * embedding_sim + 0.3 * string_sim
        
        # 4. Find connected components (threshold=0.85)
        components = connected_components(sim, threshold=0.85)
        
        # 5. Create canonical entity per component
        for component in components:
            canonical = merge(component.entities)
```

### Time Breakdown (400 documents = 70K entities)

```
Grouping by type:          0.1s
  └─ ~10K PARTY per group
  └─ ~20K DATE per group
  └─ ~5K AMOUNT per group
  └─ ~35K LEGAL_TERM per group

Embedding (most expensive):
  └─ 70K texts → embeddings
  └─ ~2200 batch calls × 0.5s = 1100s

Similarity matrix:
  └─ O(70K²) = 5 billion ops × ~1µs = 5000s

Connected components:     1000s
  └─ DFS through graph

Canonical merging:        300s
  └─ Merge mentions, chunk_ids

─────────────────────────
TOTAL: ~7400s (124 min... but observed ~5400s with optimizations)
```

---

## Files Involved in Ingestion

### Core Pipeline (95 min)
- `src/rag_pipeline.py` - orchestrator (stages 1-6)
- `src/ingest/parser.py` - stage 1: parse (fast)
- `src/ingest/chunker.py` - stage 2: chunk (fast)
- `src/ingest/entity_extractor.py` - stage 3: extract (moderate)
- `src/ingest/entity_resolver.py` - stage 4: resolve ⚠️ SLOW
- `src/ingest/relation_extractor.py` - stage 5: relationships (fast)
- `src/ingest/graph_builder.py` - stage 6: build graph (fast)

### Fast Alternative (1.5 min)
- `scripts/fast_ingest.py` - skip stages 3-5, build chunk-only graph

### Support Files
- `src/models.py` - Entity, Chunk, Relationship classes
- `src/config.py` - configuration (thresholds, model names)
- `src/utils/embeddings.py` - embedding model wrapper
- `src/ingest/rdf_exporter.py` - RDF export

---

## Optimization Strategies

### Immediate (No code changes needed)
- Use `fast_ingest.py` for rapid iteration
- Reduces feedback loop: 95 min → 1.5 min

### Short-term (Medium effort)
1. **Lazy Entity Resolution** (Option A)
   - Detect entity mentions in query
   - Resolve only relevant entities (10-100, not 70K)
   - Entity resolution time: <1s instead of 95 min upfront

2. **Incremental Ingestion** (Option B)
   - fast_ingest immediately (1.5 min)
   - Entity resolution in background
   - Seamless upgrade when background completes

3. **Two-Phase Ingestion** (Option C)
   - Phase 1: fast_ingest (1.5 min, return to user)
   - Phase 2: enhance with entities (background, user can skip)

### Medium-term (Advanced)
- FAISS for approximate nearest neighbor search in embeddings
- GPU acceleration for embedding computation
- Distributed resolution across multiple machines
- Streaming ingestion (one document at a time)

---

## Recommended Next Steps

### For Fast Results Now
```bash
# Use fast_ingest.py instead of standard pipeline
python scripts/fast_ingest.py \
  --input /path/to/documents \
  --output /path/to/graph.pkl
```

Expected time: ~1.5 minutes for 400 documents

### For Production (Hybrid Approach)
1. Implement Option A: Lazy Entity Resolution
   - Extract entities only from retrieved chunks
   - Resolve only those entities
   - Query-time entity context

2. Add entity detection heuristics
   - Recognize when query asks about entities
   - Example: "Who is the licensor?" → detect PARTY entity

3. Fall back to chunk-only answers for non-entity queries

---

## Key Metrics

```
STANDARD PIPELINE:
  Total Time:    95 minutes
  Bottleneck:    Entity Resolution (5400s = 90 minutes)
  % in bottleneck: 97%

FAST_INGEST:
  Total Time:    1.5 minutes
  Speedup:       75x faster

HYBRID (PROPOSED):
  Ingestion:     1.5 minutes (fast_ingest)
  Query 1:       0.1s (no entities)
  Query 2:       0.5s + 0.1s (with entity resolution)
  
  vs. standard:  95 min ingestion + multiple fast queries
                 STILL FAR BETTER
```

---

## Decision Matrix

Choose your approach based on use case:

```
┌──────────────────────────┬──────────┬──────────────┬────────────┐
│ Use Case                 │ Standard │ fast_ingest  │ Hybrid     │
├──────────────────────────┼──────────┼──────────────┼────────────┤
│ Need entity dedup?       │ Yes      │ No           │ On-demand  │
│ Ingestion time           │ 95 min   │ 1.5 min      │ 1.5 min    │
│ Can wait for prep?       │ No       │ Yes          │ Yes        │
│ Query entity mentions?   │ Yes      │ No           │ Yes        │
│ Entity extraction q/a    │ Yes      │ No           │ Limited    │
│ Relationship queries?    │ Yes      │ No           │ Limited    │
│ Complexity to build      │ Done     │ Done         │ Medium     │
└──────────────────────────┴──────────┴──────────────┴────────────┘
```

---

