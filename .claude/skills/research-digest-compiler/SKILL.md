---
name: research-digest-compiler
description: Summarize external research (Perplexity, Gemini, industry reports) into actionable insights and update living documentation.
---

# Research Digest Compiler

## When to Use
- New research responses arrive (Perplexity/Gemini).  
- Existing findings need refreshing or synthesising before a build sprint.  
- Product decisions require evidence summaries.

## Workflow
1. **Collect Sources**
   - Gather raw responses from `{domain}/{idea}/research/response.json` or external notes.  
   - If necessary, trigger new research via CLI (Perplexity or Gemini) before proceeding.

2. **Synthesis**
   - Distill key facts, metrics, and regulatory notes into bullet points.  
   - Cross-check for contradictions with current docs; flag discrepancies.

3. **Documentation Updates**
   - Insert summary into the idea’s `docs/project-brief.md` under Research section.  
   - Update `docs/PLAN.md` research status + execution queue if priorities change.  
   - Record activity in `docs/progress.md` and adjust `docs/active-context.md` next actions.

4. **Escalation**
   - If research exposes new compliance needs or product pivots, update Level 0 digest and domain snapshot.  
   - Recommend follow-up actions (e.g., legal review, pricing adjustments).

## Output Template
```
### Research Summary (Date)
- Topic:
- Sources:
- Findings:
  - ...
- Risks / Open Questions:
- Recommended Actions:
```
