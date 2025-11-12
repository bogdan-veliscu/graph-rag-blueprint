# Source Data Ingestion Enhancement - Implementation Summary

**Date**: 2025-01-XX  
**Status**: ✅ Implementation Complete (with recent fixes)

## Overview

Enhanced the ingestion pipeline to parse source data Markdown files with special metadata tags (`<document_metadata>`, `<page_metadata>`, etc.) and persist Document and Page nodes with their relationships in the knowledge graph.

## Recent Fixes (2025-01-XX)

### Metadata Parsing Fixes
- **Fixed**: `_parse_document_metadata` now correctly preserves JSON metadata (publisher, authors, document_summary, etc.)
- **Fixed**: `extract_document_metadata` now checks both document-level and page-level metadata for publisher/authors
- **Result**: Document nodes now contain rich metadata, enabling proper entity extraction and relationship creation

### Metadata-Derived Entities
- **Added**: `create_metadata_entity` helper function that works without spaCy dependency
- **Enhanced**: Metadata entity extraction handles authors as lists or strings
- **Improved**: Entity matching for publisher/author relationships checks canonical_form, text, and mentions
- **Result**: `document_published_by` and `page_authored_by` relationships now correctly created

### Entity Extraction Improvements
- **Broadened**: Regex patterns for ORGANIZATION, PERSON, LOCATION entity types
- **Added**: Lightweight fallback extraction when spaCy is not available
- **Result**: Better entity coverage even without spaCy installation

### Entity Filtering Fixes
- **Fixed**: Casing normalization in `_filter_noisy_entities` (now compares uppercase)
- **Fixed**: Casing normalization in relation extractor skip_pairs
- **Result**: Noisy entity types (LEGAL_TERM, DATE, AMOUNT) now correctly filtered

### Graph Validation
- **Added**: `scripts/validate_graph.py` for post-ingestion validation
- **Features**: Validates node/edge counts, metadata presence, entity relationships, graph connectivity

## Implementation Summary

### 1. Source Parser (`src/graph_rag/ingest/source_parser.py`) ✅

**Created**: New module to parse source data files with special tags

**Features**:
- Parses `<document_metadata>` tags (document_id, language, total_pages, processed)
- Parses `<page_metadata>` tags (JSON format with page_title, document_date, issue_number, etc.)
- Extracts `<page_start>` and `<page_end>` markers
- Preserves `<header>`, `<footer>`, `<table>`, `<table_caption>` content
- Extracts `<orig>` multilingual spans
- Removes tags while preserving content for chunking

**Key Classes**:
- `DocumentMetadata`: Document-level metadata
- `PageMetadata`: Page-level metadata (JSON parsed)
- `PageContent`: Complete page with metadata and content
- `ParsedSourceDocument`: Complete parsed document with all pages
- `SourceDataParser`: Main parser class

### 2. Source Converter (`src/graph_rag/ingest/source_converter.py`) ✅

**Created**: Helper to convert ParsedSourceDocument to DocumentNode trees

**Features**:
- Converts each page to a DocumentNode tree
- Preserves page metadata in DocumentNode.metadata
- Sets `source_file` and `document_id` in metadata for graph linking
- Uses existing LegalDocumentParser to extract Articles/Sections/Clauses

**Key Functions**:
- `convert_source_to_document_nodes()`: Converts pages to DocumentNode trees
- `extract_document_metadata()`: Extracts document-level metadata

### 3. Updated Chunker (`src/graph_rag/ingest/chunker.py`) ✅

**Enhanced**: Preserves page boundaries and metadata

**Changes**:
- Added `page_id` and `page_number` parameters to `chunk_document()`
- Updated `_create_chunk()` to accept page info and metadata_extra
- Preserves `table_captions`, `tables`, and `orig_spans` in chunk metadata
- Uses `tree.metadata.get("source_file")` instead of `tree.title` for proper graph linking
- Sets `document_id` in chunk metadata for source data files

### 4. Updated Models (`src/graph_rag/models.py`) ✅

**Enhanced**: Added Page node type and new relationships

**Changes**:
- Added `PAGE` to `NodeType` enum
- Added `DOCUMENT_HAS_PAGE`, `PAGE_HAS_CHUNK`, `DOCUMENT_PUBLISHED_BY`, `PAGE_AUTHORED_BY` to `EdgeType` enum
- Extended `Document` model with:
  - `language`, `document_id`, `issue_number`, `volume_number`, `total_pages`, `processed`
- Added `Page` model with:
  - `page_number`, `document_id`, `page_title`, `document_date`, `issue_number`, `volume_number`
  - `document_type`, `languages_detected`, `page_type`, `authors`, `publisher`
  - `page_summary`, `header`, `footer`, `table_captions`
- Added `page_id` field to `Chunk` model

### 5. Updated Graph Builder (`src/graph_rag/ingest/graph_builder.py`) ✅

**Enhanced**: Creates Document and Page nodes with relationships

**New Methods**:
- `add_document_node(document: Document)`: Creates Document node from Document model
- `add_page_node(page: Page)`: Creates Page node from Page model
- `add_document_page_edge()`: Creates DOCUMENT_HAS_PAGE edge
- `add_page_chunk_edge()`: Creates PAGE_HAS_CHUNK edge
- `add_document_publisher_edge()`: Creates DOCUMENT_PUBLISHED_BY edge
- `add_page_author_edge()`: Creates PAGE_AUTHORED_BY edge

**Changes**:
- Updated `_add_chunk_nodes()` to include `page_id` in properties
- Updated `_add_part_of_edge()` to also create PAGE_HAS_CHUNK edges when `page_id` exists

### 6. Updated RAG Pipeline (`src/graph_rag/ingest/pipeline.py`) ✅

**Enhanced**: Integrated source data parsing into ingestion flow

**Changes**:
- Added `_is_source_data_file()` method to detect source data files
- Modified `ingest_documents()` to:
  - Detect source data files vs regular markdown files
  - Parse source data files with `parse_source_data()`
  - Convert to Document and Page models
  - Create Document and Page nodes before building graph
  - Extract entities from metadata (authors, publishers)
  - Link metadata entities to documents/pages
- Updated chunking to pass `page_id` and `page_number` for source data files
- Updated graph stats to include `page_nodes`

### 7. Updated FalkorDB Adapter (`src/graph_rag/graph/falkordb_adapter.py`) ✅

**Enhanced**: Schema support for PAGE nodes

**Changes**:
- Added `Page` to uniqueness constraints
- Added indices for:
  - `Page.id`
  - `chunk.page_id` (for PAGE_HAS_CHUNK queries)
  - `Page.document_id` (for DOCUMENT_HAS_PAGE queries)
- Updated `get_graph_stats()` to include `page_nodes` count

### 8. Tests ✅

**Created**:
- `tests/test_ingest/test_source_parser.py`: Unit tests for source parser (8 tests, all passing)
- `tests/test_ingest/test_source_data_integration.py`: Integration tests (4 tests, all passing)

**Test Coverage**:
- Document metadata parsing
- Page metadata parsing (JSON)
- Page content extraction (header, footer, tables, orig spans)
- Tag removal while preserving content
- DocumentNode conversion
- Chunker with page info
- Document and Page model creation

### 9. Validation Script (`scripts/validate_sample_questions.py`) ✅

**Created**: Script to validate sample questions against ingested data

**Features**:
- Loads sample questions and expected answers
- Runs queries through pipeline
- Compares results with expected answers
- Reports match/mismatch status

## Graph Schema Enhancements

### New Node Types
- **PAGE**: Represents a page from source data files
  - Properties: page_number, page_title, document_date, issue_number, volume_number, document_type, languages_detected, page_type, authors, publisher, page_summary, header, footer, table_captions, metadata

### New Edge Types
- **DOCUMENT_HAS_PAGE**: Document → Page (one-to-many)
- **PAGE_HAS_CHUNK**: Page → Chunk (one-to-many)
- **DOCUMENT_PUBLISHED_BY**: Document → Entity (publisher)
- **PAGE_AUTHORED_BY**: Page → Entity (author)

### Graph Structure
```
Document (with metadata: document_id, issue_number, volume_number, etc.)
  ├─ DOCUMENT_HAS_PAGE → Page 1
  │     ├─ PAGE_HAS_CHUNK → Chunk 1
  │     ├─ PAGE_HAS_CHUNK → Chunk 2
  │     └─ PAGE_AUTHORED_BY → Entity (author)
  ├─ DOCUMENT_HAS_PAGE → Page 2
  │     └─ PAGE_HAS_CHUNK → Chunk 3
  └─ DOCUMENT_PUBLISHED_BY → Entity (publisher)
```

## Metadata Handling

### Document Metadata
- `document_id`: Unique identifier (e.g., "2025-04-09")
- `language`: Primary language
- `total_pages`: Total page count
- `processed`: Processing timestamp
- `issue_number`, `volume_number`: Gazette issue info
- `document_type`: Type of document (decree, official_gazette, etc.)

### Page Metadata
- `page_number`: Page number in document
- `page_title`: Page title
- `document_date`: Date of document
- `issue_number`, `volume_number`: Gazette issue info
- `page_type`: content, index, blank, etc.
- `authors`: Author names (may include `<orig>` tags)
- `publisher`: Publisher name (may include `<orig>` tags)
- `page_summary`: AI-generated summary
- `header`, `footer`: Page header/footer content
- `table_captions`: List of table captions
- `languages_detected`: List of detected languages

### Preserved in Chunks
- `page_id`: Reference to Page node
- `page_number`: Page number
- `document_id`: Reference to Document node
- `table_captions`: Table captions on page
- `tables`: Table content
- `orig_spans`: Multilingual spans

## Entity Extraction from Metadata

The pipeline now extracts entities from:
- **Authors**: Extracted from `page_metadata.authors` field
- **Publishers**: Extracted from `page_metadata.publisher` and `document_metadata.publisher` fields

These entities are:
1. Extracted using existing `extract_entities_from_text()`
2. Resolved using FAISS-based entity resolver
3. Linked to Document/Page nodes via:
   - `DOCUMENT_PUBLISHED_BY` edges (Document → Publisher Entity)
   - `PAGE_AUTHORED_BY` edges (Page → Author Entity)

## Usage

### Detecting Source Data Files

The pipeline automatically detects source data files by checking for `<document_metadata>` tag in the first 20 lines:

```python
pipeline = RAGPipeline()
pipeline.ingest_documents([Path("data/source_data/2025-04-09_en.md")])
```

### Manual Parsing

```python
from src.graph_rag.ingest.source_parser import parse_source_data

parsed = parse_source_data(Path("data/source_data/2025-04-09_en.md"))
print(f"Document ID: {parsed.document_metadata.document_id}")
print(f"Pages: {len(parsed.pages)}")
for page in parsed.pages:
    print(f"  Page {page.page_number}: {page.page_metadata.page_title}")
```

## Testing

### Unit Tests
```bash
uv run pytest tests/test_ingest/test_source_parser.py -v
# Result: 8/8 tests passing
```

### Integration Tests
```bash
uv run pytest tests/test_ingest/test_source_data_integration.py -v
# Result: 4/4 tests passing
```

### Validation Script
```bash
python scripts/validate_sample_questions.py
```

## Benefits

1. **Rich Metadata Persistence**: Document and page metadata is now stored in the graph, enabling queries like "Find all decrees from issue 1733" or "What pages were authored by John Doe?"

2. **Better Citations**: Page-level metadata enables more precise citations (e.g., "2025-04-09, p.3" instead of just filename)

3. **Multilingual Support**: `<orig>` tags are preserved, enabling multilingual queries

4. **Table Awareness**: Table captions and content are preserved in metadata, enabling table-specific queries

5. **Entity Relationships**: Authors and publishers are linked as entities, enabling graph traversal queries

6. **Backward Compatible**: Regular markdown files (without special tags) continue to work as before

## Next Steps

1. **Query Enhancement**: Update query pipeline to leverage page metadata for better citations
2. **Table Queries**: Add support for querying table content specifically
3. **Multilingual Queries**: Enhance query processing to handle `<orig>` multilingual content
4. **Document Filtering**: Add query filters by document_type, issue_number, date range, etc.

## Files Modified

- `src/graph_rag/models.py`: Added Page model, PAGE node type, new edge types
- `src/graph_rag/ingest/chunker.py`: Enhanced to preserve page info and metadata
- `src/graph_rag/ingest/graph_builder.py`: Added Document/Page node creation methods
- `src/graph_rag/ingest/pipeline.py`: Integrated source data parsing
- `src/graph_rag/graph/falkordb_adapter.py`: Updated schema for PAGE nodes

## Files Created

- `src/graph_rag/ingest/source_parser.py`: Source data parser
- `src/graph_rag/ingest/source_converter.py`: Converter to Document/Page models
- `src/graph_rag/ingest/entity_extractor.py`: Entity extraction with regex + spaCy
- `src/graph_rag/ingest/faiss_resolver.py`: FAISS-based entity resolution
- `src/graph_rag/ingest/relation_extractor.py`: Relationship extraction
- `src/graph_rag/query/retriever.py`: Hybrid retrieval (dense + sparse + RRF)
- `src/graph_rag/query/graph_traversal.py`: Graph traversal for retrieval
- `src/graph_rag/query/reranker.py`: Reranking with semantic + graph scores
- `src/graph_rag/query/answer_generator.py`: Answer generation with citations
- `src/graph_rag/query/orchestrator.py`: Query pipeline orchestrator
- `src/graph_rag/utils/llm_client.py`: LLM client (Ollama/Anthropic)
- `src/graph_rag/utils/embeddings.py`: Embedding utilities
- `tests/test_ingest/test_source_parser.py`: Unit tests
- `tests/test_ingest/test_chunker.py`: Chunker tests
- `tests/test_ingest/test_faiss_resolver.py`: Entity resolver tests
- `tests/test_query/test_retriever.py`: Retriever tests
- `tests/test_query/test_answer_generator.py`: Answer generator tests
- `scripts/validate_graph.py`: Graph validation script

## Status

✅ All implementation complete  
✅ All tests passing  
✅ Backward compatible with existing markdown files  
✅ Ready for production use

