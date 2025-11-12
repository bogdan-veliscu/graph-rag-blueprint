---
name: human-review-checkpoint
description: Decide when to loop in a human reviewer by summarising impact, risk, and decision needs in an executive briefing format.
---

# Human Review Checkpoint

Use this skill whenever work touches ambiguous product calls, high-risk deployments, or stakeholder-sensitive outputs. It packages context like a C-suite briefing so humans can decide fast.

## When to Trigger
- Blocking uncertainty: Requirements unclear, conflicting goals, or missing approvals.
- High impact: Changes affecting revenue-critical flows, compliance posture, or investor deliverables.
- Elevated risk: Security/privacy implications, legal exposure, or irreversible data migrations.
- Cross-team dependency: Work that requires coordination with design, ops, or external partners.
- Quality flags: LLM output with low confidence, benchmark gaps, or manual reviewer overrides needed.

## Workflow
1. Load the latest context from Level 0–2 docs (`/skills load living-docs-consultant`) and relevant project docs.
2. Capture evidence: test results, metrics, scan findings, or LLM validation signals.
3. Apply the decision gates below; if any trigger, prepare a briefing.
4. Produce the executive summary format and highlight the ask.
5. Log the request in `docs/active-context.md` or the project progress log so the next agent sees the handoff.

### Decision Gates
- **Mission Alignment:** Does the work still serve the current portfolio priority? If uncertain, escalate.
- **Risk > Automation Threshold:** Would failure create legal, financial, or reputational damage beyond the automated rollback plan? Escalate.
- **Confidence Gap:** Are tests/LLM validations failing or unavailable? Escalate.
- **Stakeholder Impact:** Does the change affect investor/customer-facing deliverables due within 72 hours? Escalate.
- **Resource Conflict:** Does execution require budget, access, or policy changes outside agent authority? Escalate.

## Output Template
```
### Executive Summary
- Decision Needed: <clear yes/no or choice>
- Impact Window: <timeline / deadline>
- Primary Owner: <who should respond>

### Situation
- Context: <1-2 sentences referencing docs/ files with line numbers>
- Current Status: <tests, scans, blockers>

### Impact & Risk
- Business Impact: <revenue/compliance/customer effect>
- Risk Assessment: <likelihood + mitigation status>

### Recommendation
- Preferred Option: <what you recommend and why (focus on ROI)>
- Alternatives: <if applicable, bullet trade-offs>

### Attachments
- Evidence: <metrics/logs/paths>
- Next Checkpoint: <suggested follow-up time>
```

Keep the tone concise, decision-oriented, and free of jargon—assume an executive with limited time needs to act.
