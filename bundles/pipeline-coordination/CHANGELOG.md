# Changelog — pipeline-coordination

This bundle's version is independent of the Workflow Kit's top-level version.

## 1.0.0 — 2026-05-28

Initial self-contained bundle of the Coordinated Pipeline Execution delegation layer.

### Added
- `meta-plan-init` skill: the guided front door (installer + onboarder + meta-plan builder
  + first-HAN drafter + launcher). Messy-work-adopt is the primary path; clean-start is the
  degenerate case. Ships its own `templates/` (coordination-pl, first-han) and `overlays/`
  (create-note, pickup) so it runs on a clean machine.
- `meta-coordinator` skill: the coordinator playbook, auto-invoked by `/pickup` on a
  delegation HAN. Ships `SKILL.md` only; `LOCAL.md` is an installation-private overlay.
- `meta-orchestrator` agent: the planner profile bound to a coordination meta-plan PL.
- `meta-plan-worker` agent: the builder teammate profile a coordinator spawns. Its `tools:`
  list intentionally retains `SendMessage` / `TaskUpdate` / `TaskOutput` (required for the
  lead-worker reporting handshake).
- Handoff-handling overlays for `create-note` (HAN type + template + routing) and `pickup`
  (HAN detection + delegation-vs-transfer classification + coordinator routing), installed
  as `LOCAL.md` files beside the host skills, never as body edits.

### Notes
- Fully generalized: zero environment-specific identifiers in any shipped file. Operators
  add their own specifics via the optional `meta-coordinator/LOCAL.md` overlay.
- Supersedes a prior `pipeline-coordination` v0.1.0 plugin that carried only the
  orchestrator agent + a starter template, predating the coordinator/worker/handoff layer.

### Deferred to v1.1+
- Auto-detectors (supersession candidate-surfacing, stale-premise diffing).
- `/validate-artifact` N-agent review team.
- Communication-contract release gate.
