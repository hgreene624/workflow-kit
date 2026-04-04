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
- When clarifying requirements, ask questions **one at a time** with numbered options. Do not bundle multiple questions together.
- Verify assumptions against docs/code before modifying anything.
- Minimum blast radius: only change what's required. Ask before bundling refactors or "improvements" into a fix.
- Write an implementation plan before dispatching agent teams.
- **Never leave discovered issues untracked.** When you find a broken system, failing service, or bug during work on a different task — create a PIC before moving on.
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
| `MN` | Meeting Note | `MN - 2026-03-25 (Topic).md` |
| `IN` | Initiative Log | `IN - Cost Optimization.md` |
| `QA` | Quality Audit | `QA - Feature Validation.md` |
| `ARE` | Agent Report | `ARE - Spec Review.md` |
| `DD` | Design Discussion | `DD - Feature Design.md` |
| `SO` | Structure Outline | `SO - Feature Outline.md` || `HAN` | Handoff | `HAN - Sprint 6.md` |

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

<!-- LOCAL:START - Add your vault-specific rules below this line -->
<!-- LOCAL:END -->
