---
name: implement
description: >-
  Execute implementation plans with minimal ceremony — dispatch workers, track progress inline
  in the plan file. No external PM tools. Redesigned based on Anthropic's agent team research: default to the
  simplest pattern that works, replace agent-based QA with automated checks, eliminate PM relay.
  Use this skill when the user has a ready plan (PL - *.md) and wants to start building, resume
  a partial implementation, or when create-plan has just finished. Trigger on "implement", "build
  this", "start the plan", "kick off", "resume implementation", "let's go", "execute", or the
  user pointing at a plan file. Third step in the spec>plan>implement pipeline.
---

# Implement

Execute a plan by dispatching workers directly. You are the orchestrator — no PM tracker, no QA
auditor agent. Workers report to you. Quality comes from automated checks and live testing, not
agent-written reports.

**Design principles** (from Anthropic research):
- Start with the simplest pattern. Escalate only when measurement proves it necessary.
- Workers communicate via filesystem and git, not relay agents.
- A test harness that prints pass/fail beats a QA agent that writes 150-line reports.
- Audit gates only for irreversible operations (schema migrations, bulk emails, production deploys).

## Entry

**Arguments:** $ARGUMENTS — plan file path, spec path, or nothing (will ask).

1. If no plan provided, ask for the path via AskUserQuestion.
2. Read the plan frontmatter for `ceremony_tier`, `completed`, and `total`.
3. Read `references/tiers.md` to understand what the tier enables.
4. Determine state: fresh start (all tasks `todo`), resume (some `done`/`in-progress`), or complete.

## Ceremony Tiers

Plans set `ceremony_tier: light | standard | heavy` in frontmatter. Default is `light`.

| Tier | When | What's on | What's off |
|------|------|-----------|------------|
| **light** | UI, CRUD, config, docs, <15 tasks | Workers + smoke checks | Gates, audit agents |
| **standard** | Auth, schema migrations, production deploys | Workers + smoke checks + security eval + deploy gates | PM tracker, QA auditor agent |
| **heavy** | Multi-day, multi-team, infrastructure migrations | Everything from v1 | Nothing — full ceremony |

If the plan has no `ceremony_tier`, infer: <15 tasks with no DB/deploy = light. Auth or schema work = standard. Multi-service infrastructure = heavy.

**If tier is `heavy`:** load the original `/implement` skill instead. v2 handles light and standard only.

## Context Loading

Before dispatching work:

0. **Oracle check:** Read the project's PJL frontmatter for `oracles:`. If an oracle exists, note it for mid-build queries. When a worker hits a design choice not covered by the plan, query the oracle: "What's the recommended approach for {specific question}?" Surface to user: "Implementation question: {question}. Oracle recommends {approach} (source: {citation}). Proceed with this approach?" Never silently apply oracle recommendations. See [[SD - Oracle System]].
1. Read the plan, spec, project `CLAUDE.md` and `lessons.md`, and `REF - Agent Lessons.md`
2. **Read the Project Log** — If a PJL exists at `02_Projects/<project>/PJL - <Project Name>.md`, read the most recent 3–5 date sections. This is critical context for implementation:
   - **Decisions already made** — don't re-litigate what's in the PJL
   - **What was tried and failed** — don't repeat failed approaches
   - **Current deployment state** — know what's live before making changes
   - **Known issues** — avoid tripping over documented gotchas
   Pass relevant PJL context to workers when dispatching them. A worker building Phase 2 needs to know what Phase 1 discovered.
3. Check task statuses in the plan tables — which are `done`, `in-progress`, `todo`
4. Scan for activated lessons (L25 deploy != push, L27 environment declaration, L9 schema inspection)
5. Present summary: "Plan has N phases, M tasks ({completed} done, K ready). Tier: {tier}. Ready?"

## Environment Declaration ({{ORG}} apps only)

Before dispatching ANY {{ORG}} worker, determine and declare the environment: LOCAL, REMOTE, or BOTH.
If ambiguous, ask the user. Inject the declaration into every worker prompt. See `references/worker.md`.

## Dispatch

Create a team via TeamCreate. Dispatch workers directly — you manage them, no PM relay.

For each unblocked task or batch of independent tasks:

1. Choose model per `references/worker.md` model guide
2. Dispatch with the worker template, injecting: task details, context files, relevant checklists
3. Workers report completion to YOU with: what was done, commit hash, verification URL (if {{ORG}})
4. Update the plan file: set task Status to `done`, add Notes, append to Work Log, increment
   frontmatter `completed` count

**Parallel dispatch:** Tasks with no dependency on each other run in parallel. Tasks with deps wait.
When in doubt, run sequentially — parallel bugs cost more than slow progress.

## Quality: Smoke Checks (Not Audit Agents)

After each phase or deploy, run inline checks — not a separate agent. See `references/smoke-checks.md`.

- Build passes? (`pnpm --filter <app> build`)
- Key routes return expected status? (curl checks)
- No secrets or debug artifacts in diff? (grep)
- Schema migration has rollback? (check for down method)

Binary pass/fail. If fail, tell the worker what broke. No 150-line report.

## Quality: Security Eval (Standard Tier Only)

For auth/middleware code changes, run the focused eval from `references/security-eval.md`.
An LLM review of ONLY the auth diff against a checklist: session validation, error message leaks,
parameterized queries, CSRF, rate limiting. Skip for CRUD, UI, config.

## Gates

**Light tier:** No gates. Workers self-verify via smoke checks.

**Standard tier:** Gates only for:
- Schema migrations touching production data (review migration SQL before running)
- Production deploys (smoke check must pass before reporting "deployed")
- Bulk operations affecting real users (explicit user approval required)
- Auth/security code (security eval must pass)

Present gates to the user directly via AskUserQuestion. No PM relay.

## Phase Transitions

If plan has phases:
- **Default: chain directly to the next phase.** Don't ask "ready for Phase N?" when work is flowing
  and there's no blocker. The user will interrupt if they want to pause.
- **Stop and ask only when:** a gate requires user input (bulk operation approval, deploy to production
  with real users, design decision not covered by spec), or the previous phase had failures that
  change the plan.
- Update plan file with phase status at each transition.

## Completion

When all tasks are done:

1. Update plan frontmatter: `status: Complete`, `completed_date: today`, verify `completed` = `total`
2. Invoke `/log-work` with summary
4. Invoke `/retro` for retrospective + handoff
5. Delete team
6. Offer next steps: `/learn`, `/kb-doc`, spec update

## Partial Shutdown

If session ends before sprint finishes:

1. Update plan file with current progress (all in-progress tasks noted, frontmatter current)
2. Invoke `/retro` for handoff
4. Clean up team

## Reference Files

| File | Purpose | When to load |
|------|---------|-------------|
| `references/tiers.md` | Tier definitions and flag mappings | Always |
| `references/worker.md` | Worker dispatch template + model guide | When dispatching |
| `references/smoke-checks.md` | Automated pass/fail checks | After deploys/phases |
| `references/security-eval.md` | LLM auth code review prompt | Standard tier, auth changes |
| `references/checklists/deploy.md` | VPS deploy verification | Workers touching production |
| `references/checklists/frontend.md` | basePath, AG Grid, rendering | Frontend workers |
| `references/checklists/db.md` | Schema inspection, migration safety | DB workers |
