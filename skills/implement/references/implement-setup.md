# Implement — Setup Phase

Load context, create the team, and spin up the PM tracker and QA auditor. This phase completes before any workers are dispatched.

## Architecture

```
┌──────────────────────────────────────────────┐
│  Orchestrator (you)                          │
│  - Loads context, reads plans                │
│  - Creates team + tasks + dependencies       │
│  - Spins up PM tracker + QA auditor          │
│  - Dispatches workers (PM can't — flat       │
│    roster restriction)                       │
│  - Relays user testing gate results          │
│  - Phase transition approvals                │
└─────────┬────────────────────────────────────┘
          │ PM requests workers,
          │ you dispatch them
          ▼
┌──────────────────────────────────────────────┐
│  PM Tracker                                  │
│  - Owns ALL worker communication             │
│  - Plane PATCH across ALL projects           │
│    (orchestration + sub-projects)            │
│  - Daily note + work log updates              │
│  - Monitors workers, nudges idle ones        │
│  - Enforces user testing gates               │
│  - Reports phase completions to orchestrator │
└─────────┬──────────────┬─────────────────────┘
          │              │
          ▼              ▼
┌─────────────┐  ┌─────────────┐
│  Worker A   │  │  Worker B   │
│  Reports    │  │  Reports    │
│  to PM      │  │  to PM      │
└─────────────┘  └─────────────┘

┌──────────────────────────────────────────────┐
│  QA Auditor (independent — reports to lead)  │
│  - Runs after each phase completion          │
│  - Verifies git state (branches merged,      │
│    correct repos, no stashes)                │
│  - Verifies plan files match Plane state     │
│  - Checks VPS git cleanliness               │
│  - Validates quality gate criteria           │
│  - Verifies task acceptance criteria via      │
│    Playwright MCP (per-task, not just phase) │
│  - Flags issues to orchestrator              │
│  - READ-ONLY — never modifies files          │
└──────────────────────────────────────────────┘
```

## Key Design Decisions

Proven in Flora Migration Orchestration, 2026-03-20:
- **PM is event-driven, not polling** — workers message PM on status change, PM doesn't loop. Saves context tokens.
- **PM can't spawn workers** — flat roster restriction. Orchestrator dispatches, PM manages.
- **QA auditor is independent** — reports to orchestrator, not PM. Runs after each phase and on orchestrator request. Catches drift that PM misses because PM trusts worker self-reports.
- **Workers report to PM, not orchestrator** — orchestrator only hears about phase completions and gate requests.
- **Multi-project cascading** — when a plan spans multiple Plane projects (e.g., orchestration + sub-projects), the PM must update ALL relevant projects on every state change.
- **User testing gates** — any task that modifies a live service requires user manual testing before proceeding.

## Prerequisites

- **Reasoning level:** Spawned agents inherit the parent session's reasoning level. Before invoking `/implement`, ensure the session is running at **high reasoning** (`/model opus` or equivalent) — complex engineering workers need it. There is no per-agent reasoning override.

## Step 0 — Load Context

Before dispatching any work:

1. **Read the plan file** (`PL - *.md`) — understand phases, tasks, dependencies, risk register
2. **Find the Plane project(s)** — check the plan's metadata for project ID(s). If the plan is an orchestration plan spanning sub-plans, gather ALL project IDs.
3. **Query Plane states** — `GET /projects/{pid}/states/` for EACH project. Get fresh state IDs (never reuse from memory — they're per-project and can change).
4. **Read the spec** — linked in the plan's metadata, understand what "done" looks like
5. **Read project lessons** — project `lessons.md` + `agents.md` + `REF - Agent Lessons.md`. Lessons exist because past implementations hit these exact problems. Skipping them means hitting them again.
6. **Verify Plane project state** — query all issues across all projects, check which are already Done vs Todo vs Backlog. The plan may have been partially executed in a previous session.
7. **Build the issue mapping** — for orchestration plans, map each orchestration task to its sub-project issues.

Present a summary: "Plan has N phases, M total tasks. Phase 0 has K tasks ready. Plane project(s) at [URLs]. Ready to start?"

## Step 1 — Create Team and PM Tracker (HARD GATE)

**You MUST complete this step before dispatching ANY workers.** The PM tracker exists because orchestrators who also track inevitably skip the tracking when deep in dispatch.

### 1a. Create the Team

```
TeamCreate(team_name: "{plan-name}-{sprint}", description: "...")
```

### 1b. Spin Up the QA Auditor

Spawn the QA auditor as a teammate. Use the template from `references/auditor-prompts.md`, customized with:
- All repo paths (local + VPS) involved in this sprint
- Plane API details (same as PM gets)
- The plan file path

The auditor is **read-only** and reports to YOU (the orchestrator), not the PM. It runs checks after each phase completion and before session shutdown.

**QA auditor model:** Use `model: "sonnet"` — it's read-only research, not engineering.

### 1c. Create Tasks with Dependencies

For each phase/sprint task:
1. `TaskCreate` with clear description including Plane issue IDs
2. `TaskUpdate` with `addBlockedBy` for dependency chains

### 1d. Spin Up the PM Tracker

Spawn the PM tracker as a teammate. Use the template from `references/tracker-prompts.md`, customized with:

- All Plane project IDs and their state IDs
- The full task → issue mapping (orchestration AND sub-project issues)
- Multi-project cascading instructions
- User testing gate rules
- Worker management protocol

**The PM tracker's responsibilities:**
1. Workers report to PM (started, progress, blocked, completed)
2. On status change → PATCH ALL relevant Plane projects (never skip In Progress)
3. Add completed work to daily note
4. When worker completes → check TaskList for unblocked work → request orchestrator dispatch
5. Enforce user testing gates (tell worker to stop, escalate to orchestrator)
6. Proactively nudge idle workers for status updates

**PM model selection:** Use `model: "sonnet"` for the PM tracker — it's coordination work, not complex reasoning.

Wait for PM to confirm ready with verified issue mapping before proceeding.

---

Setup complete. Write routing manifest entry for 'setup'. Proceed to execute phase.
