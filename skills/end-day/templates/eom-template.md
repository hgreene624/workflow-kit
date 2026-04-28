# EOM Template

Produced on the last workday of the month.

## Context to Gather
- All EOWs from this month
- Current SOM (if exists)

## Template

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
{5-8 sentences. Initiatives that shipped, progressed, or stalled.}

## Initiative Progress
{For each monthly objective from SOM or EOWs:}
- **Initiative**: status -- key milestones hit or missed

## Month Retro
### Wins
{4-5 bullets}
### Losses
{4-5 bullets}
### Systemic Issues
{Patterns that repeated across weeks -- need structural fixes.}

## Infrastructure & Workflow Evolution
{Major changes to how agents work -- new skills, pipeline restructuring,
safety protocols, workflow simplifications. Strategic view.}

## Next Month Setup
{What carries over. What's new. Feeds next month's SOM.}
```

Save to `01_Notes/Reports/EOM/EOM - {YYYY-MM}.md`.
