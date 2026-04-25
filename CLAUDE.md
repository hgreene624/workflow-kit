# Vault — Claude Instructions

<!-- WFK:START - Session Startup -->
## Session Startup

Run `/orient` at the start of every conversation. No exceptions.
<!-- WFK:END -->

<!-- WFK:START - Core Behavior -->
## Core Behavior

- Do not infer or invent details. Log only what is explicitly stated.
- When information is incomplete, leave it blank or ask — do not guess.
- Keep instructions out of user-facing notes. Store guidance in `agents.md` or linked reference docs.
- All questions to the user MUST use the AskUserQuestion tool, one at a time. See "Rules That Survive Compaction" below.
- Verify assumptions against docs/code before modifying anything. Don't guess at syntax, dependencies, or config.
- Minimum blast radius: only change what's required. Ask before bundling refactors or "improvements" into a fix.
- Write an implementation plan before dispatching agent teams. The spec defines what; the plan defines how and in what order.
- **Never leave discovered issues untracked.** When you find a broken system, failing service, or bug during work on a different task — even if it seems "unrelated" — you must either fix it now or create a PIC before moving on. Saying "that's a separate issue" without a tracking mechanism means the issue gets forgotten. Ask the user: "I found [issue]. Fix now or create a PIC?"
- **Always clean up after a fix.** When you rename, replace, migrate, or remove something, actively hunt for and delete the stale artifacts left behind: old DB rows, superseded branches, dead code paths, orphaned registry entries, obsolete cron jobs, unused prompt versions, etc. Cleanup is part of the fix, not a separate task. If you're unsure whether an artifact is safe to remove, ask — but don't just leave it.
<!-- WFK:END -->

<!-- WFK:START - Agent Teams -->
## Agent Teams — Mandatory

When dispatching multiple agents or subagents for ANY purpose (parallel research, implementation, reviews, syncs — anything), you MUST use Claude Code Agent Teams (`TeamCreate` → workers) so every agent appears in a tmux pane the user can monitor.

**Never use bare background subagents** (`Agent` tool with `run_in_background: true` without a team). No exceptions.

The correct pattern:
1. `TeamCreate` to set up the team
2. Launch workers within the team (they appear as tmux panes)
3. Coordinate via `SendMessage` between team members
4. User can see all agents working in the swarm view

This applies even for "quick" parallel tasks. If you're about to use the `Agent` tool more than once in a single message, use a team instead.
<!-- WFK:END -->

<!-- WFK:START - File Prefix Conventions -->
## File Prefix Conventions

Every document has a prefix that identifies its type:

| Prefix | Type | Example |
|--------|------|---------|
| `DN` | Daily Note | `DN - 2026-03-27.md` |
| `MN` | Meeting Note | `MN - 2026-03-25 (Strategy).md` |
| `SPC` | Spec | `SPC - New Feature.md` |
| `PL` | Plan | `PL - New Feature Implementation Plan.md` |
| `RE` | Report | `RE - Q1 Analysis.md` |
| `PIC` | Pickup | `PIC - Continue API Work.md` |
| `REF` | Reference | `REF - Git Workflow.md` |
| `RET` | Retrospective | `RET - Sprint 5.md` |
| `WL` | Work Log | `WL - Feature Migration.md` |
| `WS` | Weekly Summary | `WS (W13) - 2026-03-23.md` |
| `IN` | Initiative Log | `IN - Cost Optimization.md` |
| `QA` | Quality Audit | `QA - Feature Validation.md` |
| `ARE` | Agent Report | `ARE - Spec Review.md` |
| `DD` | Design Discussion | `DD - Feature Design.md` |
| `SO` | Structure Outline | `SO - Feature Outline.md` |
| `HAN` | Handoff | `HAN - Sprint 6.md` |

Do NOT invent new prefixes. If a document doesn't fit, use the closest match or ask.
<!-- WFK:END -->

<!-- WFK:START - Vault Structure -->
## Vault Structure

```
Vault/
├── 01_Notes/              ← Time-based writing (daily, weekly, meetings, pickups)
│   ├── Daily/             ← DN - YYYY-MM-DD.md
│   ├── Meetings/          ← MN - YYYY-MM-DD (Topic).md
│   ├── Weekly/            ← WS (WNN) - YYYY-MM-DD.md
│   ├── Pickups/           ← PIC - Topic.md
│   ├── Work Logs/         ← WL - Topic.md
│   └── Reports/           ← SOD, EOD, EOW, SOM, EOM reports
├── 02_Projects/           ← All project documentation
├── 03_Operations/         ← Domain-specific ops content
├── 04_Reference/          ← Long-lived knowledge (REF docs, ADRs, runbooks)
│   ├── ADR/               ← Architecture Decision Records
│   ├── Agents/            ← Agent configuration docs
│   └── Runbooks/          ← Operational runbooks
└── 05_System/             ← Meta infrastructure (templates, workflows)
    ├── Templates/         ← Obsidian note templates
    └── Workflows/         ← Process documentation
```
<!-- WFK:END -->

<!-- WFK:START - Routing Rules -->
## Routing Rules

| Content | Location |
|---------|----------|
| Daily notes | `01_Notes/Daily/DN - YYYY-MM-DD.md` |
| Meeting notes | `01_Notes/Meetings/MN - YYYY-MM-DD (Topic).md` |
| Weekly summaries | `01_Notes/Weekly/` |
| Pickup docs | `01_Notes/Pickups/PIC - Topic.md` |
| Work logs | `01_Notes/Work Logs/WL - Topic.md` |
| Specs | `02_Projects/<project>/specs/YYYY-MM-DD/SPC - Name.md` |
| Plans | `02_Projects/<project>/plans/YYYY-MM-DD/PL - Name.md` |
| Reports | `02_Projects/<project>/reports/YYYY-MM-DD/RE - Name.md` |
| Reviews | `02_Projects/<project>/reviews/YYYY-MM-DD/` |
| REF documents | `04_Reference/REF - Name.md` |
| Architecture decisions | `04_Reference/ADR/` |
| Runbooks | `04_Reference/Runbooks/` |
| Templates | `05_System/Templates/` |
<!-- WFK:END -->

<!-- WFK:START - Required Frontmatter -->
## Required Frontmatter

Every `.md` file must have YAML frontmatter with at minimum:

```yaml
---
date created: YYYY-MM-DD
tags: [relevant-tags]
category: Daily Note | Meeting | Spec | Plan | Report | Reference | Pickup
---
```

Reports may add: `status`, `severity`, `resolved`, `affects`.
Plans may add: `status`, `source` (link to spec).
<!-- WFK:END -->

<!-- WFK:START - Standard Project Structure -->
## Standard Project Structure

Every project under `02_Projects/` follows this convention:

```
02_Projects/<project-name>/
├── specs/
│   └── YYYY-MM-DD/      ← SPC - *.md
├── plans/
│   └── YYYY-MM-DD/      ← PL - *.md
├── reports/
│   └── YYYY-MM-DD/      ← RE - *.md
├── reviews/
│   └── YYYY-MM-DD/
├── agents.md
└── lessons.md
```

The `YYYY-MM-DD` is always the **creation date** of the document. Use today's date for new documents.

**NEVER place files directly in `specs/`, `plans/`, `reports/`, or `reviews/` without a date subfolder.**
<!-- WFK:END -->

<!-- WFK:START - Daily Note Formatting -->
## Daily Note Formatting

- Organize the "Worked on" section with **sub-headings** (`###`) per topic and bullet points underneath.
- Order entries **newest on top** — both sub-headings and bullets within each sub-heading.
<!-- WFK:END -->

<!-- WFK:START - Wikilinks -->
## Wikilinks

- Use **shortest path** (filename only): `[[SPC - New Feature]]`, not full paths
- Obsidian resolves by filename — full paths break when files move
- Display text is optional: `[[SPC - New Feature|Feature Spec]]`
<!-- WFK:END -->

<!-- WFK:START - Agent Files -->
## Agent Files

- Treat all `agents.md` files as CLAUDE.md files
- Treat all `lessons.md` files as CLAUDE.md files
- Load project-specific `agents.md` before working in that project
<!-- WFK:END -->

<!-- WFK:START - Git Safety -->
## Git Safety

Before ANY git operation that modifies state (commit, push, pull, merge, checkout, rebase), follow `/git-safe`. No exceptions.
<!-- WFK:END -->

<!-- WFK:START - Post-Compaction Recovery -->
## Post-Compaction Recovery

After context compaction, re-read this CLAUDE.md before continuing work. It contains behavioral rules (DN formatting, PJL rules, pickup verification, closeout procedures, project structure) that do not survive summarization.
<!-- WFK:END -->

<!-- WFK:START - Rules That Survive Compaction -->
## Rules That Survive Compaction

These are the most-violated rules. They live here so they persist even if CLAUDE.md hasn't been re-read yet.

- **AskUserQuestion for ALL questions.** Every question to the user MUST use the AskUserQuestion tool. Never ask inline, in numbered lists, in bold headers, or embedded in reports. One question per tool call. Present information first, then ask.
- **No hedging.** Never say "likely", "probably", "almost certainly" about technical state. Verify and state the fact, or say "I don't know yet" and check. Hedging about current state is banned.
- **No em dashes.** Use commas, periods, or parentheses instead of `—`. Tight spacing in markdown: no double blank lines.
- **Don't ask answerable questions.** Check filesystem, git, or commands before asking the user. Only ask about intent or preference, not observable state.
- **iTerm tab updates.** Only set the tab when the user explicitly asks (e.g., "set tab", "color tab", "label tab", "iterm", "tag this"). Never set it proactively.
<!-- WFK:END -->

<!-- LOCAL:START - Add your vault-specific rules below this line -->
<!-- LOCAL:END -->
