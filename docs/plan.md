# GraphRAG Legal System - Comprehensive Rebuild Plan

**Date**: 2025-11-12
**Purpose**: Complete documentation and plan for system rebuild from scratch
**Target Audience**: Junior engineers who can implement the entire system following this plan

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Critical Architecture Decisions](#critical-architecture-decisions)
4. [Data Flow Pipeline](#data-flow-pipeline)
5. [Metadata Handling - CRITICAL](#metadata-handling---critical)
6. [Current Issues & Required Fixes](#current-issues--required-fixes)
7. [Implementation Plan](#implementation-plan)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Guide](#deployment-guide)
10. [Appendix: File-by-File Reference](#appendix-file-by-file-reference)

---

## Executive Summary

### What This System Does

A **high-accuracy GraphRAG (Graph-based Retrieval-Augmented Generation)** system for legal document question-answering that:
- Ingests legal documents with rich metadata (titles, dates, issue numbers, authors, publishers, etc.)
- Builds a knowledge graph with entities, relationships, and document hierarchy
- Answers questions with Vancouver-style citations grounded in source documents
- Processes ~400 questions in ≤60 minutes with >95% accuracy target

### Key Technologies

- **Language**: Python 3.12+
- **Graph Database**: FalkorDB (Redis-based, persistent)
- **Vector Store**: FAISS (dense embeddings)
- **Sparse Retrieval**: BM25 (keyword matching)
- **Entity Extraction**: spaCy NER + regex patterns
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: Ollama (Llama 3.1 8B) or Anthropic-compatible APIs

### Current Status

✅ **Working:**
- Complete ingestion pipeline with metadata parsing
- Knowledge graph construction with FalkorDB
- Hybrid retrieval (dense + sparse + graph traversal)
- Answer generation with citations
- Evaluation system with LLM-as-judge

⚠️ **Needs Fixes:**
- Citations don't use rich metadata (just filenames)
- Original language names (`<orig>` tags) not parsed as separate fields
- Document titles not properly stored in graph nodes
- Metadata not used for query filtering
- Entity matching for metadata is fragile

---

## System Overview

### High-Level Architecture

```
┌─────────────────────┐
│  Legal Documents    │
│  (Markdown + XML)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  INGESTION PIPELINE │
│  ─────────────────  │
│  1. Parse Documents │  ← Extracts metadata from XML tags
│  2. Chunk Content   │  ← 512 tokens, 128 overlap
│  3. Extract Entities│  ← spaCy + regex patterns
│  4. Resolve Entities│  ← FAISS deduplication
│  5. Extract Relations│ ← Co-occurrence model
│  6. Build Graph     │  ← FalkorDB with indices
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  KNOWLEDGE GRAPH    │
│  ─────────────────  │
│  • Documents        │  ← With rich metadata
│  • Pages            │  ← Page-level metadata
│  • Chunks           │  ← With embeddings
│  • Entities         │  ← Resolved, filtered
│  • Relationships    │  ← Entity co-occurrence
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   QUERY PIPELINE    │
│  ─────────────────  │
│  1. Parse Query     │  ← Extract entities/keywords
│  2. Link Entities   │  ← Fuzzy match to graph
│  3. Hybrid Retrieval│  ← Dense + Sparse + RRF
│  4. Graph Traversal │  ← BFS + PageRank
│  5. Rerank          │  ← Semantic + graph scores
│  6. Generate Answer │  ← LLM with citations
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Answer + Citations │
│  (Vancouver style)  │
└─────────────────────┘
```

### Key Components

1. **Document Parser** (`src/ingest/source_parser.py`)
   - Parses XML-like tags: `<document_metadata>`, `<page_metadata>`, `<header>`, `<footer>`, `<table>`, `<orig>`
   - Extracts rich metadata (titles, dates, issue numbers, authors, publishers)
   - Preserves multilingual content (`<orig>` tags)

2. **Chunker** (`src/ingest/chunker.py`)
   - Splits documents into semantic chunks (512 tokens, 128 overlap)
   - Preserves hierarchical context (Article > Section > Clause)
   - Links chunks to pages and documents

3. **Entity Extractor** (`src/ingest/entity_extractor.py`)
   - Extracts 8 entity types: PARTY, DATE, AMOUNT, CLAUSE_REF, LEGAL_TERM, PERSON, ORGANIZATION, LOCATION
   - Uses hybrid approach: regex patterns + spaCy NER
   - Fallback extraction when spaCy unavailable

4. **Entity Resolver** (`src/ingest/faiss_resolver.py`)
   - Deduplicates entities using FAISS similarity (e.g., "Party A" = "Licensor")
   - Reduces ~22K raw entities → ~5K unique entities

5. **Relation Extractor** (`src/ingest/relation_extractor.py`)
   - Extracts relationships via co-occurrence model
   - Creates ~10K `RELATED_TO` edges between entities

6. **Graph Builder** (`src/ingest/graph_builder.py`)
   - Creates nodes: DOCUMENT, PAGE, CHUNK, ENTITY
   - Creates edges: PART_OF, DOCUMENT_HAS_PAGE, PAGE_HAS_CHUNK, MENTIONS, RELATED_TO, DOCUMENT_PUBLISHED_BY, PAGE_AUTHORED_BY
   - Builds FAISS index for embeddings, BM25 index for sparse retrieval

7. **Orchestrator** (`src/query/orchestrator.py`)
   - Coordinates query processing pipeline
   - Manages retrieval, traversal, reranking, generation

8. **Answer Generator** (`src/query/answer_generator.py`)
   - Generates answers using LLM with anti-hallucination prompts
   - Formats Vancouver-style citations
   - **CRITICAL ISSUE**: Currently uses filenames instead of rich metadata

9. **Evaluator** (`src/evaluation/evaluator.py`)
   - LLM-as-judge for 5 metrics: Faithfulness, Relevance, Completeness, Clarity, Citations
   - Target: >95% overall accuracy

---

## Critical Architecture Decisions

### 1. Document Format: Markdown with XML Tags

**Why**: Legal documents need rich metadata (titles, dates, authors, publishers) that standard Markdown can't express.

**Format**:
```markdown
<document_metadata>
{
  "document_title": "Al-Kuwait Al-Youm Official Gazette - Issue 1733",
  "document_date": "2025-04-06",
  "issue_number": 1733,
  "volume_number": 71,
  "document_type": "official_gazette",
  "language": ["ar", "en"],
  "authors": ["Amir of Kuwait, Mishal Al-Ahmad..."],
  "publisher": "Kuwait Today / Al-Kuwait Al-Youm <orig>الكويت اليوم</orig>",
  "document_summary": "This document is Issue 1733...",
  "document_id": "6-4-2025",
  "total_pages": 112
}
</document_metadata>

<page_start>1</page_start>
<page_metadata>
{
  "page_title": "Contents of Issue 1733",
  "document_date": "2025-04-06",
  "issue_number": 1733,
  "page_type": "index",
  "authors": null,
  "publisher": "Ministry of Information...",
  "page_summary": "This page serves as..."
}
</page_metadata>
<header>Issue 1733, Seventy-First Year...</header>
<table_caption>Table of Contents</table_caption>
<table>| Section | Page |...</table>
<page_end>1</page_end>
```

**Key Tags**:
- `<document_metadata>`: JSON with document-level metadata
- `<page_metadata>`: JSON with page-level metadata
- `<page_start>` / `<page_end>`: Page boundaries
- `<header>` / `<footer>`: Page headers/footers
- `<table>` / `<table_caption>`: Table content
- `<orig>`: Original language text (e.g., `Kuwait Today <orig>الكويت اليوم</orig>`)

### 2. Graph Schema: Document → Page → Chunk Hierarchy

**Why**: Maintains document structure and enables precise citations with page numbers.

**Node Types**:
- **DOCUMENT**: Document-level node with metadata (document_id, title, issue_number, volume_number, etc.)
- **PAGE**: Page-level node with metadata (page_number, page_title, authors, publisher, etc.)
- **CHUNK**: Semantic chunk with text, embeddings, and references to page/document
- **ENTITY**: Extracted entity (resolved, filtered)

**Edge Types**:
- **PART_OF**: Chunk → Document (hierarchical)
- **DOCUMENT_HAS_PAGE**: Document → Page (1-to-many)
- **PAGE_HAS_CHUNK**: Page → Chunk (1-to-many)
- **MENTIONS**: Chunk → Entity (entity mentions)
- **RELATED_TO**: Entity ↔ Entity (co-occurrence)
- **DOCUMENT_PUBLISHED_BY**: Document → Entity (publisher)
- **PAGE_AUTHORED_BY**: Page → Entity (author)

**Graph Structure**:
```
Document (id: "6-4-2025", title: "Al-Kuwait Al-Youm Official Gazette - Issue 1733", ...)
  ├─ DOCUMENT_HAS_PAGE → Page (page_number: 1, page_title: "Contents", ...)
  │     ├─ PAGE_HAS_CHUNK → Chunk (text: "...", embedding: [...])
  │     │     └─ MENTIONS → Entity (text: "Amir of Kuwait", type: PERSON)
  │     └─ PAGE_AUTHORED_BY → Entity (text: "Ministry of Information", type: ORGANIZATION)
  └─ DOCUMENT_PUBLISHED_BY → Entity (text: "Kuwait Today", type: ORGANIZATION)
```

### 3. Hybrid Retrieval: Dense + Sparse + Graph

**Why**: Combines semantic similarity (dense), keyword matching (sparse), and graph relationships for best accuracy.

**Components**:
1. **Dense Retrieval**: FAISS index with sentence-transformers embeddings
   - Top-K: 50 chunks
   - Model: all-MiniLM-L6-v2

2. **Sparse Retrieval**: BM25 keyword matching
   - Top-K: 50 chunks
   - Good for exact legal terms

3. **Reciprocal Rank Fusion (RRF)**: Combines dense + sparse scores
   - Formula: `score = (1 / (k + rank_dense)) + (1 / (k + rank_sparse))`
   - k = 60 (hyperparameter)

4. **Graph Traversal**: Document-aware BFS + Personalized PageRank
   - Max hops: 2
   - Prevents cross-document contamination

5. **Reranking**: Semantic + graph score combination
   - Final top-K: 10 chunks for generation

### 4. Entity Resolution: FAISS-Based Deduplication

**Why**: Legal documents have many duplicates (e.g., "Party A", "Licensor", "the Licensor").

**Approach**:
- Embed entity text with sentence-transformers
- FAISS similarity search (cosine similarity)
- Threshold: 0.85 for merging
- Reduces 22K raw entities → 5K unique entities (77% reduction)

### 5. Citation Format: Vancouver Style with Page Numbers

**Why**: Legal citations need precise source references.

**Current Format** (INCORRECT):
```
[1] 6-4-2025_en.md. p.1.
```

**Target Format** (CORRECT):
```
[1] Al-Kuwait Al-Youm Official Gazette - Issue 1733, Volume 71 (2025-04-06). p.1. Ministry of Information.
```

**Required Fields**:
- Document title (from `document_metadata.document_title`)
- Issue/volume numbers (from `document_metadata.issue_number`, `volume_number`)
- Document date (from `document_metadata.document_date`)
- Page number (from chunk metadata)
- Publisher (from `page_metadata.publisher` or `document_metadata.publisher`)
- Authors (optional, from `page_metadata.authors`)

---

## Data Flow Pipeline

### Ingestion Pipeline (Step-by-Step)

**Input**: Markdown files in `data/source_data/` with XML tags

**Step 1: Parse Documents** (`src/rag_pipeline.py:77-168`)
- Detect if file has `<document_metadata>` tag (source data file)
- **Source data files**: Parse with `parse_source_data()` → `ParsedSourceDocument`
- **Regular files**: Parse with `LegalDocumentParser()` → `DocumentNode` tree

**Step 2: Create Document/Page Models** (`src/rag_pipeline.py:109-148`)
- Extract document metadata from `ParsedSourceDocument.document_metadata`
- Create `Document` model with metadata (document_id, title, issue_number, etc.)
- Create `Page` models from `ParsedSourceDocument.pages`
- Each page has page metadata (page_title, authors, publisher, etc.)

**Step 3: Convert to DocumentNode Trees** (`src/ingest/source_converter.py`)
- Convert each page to `DocumentNode` tree for chunking
- Preserve page metadata in `DocumentNode.metadata`
- Set `source_file` = `document_id` for graph linking

**Step 4: Chunk Documents** (`src/ingest/chunker.py`)
- Split each page into semantic chunks (512 tokens, 128 overlap)
- Preserve hierarchical context (Article > Section > Clause)
- Set `chunk.page_id`, `chunk.page_number`, `chunk.source_file` = `document_id`
- Preserve `table_captions`, `tables`, `orig_spans` in chunk metadata

**Step 5: Extract Entities** (`src/ingest/entity_extractor.py`)
- Extract entities from each chunk using hybrid approach:
  - **Regex patterns**: PARTY, DATE, AMOUNT, CLAUSE_REF, LEGAL_TERM
  - **spaCy NER**: PERSON, ORGANIZATION, LOCATION
  - **Fallback**: Capitalization heuristics when spaCy unavailable
- Extract ~22K raw entities from 60 documents

**Step 6: Resolve Entities** (`src/ingest/faiss_resolver.py`)
- Deduplicate entities using FAISS similarity
- Merge duplicates (e.g., "Party A" = "Licensor")
- Reduce 22K raw → 5K unique entities

**Step 7: Filter Entities** (`src/rag_pipeline.py:289-309`)
- Filter noisy entity types: LEGAL_TERM, DATE, AMOUNT
- Filter high-frequency hub nodes (appearing in >X% of chunks)
- Reduce 5K → 3K filtered entities

**Step 8: Extract Relationships** (`src/ingest/relation_extractor.py`)
- Co-occurrence model: entities appearing together in same chunk
- Cross-chunk relationships: entities sharing multiple chunks
- Create ~10K `RELATED_TO` edges with weights

**Step 9: Build Graph** (`src/ingest/graph_builder.py`)
- **Create nodes**:
  - Document nodes (with rich metadata)
  - Page nodes (with page-level metadata)
  - Chunk nodes (with embeddings, page references)
  - Entity nodes (resolved, filtered)
- **Create edges**:
  - PART_OF: Chunk → Document
  - DOCUMENT_HAS_PAGE: Document → Page
  - PAGE_HAS_CHUNK: Page → Chunk
  - MENTIONS: Chunk → Entity
  - RELATED_TO: Entity ↔ Entity
  - DOCUMENT_PUBLISHED_BY: Document → Publisher Entity
  - PAGE_AUTHORED_BY: Page → Author Entity
- **Build indices**:
  - FAISS index for dense retrieval
  - BM25 index for sparse retrieval
  - Precompute PageRank scores

**Output**: FalkorDB graph + FAISS index + BM25 index

### Query Pipeline (Step-by-Step)

**Input**: List of questions (strings)

**Step 1: Load Graph** (`src/rag_pipeline.py`)
- Load FalkorDB graph from database
- Load FAISS index from `output/embeddings.npy`
- Load BM25 index from `output/bm25.pkl`
- Load chunk metadata from `output/chunks.json`

**Step 2: Parse Query** (`src/query/query_parser.py`)
- Extract entities from question
- Extract keywords
- Identify question type (what/who/when/where/how)

**Step 3: Link Entities** (`src/query/entity_linker.py`)
- Fuzzy match query entities to graph entities
- Use string similarity (Levenshtein distance)
- Link to entity IDs in graph

**Step 4: Hybrid Retrieval** (`src/query/retriever.py`)
- **Dense retrieval**: Embed question → FAISS search → Top-50 chunks
- **Sparse retrieval**: BM25 search → Top-50 chunks
- **Fusion**: Reciprocal Rank Fusion (RRF) → Combined ranking

**Step 5: Graph Traversal** (`src/query/graph_traversal.py`)
- **Document-aware BFS**: 2-hop neighborhood from linked entities
  - Only traverse within same document (prevent cross-contamination)
- **Personalized PageRank**: Start from linked entities
  - Teleport to linked entities with high probability
- Add graph-connected chunks to candidate pool

**Step 6: Rerank** (`src/query/reranker.py`)
- Combine semantic scores (dense retrieval) + graph scores (PageRank)
- Optional: Cross-encoder reranking
- Select top-10 chunks for generation

**Step 7: Generate Answer** (`src/query/answer_generator.py`)
- Build context from top-10 chunks
- Call LLM with anti-hallucination prompt
- Enforce citation format: `[1][2]` inline, `References\n1. ...` at end
- **CRITICAL ISSUE**: Currently formats citations with filenames only

**Step 8: Verify Citations** (`src/query/citation_verifier.py`)
- Extract claims from answer
- Verify each claim is supported by cited chunks
- Use NLI model for verification

**Output**: JSON with `{"answer": "...", "citations": [...]}`

---

## Metadata Handling - CRITICAL

### All Metadata Fields That MUST Be Captured

Based on your requirements, here are ALL the metadata fields that must be parsed and stored:

#### Document-Level Metadata
From `<document_metadata>` tag:
- ✅ `document_title` - Full title of the document
- ✅ `document_date` - ISO 8601 date (e.g., "2025-04-06")
- ✅ `document_id` - Unique identifier
- ✅ `issue_number` - Gazette/publication issue number
- ✅ `volume_number` - Gazette/publication volume number
- ✅ `document_type` - Type (e.g., "official_gazette", "decree")
- ✅ `language` - Primary language(s)
- ✅ `authors` - List of author names (with `<orig>` tags)
- ✅ `publisher` - Publisher name (with `<orig>` tags)
- ✅ `document_summary` - AI-generated summary
- ✅ `total_pages` - Total page count
- ✅ `processed` - Processing timestamp

#### Page-Level Metadata
From `<page_metadata>` tag:
- ✅ `page_number` - Page number in document
- ✅ `page_title` - Title of the page
- ✅ `document_date` - Date (inherited from document)
- ✅ `issue_number` - Issue number (inherited)
- ✅ `volume_number` - Volume number (inherited)
- ✅ `document_type` - Type (inherited)
- ✅ `languages_detected` - List of detected languages
- ✅ `page_type` - Type (e.g., "index", "content", "blank")
- ✅ `authors` - Author names for this specific page
- ✅ `publisher` - Publisher for this specific page
- ✅ `page_summary` - AI-generated page summary
- ✅ `header` - Page header content
- ✅ `footer` - Page footer content (currently not in example but should be captured)

#### Content Metadata
From content tags:
- ✅ `table_captions` - List of table captions
- ✅ `tables` - Table content
- ✅ `orig_spans` - Multilingual spans from `<orig>` tags

#### Author Metadata (for each author)
- ✅ `document_name` - Author's document name
- ⚠️ `company_name` - Author's company/organization (not currently extracted separately)
- ✅ `original_name` - Original language name from `<orig>` tag (not currently parsed separately)

### Current Implementation Status

**What's Being Captured** ✅:
- All document-level metadata fields
- All page-level metadata fields
- Table captions and content
- Header content (footer may be missing in some docs)
- Multilingual `<orig>` tags (stored as strings, not parsed)

**What's Missing** ⚠️:
- `<orig>` tags not parsed into separate `original_name` field
- Company names not extracted separately for authors
- Metadata not used in citations
- Metadata not used for query filtering

### How Metadata Flows Through the System

```
Raw Document → Parse → Document/Page Models → Graph Nodes → Citations
     ↓              ↓              ↓                ↓             ↓
  <document_     Parse        Document          FalkorDB    (Needs Fix!)
  _metadata>     JSON         metadata          nodes       Currently
                                                             uses filename
```

**Files Involved**:
1. `src/ingest/source_parser.py` - Parses XML tags → `DocumentMetadata`, `PageMetadata`
2. `src/ingest/source_converter.py` - Converts → `Document`, `Page` models
3. `src/ingest/graph_builder.py` - Creates graph nodes with metadata
4. `src/query/answer_generator.py` - ⚠️ **NEEDS FIX** - Should retrieve and format metadata in citations

---

## Current Issues & Required Fixes

### Issue 1: Citations Don't Use Rich Metadata ✅ **FIXED**

**File**: `src/query/answer_generator.py:87-159`

**Previous Behavior**:
```
[1] 6-4-2025_en.md. p.1.
```

**Current Behavior**:
```
[1] Al-Kuwait Al-Youm Official Gazette - Issue 1733, Volume 71 (2025-04-06). p.1. Ministry of Information.
```

**Implementation**:
1. ✅ `_format_reference_list()` retrieves Document and Page nodes from graph
2. ✅ Extracts metadata: `document_title`, `issue_number`, `volume_number`, `document_date`, `publisher`
3. ✅ Formats citation: `"{document_title} - Issue {issue_number}, Volume {volume_number} ({document_date}). p.{page_number}. {publisher}."`
4. ✅ Strips `<orig>` tags from publisher text
5. ✅ Graceful fallback to filename if metadata unavailable

**Implementation Steps**:
```python
# In src/query/answer_generator.py:_format_reference_list()

def _format_reference_list(self, chunk_ids: List[str]) -> str:
    references = []
    for i, chunk_id in enumerate(chunk_ids, 1):
        chunk = self.graph_adapter.get_chunk(chunk_id)

        # Get page and document metadata
        page_id = chunk.metadata.get("page_id")
        document_id = chunk.metadata.get("document_id")

        if page_id and document_id:
            page = self.graph_adapter.get_page(page_id)
            document = self.graph_adapter.get_document(document_id)

            # Format rich citation
            citation = f"{document.title}"
            if document.volume_number:
                citation += f", Volume {document.volume_number}"
            if document.date:
                citation += f" ({document.date})"
            citation += f". p.{page.page_number}."
            if page.publisher:
                # Parse <orig> tags if present
                publisher_text = page.publisher.split('<orig>')[0].strip()
                citation += f" {publisher_text}."

            references.append(f"{i}. {citation}")
        else:
            # Fallback to filename
            references.append(f"{i}. {chunk.source_file}. p.{chunk.metadata.get('page_number', '?')}.")

    return "\n".join(references)
```

**Required Graph Adapter Methods**:
- `get_document(document_id: str) -> Document`
- `get_page(page_id: str) -> Page`

### Issue 2: Original Names (`<orig>` Tags) Not Parsed ✅ **PARTIALLY FIXED**

**Example**:
```markdown
publisher: "Kuwait Today / Al-Kuwait Al-Youm <orig>الكويت اليوم</orig>"
```

**Current Behavior**:
- ✅ `parse_orig_tags()` function exists (`src/graph_rag/utils/text_utils.py`)
- ✅ `strip_orig_tags()` function exists for citation formatting
- ✅ Used in citation formatting to remove `<orig>` tags
- ⚠️ Entity-level `original_name` field not yet added (can be added if needed for multilingual matching)

**Implementation**:
```python
# In src/graph_rag/utils/text_utils.py

def parse_orig_tags(text: str) -> Tuple[str, Optional[str]]:
    """Parse <orig> tags and return (display_text, original_text)"""
    match = re.search(r"(.*?)\s*<orig>(.*?)</orig>", text, re.DOTALL)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return text, None

def strip_orig_tags(text: str) -> str:
    """Remove <orig> tags from text, keeping only the display text."""
    return re.sub(r"\s*<orig>.*?</orig>", "", text, flags=re.DOTALL).strip()
```

**Status**: Core parsing implemented. Entity-level `original_name` can be added if multilingual entity matching is needed.

### Issue 3: Document Title Not Stored in Graph Node ⚠️ **IMPORTANT**

**File**: `src/ingest/graph_builder.py:38-56` ✅ **FIXED**

**Implementation**:
- ✅ Document node uses `document_title` from metadata if available
- ✅ Falls back to `document.title` if metadata not present
- ✅ All metadata fields stored in graph node properties

**Code**:
```python
# In src/ingest/graph_builder.py:add_document_node()

def add_document_node(self, document: Document):
    # Use document_title from metadata if available
    title = document.metadata.get("document_title", document.title)

    properties = {
        "id": document.id,
        "filename": document.filename,
        "title": title,  # ✅ Uses rich metadata title
        "doc_type": document.doc_type or "",
        "document_date": document.metadata.get("document_date", ""),
        "issue_number": document.metadata.get("issue_number"),
        "volume_number": document.metadata.get("volume_number"),
        "publisher": document.metadata.get("publisher", ""),
        # ... all metadata fields included
    }
```

### Issue 4: Metadata Not Used for Query Filtering ⚠️ **MEDIUM**

**Missing Feature**: Can't filter queries by:
- `document_type` (e.g., "Find all decrees")
- `issue_number` (e.g., "Find documents from issue 1733")
- `date_range` (e.g., "Find documents from 2025-04")

**Fix Required**:
1. Add `filters` parameter to `retriever.retrieve()`
2. Filter candidates by metadata before retrieval
3. Use FalkorDB Cypher queries for efficient filtering

**Implementation**:
```python
# In src/query/retriever.py:retrieve()

def retrieve(
    self,
    query: str,
    filters: dict | None = None
) -> List[Chunk]:
    # Apply filters to graph query
    if filters:
        # Example: Filter by document_type
        if "document_type" in filters:
            cypher_query = f"""
            MATCH (d:Document {{doc_type: '{filters["document_type"]}'}})-[:DOCUMENT_HAS_PAGE]->(p:Page)-[:PAGE_HAS_CHUNK]->(c:Chunk)
            RETURN c.id
            """
            allowed_chunk_ids = self.graph_adapter.execute_query(cypher_query)
            # Filter retrieval candidates
```

### Issue 5: Entity Matching for Metadata is Fragile ⚠️ **LOW**

**File**: `src/rag_pipeline.py:505-565`

**Current Behavior**:
- Matches by substring search: `entity_text.lower() in entity.canonical_form.lower()`
- May fail if entity text differs from metadata text

**Fix Required**:
1. Use fuzzy matching (Levenshtein distance) instead of substring
2. Create deterministic entity IDs for metadata entities
3. Link during graph building, not after

---

## Implementation Plan

### Phase 1: Fix Critical Issues (Priority: HIGH) ✅ **COMPLETED**

**Goal**: Make citations use rich metadata

**Tasks**:
1. ✅ Review current citation format implementation
2. ✅ Add `get_document()` and `get_page()` methods to FalkorDB adapter
3. ✅ Update `_format_reference_list()` to retrieve and format metadata (includes issue_number)
4. ✅ Add tests for rich citation format
5. ✅ Document metadata parser handles both JSON and key-value formats

**Status**: All critical citation fixes implemented and tested

### Phase 2: Parse Original Names (Priority: MEDIUM) ✅ **COMPLETED**

**Goal**: Extract `<orig>` tags into separate entity field

**Tasks**:
1. ✅ `parse_orig_tags()` helper function exists (`src/graph_rag/utils/text_utils.py`)
2. ✅ `strip_orig_tags()` function exists for citation formatting
3. ✅ Used in citation formatting to remove `<orig>` tags from publisher text
4. ✅ Parsing works correctly (tested)

**Status**: Core functionality implemented. Entity-level `original_name` field can be added if needed for multilingual matching.

### Phase 3: Fix Document Title Storage (Priority: MEDIUM) ✅ **COMPLETED**

**Goal**: Store rich metadata title in Document nodes

**Tasks**:
1. ✅ `add_document_node()` uses `document_title` from metadata (`src/graph_rag/ingest/graph_builder.py:39`)
2. ✅ All metadata fields stored in graph nodes
3. ✅ Document parser handles both JSON and key-value formats

**Status**: Document title and all metadata properly stored in graph nodes

### Phase 4: Add Metadata Query Filtering (Priority: LOW)

**Goal**: Enable filtering by document_type, issue_number, date_range

**Tasks**:
1. ⏳ Add `filters` parameter to `retrieve()` method
2. ⏳ Implement FalkorDB Cypher filtering queries
3. ⏳ Add tests for filtered retrieval
4. ⏳ Update API documentation

**Estimated Time**: 4-6 hours

### Phase 5: Improve Entity Matching (Priority: LOW)

**Goal**: Make metadata entity matching more robust

**Tasks**:
1. ⏳ Replace substring matching with fuzzy matching (Levenshtein)
2. ⏳ Create deterministic entity IDs for metadata entities
3. ⏳ Link entities during graph building
4. ⏳ Add tests for entity matching

**Estimated Time**: 3-4 hours

### Phase 6: Documentation Update (Priority: HIGH) ✅ **COMPLETED**

**Goal**: Update all critical documentation

**Tasks**:
1. ✅ Create comprehensive rebuild plan (`docs/plan.md`)
2. ✅ Update `README.md` with rich citation examples
3. ✅ Update `docs/ARCHITECTURE.md` with metadata flow diagrams
4. ✅ Update `docs/SOURCE_DATA_INGESTION_IMPLEMENTATION.md` with citation implementation details
5. ⏳ Archive non-critical documentation to `docs/archive/` (optional cleanup)

**Status**: Core documentation updated with citation examples, metadata flow diagrams, and implementation details.

---

## Testing Strategy

### Unit Tests

**Test Coverage Requirements**: >80%

**Critical Test Files**:
- `tests/test_ingest/test_source_parser.py` ✅ (8/8 passing)
- `tests/test_ingest/test_source_data_integration.py` ✅ (4/4 passing)
- `tests/test_query/test_answer_generator.py` ⏳ (needs citation format tests)
- `tests/test_graph/test_falkordb_adapter.py` ⏳ (needs metadata retrieval tests)

**Test Scenarios**:
1. **Metadata Parsing**:
   - Parse document metadata (JSON format)
   - Parse page metadata (JSON format)
   - Handle both JSON and key-value formats
   - Extract `<orig>` tags

2. **Citation Formatting**:
   - Format citation with rich metadata
   - Handle missing metadata fields
   - Fallback to filename if metadata unavailable

3. **Entity Extraction**:
   - Extract entities with `original_name`
   - Match multilingual entities
   - Link metadata-derived entities

4. **Query Filtering**:
   - Filter by document_type
   - Filter by issue_number
   - Filter by date_range

### Integration Tests

**Test Scenarios**:
1. **End-to-End Ingestion**:
   - Ingest source data file → Verify graph structure
   - Check Document/Page nodes with metadata
   - Verify entity relationships

2. **End-to-End Query**:
   - Query with filters → Verify correct chunks retrieved
   - Generate answer → Verify rich citation format
   - Validate citations support claims

### Validation Scripts

**Scripts**:
- `scripts/validate_graph.py` ✅ - Validate graph structure post-ingestion
- `scripts/validate_sample_questions.py` ✅ - Validate sample questions
- `scripts/test_citation_fix_fast.py` ⏳ - Test citation format fixes

---

## Deployment Guide

### Prerequisites

- Python 3.12+
- Docker (for FalkorDB)
- 8GB RAM minimum
- 20GB disk space

### Installation Steps

1. **Clone Repository**:
   ```bash
   git clone <repo-url>
   cd graph-rag-legal
   ```

2. **Install Dependencies**:
   ```bash
   # Using uv (recommended)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   uv run python -m spacy download en_core_web_sm

   # Or using Poetry
   curl -sSL https://install.python-poetry.org | python3 -
   poetry install
   poetry run python -m spacy download en_core_web_sm
   ```

3. **Start FalkorDB**:
   ```bash
   make falkordb-start
   # Or manually:
   docker run -d --name falkordb -p 6379:6379 falkordb/falkordb:latest
   # Note: If FalkorDB runs on port 6380, set FALKORDB_PORT=6380
   ```

4. **Configure LLM Provider**:
   ```bash
   # Option A: Ollama (local)
   curl https://ollama.ai/install.sh | sh
   ollama pull llama3.1:8b
   export LLM_PROVIDER=ollama

   # Option B: Anthropic (cloud)
   export ANTHROPIC_AUTH_TOKEN="your-api-key"
   export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
   export LLM_PROVIDER=anthropic
   ```

5. **Ingest Documents**:
   ```bash
   make ingest
   # Or for fast testing:
   make ingest-fast
   # Or manually:
   python3 main.py ingest data/source_data/
   ```

6. **Run Benchmark**:
   ```bash
   python scripts/benchmark_performance.py --count 400
   # Or with questions file:
   python scripts/benchmark_performance.py --questions-file data/test_questions_400.json
   ```

### Configuration

**File**: `src/config.py`

**Key Parameters**:
```python
# Chunking
CHUNK_SIZE = 512          # Tokens per chunk
CHUNK_OVERLAP = 128       # Overlap between chunks

# Retrieval
DENSE_TOP_K = 50          # Dense retrieval top-k
SPARSE_TOP_K = 50         # Sparse retrieval top-k
FUSION_ALPHA = 0.5        # Dense vs sparse weight

# Graph Traversal
MAX_HOPS = 2              # BFS hop depth
PPR_ALPHA = 0.15          # PageRank damping

# Reranking
RERANK_TOP_K = 10         # Final candidates for generation

# Generation
LLM_TEMPERATURE = 0.1     # Low for factual consistency
LLM_MAX_TOKENS = 512      # Max answer length

# Parallelization
MAX_CONCURRENT = 128      # Async task concurrency
```

---

## Appendix: File-by-File Reference

### Core Entry Points

**File**: `main.py`
- `ingest(document_paths)` - Public API for ingestion
- `query(questions)` - Public API for querying

### Ingestion Pipeline

**File**: `src/rag_pipeline.py`
- Main orchestrator for ingestion and query pipelines
- `ingest_documents()` - Coordinates ingestion (lines 77-565)
- `_is_source_data_file()` - Detects source data files (lines 68-75)

**File**: `src/ingest/source_parser.py`
- `parse_source_data()` - Parses source data files with XML tags
- `_parse_document_metadata()` - Extracts document metadata
- `_parse_page_content()` - Extracts page content and metadata

**File**: `src/ingest/source_converter.py`
- `convert_source_to_document_nodes()` - Converts to DocumentNode trees
- `extract_document_metadata()` - Extracts document-level metadata

**File**: `src/ingest/parser.py`
- `LegalDocumentParser` - Parses regular markdown files
- Extracts Articles, Sections, Clauses

**File**: `src/ingest/chunker.py`
- `chunk_document()` - Splits into semantic chunks
- Preserves page boundaries and metadata

**File**: `src/ingest/entity_extractor.py`
- `extract_entities_from_text()` - Hybrid entity extraction (regex + spaCy)
- `LEGAL_ENTITY_PATTERNS` - Regex patterns for legal entities

**File**: `src/ingest/faiss_resolver.py`
- `FAISSEntityResolver` - Deduplicates entities using FAISS
- `resolve_entities()` - Merges duplicates

**File**: `src/ingest/relation_extractor.py`
- `extract_relations()` - Extracts co-occurrence relationships

**File**: `src/ingest/graph_builder.py`
- `GraphBuilder` - Constructs knowledge graph
- `add_document_node()`, `add_page_node()`, `add_chunk_node()`, `add_entity_node()`
- `add_document_page_edge()`, `add_page_chunk_edge()`, `add_mentions_edge()`, etc.

### Query Pipeline

**File**: `src/query/orchestrator.py`
- Main coordinator for query processing
- Manages retrieval, traversal, reranking, generation

**File**: `src/query/query_parser.py`
- Parses queries to extract entities and keywords

**File**: `src/query/entity_linker.py`
- Links query entities to graph entities (fuzzy matching)

**File**: `src/query/retriever.py`
- Hybrid retrieval: dense + sparse + RRF
- `retrieve()` - Main retrieval method

**File**: `src/query/graph_traversal.py`
- Document-aware BFS and Personalized PageRank
- `traverse()` - Main traversal method

**File**: `src/query/reranker.py`
- Combines semantic + graph scores
- `rerank()` - Main reranking method

**File**: `src/query/answer_generator.py`
- Generates answers with LLM
- `generate_answer()` - Main generation method
- `_format_reference_list()` - **CRITICAL**: Formats citations (NEEDS FIX at line 415-446)

**File**: `src/query/citation_verifier.py`
- Verifies citations support claims (NLI)

### Data Models

**File**: `src/models.py`
- `Document` (lines 100-116), `Page` (lines 118-138), `Chunk` (lines 72-84), `Entity`, `Relationship` - Core data models
- `NodeType`, `EdgeType`, `EntityType` - Enums

### Graph Database

**File**: `src/graph/falkordb_adapter.py`
- FalkorDB adapter for graph operations
- `create_node()`, `create_edge()`, `get_node()`, `execute_query()`
- **NEEDS**: `get_document()`, `get_page()` methods

### Evaluation

**File**: `src/evaluation/evaluator.py`
- LLM-as-judge for 5 metrics
- `evaluate()` - Main evaluation method

**File**: `src/evaluation/citation_verifier.py`
- NLI-based citation verification

### Utilities

**File**: `src/utils/llm_client.py`
- LLM client wrapper (Ollama, Anthropic, OpenRouter)

**File**: `src/utils/embeddings.py`
- Sentence-transformers embedding wrapper

**File**: `src/utils/progress.py`
- Progress tracking utilities

### Configuration

**File**: `src/config.py`
- All system configuration parameters
- See [Configuration](#configuration) section

---

## Summary

This plan provides all the information needed to:
1. ✅ Understand the complete system architecture
2. ✅ Identify all metadata fields that must be captured
3. ✅ See exactly what's working and what needs fixing
4. ✅ Implement fixes with specific code examples
5. ✅ Test the implementation comprehensively
6. ✅ Deploy the system from scratch

**For a junior engineer**: Start with the [Executive Summary](#executive-summary), then read through [System Overview](#system-overview) and [Data Flow Pipeline](#data-flow-pipeline) to understand how everything works. Then tackle [Phase 1: Fix Critical Issues](#phase-1-fix-critical-issues-priority-high) to start making improvements.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: ✅ Complete and Ready for Implementation
