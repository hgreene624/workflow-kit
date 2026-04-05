---
name: plan-spec
description: >
  Take a reviewed spec (SPC - *.md) and produce a full implementation plan document (PL - *.md),
  then sync it to Plane as a project with issues, modules, labels, and work items. Reads review
  artifacts from /review-spec if they exist (scope analysis, context brief, clarification log).
  Use this skill when the user wants to create a plan from a spec, turn a spec into actionable
  work items, create a Plane project from a spec, or says "plan this", "create a plan for this
  spec", "set up the Plane project", "make this actionable". Also trigger when the user has just
  finished /review-spec and wants to proceed to planning. This is the second half of the
  review-then-plan workflow — run /review-spec first if the spec hasn't been reviewed yet.
---

# Spec-to-Plan Skill

You produce two deliverables from a reviewed spec:
1. A **plan document** (`PL - *.md`) with phases, tasks, dependencies, and a decision log
2. A **Plane project** with modules, phase labels, and work items ready for execution

This is the second half of a two-skill workflow:
1. **`/review-spec`** — analyze, critique, get clarification (run first)
2. **`/plan-spec`** (this skill) — produce plan document + Plane project

## Invocation

```
/plan-spec <path-to-spec>
```

The spec path can be relative to the vault root or absolute. If no path is given, ask the user which spec to plan.

## Step 0 — Gather Inputs

1. **Read the spec** at `{spec_path}`
2. **Infer the project** from the spec's location:
   - `01_Work/03_Projects/<ProjectName>/` → that's your project
   - Check for sub-projects (e.g., `Flora Hub/`, `Inbox Triage/`, `Signal Engine/`)
3. **Check for review artifacts** — look for a `Reviews/` directory in the project folder, find the most recent date subfolder, and read:
   - `scope-analysis.md` — what the spec touches (from Scope Analyst)
   - `context-brief.md` — lessons, references, related work (from Context Researcher)
   - `spec-review.md` — critical evaluation and clarification log (from Critical Reviewer)

   If review artifacts exist, they are your primary input alongside the spec. The clarification log contains user decisions that must be reflected in the plan.

   If no review artifacts exist, warn the user: "This spec hasn't been reviewed yet. I recommend running `/review-spec` first to catch issues before planning. Proceed anyway?" If they say yes, do your best with the spec alone.

4. **Read project context:**
   - `agents.md` in the project directory (infrastructure, paths, constraints)
   - `lessons.md` in the project directory (what's gone wrong before)
   - The Plane Development Workflow at `Documentation/Agent Workflows/Plane Development Workflow.md` (project registry, API details, conventions)

## Step 0.5 — Classify Complexity (L23)

Before drafting, assess the work complexity to determine plan shape. This prevents over-engineering simple projects with heavyweight ceremony designed for production infrastructure.

**Check these signals:**

| Signal | Light | Standard | Heavy |
|--------|-------|----------|-------|
| Deliverables | Markdown, config, skill files | Code changes to existing services | New services, infrastructure, multi-service |
| Production systems touched | None | Existing service modified | VPS, Docker, Traefik, DB migrations |
| Estimated tasks | < 15 | 15–40 | 40+ |
| Deploy required | No | Single service | Multiple services |
| Risk to live users | None | Low–Medium | High |

**Classify as one of:**

- **Light** — skill/docs/config changes, no production systems, < 15 tasks. Examples: writing a new skill, updating vault templates, documentation projects.
- **Standard** — code changes to existing services, moderate risk, 15–40 tasks. Examples: adding a feature to an existing app, API endpoint additions, single-service refactors.
- **Heavy** — multi-service deploys, infrastructure changes, production risk, 40+ tasks. Examples: new service creation, database migrations, multi-app orchestration, service separations.

**Present your assessment to the user via `AskUserQuestion`:**

Show your classification with the evidence, then ask about ceremony preferences. Suggest defaults based on complexity — the user confirms or adjusts.

Example for a Light project:
> "This looks like a **light** project (skill files, no production systems, ~10 tasks). I'd suggest:"
> - Flat task list (no phases)
> - No audit gates
> - No smoke tests or QA gates
> - Direct worker dispatch (no PM tracker)

Use a multi-select `AskUserQuestion` so the user can opt into extras:

**Question:** "I classified this as **{complexity}**. Which ceremony do you want?"

Options (pre-selected based on complexity, user can toggle):
1. **Phased plan** — group tasks into phases with checkpoints _(default: off for Light, on for Standard/Heavy)_
2. **Audit gates** — require audit pass before starting phase work _(default: off for Light, on for H/M-risk phases in Standard/Heavy)_
3. **Smoke tests** — add smoke/integration test tasks after each phase _(default: off for Light, on for Standard/Heavy if deploys involved)_
4. **QA auditor** — spawn a read-only QA agent during implementation _(default: off for Light/Standard, on for Heavy)_
5. **User testing gates** — require manual user testing before marking deploy tasks done _(default: off for Light, on for Standard/Heavy if live services touched)_
6. **PM tracker** — spawn a coordination agent during implementation _(default: off for Light, on for Standard/Heavy)_

The user's selections override the defaults. Record the final choices in the plan frontmatter:

```yaml
complexity: light | standard | heavy
ceremony:
  phases: true | false
  audit_gates: true | false
  smoke_tests: true | false
  qa_auditor: true | false
  user_testing_gates: true | false
  pm_tracker: true | false
```

**Then draft the plan according to the selected ceremony.** If phases are off, use a flat task table. If audit gates are off, skip Phase Risk Ratings. If smoke tests are off, don't generate test tasks. This frontmatter is consumed by `/implement` to determine team composition and gate enforcement.

## Step 1 — Draft the Plan

Create the plan document in the same directory as the spec.

**Filename:** `PL - {spec_name_without_SPC_prefix} Implementation Plan.md`

**Structure:**

```markdown
---
category: Plan
date created: {today}
date modified: {today}
source: "[[{spec_filename}]]"
plane_url: ""
status: Draft — Pending Review
---

# {Project Name} — Implementation Plan

## Metadata

- **Source Spec:** [[{spec_filename}]]
- **Review:** [[Reviews/{date}/spec-review.md]] (if exists)
- **Repo:** {from agents.md}
- **VPS Path:** {from agents.md, if applicable}

## Pre-Implementation Review

{If review artifacts exist, embed the Summary Verdict and any unresolved Issues from spec-review.md here. This section ensures anyone reading the plan sees the reviewer's concerns upfront.}

## Progress Overview

_Last updated: {today}_

| Phase | Name | Tasks | Completed | Status | Last Completed |
|-------|------|-------|-----------|--------|----------------|
| Phase 0 | Prerequisites | N | 0 | Pending | — |
| Phase 1 | {name} | N | 0 | Pending | — |
| Phase 2 | {name} | N | 0 | Pending | — |
{etc.}

## Decision Log

| ID | Date | Decision | Rationale |
|----|------|----------|-----------|
| D-1 | {today} | {from clarification log or review} | {why} |
{etc.}

## Phase 0 — Prerequisites

**User-testable outcome:** {what the user can verify after this phase — e.g., "User can confirm DB migration succeeded and new columns appear"}
**Checkpoint:** {explicit conditions that must be true before Phase 1 starts}

| ID | Task | Description | Acceptance Criteria | Deps |
|----|------|-------------|---------------------|------|
| T0.1 | {task} | {details} | {measurable verification — e.g., "migration runs without error, \d table shows new columns"} | — |
| T0.2 | {task} | {details} | {measurable verification} | T0.1 |

## Phase 1 — {Feature Name}

**User-testable outcome:** {what the user can do NEW after this phase — a vertical slice, not a layer}
**Checkpoint:** {explicit conditions that must be true before Phase 2 starts}

| ID | Task | Description | Acceptance Criteria | Deps |
|----|------|-------------|---------------------|------|
| T1.1 | {task} | {details} | {measurable verification} | T0.2 |
{etc.}

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| {from scope analysis risk surface} | {H/M/L} | {H/M/L} | {action} |
{etc.}

## Phase Risk Ratings

| Phase | Risk Rating | Audit Gate |
|-------|-------------|------------|
| Phase 0 | {H/M/L} | {Required / Optional} |
| Phase 1 | {H/M/L} | {Required / Optional} |
{etc.}

_Risk Rating H/M = audit-first gate required (P*.1 audit task mandatory before P*.2). Risk Rating L = audit gate optional (workers can proceed directly if task is mechanical/low-risk)._
```

> **Note:** Status tracking lives in Plane. The plan file is a static reference document. Per-task status is never tracked in the plan — only the Progress Overview table is updated (at phase boundaries, not per-task).

> **Vertical Slice Verification:** For each phase, answer: _Can the user do something new?_ If no, restructure the phase until the answer is yes.

**Planning principles:**
- Phase 0 is always setup/prerequisites — schema migrations, config changes, dependency installs
- **Vertical slicing:** Each phase must deliver a user-testable outcome — a vertical slice of functionality, not a horizontal layer. No horizontal-only phases ("all DB changes", "all API routes", "all UI updates"). If a phase is inherently horizontal (e.g., initial schema migration), justify it explicitly.
- Phases should be deployable independently when possible — each phase should leave the system in a working state
- Tasks should be small enough to complete in one work session (< 2 hours of agent time)
- Dependency chains should be explicit — if T1.3 can't start until T1.1 is done, say so
- **Every task MUST have an Acceptance Criteria column** — a concrete, verifiable check that the QA auditor can run independently. Good: "curl /api/auth returns 200 with {token: ...}". Bad: "auth works". The criteria should be testable without reading the worker's code — ideally a command, URL check, or query.
- Incorporate gotchas from the review — if lessons say "always do X before Y", encode that as a dependency
- Decisions from the clarification log become entries in the Decision Log with rationale
- Risks from the scope analysis become entries in the Risk Register with mitigations
- **Never include soak periods, monitoring gates, or "run for N days/hours" tasks.** These create artificial wait states. The existing QA safety nets (admin issues, Chawdys, Daily Brief, crawl audits) provide continuous monitoring. If a spec references a monitoring period, convert it to a concrete validation task instead (e.g., "verify no errors in last 100 signals" not "run for 7 days").

## Step 2 — Show Plan to User

Before creating the Plane project, present the plan to the user for approval:

1. Summarize the plan: number of phases, total tasks, key dependencies, timeline shape
2. Highlight any decisions you made that weren't covered by the spec or review (these need user buy-in)
3. Use `AskUserQuestion` to confirm: "Plan has X phases and Y tasks. Ready to create the Plane project, or do you want to adjust anything first?"

If the user wants changes, apply them to the plan document and re-present.

## Step 3 — Sync to Plane (Auto-Chain)

Once the user approves the plan, read and follow the instructions in `references/plan-to-plane.md` to create the Plane project, modules, labels, and work items.

This step is auto-chained — do not ask the user whether to proceed. They already approved the plan; now execute the Plane sync.

## What This Skill Does NOT Do

- It does not review or critique the spec — that's `/review-spec`
- It does not implement the plan
- It does not start any work items — Phase 0 goes to Todo, **everything else goes to Backlog**. Only `/implement` promotes items to Todo when their phase starts.
- It does not push code or make infrastructure changes
- It does not create issues without phase-prefixed names — every issue name starts with `P{phase}.{number} —`

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
