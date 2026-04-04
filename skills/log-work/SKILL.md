---
name: log-work
description: >-
  Log work to the daily note and optionally a dedicated work log file. Use this
  skill when the user wants to record what they've been working on, says "log this",
  "log work", "add to worked on", "update the daily note", or wants to capture
  implementation progress. Works in two modes: simple (daily note entry only) or
  detailed (WL file + daily note summary). Also trigger on "what did I work on"
  if the user wants to retroactively log work from the conversation.
---

# Log Work

Log work to the daily note's `## Worked on` section, and optionally to a dedicated work log (`WL -`) file for complex work.

**Arguments:** $ARGUMENTS — Description of work, path to a plan, or nothing (will scan conversation context).

## Step 1 — Determine What to Log

If the user provided arguments, use those. Otherwise, scan the current conversation for:
- Files created or modified (specs, reports, plans, code)
- Deployments or pipeline runs
- Research completed
- Decisions made

Ask the user to confirm what should be logged if it's ambiguous.

## Step 2 — Determine the Mode

**Simple mode** (daily note entry only):
- Work fits in 2-4 bullets
- Single task, quick fix, one-off research
- No associated plan, or the plan work is trivial today

**Detailed mode** (WL file + daily note summary):
- Work has 5+ distinct sub-tasks
- Work is against a plan (`PL -` file)
- Multi-step implementation, complex debugging
- User explicitly asks for a work log

If there's an associated plan, default to detailed mode. Otherwise default to simple unless the work is clearly complex.

## Step 3 — Identify the Topic and Project

Match the work to a topic name:
- If plan-backed: use the plan name (e.g., "{{ORG}} Migration Orchestration Plan")
- If project-scoped: use the project name (e.g., "Signal Engine", "IK Buckets")
- If standalone: use a descriptive label (e.g., "Vault Maintenance", "Recipe Extraction")

Identify the project path under `02_Projects/` if one exists.

## Step 3b — Merge Check (Before Writing)

Before creating a new `###` heading, scan ALL existing headings under `## Worked on` for the same underlying project or plan:

1. **Match by app/project first (highest priority):** Group all work on the same app or project under ONE heading. "Mail App — Group Intelligence Spec", "Mail App — UI Polish Phase 3", "Mail App — Feature Parity Sprint" are all `### Mail App`. "MIP Phase 2", "MIP Phases 3-5", "Meeting Intelligence Pipeline" are all `### Meeting Intelligence Pipeline`. The heading is the **app or project name**, not the specific activity.
2. **Match by plan wikilink:** If the new entry references the same `[[PL - ...|Plan]]` as an existing heading, append to it.
3. **Common abbreviations:** MIP = Meeting Intelligence Pipeline, FAO = FWIS Activation Orchestration, CC = Claude Code. Match these to their full project names.

**When merging into an existing heading:**
- Keep the heading as the broad project/app name (e.g., `### Mail App`)
- Use **bold sub-labels** within the bullets to distinguish different workstreams:
  ```markdown
  ### Mail App
  - **UI Polish Phase 3 complete** — collapsible groups, batch summarize, toolbar consolidation
  - **Group Intelligence spec** drafted — [[SPC - Mail Group Intelligence]], agentic analysis on category headers
  - [[WL - Mail UI Polish|Full log]]
  ```
- Consolidate older bullets if the entry exceeds 6 lines — summarize, don't enumerate
- If multiple plans are linked, put the most relevant one on the heading line and link others in bullets

**The daily note should have ONE heading per app/project, not one per activity, session, or phase.** All mail work = one `### Mail App` entry. All MIP work = one `### Meeting Intelligence Pipeline` entry.

## Step 4a — Simple Mode: Update Daily Note

1. Read today's daily note: `01_Notes/Daily/DN - YYYY-MM-DD.md`
2. **Run the merge check (Step 3b)** — find any existing heading for this project/plan
3. If a matching heading exists, append new bullets to it (consolidate if over 6 lines)
4. If no match, create a new `### Topic Name` heading under `## Worked on`
   - New topics go at the **top** of the Worked on section (below `## Worked on`)
   - Link spec/plan on the heading line: `### Topic — [[PL - ...|Plan]]`
5. Add concise, action-oriented bullets:
   - Lead with what was done, not what was learned
   - Bold key stats inline
   - Wikilink output artifacts
6. Done.

## Step 4b — Detailed Mode: Create/Update WL File + Daily Note

### Work Log File

1. **Find or create the WL file:**
   - Plan-backed: same directory as the plan (e.g., `02_Projects/.../plans/YYYY-MM-DD/WL - Plan Name.md`)
   - Project-scoped, no plan: `02_Projects/<project>/work-logs/WL - Topic.md`
   - No project: `01_Notes/Work Logs/WL - Topic.md`

2. **If creating new:** use frontmatter:
   ```yaml
   ---
   date created: YYYY-MM-DD
   tags: [work-log, <project-tag>]
   category: Work Log
   plan: "[[PL - Plan Name]]"       # if plan-backed
   project: "<project name>"
   ---
   ```

3. **Append entries** under today's date heading (`## YYYY-MM-DD`):
   - Create the date heading if it doesn't exist yet
   - Each entry: `### HH:MM — Short description` with detail bullets
   - Include: what changed, why, artifact links, key metrics, commit hashes, errors resolved

### Daily Note Summary

1. Read today's daily note
2. Find or create the `### Topic` heading under `## Worked on`
3. Add **3-5 summary bullets MAX** — this is a summary, NOT a task log
4. Add final bullet linking to the WL file: `- [[WL - Topic Name|Full log]]`
   - If this link bullet already exists, don't duplicate it

**HARD RULE: The daily note entry for ANY topic must be ≤ 6 lines (heading + 5 bullets max).** If you need more detail, it goes in the WL file. The daily note is a scannable overview — commit hashes, file counts, component lists, and per-task descriptions belong in the WL file ONLY.

**Good daily note entry (sprint with 16 tasks):**
```markdown
### {{ORG}} Migration — [[PL - {{ORG}} Migration Orchestration Plan|Plan]]
- Completed **Phase 14 (FWIS Viewer)** — SvelteKit → Next.js, 16 routes, 17 AG Grid instances
- **16/17 tasks Done**, 4 post-deploy fixes, build:fix ratio **73:27**
- Old <APP_1> sunset — **9.9 GB** reclaimed, M12 (Core Apps Live) achieved
- [[WL - {{ORG}} Migration Orchestration Plan|Full log]]
```

**BAD daily note entry (same sprint — too detailed):**
```markdown
### {{ORG}} Migration — [[PL - ...]]
- P14.1 Audit — 16 routes, 17 AG Grid instances...
- P14.2 Scaffold — apps/fwis-viewer/ created...
- P14.3 Meetings — AG Grid 8 cols...
- P14.4 Signal Explorer — 608-line client...
- P14.5 People Grid — dept cards...
(15 more bullets with commit hashes and component lists)
```
This is a task log, not a summary. All that detail goes in the WL file.

## Formatting Rules

Follow the daily note style preferences:
- Group by `### Topic` headings with wikilinks to spec/plan
- Short, action-oriented bullets — lead with outcomes, not per-task play-by-play
- Bold key stats inline (totals, ratios, milestones — not per-commit details)
- Wikilinks to output files and retro/handoff reports
- No prose paragraphs — bullets only
- Newer entries at top of `## Worked on` section
- NO "Lifelogs & Meeting Notes" subsection — those go in Meetings
- **≤ 6 lines per topic** (heading + 5 bullets max) — link to WL file for detail

## Examples

See `references/examples.md` for good/bad daily note and work log formatting examples.
