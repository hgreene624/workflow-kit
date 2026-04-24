---
date created: 2026-04-11
tags: [reference, changelog]
category: Reference
---

# Workflow Kit Changelog

What changed, what it means for you, and what to watch for. The `/update-wfk pull` action reads this file to show you what's new.

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
