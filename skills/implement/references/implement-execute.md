# Implement — Execute Phase

Dispatch workers, manage phases, enforce quality gates, and drive the sprint to completion. Assumes setup phase is complete (team exists, PM tracker and QA auditor are running).

## Step 2 — Execute Phases

### Audit-First Gate (P*.1 Tasks)

**For phases rated H or M risk in the plan's Phase Risk Ratings table:** No worker may start P*.2 or later until the P*.1 audit is complete and reviewed. This is a hard gate, not a suggestion.

**For phases rated L risk:** The audit-first gate is optional. Workers can proceed directly if the tasks are mechanical (file moves, CSS fixes, documentation). The orchestrator may still request an audit if something looks off.

When a P*.1 (audit) worker reports findings:
1. **PM relays findings to orchestrator** — not just "audit done" but the key findings summary
2. **Orchestrator reviews** — do the audit findings match the plan? Are there scope mismatches, missing data sources, architecture surprises?
3. **If discrepancies exist** — orchestrator resolves them (update the plan, issue a decision like D-17, or ask the user) BEFORE dispatching the P*.2 worker
4. **Only after audit findings are confirmed sensible** does the orchestrator dispatch the next worker

**Why this exists (Sprint 5):** P10 was the cleanest delivery because P10.1 was thorough. P12.1 caught that SSE streaming belonged to DocGen, not the live KB, before any code was written. Skipping the audit gate risks building against a wrong plan description.

### Dispatch Workers

When the PM requests a worker (or at sprint start for unblocked tasks):

1. **Choose the right model and reasoning level** for the worker:

| Task Type | Model | Reasoning | Why |
|-----------|-------|-----------|-----|
| Complex engineering (gateway, rewrites, new services) | `opus` | High (default) | Architecture, edge cases, deep chain-of-thought |
| VPS/infrastructure ops (deploys, migrations, separations) | `opus` | High (default) | Safety-critical, must follow procedures carefully |
| Multi-step tasks needing broad knowledge but not deep reasoning | `opus` | Medium | Opus knowledge without full reasoning overhead |
| File migration, scripting, mechanical work | `sonnet` | — | Fast, sufficient for template-following |
| Report writing, documentation | `sonnet` | — | Structured output, no deep reasoning needed |
| PM tracker (coordination, API calls) | `sonnet` | — | Coordination work, not complex reasoning |
| Quick lookups, status checks | `haiku` | — | Fastest, low-complexity |

Note: Only Opus supports reasoning level configuration. Sonnet and Haiku run at their default reasoning levels.

2. **Dispatch with standard template** from `references/worker-template.md`, customized with:
   - Task details from the plan
   - Context files to read (plan, spec, lessons, git-safe, VPS work rules if applicable)
   - **"Report ALL status updates to `pm-tracker`"** — NOT the team lead
   - Clear deliverables and validation criteria
   - `team_name` and `mode: "bypassPermissions"`

3. **Notify PM** — `SendMessage` to pm-tracker with worker name and task assignment

4. **Shut down completed workers** — send `shutdown_request` when they finish to free resources

### Multi-Project Cascading (CRITICAL)

When a plan spans multiple Plane projects (e.g., orchestration plan + sub-plans):

- When a task **starts** → PM PATCHes the orchestration issue AND all corresponding sub-project issues to In Progress
- When a task **completes** → PM PATCHes the orchestration issue AND all sub-project issues to Done
- Sub-project issues should go Backlog → In Progress → Done (skip Todo since work is actively starting)
- PM must batch PATCHes efficiently for phases with many sub-issues

### Parallel vs Sequential

Read the plan's dependency chains (`Deps` column in task tables):
- Tasks with no dependencies can run in parallel — dispatch together
- Tasks with deps must wait — only dispatch after their blockers complete
- When in doubt, run sequentially — parallel bugs are harder to debug than slow progress

### Incident Response

If a live service breaks during implementation, invoke `/troubleshoot` immediately. STOP all deploy work first.

## Step 3 — User Testing Gates

**Any task that modifies a live/running service requires user manual testing before being marked Done.** Workers cannot self-verify production behavior.

### When a Gate is Reached

1. PM tells the worker to **STOP and wait**
2. PM messages orchestrator: **"USER TEST GATE: {what to test, specific URLs/actions}"**
3. Orchestrator presents the test to the user via `AskUserQuestion` or direct message
4. User tests and reports results
5. Orchestrator relays pass/fail to PM
6. If pass → PM clears the worker to proceed
7. If fail → PM instructs worker to fix, then re-gates

### Standard Gates for Service-Touching Tasks

- **After deploying a service** → User loads the service URL, verifies it works
- **After modifying auth/proxy** → User tests sign-in flow end-to-end
- **After modifying a bot/assistant** → User sends a test message, verifies response
- **After building admin/dashboard pages** → User loads each page, confirms rendering
- **After DB migrations** → User tests a feature that queries the affected tables

### Playwright QA Verification and Per-Task QA

Before presenting a user testing gate, the QA auditor MUST run verification. See `references/implement-qa.md` for the full QA protocol including:
- Crawl-based audit (mandatory pre-gate)
- Static screenshot suite
- Per-task acceptance criteria verification
- Generator-evaluator separation principle

### Worker Context Management

Read `references/context-checkpoint.md` for the worker context checkpoint protocol — monitors for context pressure in long-running workers and handles fresh-worker handoffs.

### Deploy Protocol

For deploys, follow the zero-downtime protocol in `/vps-deploy`. Before first deploy, verify SDK versions per `/vps-deploy` checklist.

## Step 4 — Quality Gates

Quality gates (format: `QG-N`) are explicit work items in the plan, separate from user testing gates. They enforce validation between phases.

When all tasks in a phase are Done:

1. **Run the quality gate** — actually validate against spec acceptance criteria
2. **If passes** → run the code quality gate (see below)
3. **If fails** → document failure, create fix tasks, dispatch workers, re-run gate

### Code Quality Gate (Post-Phase)

After functional quality gates pass, mark QG Done, update Plane, announce to user, proceed to user test gate.

**Note:** Code quality review (`/simplify`) is deferred — the skill is not yet implemented. When available, it will be invoked here to catch cross-worker duplication and quality issues between functional QG and user test gate.

## Step 5 — Phase Transitions

Between phases:
1. Confirm with user before starting next phase (unless pre-approved)
2. Promote next phase's tasks from Backlog → Todo (only unblocked tasks)
3. Check if any new lessons were learned — offer `/learn`

## Step 6 — Completion

When all phases are Done and all gates passed:

1. **Update Plane milestones** — PATCH milestone issues to Done. Add `completed_date` to plan file frontmatter.
2. **Update Plane module** — PATCH status to `completed`, set `target_date` to today
3. **Update daily note** — add completion entry
4. **Retrospective + handoff** — invoke `/retro` (the `retro` skill). The retro now produces a single RET document that includes both the retrospective analysis AND the handoff section (carry-forwards, infra changes, Plane refs, task status). No separate HAN document needed.
   - Dispatches an audit agent, produces a structured report with handoff section, proposes concrete template changes with exact text, and applies them after user approval
   - See `~/.claude/skills/retro/SKILL.md` for the full three-phase process
5. **Shut down PM tracker**
6. **Delete team** — `TeamDelete` to clean up
7. **Summary** — tell the user what was built
8. **Offer next steps:** update spec, `/kb-doc`, `/learn`

### Before Session Shutdown (even if sprint is incomplete)

If the user ends the session or context is running low before the sprint finishes:

1. **Ask QA auditor for a final audit** — captures current state
2. **Generate retro with handoff** — invoke `/retro`. The RET document's handoff section captures carry-forwards, task status, and Plane refs. This is MANDATORY for partial sprints.
3. **Save the RET document** to the project's vault directory
4. **Shut down workers, PM, QA** — clean up team resources

## Role Boundaries — What Each Role Does NOT Do

Strict lane separation was a key success factor in Sprint 5. The risk is that shortcuts erode it over time (e.g., orchestrator starts doing PM work when PM is slow, PM starts dispatching workers). This table is the guardrail.

| Role | Does NOT do |
|------|-------------|
| **Orchestrator** | Plane API calls, direct worker management, code writing. Does not track per-task status — that's PM's job. |
| **PM Tracker** | Worker dispatch (flat roster restriction), code writing, architectural decisions, QA auditing. Does not bypass the orchestrator for phase transitions. |
| **QA Auditor** | File modifications, branch operations, Plane updates, worker communication. Read-only — observes and reports to orchestrator only. |
| **Workers** | Plane API calls, daily note updates, other workers' tasks. Reports only to PM, never to orchestrator directly. |

**If a role is slow or unresponsive**, the fix is to nudge/restart that role — not to absorb their work into your own. Absorbing work leads to context bloat and missed steps.

## What This Skill Does NOT Do

- Write code — workers do that
- Make architectural decisions without user input
- Skip quality gates or user testing gates
- Update Plane directly — only PM tracker does that
- Start a new phase without user confirmation (unless pre-approved)
- Modify the spec — specs are updated only after work is verified live

---

Execution complete. Write routing manifest entry for 'execute'.
