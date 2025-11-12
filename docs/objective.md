# GraphRAG Developer Challenge - Legal Document Processing

## Project Overview

**Role:** Senior RAG Systems Developer (Contract/Freelance)
**Compensation:** $2,000 USD (paid only if >95% benchmark is achieved)
**Timeline:** 3-5 days from materials receipt to live demo
**Purpose:** Technical evaluation for potential long-term hire
**Scope:** Backend prototype only (no frontend/UI)
**Contact:** s.lilliu@revortis.com

## Objective

Build a high-accuracy GraphRAG prototype for legal document reasoning featuring:
- Explicit knowledge-graph construction and traversal
- Multi-hop reasoning
- Agentic orchestration
- Strong focus on retrieval accuracy and explainability

## Materials Provided

- `/docs/` - Pre-processed Markdown legal documents with metadata
- `/sample_questions.json` - Example question format
- `/sample_answers_rag.json` - Example answer format
- Benchmark uses unseen questions for evaluation

## Deliverables

Implement two Python 3.12 functions in a Poetry project:

```python
def ingest(document_paths: List[str]) -> None:
    """Ingest Markdown docs and build the knowledge graph."""

def query(questions: List[str]) -> List[str]:
    """Return answers with Vancouver-style citations grounded in retrieved sources."""
```

## Technical Requirements

- **Language:** Python 3.12
- **Package Manager:** uv (with pyproject.toml)
- **No UI:** Backend prototype only
- **No API Keys Provided:** Must work with local/open-source solutions
- **Stack Flexibility:** Any stack may be used
- **Parallel Execution:** `query()` must support processing ~400 questions in ≤60 minutes
- **Progress Indicator:** Required for query execution
- **Testing:** Thoroughly test for correctness and performance before demo

## Live Demo Format (60 minutes)

1. Receive ~400 unseen questions
2. Run `query()` to produce `/answers.json`
3. Explain architecture:
   - How the knowledge graph is built
   - How the graph is traversed
   - How grounded answers are generated

**Important:** Only the developer(s) who wrote the code may present.

## Evaluation Criteria

**Passing Score:** >95% overall

Measured by LLM-as-a-judge across four dimensions:

1. **Faithfulness** - Grounded in sources, no hallucinations
2. **Relevance** - Retrieval matches question intent
3. **Completeness** - Covers key legal points
4. **Clarity** - Structured, legally coherent writing

## Payment & Next Steps

**If Passed:**
- Receive $2,000 USD after verification
- Handover requirements:
  - Codebase
  - Poetry lock file
  - Run instructions
  - Brief technical note
- Top performers may be invited for long-term paid role interview

**If Failed:**
- No payment (developer keeps code)
- Failure conditions:
  - Score ≤95%
  - Cannot complete within 60 minutes

## Key Priorities

1. **Parallelization** - Handle ~400 questions efficiently
2. **Graph-based Reasoning** - True GraphRAG with knowledge graph
3. **Correctness** - Accurate, grounded answers
4. **Explainability** - Clear architecture and reasoning paths

## Note for Agencies

No pre-contract discussions with agencies. Communication proceeds only after a proposed developer passes the benchmark test. This ensures time efficiency and direct technical validation.

## Technical Focus Areas

### Must-Have Features
- Knowledge graph construction from legal documents
- Graph traversal for multi-hop reasoning
- Agentic orchestration for query processing
- Vancouver-style citation generation
- Parallel query processing with progress tracking

### Success Metrics
- >95% accuracy across all evaluation dimensions
- ≤60 minutes to process ~400 questions
- Reproducible results
- Clear, explainable architecture
