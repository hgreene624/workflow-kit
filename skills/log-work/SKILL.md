---
name: log-work
description: >-
  Log work to the daily note AND project log. Use this skill when the user wants
  to record what they've been working on, says "log this", "log work", "add to
  worked on", "update the daily note", or wants to capture implementation progress.
  Always writes to both layers: daily note (human-readable) and PJL (agent-readable).
  Also trigger on "what did I work on" if the user wants to retroactively log work.
---

# Log Work

Log work to **both layers**: the daily note's `## Worked on` section (brief, human-focused) and the project log PJL file (complete, agent-focused). Both are mandatory on every invocation. There is no "simple mode" -- every piece of work gets recorded in both places.

**Arguments:** $ARGUMENTS — Description of work, path to a plan, or nothing (will scan conversation context).

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{paths.daily_notes}/DN - YYYY-MM-DD.md`, `{paths.projects}/<project>/PJL - <Name>.md`). If the file doesn't exist, use defaults and warn once.

## Step 1 — Determine What to Log

If the user provided arguments, use those. Otherwise, scan the current conversation for:
- Files created or modified (specs, reports, plans, code)
- Deployments or pipeline runs
- Research completed
- Decisions made

Ask the user to confirm what should be logged if it's ambiguous.

### Environment Disambiguation (MANDATORY for Flora app work)

If the work being logged touched a Flora app (KB, admin, portal, mail, fwis-viewer, home, reservations, mailbox-viewer, revenue-dashboard, culinary-cottages, or anything in `~/Repos/flora-monorepo/`), the log entry MUST disambiguate which environment was affected. Three valid forms:

- **Local-only iteration** — write `(local — verified at http://localhost:<port>/<path>)` after the bullet. Be explicit that this did NOT update production.
- **Deployed to production** — write `(deployed via flora-deploy <service> — verified at https://myarroyo.com/<app>/<path>)` after the bullet. Include the verification URL you actually hit.
- **Both** — write `(local + deployed via flora-deploy <service>)`.

Bare phrases like "fixed KB hydration", "deployed mailbox-viewer", "tested admin page" are AMBIGUOUS and create false confidence. Future agents reading the daily note will not know whether myarroyo.com was actually updated. Always include the environment label and a verification URL.

**Push ≠ Deploy.** As of 2026-04-07, `git push origin main` does NOT auto-deploy. If the work involved a code change to a Flora app and no `flora-deploy` or `safe-build` command was run, the change is LOCAL ONLY and the log must say so. Pushing to main without running the deploy command is not a deploy.

## Step 2 — Always Both Layers

Every invocation writes to **both**:
1. **Daily note** (DN) -- brief, human-readable, scannable. What you'd say in a 30-second standup.
2. **Project log** (PJL) -- complete, agent-readable. Commits, file paths, decisions, deployment commands, what was tried.

There is no mode selection. Both layers are mandatory. The only optional artifact is a **Work Log** (`WL -` file) for exceptionally heavy days where even the PJL entry would be too dense (10+ tasks, multi-phase sprints). On those days, the PJL links to the WL.

## Step 3 — Identify the Topic and Project

Match the work to a **project name** (not a plan name, not an activity name):
- "Culinary Cottages Portal", not "CCP v3 Phase 2"
- "Signal Engine", not "FWIS Spec Compliance Phase 3c"
- "Document Generator", not "DocGen NLM Guided Creation"

The project name is the broadest stable label. Plans, phases, and activities are detail that goes in the project log.

Identify the project path under `02_Projects/` if one exists.

## Step 3b — Group + Merge Check (Before Writing)

The Worked on section uses a **three-level hierarchy**: group (`###`) > project (`####`) > bullets.

### Determine the group

Match the project to its group:

| Group (`###`) | Projects (`####`) |
|---|---|
| Flora Apps | Flora KB, Document Generator, Revenue Dashboard, Reservation App, Admin Panel, Culinary Cottages Portal, Mail |
| Flora Intelligence | Signal Engine (FWIS, MIP, transcription pipeline), AI Gateway |
| Infrastructure | VPS, CI/GHCR, Local Dev, Cron System |
| Restaurant Ops | Odoo, Simphony, Server Manual, Tastings, Revenue Reports |
| Workflow Kit & Tooling | WFK, CC Analytics |

**Standalone items** (Video Research, Process Improvements, Pickup Triage, Vault Maintenance, etc.) get a `###` heading directly — no group wrapper.

### Merge into existing headings

Before creating a new `####` heading, scan ALL existing headings under `## Worked on`:

1. **Match by project:** All work on the same project goes under ONE `####`. "CCP v3 Phase 0", "CCP Owner Portal Routing Deploy" are all `#### Culinary Cottages Portal` under `### Flora Apps`.
2. **Common abbreviations:** MIP/FWIS/FAO → Signal Engine, CCP → Culinary Cottages Portal, DocGen → Document Generator.
3. **If the group `###` heading already exists**, add the new `####` project under it. If the group doesn't exist yet, create both.

**The daily note should have ONE `####` heading per project, not one per plan, phase, activity, or session.**

## Step 4 — Write Both Layers

Every invocation writes both. Do the PJL first (it's the source of truth), then summarize to the daily note.

### 4a. Project Log (PJL) — Agent Layer

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
   - **Heavy days** (major sprint, 10+ tasks, multi-phase work): write a brief summary in the PJL entry, then create a dedicated **Work Log** (`WL -` file) in `work-logs/` and link it: `[[WL - Topic YYYY-MM-DD|Full session log]]`

4. **Write for agent memory, not humans.** The daily note is the human layer; the PJL is the machine layer. Include:
   - Exact file paths, function names, table/column names, container names
   - Commit hashes and migration filenames
   - What was deployed, where, and how (environment + URL + command used)
   - Decisions made and **why** (so future agents don't re-litigate)
   - Known issues, blockers, and workarounds still in place
   - What was tried and didn't work (prevents repeating failures)
   - Wikilinks to specs, plans, PICs, IRs, ADRs

### Work Log File (WL) — Heavy Days Only

Only create a WL when the PJL entry would be too dense:
- `02_Projects/<project>/work-logs/WL - <Topic> <YYYY-MM-DD>.md`
- **All granular detail goes here** -- commit hashes, migration numbers, per-task breakdowns, component lists, bug lists
- Linked from the PJL entry for that date

### 4b. Daily Note (DN) — Human Layer

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
   - **Bad:** "Phase 3a entity resolution 6/7 PASS, 2,763 stuck MIP runs cleaned up"
   - **Good:** "Verified the signal pipeline works after the gateway refactor"
   - **Bad:** "FWIS pipeline health check after gateway refactor -- gateway integration verified working"
   - Wikilink output artifacts (specs, plans, reports) only when they add context
   - Link to the PJL file: `[[PJL - Project Name|Project log]]`
6. **HARD RULE: ≤ 4 lines per project (heading + 3 bullets max).** The daily note is a table of contents for the day. Everything else is in the PJL (and WL for heavy days).

**Good daily note (heavy day, multiple groups):**
```markdown
## Worked on

### Flora Apps
#### Culinary Cottages Portal
- **Built the full owner portal** -- authentication, ownership cards, voting flow, and admin controls all live at myarroyo.com/owners/
- Ran live UAT with dad, caught and fixed 9 bugs during testing
- Bulk signup emails and Patrick's final review still needed before owners can use it -- [[PJL - Culinary Cottages Portal|Project log]]
#### Document Generator
- **Shipped the guided document creation flow** -- overlay wizard walks users through research and generation -- [[PJL - Document Generator|Project log]]

### Flora Intelligence
#### Signal Engine
- **Verified signal pipeline works after gateway refactor** -- fixed two bugs that were crashing email processing and meeting tracking
- Cleaned up stuck meeting processing runs and backfilled missing staff records -- [[PJL - Signal Engine|Project log]]

### Infrastructure
- **Fixed the stale image deploy bug** and built automatic cron-to-database sync -- [[PJL - Infrastructure|Project log]]

### Video Research
- Watched 4 videos, 2 deep dives on harness design and context engineering for coding agents
```

**BAD daily note (too technical):**
```markdown
#### Signal Engine
- **FWIS pipeline health check after gateway refactor** -- gateway integration verified working, Phase 3a entity resolution 6/7 PASS, 2,763 stuck MIP runs cleaned up
- Fixed two pipeline bugs: MIP run-tracking (dirty transaction retry) and email classification query crash (`attachment_names` column)
- Disabled all FWIS crons until validation complete; backfilled people tiers (jamie to manager, reservations@ as system)
```
Phase numbers, pass/fail counts, row counts, column names, function names -- all PJL material. The daily note should tell you what moved the project forward, not how the sausage was made.

**Also BAD (build-log style):**
```markdown
#### Culinary Cottages Portal
- **CCP v3 Phases 0-6 complete** (62/69 tasks) -- auth, ownership, voting, admin
- 10 schema migrations, 9 bugs fixed
- Phase 7 cutover remaining
```
Phase numbers, task counts, and migration counts are for the PJL.

## Formatting Rules

Follow the daily note style preferences:
- **Three-level hierarchy:** `## Worked on` > `### Group` > `#### Project`
- **ONE `####` heading per project** — never per plan, phase, or activity
- **≤ 4 lines per project** (heading + 3 bullets max)
- Lead with what moved the project forward -- features added, bugs fixed, things shipped
- Bold the key accomplishment or outcome
- Wikilink output artifacts and the PJL file
- **Nothing technical in the DN.** No commit hashes, migration filenames, component lists, file counts, phase numbers, pass/fail counts, row counts, column names, function names, container names, or validation metrics
- No prose paragraphs — bullets only
- Newer groups at top of `## Worked on` section
- Standalone items (no group) use `###` directly
- NO "Lifelogs & Meeting Notes" subsection — those go in Meetings

## Examples

See `references/examples.md` for good/bad daily note and work log formatting examples.
