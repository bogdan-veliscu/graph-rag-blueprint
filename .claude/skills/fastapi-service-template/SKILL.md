---
name: fastapi-service-template
description: Scaffold and extend FastAPI backends following the standardized project structure, tooling, and quality gates defined in the living docs.
---

# FastAPI Service Template

## When to Use
- Creating or updating the FastAPI backend for any MVP.  
- Aligning a repo with the uv-based structure and patterns documented in `fastapi-backend-agent.md`.

## Reference Material
- `fastapi-backend-agent.md:1` (project layout, responsibilities).  
- `complete-mvp-docs.md` for domain-specific schemas/prompts.  
- `docs/10-build-process.md` for delivery rhythm and testing expectations.  
- Domain-specific policies and research (e.g., `babybit-es/.../policies.md`).

## Workflow
1. **Setup**
   - Generate directory skeleton per `fastapi-backend-agent.md` (app/, core/, api/v1, models, schemas, services, tests, Docker).  
   - Create `pyproject.toml` with uv, Python 3.11+, FastAPI, SQLAlchemy, Pydantic, pytest.  
   - Add `.env.example` including API keys, DB URL, feature flags.

2. **Domain Modelling**
   - Import schemas/Pydantic models from the idea pack or `complete-mvp-docs.md`.  
   - Align naming and validation to business rules captured in `project-brief.md`.

3. **Service Implementation**
   - Implement API routers grouped by feature (auth, assets, analytics, etc.).  
   - Keep controllers thin; push logic into `services/` with clearly typed functions.  
   - Integrate external APIs (LLM, Slack, GitHub) via dedicated service classes.

4. **Quality Gates**
   - Write pytest suites before/alongside implementation (`tests/`).  
   - Add async tests for DB and integration points using fixtures.  
   - Configure Docker Compose for local dev with Postgres or SQLite.  
   - Run lint/test hooks (optionally via Claude Code hooks) before handoff.

5. **Documentation**
   - Update `README` with setup commands (`uv sync`, `uv run uvicorn`).  
   - Log progress in `docs/progress.md` and adjust `docs/active-context.md` status.  
   - Surface any schema changes to frontend/mobile teams.

## Output Checklist
- [ ] Project conforms to documented layout.  
- [ ] API endpoints implemented with tests and validation.  
- [ ] Environment/config docs updated.  
- [ ] References added to living docs (Level 2 + Level 0 if milestone reached).
