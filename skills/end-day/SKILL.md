---
name: end-day
description: "Aggregate the day's work into an EOD report and generate tomorrow's SOD (agent context document). Rolls up all closeout entries from the daily note, compares against SOD priorities, runs a mini-retro, discovers goals for user confirmation, then writes the SOD that orient will load tomorrow. On Fridays, also produces an EOW. On the last workday of the month, also produces an EOM. Use this skill when the user says 'end day', 'end of day report', 'EOD report', 'daily report', 'wrap up the day', 'day summary', 'how did today go', 'end-day', or wants a synthesized view of what happened across all sessions. This is different from /closeout (which wraps a single terminal session and creates PICs) — end-day aggregates ALL closeouts into the day's official record and prepares tomorrow's agent context. Should typically run after the last /closeout of the day."
---

# End of Day — Daily Aggregation Report

The EOD is the **official record of what happened today**. It aggregates all closeout entries from the daily note into a single synthesized report, compares reality against the SOD's stated priorities, and discovers goals for user confirmation.

After producing the EOD, this skill also generates **tomorrow's SOD** — the agent context document that orient loads at session start. This keeps everything in one place: end-day is the only skill that writes reports.

On Fridays, this skill also produces an **EOW (End of Week)** report rolling up the week's EODs. On the last workday of the month, it also produces an **EOM (End of Month)** report rolling up the month's EOWs.

## Step 1: Gather today's context

Read in parallel. Skip missing files silently.

**Base path:** `{{VAULT_PATH}}/Work Vault`

1. **Today's daily note** — `01_Notes/Daily/DN - {today}.md`
   - Extract the full `## Worked on` section (this is what closeouts wrote)
   - Extract `## TODO` to check completion
   - Extract `## Meetings` for context
2. **Today's SOD** — `01_Notes/Reports/SOD/SOD - {today}.md`
   - Read Holden's Priorities and Suggested Start sections
   - This is the intent baseline to compare against
3. **PICs created today** — glob `02_Projects/**/PIC - *.md` where `date created` = today
   - These represent carry-forward work from today's closeouts
4. **PICs closed today** — glob for PICs where `closed_date` = today
   - These represent completed work
5. **Current SOW** — most recent in `01_Notes/Reports/SOW/` (if exists)
   - For week-level goal context

## Step 2: Synthesize the EOD

Build the report. Keep it **under 350 words** — this gets loaded into tomorrow's SOD context.

### EOD document structure

```markdown
---
date created: {today}
tags: [report, eod]
category: Report
type: EOD
period: {today}
---

# EOD - {today formatted}

## What Happened
{3-5 sentences. What was accomplished across all sessions today. Group by
project/initiative. Name specific artifacts shipped (specs, plans, deploys,
fixes). Be concrete — "shipped X" not "worked on X."}

## Priority Check
{Compare today's work against the SOD priorities. For each priority:}
- **Priority name**: hit / partial / missed — one-line explanation
{If no SOD existed: "No SOD priorities were set today."}

## What Went Well
{2-3 bullets. Patterns worth repeating — fast debugging, good skill usage,
clean handoffs, effective parallelism.}

## What Didn't
{2-3 bullets. Friction, time sinks, avoidable mistakes, scope creep.
Be honest — this feeds process improvement. If nothing: "Clean day."}

## Goal Discovery
{Based on today's work patterns, suggest 2-3 goals the user appears to be
pursuing. These are proposals — the user confirms or rejects them, and
confirmed goals appear in tomorrow's SOD priorities.

Format:}
- [ ] **Proposed goal** — evidence (what you saw today that suggests this)
- [ ] **Proposed goal** — evidence
{If goals already exist from SOW/previous EODs, carry them forward and
update their status rather than proposing duplicates.}

## Carry Forward
{PICs created today, grouped by project. One line each with the key next step.
If none: "Nothing deferred — all work completed or already tracked."}

## System Changes
{Skills, CLAUDE.md, agents.md, templates, or workflow infrastructure that was
created, modified, or restructured today. This is meta-work — changes to how
agents operate, not project deliverables. Include what changed and why.
If none: omit this section entirely.

Examples:
- "Created `grill` and `test-check` skills — new capabilities from video-intel research"
- "Restructured `plan-spec` to include design exploration and structure verification inline — previously required 3 separate skill invocations"
- "Refactored `git-safe` — moved incident narratives to references/ for token savings"

These entries carry forward in the SOD so future agents know what's new/experimental
vs battle-tested. Treat anything changed in the last 3 days as experimental.}
```

### Save location

Write to `01_Notes/Reports/EOD/EOD - {today}.md`. Create directory if needed.

## Step 3: Present to user

Show the full EOD (it's short enough) and specifically call out the Goal Discovery section — ask the user to confirm or reject each proposed goal with a checkbox interaction:

"Here are the goals I think you're working toward. Confirm the ones that are right, and I'll carry them into tomorrow's SOD:"

Then list the goals. User responds with which to keep. Update the EOD to check the confirmed ones.

## Step 4: Generate tomorrow's SOD

The SOD is an **agent-facing document** — every agent reads it via orient to understand the state of the world and Holden's priorities. It's a rolling week-to-date (WTD) context window that resets when an EOW drops.

### Determine the WTD window
- Find the most recent EOW in `Reports/EOW/` — this is the window start
- If no EOW exists, the window starts from the earliest available EOD
- The window covers everything from that point through today's EOD (just written)

### Gather SOD context
- **EODs within the window** — all EODs from window start through today (already in memory from this run)
- **Current SOW** — most recent in `Reports/SOW/` (for week-level goals)
- **Open pickups** — glob `02_Projects/**/PIC - *.md`, frontmatter only, status: open or picked-up
- **Tomorrow's daily note** — `01_Notes/Daily/DN - {next workday}.md` for TODOs and meetings (if it exists)

### SOD document structure

```markdown
---
date created: {next workday}
tags: [report, sod]
category: Report
type: SOD
period: {next workday}
wtd_window_start: {date of last EOW or earliest EOD}
---

# SOD - {next workday formatted}

## Week-to-Date Summary
{3-4 sentences max. Name what shipped, what's in progress, what stalled.
Group by project/initiative, not by day. This is an index, not a retelling —
agents can read the daily notes for detail. Be terse.}

## Holden's Priorities
{Confirmed goals from today's EOD + any carried from SOW/previous EODs.
These represent what the user is trying to accomplish — agents should align
their suggestions, tradeoff decisions, and pickup recommendations with these.}
- Priority 1
- Priority 2
- Priority 3
{If no confirmed goals exist yet: "No priorities established yet."}

## Open Work
{PICs grouped by project, one line each:}
- **Project Name**: PIC title — next step
{If no open PICs: "No open pickups."}

{IMPORTANT: For each open PIC, check if the WTD summary or recent EODs mention
the same system/pipeline/project as recently shipped or deployed. If so, add a
cross-reference note:}
- ⚠️ **[PIC topic]** touches **[system]** which was shipped [date] — if broken, check deployment state first (env vars, feature flags, container health) before investigating from scratch.
{This prevents agents from wasting sessions reverse-engineering recently-built systems
when the real issue is a deployment regression. See L18 in Agent Lessons.}

## Tomorrow
{TODOs and meetings from tomorrow's daily note. Flag time-sensitive items.
If no note exists or empty: "Nothing scheduled."}

## Recent System Changes
{Aggregate from EODs within the WTD window. Skills, CLAUDE.md, agents.md,
or workflow infrastructure that was created or modified recently. Include
the date of each change. Agents should treat anything changed in the last
3 days as experimental — expect rough edges and verify behavior before
relying on it.
If none: omit this section.}

## Suggested Start
{Recommend a PIC based on: alignment with Holden's priorities > blocking
other work > time-sensitivity > natural continuation of recent work.}
```

Save to `01_Notes/Reports/SOD/SOD - {next workday}.md`. Create directory if needed.

**Next workday calculation:** Friday → Monday, otherwise next calendar day. Skip weekends.

Keep the SOD **under 300 words** — it's loaded into every agent's context via orient.

## Step 5: EOW (Fridays only)


If today is Friday (or the last workday before a weekend), also produce an EOW.

### Gather EOW context
- Read all EODs from this week: `01_Notes/Reports/EOD/EOD - {mon through fri}.md`
- Read the SOW if one exists: `01_Notes/Reports/SOW/`
- Read the current SOM if one exists: `01_Notes/Reports/SOM/`

### EOW document structure

```markdown
---
date created: {today}
tags: [report, eow]
category: Report
type: EOW
period: {week start} to {week end}
---

# EOW - {today formatted}

## Week Summary
{4-6 sentences. What shipped, what progressed, what stalled. This resets
the SOD's WTD window — next Monday's SOD reads this instead of individual EODs.}

## Goal Progress
{For each confirmed goal from SOW or accumulated from EODs:}
- **Goal**: status (completed / on track / stalled / dropped) — evidence

## Week Retro
### Went Well
{3-4 bullets}
### Didn't Go Well
{3-4 bullets}
### Process Changes
{Concrete changes to carry forward — not vague intentions.}

## System Changes This Week
{Aggregate from EODs. Skills, CLAUDE.md, agents.md, workflow infrastructure
created, modified, or restructured this week. Summarize by theme rather than
listing every file — e.g., "Overhauled the spec-to-implement pipeline:
merged design/structure into plan-spec, added test-check to worker dispatch,
made create-spec interview adaptive." Include dates.
If none: omit this section.}

## Next Week Setup
{What's queued for Monday. Open PICs, unfinished goals, upcoming deadlines.
This feeds Monday's SOW.}
```

Save to `01_Notes/Reports/EOW/EOW - {YYYY}-W{ww}.md` (ISO week number format, e.g. `EOW - 2026-W13.md`). This matches the Periodic Notes plugin config so the calendar's week numbers link directly to EOW reports.

## Step 5: EOM (last workday of month only)

If today is the last workday of the month, also produce an EOM.

### Gather EOM context
- Read all EOWs from this month
- Read the SOM if one exists

### EOM document structure

```markdown
---
date created: {today}
tags: [report, eom]
category: Report
type: EOM
period: {YYYY-MM}
---

# EOM - {month name YYYY}

## Month Summary
{5-8 sentences. Initiatives that shipped, progressed, or stalled. Big picture.}

## Initiative Progress
{For each monthly objective from SOM or discovered through EOWs:}
- **Initiative**: status — key milestones hit or missed

## Month Retro
### Wins
{4-5 bullets}
### Losses
{4-5 bullets}
### Systemic Issues
{Patterns that repeated across weeks — these need structural fixes, not willpower.}

## Infrastructure & Workflow Evolution
{Aggregate from EOWs. Major changes to how agents work — new skills, pipeline
restructuring, new safety protocols, workflow simplifications. This is the
strategic view: not every file change, but the shifts in how work gets done.
e.g., "March saw the full CRISPY pipeline go live (create-spec → plan-spec →
implement), video-intel replaced the yt skill, and token efficiency became a
design constraint for all new skills."
If none: omit this section.}

## Next Month Setup
{What carries over. What's new. This feeds next month's SOM.}
```

Save to `01_Notes/Reports/EOM/EOM - {YYYY-MM}.md`.

## Step 6: Vault Hygiene Scan

Before dream, scan the vault for misplaced files created today. This catches routing violations early and identifies which workflows are generating files in the wrong location.

### What to scan

1. **Prefix-location mismatches** - find files created today (frontmatter `date created` = today) whose prefix doesn't match the routing rules:

   | Prefix | Expected Location Pattern |
   |--------|-------------------------|
   | `DN -` | `01_Notes/Daily/` |
   | `MN -` | `01_Notes/Meetings/` |
   | `WS -` | `01_Notes/Weekly/` |
   | `PIC -` | `01_Notes/Pickups/` or `02_Projects/**/pickups/` |
   | `WL -` | `01_Notes/Work Logs/` |
   | `SPC -` | `02_Projects/**/specs/YYYY-MM-DD/` |
   | `PL -` | `02_Projects/**/plans/YYYY-MM-DD/` |
   | `RE -` | `02_Projects/**/reports/YYYY-MM-DD/` |
   | `ARE -` | `02_Projects/**/reports/YYYY-MM-DD/` or `02_Projects/**/reviews/YYYY-MM-DD/` |
   | `REF -` | `04_Reference/` |
   | `DD -` | `02_Projects/**/designs/YYYY-MM-DD/` |
   | `SO -` | `02_Projects/**/structures/YYYY-MM-DD/` |
   | `RET -` | `02_Projects/**/reports/YYYY-MM-DD/` |
   | `HAN -` | `02_Projects/**/reports/YYYY-MM-DD/` |

2. **Project structure violations** - files in `02_Projects/` that aren't in a dated subfolder when they should be (specs, plans, reports, reviews sitting directly in the type folder without a `YYYY-MM-DD/` subdirectory).

3. **Orphan files** - markdown files at vault root or in unexpected locations (not in `01_Notes/`, `02_Projects/`, `03_Operations/`, `04_Reference/`, `05_System/`).

4. **Missing frontmatter** - files created today without required `date created`, `tags`, or `category` fields.

### How to scan

```bash
# Find all .md files created today (by frontmatter date, not filesystem)
grep -rl "date created: {today}" "Work Vault/" --include="*.md"
```

Then for each file, check its prefix against the expected location table above.

### Actions

- **Auto-fix obvious cases**: A `DN - 2026-04-04.md` found at vault root can be moved to `01_Notes/Daily/` without asking.
- **Flag ambiguous cases**: A `RE -` file outside any project needs user input on which project it belongs to. Present as a numbered list.
- **Track the source**: For each violation, note what likely created it (check today's daily note for the matching topic). Add a one-line note in the EOD's "What Didn't" section: "Vault hygiene: [file] was created in [wrong location], likely by [skill/action]. Should go in [correct location]."
- **If zero violations**: Skip silently. Don't report "vault is clean" unless the user asks.

### Improving the workflow

When a violation is traced to a specific skill, park a note to that skill's project agents.md:
```
- **Routing bug**: [skill name] created [file] in [wrong location] on [date]. Expected location: [correct path]. Fix the skill's file creation logic.
```

This creates a feedback loop: vault scan finds violations, parks bugs, future agents fix the skills.

## Step 7: Dream (memory consolidation)

After all reports are written, run `/dream` to consolidate automemory. This is the natural end-of-day moment for memory hygiene — the day's work is captured in reports, and any new memories from the session should be merged, deduplicated, and pruned before the next day starts.

Invoke the dream skill directly. No user confirmation needed — it runs automatically as the final step of end-day.

## Constraints
- Always produce EOD. EOW and EOM are conditional on the day.
- Always run `/dream` as the final step — no exceptions.
- Goal discovery is the key differentiator — don't skip it even on light days.
- Don't duplicate closeout's work — closeout writes to the daily note and creates PICs. End-day reads what closeout wrote and synthesizes.
- If no closeouts happened today (daily note Worked on is empty), produce a minimal EOD noting it was a light/off day.
- Confirmed goals persist across EODs until completed or explicitly dropped.
