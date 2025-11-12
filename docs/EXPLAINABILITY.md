# Explainability Feature

## Overview

The explainability feature provides detailed insights into how the GraphRAG system processes queries and generates answers. It tracks information at each step of the pipeline, including entity detection, retrieval scores, graph traversal, and timing.

## Configuration

Explainability is **disabled by default** and can be enabled via environment variables in your `.env` file:

```bash
# Enable explainability
EXPLAINABILITY_ENABLED=true

# Set explainability level: minimal, standard, or detailed
EXPLAINABILITY_LEVEL=standard

# Configure what to include (all default to true)
EXPLAINABILITY_INCLUDE_RETRIEVAL=true
EXPLAINABILITY_INCLUDE_GRAPH=true
EXPLAINABILITY_INCLUDE_ENTITIES=true
EXPLAINABILITY_INCLUDE_TIMING=true
EXPLAINABILITY_INCLUDE_SCORES=true
```

### Explainability Levels

1. **minimal**: Summary statistics only (counts of entities, chunks, etc.)
2. **standard**: Includes configured components with moderate detail
3. **detailed**: Full information including individual match scores and detailed breakdowns

## What Information is Collected

### Query Parsing
- Entities detected in the query
- Query type classification

### Entity Linking
- Query entities searched
- Entities linked to the graph
- Entity details (ID, text, type, canonical form)

### Retrieval
- Dense retrieval count and top matches
- Sparse retrieval count and top matches
- Fused retrieval count and top matches
- Individual match scores

### Graph Traversal
- Entities used for traversal
- Chunks before and after traversal
- Number of chunks added via graph
- Average and maximum graph scores

### Reranking
- Chunks before and after reranking
- Top matches with score breakdowns
- Semantic scores vs graph scores

### Answer Generation
- Number of chunks used in answer
- Number of citations generated
- Chunk IDs used

### Timing
- Total query processing time
- Time per pipeline step

## Output Format

When explainability is enabled, the output JSON includes an `explainability` field:

```json
{
  "answer": "The answer text...",
  "explainability": {
    "enabled": true,
    "level": "standard",
    "timing": {
      "total_time_seconds": 2.345,
      "step_timings": {
        "query_parsing": 0.001,
        "entity_linking": 0.012,
        "retrieval": 0.234,
        "graph_traversal": 0.456,
        "reranking": 0.023,
        "answer_generation": 1.619
      }
    },
    "entities": {
      "detected": ["Decree-Law", "No. 61"],
      "linked": [
        {
          "id": "entity_123",
          "text": "Decree-Law No. 61",
          "type": "LEGAL_TERM",
          "canonical_form": "Decree-Law No. 61"
        }
      ]
    },
    "retrieval": {
      "dense_count": 50,
      "sparse_count": 50,
      "fused_count": 60,
      "top_matches": [
        {
          "chunk_id": "chunk_456",
          "score": 0.9234
        }
      ]
    },
    "graph_traversal": {
      "chunks_added": 5,
      "avg_graph_score": 0.4567
    },
    "reranking": {
      "top_matches": [
        {
          "chunk_id": "chunk_456",
          "final_score": 0.8234,
          "semantic_score": 0.9234,
          "graph_score": 0.4567
        }
      ]
    }
  }
}
```

For `detailed` level, a human-readable `explainability_text` field is also included.

## Usage Examples

### Enable Explainability

```bash
# In .env file
EXPLAINABILITY_ENABLED=true
EXPLAINABILITY_LEVEL=standard
```

### Query with Explainability

```bash
make query Q="What is Decree-Law No. 61?"
```

The explainability summary will be printed to the console, and full details will be saved in `answers.json`.

### Programmatic Access

```python
from src.graph_rag.query.async_orchestrator import AsyncQueryOrchestrator

orchestrator = AsyncQueryOrchestrator()
result = await orchestrator.process_query_async("Your question")

if result.explainability:
    print(f"Entities detected: {result.explainability['summary']['entities_detected']}")
    print(f"Total time: {result.explainability['timing']['total_time_seconds']}s")
```

## Performance Impact

Explainability adds minimal overhead:
- **minimal**: ~1-2ms per query
- **standard**: ~2-5ms per query
- **detailed**: ~5-10ms per query

The overhead is primarily from data collection and formatting, not from the actual query processing.

## Use Cases

1. **Debugging**: Understand why certain chunks were retrieved or why entities weren't linked
2. **Performance Analysis**: Identify bottlenecks in the pipeline
3. **Quality Assurance**: Verify that the system is using relevant chunks and entities
4. **Research**: Analyze retrieval patterns and graph traversal effectiveness
5. **User Trust**: Provide transparency into how answers are generated

## Limitations

- Explainability is currently only available in **parallel query mode** (default)
- Sequential mode does not yet collect explainability data
- Some internal scores may not be available if components fail gracefully

## Future Enhancements

- Add explainability to sequential query mode
- Confidence scores for answers
- Visual explainability (graph visualization)
- Export explainability data in different formats (CSV, HTML)

