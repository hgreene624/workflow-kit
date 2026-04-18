---
date created: 2026-04-11
tags: [reference, changelog]
category: Reference
---

# Workflow Kit Changelog

What changed, what it means for you, and what to watch for. The `/update-wfk pull` action reads this file to show you what's new.

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
