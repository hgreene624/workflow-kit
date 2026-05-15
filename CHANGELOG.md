---
date created: 2026-04-11
tags: [reference, changelog]
category: Reference
---

# Workflow Kit Changelog

What changed, what it means for you, and what to watch for. The `/update-wfk pull` action reads this file to show you what's new.

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
