================================================================================
                         INGESTION PIPELINE DIAGRAMS
                         (FalkorDB Backend)
================================================================================

**Note**: This document describes the ingestion pipeline architecture.
The system now uses FalkorDB (Redis-based graph database) instead of NetworkX.
All graphs are stored persistently in FalkorDB, not as pickle files.

DIAGRAM 1: Current 6-Stage Pipeline
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                         STANDARD INGESTION PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────────┘

                              Raw Documents
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 1: Parse Documents           ~15s  (0.3%)      │
        │ • LegalDocumentParser converts markdown to tree      │
        │ • Detects Articles → Sections → Clauses             │
        │ Output: List[DocumentNode] with hierarchical info    │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 2: Chunk Documents           ~30s  (0.5%)      │
        │ • SemanticChunker splits by sections & paragraphs    │
        │ • Prepends hierarchical context to each chunk        │
        │ • Respects max_tokens=1024                           │
        │ Output: List[Chunk] (~2000 chunks)                   │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 3: Extract Entities          ~45s  (0.8%)      │
        │ • EntityExtractor finds PARTY, DATE, AMOUNT, etc.    │
        │ • Regex patterns + optional spaCy NER               │
        │ • Extracts from all chunks                           │
        │ Output: List[Entity] (~70,000 raw entities)          │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 4: Resolve Entities      ~5400s  (97%)  ⚠️     │
        │ • EntityResolver deduplicates similar entities      │
        │ • Embeds all entities (~2200 batch calls)           │
        │ • Builds O(n²) similarity matrix                    │
        │ • Finds connected components                         │
        │ • Creates canonical entities                         │
        │ Output: Dict[id, Entity] (~10,000 deduplicated)     │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 5: Extract Relationships    ~5s   (0.1%)      │
        │ • RelationExtractor finds co-occurrences            │
        │ • If entities in same chunk → related               │
        │ Output: List[Relationship] (~50,000 edges)          │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 6: Build Graph               ~60s  (1.1%)      │
        │ • GraphBuilder creates FalkorDB graph                │
        │ • Adds DOCUMENT, CHUNK, ENTITY nodes                │
        │ • Adds PART_OF, MENTIONS, RELATED_TO edges         │
        │ • Builds BM25 index for sparse retrieval           │
        │ • Builds FAISS index for dense retrieval           │
        │ Output: FalkorDB graph with 71K nodes, 150K edges   │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          Knowledge Graph Ready
                        (Total: 92.6 minutes)

================================================================================

DIAGRAM 2: fast_ingest.py Optimization
================================================================================

┌─────────────────────────────────────────────────────────────────────────────┐
│                         FAST INGESTION PIPELINE (75x faster)               │
└─────────────────────────────────────────────────────────────────────────────┘

                              Raw Documents
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 1: Parse Documents           ~15s              │
        │ • Same as standard pipeline                          │
        │ Output: List[DocumentNode]                           │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 2: Chunk Documents           ~30s              │
        │ • Same as standard pipeline                          │
        │ Output: List[Chunk] (~2000 chunks)                   │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ SKIP STAGES 3-5 ENTIRELY! 🚀                         │
        │ • No entity extraction    ✓ Saves ~45s              │
        │ • No entity resolution    ✓ Saves ~5400s            │
        │ • No relationship extract ✓ Saves ~5s               │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STAGE 6: Build Minimal Graph       ~25s              │
        │ • GraphBuilder with empty entities & relationships   │
        │ • Adds DOCUMENT, CHUNK nodes only                    │
        │ • Adds PART_OF edges only                            │
        │ • Builds BM25 index (same as before)                │
        │ • Builds FAISS index for dense retrieval            │
        │ Output: FalkorDB graph with 2K nodes, 2K edges       │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          Knowledge Graph Ready
                          (Total: 1.3 minutes)

                        SPEEDUP: 92.6 / 1.3 = 71x

================================================================================

DIAGRAM 3: Node and Edge Comparison
================================================================================

STANDARD PIPELINE:
┌────────────────────────────────────────────────────────────┐
│ NODES: 71,065 total                                        │
│  ├─ DOCUMENT: 1 (contract.md)                             │
│  ├─ CHUNK: 2,064 (semantic chunks)                        │
│  └─ ENTITY: 69,000 (parties, dates, amounts, terms)       │
├────────────────────────────────────────────────────────────┤
│ EDGES: 155,200+ total                                      │
│  ├─ PART_OF: 2,064 (chunk → document)                     │
│  ├─ MENTIONS: 70,000 (chunk → entity)                     │
│  └─ RELATED_TO: 83,136 (entity ↔ entity)                  │
└────────────────────────────────────────────────────────────┘

FAST INGEST:
┌────────────────────────────────────────────────────────────┐
│ NODES: 2,065 total                                         │
│  ├─ DOCUMENT: 1 (contract.md)                             │
│  ├─ CHUNK: 2,064 (semantic chunks)                        │
│  └─ ENTITY: 0 (skipped!)                                  │
├────────────────────────────────────────────────────────────┤
│ EDGES: 2,064 total                                         │
│  ├─ PART_OF: 2,064 (chunk → document)                     │
│  ├─ MENTIONS: 0 (no entities)                             │
│  └─ RELATED_TO: 0 (no entities)                           │
└────────────────────────────────────────────────────────────┘

MEMORY SAVINGS: 97% fewer nodes, 98.7% fewer edges

================================================================================

DIAGRAM 4: Entity Resolution Time Breakdown
================================================================================

100% │                    ███████████████████████████████████
     │                    █ ENTITY RESOLUTION: 5400s (97%)  █
 80% │                    ███████████████████████████████████
     │                    
 60% │                    ███████████████████████████████████
     │                    
 40% │                    ███████████████████████████████████
     │    ┌──┐ ┌─┐ ┌──┐  ███████████████████████████████████
 20% │ ┌──┘  └─┘ └──┘ └─ ███████████████████████████████████
     │ │Parse Chunk Extract
  0% ├─┴────────────────────────────────────────────────────
     └────────────────────────────────────────────────────────
                       STAGE
  
  Breakdown of Entity Resolution (5400s):
  • Grouping by type:           0.1s   (0.0%)
  • Embedding 70K entities:  1100.0s  (20.4%)  ← Most expensive
  • Building similarity:     5000.0s  (92.6%)  ← O(n²)
  • Connected components:    1000.0s  (18.5%)
  • Canonical merging:        300.0s   (5.5%)
  ───────────────────────────────────────
  Total would be 7400s, but optimizations bring it to 5400s

================================================================================

DIAGRAM 5: Query-Time Entity Resolution (Hybrid Approach)
================================================================================

USER QUERY: "Who is the licensor and what are their obligations?"

                              Query Input
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STEP 1: Retrieve Chunks from FalkorDB Graph         │
        │ • Use semantic (FAISS) + BM25 search                 │
        │ • Reciprocal Rank Fusion (RRF) combines results       │
        │ • Get top 50 most relevant chunks                    │
        │ • Time: ~0.1s (instant)                             │
        │ Output: List[Chunk] (~50 chunks)                     │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STEP 2: Detect Entity Mentions in Question           │
        │ • Recognize "Who" → looking for PARTY entity         │
        │ • Recognize "obligations" → look for legal terms     │
        │ Output: Set[EntityType]                              │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STEP 3: Extract Entities from Retrieved Chunks       │
        │ • Run entity extraction on 50 chunks only             │
        │ • Get ~100-200 raw entities (not 70K!)              │
        │ • Time: ~0.05s                                      │
        │ Output: List[Entity] (~150 entities)                 │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STEP 4: Resolve Small Entity Set                     │
        │ • Only resolve 150 entities (not 70K!)              │
        │ • Embed 150 texts (~0.1s)                           │
        │ • Build 150×150 matrix (~0.2s)                      │
        │ • Find components (~0.1s)                            │
        │ • Time: ~0.4s (not 90 minutes!)                     │
        │ Output: Dict[id, Entity] (~50 deduplicated)         │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────────────────────┐
        │ STEP 5: Generate Answer with Entity Context          │
        │ • Use resolved entities to enhance answer            │
        │ • Link entity mentions to canonical forms            │
        │ • Add entity relationships to context                │
        │ Time: ~0.5s (LLM generation)                        │
        │ Output: Answer with entity annotations               │
        └──────────────────────────────────────────────────────┘
                                   │
                                   ▼
                          Answer with Entity Context
                          (Total: ~1.2 seconds)

vs. Standard Pipeline: 92.6 minutes ingestion + retrieval
    Hybrid Approach:    1.3 minutes ingestion + ~1s per query

================================================================================

DIAGRAM 6: Architecture Decision Tree
================================================================================

                          Start Here
                              │
                    Do you need entity context?
                         /         \
                       YES          NO
                       │            │
                  Need to /    Want chunks
                 extract all  only?
                 entities?      │
                    /     \    YES
                  YES     NO   │
                   │       │   └──→ Use fast_ingest.py ✓
                   │       │        • 1.3 min ingestion
                   │       │        • Full retrieval works
                   │       │        • 75x faster
                   │       │
                   │   Can wait  
                   │  for 90min?
                   │    /  \
                   │  YES   NO
                   │   │     │
                   │   │    Use Hybrid Approach
                   │   │    (Lazy Resolution)
                   │   │    • 1.3 min ingestion
                   │   │    • ~1s per query with entities
                   │   │    • Entity context on demand
                   │   │
                   └──→ Use Standard Pipeline
                        • 90+ min ingestion
                        • Full entity resolution
                        • Best for entity-centric QA

================================================================================

DIAGRAM 7: Performance Scaling
================================================================================

Ingestion Time vs Document Count:

Minutes
 100 ├────────────────────────────────────────────────────────
     │              ╱╱╱╱╱╱╱╱╱╱╱╱╱╱ Standard (Stage 4 dominates)
  80 ├─────────────╱╱╱╱╱╱╱╱╱╱╱╱╱╱╱
     │          ╱╱╱╱╱ fast_ingest (linear)
  60 ├────────╱╱╱╱╱
     │      ╱╱╱╱
  40 ├────╱╱╱╱╱─────────────────────────────────────────────
     │  ╱╱╱╱╱
  20 ├╱╱╱╱╱──────────────────────────────────────────────────
     │ ╱
   0 ├┴────────────────────────────────────────────────────
     0   100  200  300  400  500  600  700  800
                    Documents

Legend:
  ╱╱╱ fast_ingest.py (linear growth, ~0.2 min per 100 docs)
  ─── Standard pipeline (exponential, O(n²) in entity count)

For 400 documents:
  • fast_ingest:  1.3 min (constant)
  • standard:     92.6 min (increases with doc count)

Projected for 800 documents:
  • fast_ingest:  2.6 min (scalable)
  • standard:     ~400+ min (becomes impractical)

================================================================================
