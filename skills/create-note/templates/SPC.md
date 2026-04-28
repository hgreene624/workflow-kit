# SPC Template - Spec

## Frontmatter additions

```yaml
status: Draft
source: "[[related doc or request]]"
```

Tags: `[spec, <project-tag>]`

## Reference files

Read `references/spec-template.md` for the full 11-section template.
Read `references/update-spec.md` if updating an existing spec.

## Classify tier

Before interviewing, assess the scope:

| Tier | Signals | Sections |
|------|---------|----------|
| **Brief** | Config change, single endpoint, <5 FRs | Purpose, Scope, Requirements, Acceptance Criteria |
| **Standard** | Feature addition, 5-20 FRs | 8 sections: Purpose, Scope, FRs, NFRs, Constraints, Deliverables, SATs, Open Decisions |
| **Full** | New system, 20+ FRs | All 11 sections from spec-template.md |

Present assessment: "This looks like a **{tier}** spec. I'll ask {N} questions then draft."

## Interview

Constraint-based, not fixed-question. One question at a time via AskUserQuestion.

- **Brief (2-3 Qs):** What/why, done criteria, out of scope
- **Standard (4-6 Qs):** + success criteria, constraints, integration points
- **Full (6+ Qs):** + entity boundaries, data flows, security, research isolation

## Research isolation

For standard and full tiers, dispatch a research agent with ONLY the factual questions (not spec content or user answers) to verify DB schemas, APIs, existing patterns. Prevents research bias.

## Writing rules

- RFC-style keywords (MUST/SHOULD/MAY)
- One requirement per bullet, IDs on everything (FR-1, NFR-1, SAT-1)
- No implementation phases or build order (that's plan content)
- Open decisions must have recommendations

## Review gate

| Tier | Review |
|------|--------|
| Brief | Inline self-review (30 sec) |
| Standard | Single review agent (2-3 min) |
| Full | `/review-spec` full 3-agent team |

## Handoff

TLDR (3-5 bullets), then offer: run `/create-plan` now, or more changes first.
