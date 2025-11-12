---
name: gemini-researcher
description: Run structured research using the Gemini CLI, capture findings, and store them in the knowledge base with citations and follow-up actions.
---

# Gemini Researcher

## When to Use
- Investigating blind spots, compliance considerations, or market intel for any MVP.
- Validating assumptions or gathering supporting evidence before updating plans.

## Workflow
1. Craft a focused prompt (include goals, deliverables, citation requirements).
2. Execute `gemini -p "your prompt" > knowledge/research/YYYY-MM-topic.md` (adjust filename as needed).
3. Review the output, extract key findings, and structure the markdown (Summary, Findings, Sources, Next Actions).
4. Link the new research note from relevant domain/project docs.
5. Update project plans/briefs if the research introduces new tasks or risks.

## Tips
- Always include sources with URLs and dates; note confidence levels when Gemini hedges.
- If output is lengthy, distill it into bullet-friendly sections before storage.
- Consider pairing with `research-digest-compiler` to broadcast insights across docs.
