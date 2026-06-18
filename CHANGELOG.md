---
date created: 2026-04-11
tags: [reference, changelog]
category: Reference
---

# Workflow Kit Changelog

## v3.8.0 - 2026-06-10

### What this release is about
The oracle system is rebuilt from the ground up. The three-skill oracle family (`oracle-create` / `oracle-research` / `oracle-ask`) is retired and replaced by a single `/oracle` skill backed by a deterministic curation pipeline. The redesign exists because an audit found roughly half the "sources" in oracles built with the old skills were teasers — landing pages, tables of contents, paywall stubs — not real content. The new pipeline makes that structurally impossible.

### New skills
**`oracle`** — one skill with four commands: `build` (stand up a new oracle through an 8-question Grounding Brief and a gated curation pipeline), `research`/`expand` (add sources through the same gate), `ask` (grounded query that returns a cited proposition), and `audit`/`revalidate` (verify an oracle still matches its corpus). Every source must pass a hard full-text gate — teasers and stubs are rejected with logged reasons — then an A-F composite quality score with perspective-balance checks. Note: `build`/`research`/`audit` require the separate `oracle-forge` CLI; **`ask` works standalone** with just the `nlm` CLI, so inline callers degrade gracefully.

### What got better
- **create-note, grill, implement** — their inline oracle hooks now route through `/oracle ask`, which resolves the right oracle at runtime, returns a cited proposition, and never blocks the calling skill on any failure. Behavior at the call site is unchanged; the grounding behind it is verifiably full-text.
- **landscape-survey** — its oracle-research step points at the new commands.

### What you need to do
Nothing manual. `update-wfk pull` removes the three retired skills (any LOCAL.md you added to them is preserved) and installs `/oracle`. References to the old slash commands map as: `/oracle-create` → `/oracle build`, `/oracle-research` → `/oracle research`, `/oracle-ask` → `/oracle ask`.

### Migration
Pull handles skill removal, rename mapping, and stale-reference detection automatically via the kit manifest.


What changed, what it means for you, and what to watch for. The `/update-wfk pull` action reads this file to show you what's new.

---

## v3.7.4 - 2026-05-28

### What this release is about

Small polish on v3.7.2's three-check sweep. The local-process check was correctly catching cross-session orphan workers, but it was ALSO catching the operator's own concurrent interactive Claude sessions (a user driving multiple tmux panes), then prompting "active concurrent sessions or orphans?" every single orient. That prompt fired every time a user with more than one Claude session ran `/orient`, even though those sessions carry no orphan-worker risk by construction (no agent is auto-dispatching shell/SSH from an interactive teammate-mode pane).

### What got better

- **`/orient` Step 1c's local-process check now excludes `--teammate-mode tmux` sessions.** Those are user-driven interactive Claude sessions in tmux panes; they don't carry the cross-session orphan-worker risk the sweep is designed to catch. A separate `INFO` line reports the count of concurrent interactive sessions so they're visible but never escalate to a question. The sweep's actual matches (real `--team-name` workers, background `--dangerously-skip-permissions` processes not in teammate-mode) still surface for operator triage exactly as before. Net effect: users with multiple concurrent Claude sessions get a clean orient instead of an unnecessary triage prompt every time.

### What you need to do

Nothing. `update-wfk pull` replaces `SKILL.md` cleanly.

---

## v3.7.3 - 2026-05-27

### What this release is about

Tiny polish on v3.7.2's new orient sweep. The no-tmux branch was listing the intentional `_archive/` subdirectory under `~/.claude/teams/` as a `STALE-TEAM-DIR` candidate, producing harmless but noisy output. Filtered.

### What got better

- **`/orient` Step 1c now skips `~/.claude/teams/_archive/` in the stale-dir scan.** Single-line filter (`[ "$(basename "$d")" = "_archive" ] && continue`) added to the no-tmux branch. The tmux-alive branch already skipped it implicitly via the `leadSessionId` empty-check, but the explicit filter is added there too for symmetry.

### What you need to do

Nothing. `update-wfk pull` replaces `SKILL.md` cleanly.

---

## v3.7.2 - 2026-05-27

### What this release is about

`/orient`'s orphan-agent detection had a structural gap. The skill checked `~/.claude/teams/` for stale tmux team configs, but missed any `claude --dangerously-skip-permissions` worker running outside tmux. Cross-session orphans (workers spawned in one session that survived past its close) routinely run in non-tmux ttys with full Bash / SSH / shell tool surface, and the tmux-only check could not see them. The 2026-05-26 incident caught a PID with ~6h uptime that the prior session's orient missed entirely; in May 2026 a related class of orphans contributed to a production VPS outage. Orient's discipline at session start is supposed to be the first defense against this, closing the methodology gap had become non-optional.

### What got better

- **`/orient` Step 1c is now a three-check sweep.** The existing tmux + team-config scan stays in place (it catches stale team dirs after tmux exits). On top of it: a local `ps -ef | grep -E 'claude.*--team-name|claude.*--dangerously-skip-permissions'` check catches non-tmux Claude workers in any tty, and a templated optional remote SSH check catches workers running against production targets you configure in `LOCAL.md`. The three categories are reported separately in the orient summary because they mean different things: stale team dirs are usually harmless, live local processes need operator triage (could be concurrent sessions or cross-session orphans), live remote processes are highest-risk and need immediate confirmation. The skill detects and surfaces; it does NOT auto-kill, because killing another session's workers can destroy in-flight work. The only `AskUserQuestion` orient is allowed to issue is the live-process triage when category (b) or (c) returns matches.

### What you need to do

Nothing for the basic upgrade. If you want the optional remote check active, add a `LOCAL.md` to `~/.claude/skills/orient/` that defines your production SSH aliases and uncomment the remote loop in Step 1c.

### Migration

`update-wfk pull` replaces `SKILL.md` cleanly (Tier 2). No data migration; the new sweep runs the next time you invoke `/orient`.

---

## v3.7.1 - 2026-05-27

### What this release is about

`/orient` was quietly drifting into `/pickup`'s territory. The skill loaded session context (configs, lessons, period reports) and then proposed which PIC to start, flagged "likely deployment regressions" by cross-referencing open PICs against the EOW, and closed with an `AskUserQuestion` asking what to work on. That blurred the boundary between two skills that serve different jobs: orient establishes the agent's context; pickup decides what to work on. When orient pre-recommended, the user got the same conversation twice (once at orient, once at pickup), and the orient summary became noisier than the SOD it was reading from.

### What got better

**`/orient` is now context-load only.** The PIC cross-reference step that drew "X was shipped, so the related PIC is probably a deployment regression, investigate the deploy first" conclusions was removed; that analysis belongs to `/pickup`. The closing `AskUserQuestion` was removed; orient now ends after reporting what it loaded. A boundary note at the top of the Response Format makes the contract explicit: orient reports state, pickup recommends action. The two infrastructure-context steps (Recent Infrastructure Changes from EOW/SOD, REF doc staleness check) stay in orient because they correct the agent's factual mental model rather than recommending a next move.

The practical effect is a shorter, more focused orient summary and a cleaner handoff to `/pickup` when the user is ready to choose work. If you previously relied on orient to suggest a PIC, run `/pickup` next — it's the skill that owns that decision.

### What you need to do

Nothing required. The change is internal to the orient skill; no kit.json structure changes, no new skills, no renames, no templates affected.

### Migration

`/update-wfk pull` installs the updated `skills/orient/SKILL.md`. If you have local edits to orient, the pull will offer to preserve them to `LOCAL.md` before replacing.

---

## v3.7.0 - 2026-05-20

### What this release is about

New skill: `/landscape-survey`, a structured six-phase workflow for researching the open-source landscape before designing or rebuilding a complex system. The skill was distilled from a real two-day survey that took a knowledge-graph rebuild from "candidate set provisional verdicts" to "comparative-analysis RE + consolidated 30-question SPC backlog" in one working day. The structural insight is that landscape research is itself a process worth bracketing, and that the bracket has a small set of load-bearing rules: the first repo must be read manually (it establishes the template the rest will mimic), the synthesis pass must be single-worker (multi-worker synthesis fragments), the candidate set must be locked before parallel reads start (additions destroy parallelism), and the discovery phase composes other kit skills rather than reinventing literature search.

### New skills

**`/landscape-survey` -- open-source landscape research before the SPC.** Walks six phases: bracket the survey (with explicit anti-scope: no SPC drafting, no design recommendations, no code sketches), discover the candidate set (composing `/video-intel` + `/oracle-create` + `/oracle-research` + WebFetch validation), set up a scratch workspace outside the vault, read the 1-2 closest architectural peers manually to establish the ARE template, dispatch a parallel team for the remaining candidates with pre-allocated Q-number ranges per worker, then run a single-worker synthesis pass that produces one comparative-analysis RE. Outputs land in the vault at `02_Projects/<project>/reports/<date>/`; cloned source repos live in `~/Repos/.scratch/<topic>/` outside the vault. Every ARE frontmatter carries the upstream `commit_sha` so the scratch is deterministically reconstructable from the vault artifacts alone. Hands off to `/create-note SD` and `/create-note SPC` when complete.

The skill bundles six reference files: `ARE-template.md` and `RE-template.md` for the deliverable structures, `worker-brief-template.md` and `synthesis-worker-brief.md` for the parallel and synthesis worker dispatches, `discover.md` for the discovery-phase tool composition, `anti-patterns.md` listing ten failure modes the skill refuses to perform, and `example-survey.md` documenting the OSR knowledge-graph survey as the canonical worked example.

### What you need to do

Nothing required. The skill is available immediately after the pull and triggers on natural phrasing like "landscape survey", "deep-read these repos", "what should we borrow from X", or "research before we spec." Pointing the assistant at a candidate set of repos and asking for a build plan before the SPC will also auto-invoke it.

### Migration

`/update-wfk pull` installs `skills/landscape-survey/` and updates `kit.json` to v3.7.0. No vault changes, no template changes, no breaking changes to existing skills.

---

## v3.6.0 - 2026-05-19

### What this release is about

This release restructures `/log-work` to prevent a recurring failure mode: daily note (DN) entries silently drifting into project log (PJL) territory. The session agent that just spent two hours touching code has working memory full of commit hashes, file paths, function names, counts, and phase numbers. When that same agent is asked to write a "scannable progress update" for the DN, the technical detail looks informative rather than banned, and the DN ends up reading like a second copy of the PJL. The fix is structural: the DN entry is now authored by a fresh subagent that reads only the PJL and the writing profile, never the conversation. The same insight is what justifies the Worker/Verifier/Coordinator pattern in `/qa-coord`: the agent who did the work cannot fairly summarize it for a different audience.

### What got better

**`/log-work` -- DN is now distilled by a fresh subagent, not the session agent.** Step 4b dispatches a single `general-purpose` subagent with a strict prompt template. The subagent receives only the PJL entry, any daily-note writing profile, the existing DN heading content, and the group/merge table. It produces ready-to-write markdown bullets organized by group and project, applying the banned-token list and density rules itself. Step 4c writes the returned bullets verbatim. Hand-editing the subagent output is explicitly banned because it reintroduces the contamination the architecture exists to prevent.

**`/log-work` -- SELECT and CUT, not GROUP and STACK.** When a project's PJL has many distinct outcomes (heavy days, multi-surface sprints), the subagent prompt explicitly forbids the common failure of bundling 5+ outcomes into one bullet via commas and "ands." The directive is to pick the 2-3 most important outcomes and CUT the rest. Run-on bullets stacking multiple facts are a violation even when the individual facts are compliant.

**`/log-work` -- Heavy-day sub-projects.** When a project genuinely has 5+ distinct outcome blocks worth tracking, the subagent splits into `#### Project (sub-area)` headings with 2-3 bullets each, rather than one giant heading with 8+ bullets. The sub-area label comes from the PJL's `###` subsection headings when present.

**`/log-work` -- Banned-token list expanded and tightened.** The DN subagent prompt now explicitly bans lesson-number patterns (L\d+), skill names with leading slash, frontmatter field names, memory file names, library/framework names, UUIDs, error class names, HTTP header names, oracle scores, and review grades. Each of these was a real leak observed in DN drift cases.

### What you need to do

Nothing required. The first invocation of `/log-work` after pulling this version will dispatch the new subagent automatically. The skill no longer asks the session agent to self-compress, so if your DN entries have been drifting technical, this is the structural fix.

### Migration

`/update-wfk pull` updates `skills/log-work/SKILL.md`. No vault changes, no template changes, no manifest changes required.

---

## v3.5.2 - 2026-05-18

### What this release is about

This patch fixes a `/pickup` failure mode: when a TRI cache exists from earlier in the day, two agents reading the same TRI could produce substantially different presentations because Step 5's "Presentation rules" read like *invention* rules, not *rendering* rules. One agent would render the TRI's clusters verbatim, another would re-cluster from MRM objectives and SOD priorities, drop the TRI's batch hints (e.g., shared-codebase batches), and re-number PICs from scratch. Same input, divergent output.

### What got better

**`/pickup` — Step 5 now has explicit Render vs Invent paths.** When a cached TRI is loaded via Step 0a, the TRI's `## Project Clusters` and `## Recommended Session Order` tables are the source of truth, agents render them verbatim, do not re-cluster, do not re-number. The Invent path (no usable TRI, fresh full scan) still derives clusters from MRM objectives and walks clusters for selection IDs. Result: cached-TRI presentations become deterministic across agents.

**`/pickup` — "Validate first" cluster widened.** Previously scoped to picked-up PICs flagged in the SOD. Now also includes closed PICs that the active SOD or WRM still names as goal anchors (sourced from the TRI's `## Supersession Findings`). When yesterday's frog PIC closes overnight, the SOD's stale reference is surfaced for adjudication before regular pickup work.

**`/pickup` — Selection numbering pinned to TRI.** In the Render path, selection IDs come from the TRI's `## Recommended Session Order` and are reused verbatim. The "walk clusters top-to-bottom" numbering rule now applies only to the Invent path.

### What you need to do

Nothing required. The changes are confined to Step 5 and Step 5a. Existing TRI files continue to work, the new Render path uses fields that the TRI format has always had.

### Migration

`/update-wfk pull` updates `skills/pickup/SKILL.md`. No plan file or TRI format changes required.

---

## v3.5.1 - 2026-05-18

### What this release is about

This patch restores the Verifier role split inside `/implement` as a default-on feature and adds orphan-team detection to `/orient`. Both changes target failure modes documented in IRs from the 2026-05-17 evening session: a 7-surface parallel build that ran without verifiers because the v3.4.0 Verifier Pass was extracted from `SKILL.md` body during the v3.5.0 features split without a replacement feature, and a successor session that wasted time on a team whose lead tmux pane was gone (SendMessage returning `success: true` while messages dropped silently).

### What got better

**`/implement` — Verifier Pass restored as a default-on feature.** The new `features/verifier-pass-on-behavioral-changes.md` enforces actor/judge separation on behavioral changes. The Worker that wrote the change does NOT verify it; a separate Verifier dispatched with the template in `references/verifier.md` runs 1-3 pre-selected I/O pairs and produces the PASS/FAIL verdict. The feature fires automatically on standard tier with behavioral acceptance criteria OR on any tier when `worker_count >= 3` (the multi-surface parallel-build trigger). Model diversity preferred (Worker sonnet → Verifier opus, or vice versa). Composes with `multi-surface-parallelism`: N parallel workers produce N parallel verifiers in a matched dispatch round. The feature is based on `/qa-coord`'s three-role pattern but scaled down for general behavioral changes — full pipeline matrix work still belongs in `/qa-coord`.

**`/orient` — Step 1c orphan-team detection.** At session start, `/orient` now scans `~/.claude/teams/` and reports any team whose `leadSessionId` is no longer in tmux. The skill explains the failure mode (`SendMessage` returns `success: true` to dead panes but drops messages; `TeamDelete` cannot remove orphan teams from outside the original session). If 5+ orphans exist, the skill recommends a batch cleanup with archive-first guidance. This prevents agents from assuming an orphan team is reachable, sending messages, and waiting forever for responses that will never come.

### What you need to do

Nothing required. Both changes are default-on. The Verifier Pass fires automatically when its trigger conditions are met; plans can opt out per-PL via `features.remove: [verifier-pass-on-behavioral-changes]` when the change is purely additive or fully captured by smoke checks. Orphan-team detection runs once at orient and reports findings in the orient summary.

### Migration

`/update-wfk pull` installs `features/verifier-pass-on-behavioral-changes.md`, updates `modes/default.md` to include it (six default-on features total now), adds the Verifier Pass pointer to `SKILL.md`, and patches `orient/SKILL.md` Step 1c. No plan file changes required.

---

## v3.5.0 - 2026-05-17

### What this release is about

This release introduces a **features + modes architecture** for `/implement`. Atomic behaviors (features) live in their own files; curated collections (modes) compose them. Plans opt into experimental behaviors by declaring `mode:` or `features:` in their frontmatter — no fork of the skill, no separate `/implement-turbo` command. The default mode preserves existing behavior; experimental modes (`turbo`, `swarm`) layer in opportunities that have been validated against real parallel-worker sprints. `/retro` gains a scorecard hook so RETs running under non-default modes carry comparable metrics and can be A/B'd against baseline runs.

### What got better

**`/implement` — features + modes architecture.** The skill now reads `mode:` and `features:` from the plan's frontmatter and resolves an active feature list before any worker dispatch. Each feature is a small file under `features/` documenting what it modifies, when it activates, and how to escape if it goes wrong. Default mode loads five default-on features (pre-commit lint gate, pre-flight readiness check, paired-value smoke checks, out-of-band instruction reporting, dev-server concurrency contract). Turbo mode adds three low-risk experimental features (persistent dev-server worker, design-pass-on-first-page, parallel harness author). Swarm mode adds two heavier experimental features (multi-surface parallelism, two-team topology). Plans can also cherry-pick features beyond their mode via `features.add:` / `features.remove:`. Existing plans without a `mode:` field load the implicit default and behave exactly as before.

**`/implement` — five default-on features extracted.** Behaviors that previously lived inline in `SKILL.md` and `references/worker.md` are now first-class feature files. The pre-commit lint gate forces each worker to run the project's lint command before commit (catches the class of cross-worker style drift that integration-time fixups historically absorbed). The pre-flight readiness check runs a 60-second pre-dispatch validation (deps declared, ports free, no stale worktrees, target files exist, dev server ownership documented). Paired-value smoke checks require workers to grep for *both* expected values when checking format symmetry, not just one. Out-of-band instruction reporting requires workers to surface direct user instructions as `User routed direct instruction: [verbatim quote]` so coordinators see side-channel work. The dev-server concurrency contract codifies single-owner-per-`.next/` rules and per-worker port assignment.

**`/retro` — scorecard hook for mode + feature runs.** When a sprint ran under a non-default mode, the RET frontmatter now carries a `playbook_metrics` block (mode, features active, wall clock, fix ratio, false fails) plus a `baseline_comparison` block citing the most recent default-mode sprint of comparable scope. After two or three runs at the same mode, the user can see whether the experimental features actually saved time and decide to promote, retire, or refine them.

### What you need to do

Nothing required. Plans without `mode:` or `features:` frontmatter continue to behave exactly as before — the default mode is the implicit baseline.

If you want to try an experimental mode on a future sprint:

```yaml
---
status: Ready
ceremony_tier: light
mode: turbo
---
```

Or cherry-pick individual features:

```yaml
features:
  add: [persistent-dev-server-worker]
```

The skill will announce the active mode + feature list before dispatching any workers so you can verify it matched your intent.

### Migration

`/update-wfk pull` installs the new `features/` and `modes/` directories under `~/.claude/skills/implement/`. Existing inline sections in `SKILL.md` and `references/worker.md` are replaced with one-line citations to the feature files. No plan file changes required.

---

## v3.4.0 - 2026-05-15

### What this release is about

This release introduces three new skills focused on scope discipline and verification: `/bracket` for printed scope contracts, `/spec-guard` for pre-implementation spec checks, and `/qa-coord` for three-role pipeline coordination. The promotion and supersession path for lessons gets explicit so the same rule no longer loads from three tiers at once. `/implement` gains a Verifier Pass for standard-tier behavioral changes so the agent that writes a change is not the same agent that judges it. `/update-wfk push` now also pulls the post-push commit into `~/Repos/workflow-kit/` so the developer's local clone stays current.

### New skills

- **`/bracket`** — Open any non-trivial work session by writing a printed scope contract: Surface, Success criteria, Anti-scope, Validation plan, Handoff trigger. The contract is referenced at every progress check so the agent cannot drift into scope creep without consciously deciding to. Required before `/implement`, before any multi-step code change, and before picking up a critical PIC. The structural fix for "agent read the working contract and violated it within hours."
- **`/spec-guard`** — Pre-implementation spec check. Before building any feature on an existing system, the skill scans the project's `specs/` directory and flags any unimplemented or reviewed specs that govern the planned work. Hard-gates implementation when a `reviewed` or `conditional` spec exists and the planned work would deviate. Prevents the failure mode where an agent designs a feature from scratch when a spec already defines the canonical data model.
- **`/qa-coord`** — Three-role pipeline coordination for complex LLM-in-the-loop work where data quality is the deliverable. Coordinator designs the test matrix, Worker implements, Verifier tests pre-selected I/O pairs. No agent both implements and evaluates its own work. Includes a multi-dimensional test matrix (true positive, true negative, false-positive risk, false-negative risk, ambiguity, closed-loop), mid-bracket finding triage protocol (Internal / Adjacent / Premise-breaking), and Coordinator decision-authority rules that keep technical questions off the user's plate.

### What got better

**`/learn` — Supersession protocol.** When a lesson is promoted from a feedback memory up to a project `lessons.md`, vault-level reference, or CLAUDE.md rule, the lower-tier source now gets a supersession pointer instead of being left behind. Without this, the same rule was being loaded from three tiers every session, wasting context and creating ambiguity about which version was authoritative. The skill also now syncs a trigger index (if your vault keeps one) so newly learned lessons are immediately discoverable at the point of action.

**`/dream` — Cross-tier dedup + lesson system health.** Memory consolidation now does a second pass that checks whether any feedback memory has been superseded by a higher-tier rule, and replaces the duplicate with a pointer. Adds a Phase 5 health check that flags stale project lessons, empty `lessons.md` stubs, and cross-cutting lessons that look ready for promotion to a vault-level reference. The agent stops re-discovering the same rule across multiple memory tiers.

**`/implement` — Verifier Pass.** Standard-tier changes whose acceptance criterion is *behavioral* (auth, schema migrations with data semantics, API behavior changes, bulk operations with selection logic) now require a separate Verifier agent that tests pre-selected I/O pairs against the deployed change. The Worker that wrote the change does not verify it. The cost is one Verifier dispatch; the alternative is shipping behavioral changes whose only proof was "the deploy succeeded and the route returns 200." `/implement` also now requires the `/bracket` walkthrough to complete before workers are dispatched.

**`/pickup` — Repo freshness + spec check + documentation check.** Before reading any code files from a `~/Repos/` directory, pickup now runs `git fetch && git log HEAD..origin/main` so sessions never start against a stale tree. When the PIC's next steps involve implementing a feature on an existing system, pickup also scans the project's `specs/` directory and reads matching specs before any coding begins. At close, a mandatory documentation-stale check scans for SDs, REFs, and project CLAUDE.md files that the PIC's work may have invalidated and offers to update them.

**`/update-wfk push` — Local repo sync.** After a successful push to GitHub, the skill now pulls the new commit into `~/Repos/workflow-kit/` so the developer's persistent local clone stays in sync with the `/tmp` scratch clone. Warns if the local repo is missing instead of silently leaving it stale.

### What you need to do

Nothing required. All new skills are opt-in (`/bracket`, `/qa-coord`) or auto-invoke at safe points (`/spec-guard` before implementation work, `/learn` supersession on promotion).

If you want the new behavior immediately:
- Run `/bracket` at the start of your next non-trivial work session
- Let `/spec-guard` auto-invoke before your next implementation pass
- Use `/qa-coord` when starting any pipeline-stage evaluation where data quality matters

### Migration

`/update-wfk pull` installs the three new skills and updates the five improved ones. The `create-campaign`, `create-pulse-campaign`, and `kb-to-campaign` skills are now formally deprecated (they were already replaced by the org-only unified `campaign` skill).

---

## v3.3.0 - 2026-05-05

### What this release is about

The Period Reporting System, formalized in a new System Definition (SD), redesigns how the kit produces and consumes cadence-based documents. The old ad-hoc RM/WF/SOM/SOW structure is replaced by a principled three-layer operative chain: MRM (Monthly Roadmap), WRM (Weekly Roadmap), and SOD (Start of Day). Each cadence now produces exactly two documents: a backward-looking retrospective (EOD/EOW/EOM) and a forward-looking operative document (SOD/WRM/MRM). Retro sections across all cadences gain a structured insight routing mechanism grounded in Argyris's double-loop learning theory, ensuring observations produce structural change rather than being documented and forgotten.

### New templates
- **MRM (Monthly Roadmap)** replaces RM + SOM. Sets 3-5 monthly objectives with done-definitions, decision rules, systemic landing zones from EOM diagnosis, and carry-forward with objective alignment.
- **WRM (Weekly Roadmap)** replaces WF + SOW. Inherits from MRM, narrows to exactly 3 weekly goals with "what done looks like" criteria, explicit in/out scope lists, and directives routed from EOW retro.

### What got better

**end-day** now produces WRM on Fridays (after EOW) and MRM on last workday of the month (after EOM). The old SOM generation step is replaced by MRM. EOD and EOW retro sections gain a mandatory 4-part structure: observation, impact, action, and landing zone. The landing zone declares where each insight produces structural change (CLAUDE.md rule, writing profile, skill gate, L-entry, WRM directive, MRM decision rule). Items without landing zones are flagged as single-loop. A 3-day escalation rule detects when the same item has been carried forward without structural fix and forces the EOW to propose a governing-variable change.

**orient** loads the full operative chain (SOD + WRM + MRM) at session start instead of the old SOD + SOW/SOM/RM mix. Missing operative documents are flagged prominently with recovery instructions.

**closeout** reads MRM objectives and WRM weekly goals (instead of RM/WF) to group session summaries by goal and flag off-focus work.

**pickup** clusters PICs by MRM objective alignment (instead of RM goals), with WRM in-scope list prioritization.

**roadmap** produces MRM + WRM (instead of RM + WF). Core audit/triage/phasing logic unchanged. Output format aligned with the new templates.

**create-note** adds MRM and WRM to the lookup table (replacing SOM).

### What you need to do

After pulling, create your first MRM and WRM:
1. Run `/roadmap` to generate an MRM for the current month and a WRM for the current week
2. Or wait for the next `/end-day` on a Friday (produces WRM) or last workday of month (produces MRM)

Old RM and WF files in your vault remain as historical records. They are not deleted.

### Theoretical grounding

The SD references five frameworks that informed the design: GTD review hierarchy (Allen), OKR dual cadence (Doerr), double-loop learning (Argyris and Schon), Viable System Model (Beer), and temporal knowledge graphs (Zep/Graphiti). The insight routing mechanism and double-loop escalation rule are directly derived from Argyris's distinction between changing actions (single-loop) and changing governing variables (double-loop).

---

## v3.2.1 - 2026-05-04

### What this release is about

Pickup gains a real PJL scope-check guardrail (the v3.2.0 changelog described it but the implementation wasn't in the SKILL.md). Generalization pass replaces hardcoded vault paths and Flora-specific examples with placeholders so the skill works in any vault. Stale references to deprecated skill names cleaned up.

### What got better

**`/pickup` — PJL scope-check guardrail (real this time).** Before writing any session entry to a project log, pickup now scans the PIC body for project signals and verifies they match the PIC's `project:` frontmatter. If they don't, it asks before writing instead of silently routing work to the wrong PJL. PICs sometimes bundle work across projects or get mis-filed initially; this prevents one bad frontmatter from polluting another project's log forever.

**`/pickup` — runtime path config and generic examples.** Hardcoded `Work Vault/` paths replaced with `{vault_root}/{paths.reports}/...` placeholders that resolve via `~/.claude/wfk-paths.json`. Cluster examples ("Portal for Patrick", "KB v1 Shipped") replaced with generic labels ("Goal A", "Goal B"). Project path examples replaced with `<initiative>/<project>` placeholders. The skill now works correctly in any vault, not just the maintainer's.

**`/pickup` — deprecated skill name references cleaned up.** Three references to `/create-spec`, `/create-plan`, and `/create-pickup` in the prose updated to their current `/create-note SPC|PL|PIC` equivalents.

### What you need to do

Nothing. All changes are backwards-compatible.

### Migration

`/update-wfk pull` updates pickup automatically.

---

## v3.2.0 - 2026-04-30

### What this release is about

Oracle-informed template consolidation for create-note, plus two new skills (impeccable, resolve-ir). The SD and SPC templates now have companion writing guides, structured interviews, and anti-pattern documentation. Plan (PL) template added as a first-class document type.

### New skills

**`/impeccable`** — Frontend design audit and polish skill. Invoked when the user wants to design, redesign, critique, or improve any frontend interface. Covers websites, dashboards, product UI, and app screens.

**`/resolve-ir`** — Incident Report resolution skill. Structures IR resolution as root-cause classification (preventive vs palliative), enforces that IRs cannot close with only palliative fixes, and tracks deferred root causes.

### What got better

**`/create-note SD` — full consolidation.** The SD template now has a companion writing guide (`references/sd-guide.md`), scope classification (Entity/System/Framework), a structured discovery interview protocol, oracle check with SD-specific queries, prior decisions documentation, YAGNI enforcement, and a 9-point self-review checklist. Anti-patterns section covers the 8 most common SD writing failures. The guide names [[SD - Process Entity Model]] v3 as the exemplar.

**`/create-note SPC` — spec guide added.** A comprehensive spec writing guide (`references/spec-guide.md`) covering the 6 elements every spec needs, section-by-section guidance, golden examples, and anti-patterns. Oracle-grounded from 55 sources.

**`/create-note PL` — plan template and guide.** New template and companion guide for implementation plans. Covers task granularity, file/domain isolation for parallel dispatch, verification commands per task, and three ceremony tiers (light/standard/heavy). Plans are the primary artifact consumed by `/implement`.

**`/pickup` — PJL scope-check guardrail.** Before writing to a project log, the skill now verifies that the PIC's `project:` field matches the actual work scope by scanning the PIC body for project signals.

**`/review-spec` — updated references.** Skill now references `/create-note PL` instead of the deprecated `/create-plan`.

### What you need to do

Nothing. All changes are backwards-compatible.

### Migration

`/update-wfk pull` installs the new templates and guides automatically.

---

## v3.1.0 - 2026-04-28

### What this release is about

Adds Executive Brief (EB) as a first-class document type in `create-note`. EBs are one-page distillates of longer reports, optimized for executive, investor, or stakeholder readers who need the thesis without the methodology. Previously, EBs were ad-hoc — there was no template, no prefix, and no routing convention.

### What got better

**`/create-note` now handles EB.** Pass `EB` as the type or say "executive brief" / "create EB" / "write a brief" and the skill routes the document to `{project}/reports/{date}/EB - {Name}.md` with the correct frontmatter (category `Report`) and applies the RE writing profile. A new template at `templates/EB.md` enforces the EB structure: 3-5 sentence summary, one-line product/position statement, why-it-matters table, proof table, target audience, recommended next moves, and a mandatory source link back to the underlying analysis.

EBs are explicitly framed as distillates — the template tells the skill not to write a standalone EB without an underlying RE or analysis to point at.

### What you need to do

Update your vault's prefix table to include `EB | Executive Brief | Report` if you maintain a manual prefix list in `Work Vault/CLAUDE.md`. The kit's CLAUDE.md template already includes it.

### Migration

`/update-wfk pull` will:
1. Update the `create-note` SKILL.md with the EB type entry in the trigger and lookup tables
2. Install `skills/create-note/templates/EB.md`
3. Bump your sync manifest to v3.1.0

No deprecations, no breaking changes.

---

## v3.0.0 - 2026-04-28

### What this release is about

Document creation consolidated from 8 separate skills into one. Strategic planning becomes a first-class workflow with the new roadmap skill. Lessons extraction is now automated. Deployment verification patterns hardened across closeout, end-day, log-work, and pickup. Major org-content scrub pass.

### Breaking changes

**8 document creation skills replaced by `/create-note`.** The individual skills (`/create-sd`, `/create-spec`, `/create-pickup`, `/create-MN`, `/create-concept-brief`, `/create-plan`, `/design`, `/structure`) are removed. Use `/create-note` with a type argument instead:

| Old command | New command |
|---|---|
| `/create-sd` | `/create-note SD` |
| `/create-spec` | `/create-note SPC` |
| `/create-pickup` | `/create-note PIC` |
| `/create-MN` | `/create-note MN` |
| `/create-concept-brief` | `/create-note PD` |
| `/create-plan` | `/create-note PLN` |
| `/design` | `/create-note DD` |
| `/structure` | `/create-note SO` |

You can also just say "create a spec" or "write meeting notes" and `create-note` will detect the type from context. All templates, frontmatter conventions, writing profile lookups, and routing rules are preserved. The skill also handles `RE` (reports) which had no dedicated skill before.

**`/pipeline-qa` removed from core.** This was always org-specific (FWIS signal engine checks). Moved to org_skills. If you had it installed, it will be removed on pull. If you built your own checks on top of it, save your LOCAL.md first.

### New skills

**`/create-note`**
One skill for all vault document types. Pass a type (SD, SPC, PIC, MN, PD, PLN, DD, SO, RE) or let it detect from context. Loads the correct writing profile, applies type-specific frontmatter, routes to the right directory, and follows the established structure for each document type. Includes all templates that were previously scattered across 8 separate skills.

**`/roadmap`**
Strategic planning that maps all active work to stated goals. Audits open PICs, Patrick Requests, and project logs. Triages PICs into active/parked/blocked with a capacity gate (8 max). Phases tasks across weeks with dependency tracking. Produces both a Roadmap (RM, multi-week strategic view) and Weekly Focus (WF, this-week tactical view). Three modes: full creation, refresh (update existing), or weekly-focus-only (new WF from current RM). Integrates with orient (reads RM at startup), end-day (goal progress reporting), triage-patrick (weekly focus gate), and pickup (goal-aligned clustering).

**`/distill-lessons`**
Extracts reusable lessons from the current conversation into CLAUDE.md and lessons.md files. Watches for corrections, failures, surprising fixes, and non-obvious workarounds. Formats each lesson with trigger condition, action, and rationale so future agents can apply them as active constraints.

### What got better

**Closeout verifies deployment state before logging.** A new pre-flight step audits whether code changes in the session were actually deployed. If you pushed but didn't deploy, closeout catches the gap before it becomes a false record in your daily note. Automatic commit, push, and deploy during closeout for any stale services.

**End-day runs a machine-wide state audit.** Beyond the single-session closeout, end-day now checks every repo on the machine for uncommitted changes, every deployed service for stale containers, and every auto-memory directory for drift. Reports findings as actionable items, not automated fixes.

**Log-work requires environment disambiguation.** When logging work that touches deployed applications, the entry must specify LOCAL, REMOTE, or BOTH, with a verification URL. Prevents the "deployed the fix" claim when the fix only exists locally.

**Pickup declares environment before starting.** For PICs that involve deployed code, pickup forces an environment declaration (LOCAL/REMOTE/BOTH) before any work begins. This prevents investigating a production bug against localhost.

**15 additional skills updated** with structural improvements, better scrubbing, and tighter integration with the strategic planning layer.

### What you need to do

**Update your command muscle memory.** If you type `/create-spec` by habit, it will no longer resolve. Use `/create-note SPC` or just say "create a spec" and the unified skill handles it. The old command names still work as natural language triggers for `create-note`.

**Check your LOCAL.md files.** If you customized any of the 8 removed skills via LOCAL.md, those files will be preserved in backups during the pull. Review and migrate any customizations to `~/.claude/skills/create-note/LOCAL.md`.

### Migration

When you run `/update-wfk pull`:
1. 8 deprecated skills will be backed up and removed (create-sd, create-spec, create-pickup, create-MN, create-concept-brief, create-plan, design, structure)
2. pipeline-qa will be removed (moved to org-only)
3. 3 new skills installed (create-note, roadmap, distill-lessons)
4. 15 existing skills updated
5. References to old skill names in your CLAUDE.md will be flagged for update
6. Your sync manifest will be updated to v3.0.0

---

## v2.3.0 - 2026-04-23

### What this release is about

Strategic awareness across the workflow. Skills that begin, close, and report on work now read strategic planning documents (roadmaps, weekly focus files) to anchor decisions in goals, not just tasks. Closeout gained two new pre-flight checks that prevent duplicate PICs and make deployment automatic. A new prototype skill generates Claude Design-ready documents from specs.

### New skills

**`/prototype`**
Ingests a spec and produces a Prototype Design Discussion (DD) optimized for Claude Design (claude.ai/design). Extracts user flows, screen inventory, component inventory, data model summary, and interaction patterns into a single document you can paste directly into Claude Design for interactive UI prototyping.

### What got better

**Closeout wraps up your work without asking.**
Closeout now auto-commits, auto-pushes, and auto-deploys your session's changes. The closeout invocation IS the approval. Two new pre-flight steps: Strategic Context (groups work by goals, flags off-focus work) and PIC State Snapshot (scans open PICs to prevent duplicates and catch PICs closed by parallel sessions).

**End-day captures subjective state first.**
A Day Rating step (1-5 scale) runs before the analytical aggregation, capturing how the user felt about the day before the numbers reframe their perception. Strategic context adds a Goal Progress section to the EOD that makes multi-day goal stalls visible.

**Pickup clusters by strategic goals.**
When roadmap or weekly focus documents exist, pickup groups PICs by strategic goal (not just project theme). "Unaligned" work surfaces last, making priority visible at a glance. A capacity gate in create-pickup warns when open PICs exceed 7 and offers merge alternatives.

**Orient loads strategic context.**
A new step (7b) reads roadmap and weekly focus documents at session start, anchoring the session in strategy with a brief summary of active goals and PIC alignment.

**Meeting notes support multi-part meetings.**
Create-MN gained Parts Detection for meetings with distinct temporal segments (location changes, participant changes, reconvening after breaks). Format B provides a template with Part containers wrapping topic blocks.

**Forward momentum is the default.**
Several skills (create-plan, create-spec, design, structure, recap) now proceed to the next workflow step automatically instead of offering pause points. The philosophy: the skill invocation IS the intent. Users who want to stop can always say so.

### What you need to do

Nothing. Strategic context features gracefully degrade when no planning documents exist. The auto-commit/push/deploy behavior in closeout can be overridden via LOCAL.md if you prefer confirmation prompts.

### Migration

`/update-wfk pull` will install the new prototype skill and update all modified skills. Concept brief now ships with generalized reference files (org-context.md and cb-template.md) you can customize for your organization.

---

## v2.2.0 - 2026-04-22

### What this release is about

Oracle System: a research grounding layer that prevents speculating solutions to solved problems. Before designing a system, the oracle researches what the world already knows about the domain and brings established patterns, industry standards, and known pitfalls into the conversation. Four new skills, five existing skills updated with oracle integration.

### New skills

**`/oracle-create`**
Creates a NotebookLM research notebook for a project or sub-domain. Runs deep research to discover external sources (industry papers, frameworks, production case studies), imports them, and synthesizes a grounding report. Registers the oracle in the project's PJL frontmatter so future sessions can find it. One oracle per project by default.

**`/oracle-ask`**
Queries an existing oracle for design guidance. Looks up the project's oracle from PJL, queries it, and formats the response as a proposition with source citations. Works standalone ("ask the oracle about X") or inline from other skills at design decision points. Supports follow-up conversations for multi-turn research.

**`/oracle-research`**
Expands an existing oracle's knowledge when the project scope grows. Adds new research and sources to the notebook, updates the PJL ledger, and optionally appends new findings to the grounding report.

**`/create-sd`**
Creates System Definition (SD) documents with correct structure and frontmatter. SDs are constitutional, living references that define what a system is and what principles govern it. The skill enforces the common structure across existing SDs: opening declaration, conceptual model, business impact, boundaries, principles, theoretical grounding, and change log. Prevents the spec-vs-SD confusion by providing guidance on when to use each.

### What got better

**Design work starts with what the world knows.**
`/create-spec`, `/design`, `/grill`, `/create-plan`, and `/implement` all gained an oracle check step. Before writing a spec or interrogating a design, the skill checks if the project has an oracle and queries it for domain grounding. The oracle's response is surfaced as a proposition (never applied silently) so the user can adopt, adapt, or discard it.

**Grill has an external pressure dimension.**
`/grill` now uses the oracle to compare the user's design decisions against industry patterns. When the user's approach departs from what the oracle reports as standard practice, the grill surfaces the departure as a question, not a judgment.

### What you need to do

Nothing. Oracle integration is prompted, not mandatory. If a project has no oracle, skills suggest creating one and proceed without if declined. NotebookLM MCP server is required for oracle functionality (install with `uv tool install notebooklm-mcp-cli`).

### Migration

`/update-wfk pull` will install the 4 new skills and update the 5 modified skills automatically.

---

## v2.1.0 - 2026-04-17

### What this release is about

New skill for capturing stakeholder ideas before they become specs. Five skills got significant generalization work to remove hardcoded assumptions and work better across different environments. Org-specific content scrubbed from several files that slipped through v2.0.0.

### New skills

**`/create-concept-brief`**
When someone describes a feature idea, product vision, or system concept, this skill captures it as a structured Concept Brief (CB). It interviews the stakeholder about outcomes and frustrations (not technology), grounds their ideas against what already exists, and produces a document a developer can act on without guessing intent. The CB feeds into `/create-spec` as the first step in the idea-to-implementation pipeline.

### What got better

**Implementation scales without external tools.**
`/implement` was rewritten to use ceremony tiers (light/standard/heavy) that match the plan's complexity. Light plans skip team setup entirely, dispatching workers directly with inline tracking. Standard plans add security eval and deploy gates. Heavy plans get full ceremony. The plan file tracks everything, no external project management dependency.

**Pickup handles deployable projects more carefully.**
`/pickup` now includes an environment declaration step for projects with deployment targets. Before starting work on a PIC that involves deployed code, it determines whether you're working LOCAL, REMOTE, or BOTH, and injects that context into every action. This prevents the "pushed but not deployed" false confidence pattern.

**End-of-day audit is environment-aware.**
`/end-day` now adapts its audit to your actual setup. It checks for uncommitted changes, unpushed commits, and stale deployments based on what it discovers in your environment, not a hardcoded service list.

**Pipeline QA has a reusable framework.**
`/pipeline-qa` now provides a generic spec-compliance evaluation framework: infrastructure pre-checks as hard blockers, subsystem isolation, automated scoring with configurable thresholds, and content truth verification. The specific checks are yours to define for your pipeline.

**Skill chains documented in `/discover`.**
`/discover` now shows how skills compose into chains (Daily: orient to pickup to log-work to closeout to end-day to dream; Build: create-spec to review-spec to create-plan to implement to pr-review to retro) and suggests the natural next step based on where you are.

### Scrub fixes

Several files from v2.0.0 contained leaked org-specific references (domain names, repo paths, deploy commands). These have been scrubbed: closeout, log-work, create-pickup, README.

### What you need to do

Nothing required. All changes are backward-compatible.

### Migration

When you run `/update-wfk pull`:
1. `create-concept-brief` will be offered for installation
2. Five skills (implement, pickup, end-day, pipeline-qa, discover) will be updated
3. Scrubbed files (closeout, log-work, create-pickup) will be refreshed
4. Your sync manifest will be updated to v2.1.0

---

## v2.0.0 - 2026-04-11

### What this release is about

The session lifecycle skills (closeout, end-day, log-work, pickup) now verify claims against actual state before recording them. The creation skills (create-spec, create-plan, implement) now scale their process to match the size of the work.

### New skills

**`/create-plan`** (replaces `/plan-spec`)
Write "create a plan" and get a plan sized to your work. A config change gets a flat checklist. A multi-phase project gets phased milestones with design exploration. The plan file itself tracks progress - no external project management tool needed.

**`/explain`**
Three modes depending on what you need:
- Point it at a file: get an executive summary, key decisions, and what's missing
- Ask about a concept: get a concise explanation in context of your project
- Say "where are we": get a status snapshot of the current session - what's done, what's left, what's blocking

### New feature: Project Logs and Work Logs

**This is the biggest quality-of-life improvement in v2.** Every project now gets a persistent Project Log (`PJL - <Project>.md`) that accumulates across sessions. When Claude picks up a project, it reads the PJL and immediately knows: what was built, what decisions were made (and why), what was tried and didn't work, what's deployed where, and what to watch out for.

Your daily notes stay short and scannable (max 4 lines per project). The detail that agents need - file paths, function names, commit hashes, deployment commands, migration filenames - goes in the PJL instead of cluttering your daily note.

On heavy work days, a Work Log (`WL - <Topic> <Date>.md`) captures the full session: per-task breakdowns, investigation notes, error messages, SQL queries. Linked from the PJL so nothing is lost but nothing bloats the daily note either.

**The PJL is wired into the full session lifecycle.** It's not just a file that `/log-work` writes to - it's read and updated by the skills that open and close work sessions:
- `/pickup` reads the PJL when loading a project and logs a "session start" entry so the timeline shows when work resumed
- `/create-pickup` logs a "session end" entry and links the new PIC, so the next agent sees a complete arc
- `/implement` reads the PJL before dispatching workers so they know what was tried, what failed, and what decisions were already made
- `/closeout` cross-references the PJL before logging to avoid duplicate entries

**What this means in practice:** When you start a session on a project you haven't touched in a week, Claude reads the PJL and knows exactly where things stand - no "let me investigate the codebase" ramp-up, no asking you to re-explain context. The more you use the system, the faster project ramp-up gets.

### What got better

**Your daily notes are more trustworthy now.**
`/closeout` and `/log-work` now require Claude to verify the state of work before recording it. If code was only committed but not deployed, that's what gets logged - not "deployed the fix." If Claude can't determine the state, it asks you instead of guessing.

**End-of-day tidies up your working environment.**
`/end-day` now scans your environment before writing the EOD report. It detects what you're working with - git repos, deployment targets, backup locations - and checks for loose ends: uncommitted changes, work that didn't get pushed, backups that drifted. You see what it found and decide what to act on. The checks adapt to your setup - a user with one repo sees a quick check, a user with multiple deployment targets sees a more thorough audit. Memory consolidation (`/dream`) now runs automatically at the end instead of being optional.

**Closeout catches documentation drift.**
`/closeout` now notices when a session changed how a system works - renamed a service, changed a config pattern, modified a deployment process. When that happens, it prompts you to update the relevant docs or create a PIC to hand it off. The specifics depend on what you changed and what documentation exists in your vault. This prevents the pattern where something gets rebuilt but future agents still read docs describing the old version.

**Specs and plans match the size of the work.**
`/create-spec` now detects whether you're describing a quick tweak or a complex system and adjusts its interview accordingly. Brief specs get 2-3 questions and a quick self-review. Full specs get the deep interview and multi-agent review team. `/create-plan` (replacing `/plan-spec`) does the same - flat task lists for simple work, phased plans for complex systems.

**PICs don't fragment or carry false claims.**
`/create-pickup` now checks for existing open PICs in the same project before creating a new one, and offers to merge context instead of creating duplicates. Every PIC now requires a Known Issues section - bugs and edge cases discovered during work can't be silently dropped. `/pickup` verifies state claims in PICs before acting on them.

**Implementation scales down without losing structure.**
`/implement` reads complexity from the plan and adjusts its process. Light plans skip the full team setup entirely. Heavy plans get the full ceremony. You don't have to manually choose - it reads what `/create-plan` wrote.

**Pipeline QA is comprehensive.**
`/pipeline-qa` expanded from a basic evaluator to a full subsystem audit framework. Infrastructure checks run first as hard blockers, then spec compliance criteria (translated directly from your specs, not arbitrary quality scores), then content truth verification that catches hallucination and cross-contamination.

### Keeping your customizations safe

Every skill now supports `LOCAL.md` - a file in the skill directory where your customizations live. When you pull updates, the new `/update-wfk pull` will:
- Detect if you've edited any skill files since your last pull
- Ask you one-by-one how to handle conflicts: save your edits to LOCAL.md, take the clean update, or skip that skill
- Show you a changelog summary before updating anything
- Preserve LOCAL.md files across all future pulls

Your edits are never silently overwritten.

### What you need to do

**`/plan-spec` is now `/create-plan`.** If you have `/plan-spec` in any of your own notes or custom skills, update the reference. The pull will offer to clean this up for you in CLAUDE.md and agents.md.

**Daily notes will look different.** `/log-work` now uses a three-level hierarchy (Group > Project > Bullets) and caps each project at 4 lines. The detail goes into Project Log files instead. This keeps your daily notes scannable as they grow.

**Closeout takes slightly longer.** The verification and documentation checks add a minute or two to `/closeout`. This is intentional - the cost of catching a false record now is much lower than the cost of a future session acting on one.

### Migration

When you run `/update-wfk pull`:
1. `plan-spec` will be backed up and removed
2. `create-plan` and `explain` will be installed
3. References to `/plan-spec` in your CLAUDE.md and agents.md will be flagged for update
4. Your sync manifest will be updated with the new version

---

## v1.0.0 - 2026-03-30

Initial public release. 38 core skills, Obsidian vault scaffold, section-marker sync, scrub-map distribution.
