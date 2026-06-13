# Pipeline Coordination

A self-contained Claude Code plugin for running multi-stream work across many sessions
without losing the thread. You install it once, run one setup skill, and end up with a
working coordination meta-plan, a first delegation handoff, and the three-role machinery
that keeps long-running work organized.

## What problem it solves

When work piles up across sessions (open pickups, half-built plans, parallel streams), you
lose track of what to do next and which pieces conflict. This plugin packages a proven
pattern for that: separate the *deciding* from the *doing* from the *checking*, and let a
lean written contract flow between them.

## The three roles (plain words)

- **Orchestrator** — the planner. It owns a single coordination meta-plan and never does
  the work itself. It reads current state, updates the status board, tells you what to spin
  up next, and answers coordinators' questions. You talk to it by picking up the meta-plan
  in a session.
- **Coordinator** — the runner. You hand it one *handoff* (a HAN) and it runs that one
  slice: breaks the work into pieces, spawns worker helpers, validates their output is
  actually correct, and reports lean progress back into the handoff. This is who you chat
  with while a slice is being built.
- **Worker** — the builder. The coordinator spawns workers to do the actual building. Each
  gets one bounded piece, builds it, and reports back with proof. Workers never certify
  their own work; the coordinator validates it.

The **handoff (HAN)** is the contract that flows between them: the orchestrator writes it,
the coordinator runs it and posts checkpoints, the orchestrator reads those checkpoints and
reconciles. Keep the handoff lean: it is a decision signal, not a work log.

## What ships in this bundle

| Component | What it is | Installs to |
|---|---|---|
| `meta-plan-init` (skill) | The front door: installer + onboarder + meta-plan builder + first-HAN drafter + launcher | `~/.claude/skills/meta-plan-init/` |
| `meta-coordinator` (skill) | The coordinator playbook (auto-invoked by `/pickup` on a delegation HAN) | `~/.claude/skills/meta-coordinator/` |
| `meta-orchestrator` (agent) | The planner agent profile, bound to a meta-plan PL | `~/.claude/agents/meta-orchestrator.md` |
| `meta-plan-worker` (agent) | The builder teammate profile spawned by a coordinator | `~/.claude/agents/meta-plan-worker.md` |
| `create-note.LOCAL.md` / `pickup.LOCAL.md` (overlays) | Handoff-handling behavior, dropped beside the host skills (never edits their bodies) | runtime, by `/meta-plan-init` |
| `coordination-pl.md` / `first-han.md` (templates) | The meta-plan and first-handoff templates the setup skill instantiates | bundled inside `meta-plan-init/` |

The overlays and templates ship *inside* `skills/meta-plan-init/` so the setup skill is
self-contained and runs on a clean machine before any other component is consulted. The
`meta-coordinator` skill ships `SKILL.md` only; its `LOCAL.md` is an installation-private
overlay you author for your own environment's specifics and is never distributed.

## Install

This bundle ships in the Workflow Kit. Install it the same way you install the kit:

```
/update-wfk pull
```

When the new bundle is detected you will be offered a single yes/no install for all
components. (A thin `/install-bundle pipeline-coordination` wrapper pre-answers yes.)

Then run the front door once, inside the project you want to coordinate:

```
/meta-plan-init
```

It scans your recent work, proposes a goal and a candidate work-pile, sorts the pile *with*
you, writes the coordination meta-plan and the first handoff, installs the two overlays,
teaches the three roles, and prints exact launch instructions.

### Launch, after init

1. **Run the orchestrator (plan / decide what's next):** open a session in the project and
   `/pickup PL - <Project> Meta-Plan Execution`. It loads as the orchestrator.
2. **Run the first slice (coordinator):** open a fresh session and `/pickup HAN - <Name>`.
   It routes to the coordinator playbook, which stands up workers and builds the slice.
   (Custom agent profiles load at session start, so use a fresh session.)
3. One work-doing session at a time on the critical path; up to two in parallel only if they
   are in different streams and share no files.

## Uninstall

Delete the two installed overlay files (`~/.claude/skills/create-note/LOCAL.md` and
`~/.claude/skills/pickup/LOCAL.md`) and the `## Local Customizations` footer in
`create-note/SKILL.md` if `/meta-plan-init` added it. Behavior reverts with no residue; the
upstream skill bodies were never edited.

## Customizing for your environment (optional)

The `meta-coordinator` skill loads an optional `LOCAL.md` from its own directory after its
generic instructions. Drop a `~/.claude/skills/meta-coordinator/LOCAL.md` to restate your
environment's concrete forms of the standing constraints (your deploy command, your
infrastructure rate limits, your runtime environments, your home/known-safe IPs). The public
bundle ships only the generic principles; your specifics stay private to your machine.

## Contributor note (symlink mode)

When editing the bundle source, symlink the bundle's skill/agent files into `~/.claude/` so
edits are live without reinstalling. The bundle source is the authority; `~/.claude/` copies
are the install target.

## Versioning

The bundle's `version` (see `bundle.json` / `CHANGELOG.md`) is independent of the Workflow
Kit's top-level version. This bundle is v1.0.0.

## Deferred to v1.1+

Not in this bundle (parked roadmap): auto-detectors (supersession / stale-premise), the
`/validate-artifact` N-agent review team, and the communication-contract release gate. See
`SD - Coordinated Pipeline Execution` and `SPC - Pipeline Coordination Toolkit` for the full
future-direction scope.
