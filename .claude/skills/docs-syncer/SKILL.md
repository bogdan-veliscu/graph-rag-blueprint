---
name: docs-syncer
description: Keep the living documentation pyramid synchronized by propagating changes across Levels 0–3 after any significant update.
---

# Docs Syncer

## When to Use
- After completing feature work, research, or policy updates.  
- Before handing off to another agent or closing a sprint.  
- Whenever new files should surface in Level 0/1/2 summaries.

## Workflow
1. **Identify Changes**
   - Review git diff for docs/ and `{domain}/{idea}/docs/`.  
   - Note new research, policies, or plan adjustments.

2. **Propagate Updates**
   - Update relevant domain snapshot in `docs/domains/`.  
   - Refresh `docs/00-portfolio-digest.md` if priorities/blockers changed.  
   - Add or modify entries in `docs/20-reference-index.md` for new resources.  
   - Ensure Level 1 guides (`docs/10-12`) include new process learnings if applicable.

3. **Log Progress**
   - Record summary in the idea’s `docs/progress.md`.  
   - Adjust `docs/active-context.md` next actions and status.  
   - If cross-cutting, add note to `PLAN.md` execution queue.

4. **Validation**
   - Confirm links/line references are accurate.  
   - Run spellcheck/formatting if hooks are configured.  
   - Commit with descriptive message (`docs: sync pyramid after XYZ`).

## Checklist
- [ ] Domain snapshot updated.  
- [ ] Portfolio digest reflects latest status.  
- [ ] Reference index entry added/edited.  
- [ ] Idea-level docs (plan, active-context, progress) updated.  
- [ ] Commit message and summary prepared.
