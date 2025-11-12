---
name: llm-prompt-guardrails
description: Design, validate, and instrument LLM prompts with JSON schemas, safety guidance, and logging for all MVPs.
---

# LLM Prompt Guardrails

## When to Use
- Creating or updating prompts for LLM-powered features (tagging, workout plans, compliance checks, diligence reports).  
- Ensuring outputs are validated and logged according to project standards.

## Reference Material
- Prompt templates in `complete-mvp-docs.md`, `all-projects.md`, and idea packs (`docs/project-brief.md`).  
- Validation patterns: Pydantic schemas in each MVP doc.  
- Logging + guardrails guidelines in `claude-prompts.md` and `docs/10-build-process.md`.

## Workflow
1. **Context Gathering**
   - Extract business requirements and constraints from domain docs.  
   - Identify sensitive content (medical, mental health, diligence) requiring tone + disclaimers.

2. **Prompt Authoring**
   - Follow structure: role → context → constraints → output schema.  
   - Include safety instructions (“not medical advice”, “respect privacy”), referencing policy docs when applicable.  
   - For iterative flows, detail system/assistant prompts plus developer notes.

3. **Validation**
   - Implement Pydantic models to enforce schema.  
   - Add unit tests with mocked LLM responses verifying schema compliance.  
   - Log prompt + response metadata (timestamp, request id) for auditing.

4. **Runtime Guardrails**
   - Set temperature, max tokens, and stop sequences appropriate to domain.  
   - Add retry/repair logic for invalid JSON.  
   - For high-risk outputs, add human-in-the-loop checkpoints.

5. **Documentation**
   - Update prompt sections within domain idea packs.  
   - Note changes in `docs/progress.md`; bubble major updates to `docs/20-reference-index.md` if reusable.  
   - Provide usage snippets (Python/TypeScript) for backend integration.

## Output Checklist
- [ ] Prompt text aligned with domain constraints + tone.  
- [ ] Validated via Pydantic tests.  
- [ ] Logging strategy defined.  
- [ ] Documentation updated with new prompt and schema references.
