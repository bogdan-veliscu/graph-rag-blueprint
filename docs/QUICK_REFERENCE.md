# Ingestion Pipeline - Quick Reference Guide

## Current Implementation

The system uses a **standard ingestion pipeline** with optimized batch processing for entity resolution and edge creation.

```
Why Entity Resolution is Slow:
  • O(n²) pairwise comparisons: 70K entities = 2.45 billion comparisons
  • Embedding computation: 70K embeddings at ~0.1-0.5s each
  • Similarity matrix: O(n²) memory = 37GB for 70K entities
  • Connected components: Expensive DFS traversal
```

---

## Ingestion Commands

**Full ingestion** (all documents):
```bash
make ingest
# Processes all documents in data/source_data/
```

**Fast testing** (single file):
```bash
make ingest-fast
# Processes single file from data/fast_data/ for quick testing
```

### What You Get
✓ Document-based chunks with embeddings  
✓ Full BM25 sparse retrieval index  
✓ FAISS dense retrieval index  
✓ Entity extraction and resolution (FAISS-based deduplication)  
✓ Entity relationships (co-occurrence)  
✓ Knowledge graph in FalkorDB  
✓ Semantic search working perfectly  

---

## Ingestion Pipeline Stages

1. **Parse Documents** - Extract metadata and content
2. **Chunk Content** - Split into semantic chunks (512 tokens, 128 overlap)
3. **Extract Entities** - spaCy NER + regex patterns
4. **Resolve Entities** - FAISS-based deduplication (batched for performance)
5. **Extract Relationships** - Co-occurrence model
6. **Build Graph** - Create nodes and edges in FalkorDB (batched edge creation)

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

Current implementation includes all stages with optimized batch processing.
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

### Current Graph Structure
```
Nodes: Documents, Pages, Chunks, Entities
Edges: 
  • PART_OF: chunk → document
  • DOCUMENT_HAS_PAGE: document → page
  • PAGE_HAS_CHUNK: page → chunk
  • MENTIONS: chunk → entity (batched creation)
  • RELATED_TO: entity ↔ entity (batched creation)
  • DOCUMENT_PUBLISHED_BY: document → publisher entity
  • PAGE_AUTHORED_BY: page → author entity
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

### Core Pipeline
- `src/graph_rag/ingest/pipeline.py` - orchestrator (stages 1-6)
- `src/graph_rag/ingest/source_parser.py` - stage 1: parse (fast)
- `src/graph_rag/ingest/chunker.py` - stage 2: chunk (fast)
- `src/graph_rag/ingest/entity_extractor.py` - stage 3: extract (moderate)
- `src/graph_rag/ingest/faiss_resolver.py` - stage 4: resolve (batched, optimized)
- `src/graph_rag/ingest/relation_extractor.py` - stage 5: relationships (fast)
- `src/graph_rag/ingest/graph_builder.py` - stage 6: build graph (batched edge creation)

### Support Files
- `src/graph_rag/models.py` - Entity, Chunk, Relationship classes
- `src/graph_rag/config.py` - configuration (thresholds, model names)
- `src/graph_rag/utils/embeddings.py` - embedding model wrapper
- `src/graph_rag/graph/falkordb_adapter.py` - FalkorDB graph operations

---

## Optimization Strategies

### Current Optimizations
- **Batch edge creation**: 1000 edges per batch (significantly faster)
- **FAISS batch processing**: Entity resolution in batches of 10K
- **Parallel file processing**: Async processing with configurable workers
- **Progress indicators**: Real-time feedback during ingestion

### Performance Improvements
- Entity resolution: Batched FAISS similarity search
- Edge creation: Batch Cypher queries (1000 edges per query)
- File processing: Parallel async processing (up to 8 workers)

### Future Optimizations
- GPU acceleration for embedding computation
- Distributed resolution across multiple machines
- Streaming ingestion (one document at a time)
- Query-time entity resolution for specific queries

---

## Recommended Usage

### For Fast Testing
```bash
# Use single-file ingestion for quick iteration
make ingest-fast
```

Expected time: ~30-60 seconds for single file

### For Full Ingestion
```bash
# Ingest all documents
make ingest
```

Expected time: ~25-30 minutes for 60 documents (with batch optimizations)

### For Production
1. Use batch optimizations (already implemented)
2. Monitor performance with `scripts/benchmark_performance.py`
3. Adjust `max_concurrent` and `query_batch_size` in config as needed

---

## Key Metrics

```
CURRENT PIPELINE (with optimizations):
  Total Time:    ~25-30 minutes (60 documents)
  Entity Resolution: Batched FAISS (optimized)
  Edge Creation: Batched Cypher queries (1000 per batch)
  File Processing: Parallel async (8 workers)

PERFORMANCE BREAKDOWN:
  - File parsing: ~5-10 seconds (parallel)
  - Entity resolution: ~5-10 minutes (batched)
  - Edge creation: ~2-5 minutes (batched)
  - Index building: ~1-2 minutes

QUERY PROCESSING:
  - Single query: ~4-5 seconds
  - Parallel (400 queries): ~28-34 minutes
  - Target: ≤60 minutes for 400 questions
```

---

## Commands Reference

```bash
# Ingestion
make ingest              # Ingest all documents
make ingest-fast         # Fast test with single file

# Querying
make query Q="question"  # Single question
make query-file FILE=... # From JSON file

# Validation
make validate-graph      # Check graph structure

# Services
make falkordb-start     # Start FalkorDB
make falkordb-status     # Check status
make falkordb-stop       # Stop FalkorDB

# Testing
make test                # Run tests
make demo                # Run complete demo
```

---

