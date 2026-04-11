---
name: log-work
description: >-
  Log work to the daily note and optionally to project logs and work log files.
  Use this skill when the user wants to record what they've been working on, says
  "log this", "log work", "add to worked on", "update the daily note", or wants
  to capture implementation progress. Works in two modes: simple (daily note entry
  only) or detailed (PJL + optional WL file + daily note summary). Also trigger on
  "what did I work on" if the user wants to retroactively log work from the
  conversation.
---

# Log Work

Log work to **both layers**: the daily note's `## Worked on` section (brief, human-focused) and the project log PJL file (complete, agent-focused). Both are mandatory on every invocation. There is no "simple mode" - every piece of work gets recorded in both places.

**Arguments:** $ARGUMENTS — Description of work, path to a plan, or nothing (will scan conversation context).

## Step 1 — Determine What to Log

If the user provided arguments, use those. Otherwise, scan the current conversation for:
- Files created or modified (specs, reports, plans, code)
- Deployments or pipeline runs
- Research completed
- Decisions made

Ask the user to confirm what should be logged if it's ambiguous.

### Deployment state verification

If the work involved deploying or modifying a live system, verify the state before logging. Check whether code was actually pushed, whether deploys actually ran, whether the change is live. Log what's true, not what was intended:
- Committed but not pushed: log "(committed, not yet pushed)"
- Pushed but not deployed: log "(pushed, not yet deployed)"
- Deployed and verified: log "(deployed - verified at <URL>)"
- If unsure: ask the user

Never log "shipped" or "deployed" without verifying. Future agents trust these entries.

## Step 2 — Always Both Layers

Every invocation writes to:
1. **Daily note** (DN) - brief, human-readable. Outcomes, milestones, what shipped.
2. **Project log** (PJL) - complete, agent-readable. Commits, file paths, decisions, deployment commands, what was tried.

There is no mode selection. Both layers are mandatory. The only optional artifact is a **Work Log** (`WL -` file) for exceptionally heavy days where even the PJL entry would be too dense (10+ tasks, multi-phase sprints). On those days, the PJL links to the WL.

## Step 3 — Identify the Project

Match the work to a **project name** (not a plan name, not an activity name):
- "My SaaS App", not "SaaS App Auth Phase 2"
- "Data Pipeline", not "Pipeline Spec Compliance Phase 3c"

The project name is the broadest stable label. Plans, phases, and activities are detail that goes in the project log.

Identify the project path under `02_Projects/` if one exists.

## Step 3b — Group + Merge Check (Before Writing)

The Worked on section uses a **three-level hierarchy**: group (`###`) > project (`####`) > bullets.

### Determine the group

Groups come from how projects are organized under `02_Projects/`. Check the vault's project structure:

```bash
ls -d 02_Projects/*/
```

Umbrella directories (containing 3+ related projects) become `###` group headings. Standalone projects get a `###` heading directly with no group wrapper.

### Merge into existing headings

Before creating a new `####` heading, scan ALL existing headings under `## Worked on`:

1. **Match by project:** All work on the same project goes under ONE `####`. Different plans, phases, and activities for the same project are the same heading.
2. **If the group `###` heading already exists**, add the new `####` project under it. If the group doesn't exist yet, create both.

**The daily note should have ONE `####` heading per project, not one per plan, phase, activity, or session.**

Every invocation writes both. Do the PJL first (it's the source of truth), then summarize to the daily note.

## Step 4a — Project Log (PJL) — Agent Layer

The PJL is the **knowledge compounding layer** for each project. It accumulates across sessions. When an agent picks up a project, it reads the PJL and immediately knows: what was built, what decisions were made (and why), what was tried and didn't work, what's deployed where, and what to watch out for. The more sessions that log to it, the faster future ramp-up becomes.

1. **Find or create the PJL file** at the project root:
   - `02_Projects/<project>/PJL - <Project Name>.md`
   - No project: `01_Notes/Project Logs/PJL - Topic.md`
   - **One PJL per project.** If one already exists, append to it.

2. **If creating new:** use frontmatter:
   ```yaml
   ---
   date created: YYYY-MM-DD
   tags: [project-log, <project-tag>]
   category: Project Log
   project: "<project name>"
   ---
   ```

3. **Append entries** under today's date heading (`## YYYY-MM-DD`):
   - Create the date heading if it doesn't exist yet
   - **Newest date section at the top** (below frontmatter / title)
   - **Light days:** inline bullets under the date heading
   - **Heavy days** (major sprint, 10+ tasks, multi-phase work): write a brief summary in the PJL entry, then create a dedicated Work Log and link it: `[[WL - Topic YYYY-MM-DD|Full session log]]`

4. **Write for agent memory, not humans.** The daily note is the human layer; the PJL is the machine layer. Include:
   - Exact file paths, function names, table/column names
   - Commit hashes and migration filenames
   - What was deployed, where, and how (environment + URL + command used)
   - Decisions made and **why** (so future agents don't re-litigate)
   - Known issues, blockers, and workarounds still in place
   - What was tried and didn't work (prevents repeating failures)
   - Wikilinks to specs, plans, PICs, IRs, ADRs

### Work Log File (WL) — Heavy Days Only

Only create a WL when the PJL entry would be too dense:
- `02_Projects/<project>/work-logs/WL - <Topic> <YYYY-MM-DD>.md`
- **All granular detail goes here** -- per-task breakdowns, component lists, bug investigation notes, error messages, SQL queries run, config changes made
- Linked from the PJL entry for that date

## Step 4b — Daily Note (DN) — Human Layer

1. Read today's daily note: `01_Notes/Daily/DN - YYYY-MM-DD.md`
2. **Run the group + merge check (Step 3b)** — find the group and any existing heading for this project
3. If a matching `####` heading exists, append new bullets (consolidate if over 4 lines)
4. If no match:
   - Find or create the `### Group Name` heading
   - Add a new `#### Project Name` heading under the group
   - New groups go at the **top** of the Worked on section
   - For standalone items (no group), create a `###` heading directly
5. Add concise, human-friendly bullets:
   - **Write like a progress update to yourself.** What feature was added? What bug was fixed? What shipped? What moved the project forward?
   - Bold the key accomplishment
   - **No technical internals in the DN.** These all belong in the PJL, never the daily note:
     - Phase numbers, task IDs, pass/fail counts ("Phase 3a 6/7 PASS")
     - Commit hashes, migration filenames, line numbers
     - Function names, table/column names, container names
     - Validation metrics, test results, row counts
   - **Good:** "Fixed two pipeline bugs that were crashing email processing and meeting tracking"
   - **Bad:** "Phase 3a entity resolution 6/7 PASS, 2,763 stuck runs cleaned up"
   - **Good:** "Verified the signal pipeline works after the gateway refactor"
   - **Bad:** "Pipeline health check after gateway refactor -- gateway integration verified working"
   - Wikilink output artifacts (specs, plans, reports) only when they add context
   - Link to the PJL file: `[[PJL - Project Name|Project log]]`
6. **HARD RULE: max 4 lines per project (heading + 3 bullets).** The daily note is a table of contents for the day. Everything else is in the PJL (and WL for heavy days).

**Good daily note (heavy day, multiple groups):**
```markdown
## Worked on

### Web Apps
#### Customer Portal
- **Built the full authentication and dashboard** -- login, role-based access, and analytics widgets all live
- Ran UAT with stakeholder, caught and fixed 9 bugs during testing
- Bulk invite emails and final review still needed -- [[PJL - Customer Portal|Project log]]

### Data Systems
#### Analytics Pipeline
- **Wired up initiative linking and meeting intelligence** -- signals auto-tag to active initiatives
- Known limitation: dedup breaks on re-runs due to non-deterministic API -- [[PJL - Analytics Pipeline|Project log]]

### Video Research
- Watched 4 videos on context engineering for coding agents
```

**BAD daily note (build-log style):**
```markdown
#### Customer Portal
- **Portal v3 Phases 0-6 complete** (62/69 tasks) -- auth, ownership, voting, admin
- 10 schema migrations, 9 bugs fixed
```
Phase numbers, task counts, and migration counts are for the PJL. The daily note should say what you accomplished in words a person would use.

## Formatting Rules

Follow the daily note style preferences:
- **Three-level hierarchy:** `## Worked on` > `### Group` > `#### Project`
- **ONE `####` heading per project** — never per plan, phase, or activity
- **Max 4 lines per project** (heading + 3 bullets)
- Lead with outcomes and milestones, not per-task play-by-play
- Bold the key stat or status change
- Wikilink output artifacts and the PJL file
- No commit hashes, migration filenames, component lists, or file counts in the daily note
- No prose paragraphs — bullets only
- Newer groups at top of `## Worked on` section
- Standalone items (no group) use `###` directly

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
