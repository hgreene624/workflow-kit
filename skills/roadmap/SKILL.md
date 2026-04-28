---
name: roadmap
description: >-
  Create or refresh a strategic roadmap (RM) and its Weekly Focus (WF) companion.
  Audits all open work, aligns it to the user's stated strategic goals, triages
  PICs into active/parked/blocked, phases tasks across weeks, and produces decision
  rules for staying focused. Use this skill when the user says "roadmap", "create
  roadmap", "refresh roadmap", "strategic plan", "what should I focus on", "priority
  reset", "workload audit", "realign priorities", or after a major Patrick meeting
  changes strategic direction. Also use when the current RM is expired (past its
  week range) and orient flags "no current roadmap."
---

# Roadmap — Strategic Planning and Weekly Focus

Create a goal-driven strategic roadmap (RM) that maps all active work to the user's
stated goals, triages open PICs, phases tasks across weeks, and produces a Weekly Focus
(WF) as the operational lever. The RM is the "why" behind every PIC and SOD priority.
The WF is the "what this week" derived from it.

**Design principles:**
- Goal-driven, not project-driven. Work organizes under strategic goals, not project names.
- PICs are the unit of work. The RM references existing PICs, it does not invent tasks.
- Capacity is finite. The skill enforces triage: active vs parked vs blocked.
- Decision rules prevent accumulation. Every RM includes situational rules for handling new requests.
- The WF is derived from the RM, never created independently.

## Path resolution

Read `~/.claude/wfk-paths.json` at startup for vault paths. Fall back to defaults if missing.

## Input

Accept one of:
- No argument: full roadmap creation from current state
- `refresh`: update the existing RM with current work state (close completed phases, open new ones)
- `weekly-focus` or `wf`: generate only a new WF from the current RM (for a new week)
- A path to a meeting note (MN): create roadmap incorporating freshly triaged Patrick requests

## Step 0: Load context

Read in parallel:

1. **Current RM** (most recent file in `{vault_root}/01_Notes/Roadmaps/`). If one exists, note its week range and status. A refresh updates it; a new creation supersedes it.
2. **Current WF** (most recent `WF - *.md` in `{vault_root}/01_Notes/Reports/`). Shows what was planned this week.
3. **Patrick's strategic goals** at `{vault_root}/04_Reference/REF - Patrick Strategic Goals.md`. These are the goal headings for the RM. If this file does not exist, goals must come from the user.
4. **Patrick Request Log** at `{vault_root}/03_Operations/Work REF/Patrick Request Log.md`. Shows all requests and their current status/tier.
5. **Most recent SOD**. Shows today's priorities and open work inventory.
6. **Most recent EOW**. Shows what shipped last week, goal progress, retro findings.
7. **Most recent EOM** (if within first week of month). Shows monthly carry-forwards.

## Step 1: Audit current work

Scan the vault to build a complete inventory. Run these in parallel:

### PICs
Glob `{vault_root}/02_Projects/**/PIC - *.md` and `{vault_root}/02_Projects/**/pickups/**/PIC - *.md`.
For each PIC, read its frontmatter to extract: title, status (open/closed/picked-up), date created, project.
Count totals: open, closed, picked-up.

### Patrick Requests
Read the Patrick Request Log. Count by tier: ACT, SPEC, WATCH, PARK, DONE.
Identify any SPEC-tier PRs that have had no activity in 7+ days.

### Project Logs
Glob `{vault_root}/02_Projects/**/PJL - *.md`.
For each PJL, check the most recent date heading. Flag as "stalled" if no entry in the last 7 days.

### Recent daily notes
Read the last 5 daily notes (`DN - *.md` sorted by date). Extract:
- Context switching patterns (how many different projects per day)
- Whether SOD priorities were actually worked on

## Step 2: Confirm strategic goals

Present the audit summary to the user:

```
Workload snapshot:
- [N] open PICs ([X] active, [Y] parked, [Z] blocked)
- [N] Patrick Requests ([A] ACT, [B] SPEC, [C] WATCH)
- [N] active PJLs, [M] stalled (no activity >7 days)
- Context switching: avg [N] projects/day over last 5 days
```

Then present the strategic goals. If `REF - Patrick Strategic Goals.md` exists, show those goals and ask if they're still current. If it doesn't exist, ask the user to state 3-5 goals.

Use AskUserQuestion with multiSelect to confirm which goals are active for this roadmap period. Present each goal as an option with a brief description. The user can also add new goals via "Other."

## Step 3: Align work to goals

For each confirmed goal, scan the open PICs, active PRs, and recent PJL entries to find related work. Build a mapping:

| Goal | Related PICs | Related PRs | Recent PJL activity |
|---|---|---|---|

Present the alignment to the user. Flag:
- PICs that don't align to any goal (candidates for parking)
- Goals with no related PICs (need new PICs or the goal is aspirational)
- PRs at SPEC or WATCH tier that could be upgraded if they serve an active goal

Use AskUserQuestion to confirm the alignment. One question: "These [N] PICs don't align to any active goal. Park them?" with multiSelect showing each unaligned PIC.

## Step 4: Triage PICs

Classify every open PIC into one of:
- **Active**: serves an active goal, has a clear next step, not blocked
- **Parked**: serves a goal but is not this period's priority (with explicit reason)
- **Blocked**: has an external dependency preventing progress (name the blocker)

Apply the capacity gate: if active PICs exceed 8, flag and ask the user to park more. Present the triage result and get confirmation.

## Step 5: Phase the work

For each active goal, organize its PICs and tasks into phases with week assignments:

1. Read each active PIC's "Next steps" or equivalent section
2. Identify dependencies between PICs (if PIC A's output feeds PIC B)
3. Group into phases: Phase 1 (this week), Phase 2 (next week), Phase 3 (week after)
4. Within each phase, create a task table:

```markdown
| # | Task | PIC / Source | Status | Dependency |
|---|------|-------------|--------|------------|
| 1.1 | [task description] | [[PIC - Name]] | todo | none |
| 1.2 | [task description] | [[PIC - Name]] | todo | 1.1 |
```

Task descriptions come from the PICs' next steps, not invented. If a PIC has no next steps, flag it as needing update.

Add per-goal sections as needed:
- **Known issues**: bugs, edge cases, or risks discovered during audit
- **Supporting infrastructure**: work already done that this goal depends on
- **Parked features**: WATCH-tier items related to this goal

## Step 6: Build parked work section

Organize all non-active work into:
- **Parked PICs** (with reason for each: "blocked on external", "future phase", "not this period")
- **WATCH PRs** (Patrick requests not on critical path this period)
- **PARK PRs** (prerequisites or future phases)
- **Stalled PJLs** (no activity >7 days, listed for visibility)

## Step 7: Write decision rules

Generate 3-5 situational decision rules based on the current context. Standard rules:

1. **New Patrick request?** Check against Goals 1-N. If it serves an active goal, absorb. If not, WATCH tier.
2. **Infrastructure incident?** Fix if blocking active goals. Otherwise PIC it and continue.
3. **Minor recurring task?** Do in <30 min or park with reason.
4. **Open PIC count exceeds [threshold]?** Triage before adding more.

Add context-specific rules based on deadlines, demos, or constraints identified during audit.

## Step 8: Write the RM document

Calculate the week range. Use ISO week numbers (e.g., W17-W19). Write to:
`{vault_root}/01_Notes/Roadmaps/{today}/RM - Strategic Roadmap {week_range}.md`

**Frontmatter:**
```yaml
---
date created: YYYY-MM-DD
tags: [plan, strategic, roadmap]
category: Plan
status: active
source: "Workload audit {today}"
goals: [goal1, goal2, goal3]
week_range: "YYYY-WNN to YYYY-WNN"
active_pics: N
parked_pics: N
---
```

**Structure:**
1. Introduction paragraph: what this RM covers, how many PICs triaged, link to WF
2. One `##` section per strategic goal (with phases, task tables, known issues, parked features)
3. `## Quick wins` section (low-effort tasks not tied to a goal)
4. `## Parked work` section (PICs, WATCH PRs, PARK PRs, stalled PJLs)
5. `## Decision rules` section

## Step 9: Write the WF document

Derive the Weekly Focus from the RM's first-week phases. Write to:
`{vault_root}/01_Notes/Reports/{today}/WF - {iso_week}.md`

**Frontmatter:**
```yaml
---
date created: YYYY-MM-DD
tags: [report, weekly-focus]
category: Report
week: YYYY-WNN
status: active
source: "[[RM - Strategic Roadmap {week_range}]]"
---
```

**Structure:**
1. Introduction: how many PICs, how many goals, how many active this week
2. `## This week's goals` (one `###` per active goal):
   - Active PICs for this week (wikilinked)
   - What "done" looks like (concrete, verifiable)
   - Dependencies
3. `## Also active` (quick wins or small tasks)
4. `## Explicitly not this week` (everything parked, with reason)
5. `## Decision rules for this week` (subset of RM rules)

## Step 10: Mark previous RM/WF as superseded

If a previous RM exists, update its frontmatter: `status: superseded` and add `superseded_by: "[[RM - Strategic Roadmap {new_range}]]"`. Same for previous WF.

## Step 11: Present summary

Output a concise summary:

```
Roadmap created: [[RM - Strategic Roadmap {range}]]
Weekly Focus: [[WF - {week}]]

Goals:
1. [Goal 1] — [N] PICs active, Phase 1 this week
2. [Goal 2] — [N] PICs active, Phase 1 this week
3. [Goal 3] — [N] PICs active, starts [week]

Triage: [X] PICs active, [Y] parked, [Z] blocked
Stalled: [N] PJLs with no activity >7 days
Decision rules: [N] rules set

The orient skill will load this RM at session start.
The end-day skill will report goal progress against it.
The triage-patrick skill will gate new requests against the Weekly Focus.
```

## Refresh mode

When called with `refresh`:
1. Read the current RM
2. Re-run Steps 1-4 (audit, confirm goals, align, triage) against current state
3. Update task statuses in-place (todo -> done for completed work)
4. Close completed phases, open new ones
5. Recalculate parked work
6. Write updated RM (same file, bumped version in frontmatter)
7. If the current week's WF is stale, regenerate it

## Weekly Focus only mode

When called with `wf`:
1. Read the current RM (error if none exists)
2. Identify the upcoming week's phases from the RM
3. Generate a new WF document for that week
4. Mark the previous WF as superseded

## Writing rules

Load and follow `WP - General.md` from Writing Profiles. The RM is a Plan (category: Plan). Task tables use the established column format. No em dashes. Tight spacing. Wikilink all PICs, PRs, and PJLs.

## Error handling

- **No strategic goals found**: Ask the user. Do not proceed without confirmed goals.
- **No open PICs**: Still create the RM, but flag that goals have no active work and recommend creating PICs.
- **PIC count exceeds 12**: Hard warning. Triage must reduce to 8 or fewer before the RM is finalized.
- **Previous RM still active for current week**: Ask whether to refresh or supersede.
