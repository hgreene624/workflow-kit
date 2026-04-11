---
name: usage-audit
description: >-
  Analyze Claude Code token consumption from JSONL session logs. Use this skill when the
  user says "usage audit", "token usage", "what's eating my tokens", "rate limit",
  "usage analytics", "check my usage", "token consumption", "why am I hitting limits",
  "full audit", "usage report", "how much am I using", "compare usage", "top consumers",
  "show me anomalies", "cache efficiency", "which projects use the most", "daily trend",
  "budget window", or any question about Claude Code token/usage patterns.
---

# Usage Audit — Claude Code Token Forensics

Run forensic analysis on Claude Code's own token consumption using the cc-analytics CLI toolkit. This skill maps natural language questions to the right analysis commands and presents findings directly.

**Arguments:** $ARGUMENTS — Natural language query about usage, or blank for a full audit.

## How to Run Commands

All commands are run via:

```bash
cd "~/Repos/cc-analytics" && npx tsx src/cli.ts <command> <args>
```

The output is already formatted markdown — present it directly to the user without reformatting.

## Command Mapping

Map the user's question to the right command:

| User says | Command |
|-----------|---------|
| "full audit" / "usage report" / "what's eating my tokens" / no args | `audit` |
| "audit today" / "audit since Monday" | `audit --since today` / `audit --since 2026-03-22` |
| "compare this week to last week" / "what changed" | `compare --a 7d --b 14d..8d` |
| "top consumers today" / "biggest sessions" | `top --since today` |
| "top consumers this week" | `top --since 7d` |
| "drill into session X" / "detail on X" | `detail <session-id>` |
| "show me anomalies" / "outlier sessions" | `anomalies --since 7d` |
| "which projects use the most" / "heaviest workflows" | `projects --since 7d` |
| "cache efficiency" / "cache hit rate" | `cache --since 7d` |
| "budget window" / "when did I hit the limit" / "rate limit" | `budget` |
| "budget at 8am" | `budget --at 8am` |
| "daily trend" / "usage over time" | `trend` |
| "trend last 30 days" | `trend --days 30` |
| "model breakdown" / "model mix" / "which models" | `models --since 7d` |
| "team usage" / "agent usage" | `teams --since 7d` |
| "session list" / "scan sessions" | `scan --since today` |

## Time Arguments

The `--since` and `--until` flags accept:
- ISO dates: `2026-03-24`, `2026-03-24T08:00:00`
- Relative: `24h`, `7d`, `48h`, `30m`
- Named: `today`, `yesterday`
- Clock time: `5am`, `5:30pm`, `14:00`

## Default Behavior

If the user asks a general question about usage without specifying a time window:
1. Run `audit` (no args) for the comprehensive report
2. The audit command covers: 14-day trend, week-over-week comparison, top 10 sessions, anomalies, model mix, cache efficiency, and project breakdown

## Follow-Up Guidance

After presenting results, if the output reveals issues, offer to drill deeper:
- **Anomalies found** -> "Want me to drill into any of these sessions? Give me the session ID."
- **Spike in trend** -> "There's a spike on [date]. Want me to run `top --since [date] --until [next-day]` to see what caused it?"
- **Low cache efficiency** -> "Cache efficiency is low for [project]. Want me to check the session-level breakdown?"
- **High team usage** -> "Team sessions are dominating. Want to see the per-agent breakdown with `teams --since [window]`?"
- **Model mix shift** -> "Sonnet usage jumped [X]%. Want to see which sessions switched models?"

## JSON Output

All commands support `--json` for machine-readable output. Use this if you need to do further analysis on the data programmatically.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
