---
name: repo-reviewer
description: Use repomix and Gemini CLI to review an MVP codebase, adapt output scope when the repo is large, and highlight gaps or next steps.
---

# Repo Reviewer

## When to Use
- Performing high-level audits of an MVP repo (architecture, docs, tests) before planning new work or handovers.
- Producing summaries for status updates or cross-checking implementation against plans.

## Workflow
1. Run `npx --yes repomix@latest --no-gitignore . > repomix-summary.txt` (from project root). If output is too large, rerun with `--include=path` filters (e.g., `app/**`, `docs/**`).
2. Execute `gemini -p "Review repomix-summary.txt focusing on ..." > knowledge/projects/<project>-review.md`.
3. Capture key findings: strengths, risks, missing tests/docs, recommended actions.
4. Update Level 0/1/2 docs if the review opens new tasks or shifts priorities.

## Tips
- Note any omitted directories and explain why (e.g., generated assets, vendor code).
- Keep reviews actionable (findings + suggested next step).
- Store the markdown in `knowledge/projects/` with date stamped title.
