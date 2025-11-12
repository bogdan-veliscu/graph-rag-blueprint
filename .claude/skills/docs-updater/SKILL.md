---
name: living-docs-updater
description: Propagate changes across the living documentation pyramid (Levels 0–3) to keep knowledge in sync after completing work.
---

# Living Docs Updater

## When to Use
- After delivering code or research that affects Level 0/1/2 summaries.
- When you notice outdated information across `docs/` or `knowledge/` hierarchies.

## Workflow
1. Identify the source of truth (project-level docs or knowledge repo).
2. Update Level 3 docs first (`{domain}/{idea}/docs/`), then bubble highlights to `docs/domains/` and `knowledge/domains/`.
3. Refresh Level 0 digest if portfolio priorities shift.
4. Check `knowledge/foundations/*` and `knowledge/projects/` for related synopses.
5. Record changes in `docs/progress.md` or relevant progress logs.
6. Use `docs-syncer` skill if the updates are mechanical; otherwise write tailored summaries.

## Guidelines
- Include timestamps (`last_updated`) when touching knowledge files.
- Keep cross-links accurate (relative paths preferred).
- If conflicting info exists, resolve or flag for human review.
