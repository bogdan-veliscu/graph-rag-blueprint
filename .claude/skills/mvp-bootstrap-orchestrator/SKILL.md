---
name: mvp-bootstrap-orchestrator
description: Plan and kick off a new domain MVP by harvesting the living documentation pyramid, selecting the right playbooks, and producing a ready-to-execute backlog.
---

# MVP Bootstrap Orchestrator

## When to Use
- Starting work on any of the nine domain MVPs (adguild.io → neoforge.dev).  
- Preparing a kickoff brief for implementation agents.  
- Auditing that research, policies, and plans are aligned before coding.

## Workflow
1. **Load portfolio context**
   - Read `docs/00-portfolio-digest.md` for current priorities and blockers.  
   - Open the relevant domain snapshot in `docs/domains/`.  
   - Inspect the idea pack at `{domain}/{idea}/docs/` (especially `project-brief.md`, `PLAN.md`, `active-context.md`).

2. **Assemble execution plan**
   - Capture Phase 0 readiness tasks (research, compliance, tooling) from the idea’s `PLAN.md`.  
  - Enumerate Phase 1–3 tasks that must happen before feature work; include links to prompts or specs in `all-projects.md` / `complete-mvp-docs.md`.  
   - Note critical policies/playbooks that must be obeyed (e.g., `babybit-es/.../policies.md`, `calmconnect-io/.../moderator-playbook.md`).

3. **Produce kickoff output**
   - Draft a `docs/active-context.md` update summarising focus, next steps, and blockers.  
   - Generate a ticket-style backlog (bullets grouped by phase) referencing source files + line numbers.  
   - Recommend required Claude Code skills (from this repo) and any subagents to engage.

4. **Validation**
   - Confirm plan aligns with `PLAN.md` execution queue.  
   - Ensure research status is up to date; if not, queue `research-digest-compiler` skill.  
   - Check that compliance items are mapped for regulated domains (BabyBites, CalmConnect, CodeSwiftr).

## Output Template
```
## Kickoff Summary
- Domain / Idea:
- Current Status:
- Immediate Objectives (next 3 tasks):

## Phase Tasks
- Phase 0:
  - [ ] ...
- Phase 1:
  - [ ] ...
- Phase 2:
  - [ ] ...

## Dependencies & References
- Policies:
- Prompts/Specs:
- Research Artifacts:

## Recommended Tools/Skills
- ...
```
