---
name: create-spec
description: >-
  Create or update a spec document (SPC - *.md) with tiered depth — lightweight specs for simple
  work, full specs for complex systems. Redesigned based on Anthropic's agent research: match
  document complexity to work complexity. Use this skill when the user wants to create, write,
  draft, or update a spec — "spec this out", "turn this into a spec", "new spec for", "write a
  spec", "add this to the spec", "update the spec with", or describes a feature/system they want
  to formalize. Also trigger for "I have an idea for", "let's spec", or casual requests like
  "dad wants X, can we spec that?". Does NOT trigger for reviewing existing specs (use review-spec)
  or planning from specs (use create-plan).
---

# Spec Creator

Create specs with depth proportional to complexity. A config change doesn't need 11 sections. A multi-service platform does.

**Design principle:** The spec defines *what* to build and *why*. The plan defines *how* and *in what order*. If you're writing phases or task lists, stop — that's plan content.

## Entry

0. **Oracle check:** Read the project's PJL frontmatter for `oracles:`. If an oracle exists, query it: "What are the key design considerations, established patterns, and common pitfalls for building {spec subject}?" Surface the response as context before the interview using the standard proposition format. If no oracle exists, prompt: "This project has no oracle for domain grounding. Want to create one with `/oracle-create` before speccing?" If the user declines, proceed without. See [[SD - Oracle System]].
1. Orient: run `date`, read vault `AGENTS.md`, read project `agents.md` + `lessons.md` if they exist
2. Detect mode: interactive (user talking) or agent (programmatic invocation)
3. Route: creating new or updating existing? If ambiguous, check for existing specs in the project and ask.
   - **Update** → read `references/update-spec.md` and follow it
   - **Create** → continue below

## Classify Tier

Before interviewing, assess what the user described:

| Tier | Signals | Spec shape |
|------|---------|------------|
| **Brief** | Config change, skill file, single endpoint, tooling fix. <5 FRs expected. | 4 sections: Purpose, Scope, Requirements, Acceptance Criteria |
| **Standard** | Feature addition, service modification, API work. 5-20 FRs. | 8 sections: Purpose, Scope, FRs, NFRs, Constraints, Deliverables, SATs, Open Decisions |
| **Full** | New system, multi-service, platform feature, complex domain. 20+ FRs. | All 11 sections from `references/spec-template.md` |

Present your assessment: "This looks like a **{tier}** spec. I'll ask {N} questions then draft. Sound right?"

If the user wants more or less depth, adjust.

## Interview

Constraint-based, not fixed-question. Interview until you can confidently draft all sections for the tier.

**Brief tier (2-3 questions):**
- What is this and why?
- What does "done" look like?
- Anything explicitly out of scope?

**Standard tier (4-6 questions):**
- What and why?
- Success criteria?
- Scope boundaries (in/out)?
- Hard constraints?
- Walk the design tree for integration points and edge cases
- Confirm understanding (3-5 bullet summary)

**Full tier (6+ questions):**
- All of standard, plus:
- Deep-dive into entity boundaries, data flows, security model
- Research isolation for external system verification (see below)
- Open decisions with recommendations

One question at a time. Use AskUserQuestion for every question. If you can answer by reading the codebase, do that instead of asking.

## Research Isolation

For standard and full tiers, if you need to verify external systems (DB schemas, API endpoints, existing code patterns):

1. Generate specific factual questions
2. Dispatch a research agent with ONLY the questions — not the spec content or user's answers
3. Receive facts back and incorporate into draft

This prevents research bias. Skip for brief tier or when facts are already known.

## Draft

Read `references/spec-template.md` for the full template. For brief and standard tiers, include only the sections listed above.

**Drafting rules (all tiers):**
- Frontmatter: category, dates, status, project, source
- IDs on everything trackable (FR-1, NFR-1, SAT-1, A-1)
- No implementation phases or build order
- Open decisions must have recommendations
- Verify external references against actual systems

**File placement:**
- Existing project: `02_Projects/<project>/specs/{today}/SPC - {Name}.md`
- New project: create directory, spec at root of date subfolder
- Confirm path with user in interactive mode

Write the file. Log to daily note.

## Review Gate

Tiered review matching spec depth:

| Tier | Review |
|------|--------|
| **Brief** | Inline self-review: verify scope boundaries clear, SATs testable, no implementation leakage. 30 seconds. No agent dispatch. |
| **Standard** | Single review agent: reads spec + project context, flags issues, checks assumptions against codebase. 2-3 minutes. |
| **Full** | Invoke `/review-spec` — full 3-agent team (Scope Analyst, Context Researcher, Critical Reviewer). 5-10 minutes. |

For brief and standard: present findings inline and apply fixes. For full: let review-spec run its flow.

## Handoff

TLDR (3-5 bullets), then offer:
1. Run /create-plan now
2. More changes first

## Reference Files

| File | Purpose |
|------|---------|
| `references/spec-template.md` | Full 11-section template (same as v1) |
| `references/update-spec.md` | Update flow for existing specs |
