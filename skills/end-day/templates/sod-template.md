# SOD Template

The SOD is an agent-facing document loaded during orient. It tells a fresh agent: what's the state of the world, what are the priorities, and what to do first.

Same writing rules as EOD (movement not status, conclusion first, assume zero context, no jargon without parenthetical).

## WTD Window
- Find the most recent EOW in `Reports/EOW/` -- this is the window start
- If no EOW exists, the window starts from the earliest available EOD
- The window covers everything from that point through today's EOD

## Context to Gather
- EODs within the window
- Current SOW (most recent in `Reports/SOW/`)
- Strategic goals reference docs (if any exist in `04_Reference/`)
- Open pickups: glob `02_Projects/**/PIC - *.md`, status: open or picked-up
- Tomorrow's daily note (if it exists)

## Template

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
{3-4 sentences. Name what shipped (with counts), what's in progress, what stalled.
Group by project/initiative, not by day. Every project name includes a parenthetical
explaining what it is on first mention.}

## User's Priorities
{Confirmed goals from the most recent EOD. Numbered by priority.
Each goal includes: the goal name, the PIC or artifact that advances it,
and the concrete outcome expected this session.}
1. **{Goal}** -- {PIC or next step}. Target: {concrete outcome for today}.
2. **{Goal}** -- {PIC or next step}. Target: {outcome}.

## Strategic Goals
{Read from reference docs. List each active goal with one-line status.
Flag goals with "no movement" for 3+ consecutive SODs.}
- **{Goal name}**: {advancing / no movement / not yet started}. {One sentence of evidence.}

## Open Work
{PICs grouped by project. Project names include parenthetical on first mention.
One line each: PIC name, next step.}

**{Project} ({what the project is}):**
- [[PIC - Name]] -- {next step}

{Cross-reference PICs against recently shipped systems:}
- If a PIC touches a system shipped in the last 3 days, flag: "check deployment state before investigating from scratch"

## Tomorrow
{TODOs and meetings from the daily note. If empty: "Nothing scheduled."}

## Recent System Changes
{From EODs in the WTD window. Date each. Group by theme.
Anything changed in last 3 days is experimental.}

## Suggested Start
{Directive, not descriptive. Tell the agent exactly what to do first.
Include: which PIC to load, what the target outcome is, and why this is priority #1.
"Load [[PIC - Name]]. Target: {outcome} by end of session. Why first: {deadline/blocker/dependency}."}
```

Save to `01_Notes/Reports/SOD/SOD - {next workday}.md`.

**Next workday calculation:** Friday -> Monday, otherwise next calendar day. Skip weekends.

Keep the SOD **under 300 words** (excluding the Open Work PIC list).
