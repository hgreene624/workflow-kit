---
name: implement
description: >-
  Execute or resume an implementation plan — dispatch teams, track progress in Plane, and
  update the plan file in real-time. Use this skill when the user has a ready plan
  (PL - *.md) and approved Plane project and wants to start building OR wants to resume
  a partially-complete implementation. Accepts a plan path, spec path, or Plane project
  URL/ID as entry point — evaluates current state and picks up where things left off.
  Also trigger on "implement this plan", "start working on this", "execute the plan",
  "let's build", "kick off implementation", "start phase 1", "pick up where we left off",
  "resume implementation", "continue building", "what's the status of the implementation",
  or when plan-spec has just finished and the user wants to proceed. This is the third step
  in the spec→plan→implement pipeline. Do NOT use this for creating plans (use plan-spec)
  or reviewing specs (use review-spec).
---

# Implement — Router

This skill is a **stateless router** that classifies the current state and loads the appropriate sub-skill. You never invoke sub-skills directly — this router handles dispatch.

**Arguments:** $ARGUMENTS — Path to plan file, spec file, or Plane project URL. Or nothing (will ask).

## Step 0.5 — Classify Complexity (L23)

Before classifying state, read the plan's frontmatter for the `complexity` and `ceremony` fields. These were set during `/plan-spec` based on the user's choices.

**Read the ceremony config:**
```yaml
ceremony:
  phases: true | false
  audit_gates: true | false
  smoke_tests: true | false
  qa_auditor: true | false
  user_testing_gates: true | false
  pm_tracker: true | false
```

**Apply ceremony selections:**

| Setting | If `false` | If `true` |
|---------|-----------|-----------|
| `pm_tracker` | You (orchestrator) manage workers directly. Workers report to you. Skip `implement-setup.md` PM section. | Spawn PM tracker per `implement-setup.md`. |
| `qa_auditor` | No QA agent. Skip auditor spawn. | Spawn QA auditor per `implement-setup.md`. |
| `audit_gates` | Workers start immediately when unblocked. No P*.1 audit-first requirement. | P*.1 audit must complete and be reviewed before P*.2 starts. |
| `user_testing_gates` | Workers self-verify. No gate escalation to user. | Deploy tasks require user manual testing before Done. |
| `smoke_tests` | No smoke test tasks in the plan. | Run smoke/integration tests after each phase. |
| `phases` | Flat task list — dispatch workers by dependency order, no phase transitions. | Phase-based execution with checkpoints between phases. |

**If the plan has no `ceremony` field** (legacy plans), infer from `complexity`:
- `light` → all ceremony off
- `standard` → phases + pm_tracker on, rest off unless plan has H/M risk phases
- `heavy` → all ceremony on

**If ALL ceremony is off** (typical for light plans): skip `implement-setup.md` entirely. Just read the plan, dispatch workers directly (one per deliverable), track completion yourself, and batch-update Plane when done. No routing manifest needed.

**If ANY ceremony is on**: continue to Step 1 below, but only spin up the agents/gates that are enabled.

## Step 1 — Classify State

Determine which sub-skill to load by checking these conditions in order:

1. **No plan identified?**
   - If no argument provided and no plan file is obvious from context → ask the user for the plan path via `AskUserQuestion`
   - If argument is a spec file → search for `PL - *.md` in the same directory. If none exists, suggest `/plan-spec` first.

2. **Resuming a partial implementation?**
   - Check: does a Plane project already exist for this plan? (check plan metadata for `plane_url`)
   - Check: are there issues in In Progress or Done state?
   - If yes → this is a **resume**. Load `references/implement-resume.md`.

3. **Fresh start?**
   - Plan exists, Plane project exists, but no issues are In Progress or Done (all Todo/Backlog)
   - → this is a **fresh start**. Load `references/implement-setup.md`.

4. **Active sprint (mid-execution)?**
   - Team already exists, PM tracker is running, work is in progress
   - → this is **continuing execution**. Load `references/implement-execute.md`.

## Step 2 — Write Routing Manifest

Before loading the sub-skill, follow the routing manifest protocol from `references/routing-manifest.md`:
- Write the manifest with the expected sub-skill chain (e.g., ["setup", "execute"] for fresh start, ["resume", "execute"] for resumption)
- The sub-skills will update the manifest as they complete

## Step 3 — Load and Follow Sub-Skill

Read the appropriate reference file and follow its instructions within this same context window. The sub-skill IS your instruction set — follow it completely.

| State | Sub-skill | What it does |
|-------|-----------|-------------|
| Fresh start | `references/implement-setup.md` | Load context, create team, spin up PM + QA, create tasks. Then auto-chain to execute. |
| Active sprint | `references/implement-execute.md` | Dispatch workers, manage phases, run gates, handle completion. |
| Resuming | `references/implement-resume.md` | Reconcile state from Plane + git, re-spin PM, then hand off to execute. |

**QA reference:** When execute needs QA verification details, read `references/implement-qa.md`.

**If a live service breaks during implementation:** STOP all work. Invoke `/troubleshoot` immediately.

## Sub-Skill Reference Files

All sub-skills live in `references/` alongside existing templates:

| File | Purpose | Instructions |
|------|---------|-------------|
| `implement-setup.md` | Team creation, context loading | ~22 |
| `implement-execute.md` | Phase execution, gates, completion | ~28 |
| `implement-qa.md` | Playwright audit, acceptance criteria | ~12 |
| `implement-resume.md` | State reconciliation, continuation | ~14 |
| `routing-manifest.md` | Manifest protocol (shared infra) | — |
| `context-checkpoint.md` | Worker context management | — |
| `worker-template.md` | Worker dispatch template | — |
| `auditor-prompts.md` | QA auditor template | — |
| `tracker-prompts.md` | PM tracker template | — |
| `handoff-template.md` | Handoff document template | — |
