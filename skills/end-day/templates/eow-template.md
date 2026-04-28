# EOW Template

Produced on Fridays (or last workday before weekend). Resets the SOD's WTD window.

Same writing rules as EOD apply here, plus:

## Additional Writing Rules

6. **Standalone document.** The EOW must make sense to someone who didn't read any daily notes this week. Every project reference includes what the project IS, not just its name.
7. **Week-level patterns, not day-level replay.** Don't list Monday's work then Tuesday's work. Synthesize: what themes emerged, what moved across the week, what's stuck.
8. **Retro items carry forward only if unresolved.** A retro item with a completed action doesn't repeat next week. An item without a fix carries forward until resolved.

## Context to Gather
- All EODs from this week
- All DNs from this week (for `day_rating` frontmatter values)
- Current SOW (if exists)
- Current SOM (if exists)

## Template

```markdown
---
date created: {today}
tags: [report, eow]
category: Report
type: EOW
period: {week start} to {week end}
week_rating_avg: {average of day_rating values from this week's DNs, 1 decimal place}
---

# EOW - {today formatted}

## Summary
{3-4 sentences. The 15-second scan.
Lead with the single most important outcome of the week.
Name what shipped (with counts). Name what's blocked.
End with what's set up for next week.
This paragraph alone should tell someone "what happened this week."}

## What Shipped
{Concrete deliverables grouped by project. Metrics first.
Each project gets a one-line description in parentheses on first mention
so a reader doesn't need to know project names.}

### {Project Name} ({what the project is})
- {count/artifact}: {what it does, why it matters}

## Goal Progress

### User's Priorities
{For each confirmed goal:}
- **{Goal}**: {completed / on track / partial / stalled / dropped}. {One sentence with concrete evidence. Include numbers.}

### Strategic Goals
{Assess each active goal against this week's work.
Flag any goal with "no movement" for 3+ weeks.}
- **{Goal name}**: {advancing / no movement / not yet started}. {Which deliverables from "What Shipped" advanced it, or why it didn't move.}

## Retro
{3-5 items. Same 3-part structure as EOD: observation, impact, action. ALL THREE REQUIRED.
Synthesize across the week, don't repeat individual EOD retro items.
Focus on week-level patterns, not one-day events.}

- **Observation:** {what happened, grounded in project and system names}
  **Impact:** {what would be different}
  **Action:** {what changed, or "unresolved, carrying forward"}

## Metrics
{Hard numbers from the week. Agent-parseable. Skip metrics that don't mean anything standalone.}

| Metric | Value | Change |
|--------|-------|--------|
| PICs closed | {N} | |
| PICs opened | {N} | net: {+/-N} |
| Open PIC count | {N} | |
| Briefs deployed | {N} | |
| Services deployed | {N} | |
| Skills created/modified | {N} | |
| IRs filed | {N} | |

## System Changes
{Aggregated from EODs. Group by theme, not by day.
Each entry: what changed, why, what it affects.}

## Next Week
{2-3 sentences. What's the Monday priority? What deadline is approaching?
What decision needs to be made?
End with the single "frog" for Monday morning.}

**Monday frog:** {The single hardest/most important task to start the week with. Stated as a directive.}

**Open PICs ({N}):** {One-line list grouped by project. Just names and count, not full descriptions.}

**Decision needed:** {Any explicit decision that's been deferred and needs resolution next week. If none, omit.}
```

Save to `01_Notes/Reports/EOW/EOW - {YYYY}-W{ww}.md` (ISO week number).
