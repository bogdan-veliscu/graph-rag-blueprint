---
name: pwa-frontend-lite
description: Build lightweight HTMX/Lit PWA frontends aligned with the MVP playbooks, ensuring offline readiness and consistent UX patterns.
---

# PWA Frontend Lite

## When to Use
- Implementing web frontends for MVPs that rely on HTMX, Lit, or simple PWAs (adguild.io, leanvibe.ai, mumchef.io, etc.).

## Reference Material
- `complete-mvp-docs.md` sections per domain for UI flows and prompts (e.g., service workers).  
- `all-projects.md` quick reference for user journeys.  
- Domain policies for UX/legal copy (BabyBites safety messaging, CalmConnect anonymity, etc.).  
- `docs/10-build-process.md` delivery rhythm + testing expectations.

## Workflow
1. **Foundation**
   - Set up Vite/Lit or HTMX + Tailwind skeleton.  
   - Configure service worker (caching core assets + offline fallback).  
   - Ensure accessibility (ARIA, keyboard support) and responsive layout.

2. **Critical Flow Implementation**
   - Focus on the single happy-path journey described in `complete-mvp-docs.md`.  
   - Use HTMX for partial updates; keep DOM operations declarative.  
   - Integrate backend endpoints, handling optimistic UI and error messaging.

3. **State & Storage**
   - Use localStorage/IndexedDB for client caching where required (meal plans, workout routines).  
   - Mirror server schemas to simplify serialization and validation.

4. **Testing**
   - Add Playwright or Cypress smoke tests for the primary flow.  
   - Validate offline behavior (service worker) and fallback screens.  
   - Check compliance copy using domain policy files.

5. **Documentation**
   - Update domain `docs/PLAN.md` with completed UI tasks.  
   - Capture screenshots or GIFs for stakeholders.  
   - Log learnings + TODOs in `docs/progress.md`.

## Output Checklist
- [ ] Minimal, accessible UI covering core flow.  
- [ ] Offline-first service worker configured.  
- [ ] Tests and docs updated; cross-linked in living pyramid.  
- [ ] Compliance messaging present where required.
