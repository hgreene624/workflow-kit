---
name: create-pickup
description: Create a verified, accurate pickup document (PIC) for carrying work context to a future session. Use this skill whenever creating a PIC — either called from /closeout for each topic that needs a pickup, or directly when the user says "create a pickup", "make a PIC", "save this for later", "I need to come back to this", or wants to capture work-in-progress context for a future agent. Also trigger when /closeout identifies topics with logical next steps. This skill owns the full PIC lifecycle — verification, placement, frontmatter, and writing.
---

# Create Pickup

You are creating a pickup document (PIC) that a fresh agent will use to continue work in a future session. The PIC is the sole bridge between sessions — if information isn't in the PIC, it's lost. But if the PIC contains inaccurate information, the next agent wastes time on false assumptions or breaks things acting on wrong premises.

Your job is to produce a PIC that is **accurate, complete, and actionable** — every factual claim verified, every known issue captured, every next step concrete enough to execute without guessing.

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{paths.projects}/<project>/pickups/` for PIC placement, `{paths.projects}/<project>/PJL - <Name>.md` for project logs). If the file doesn't exist, use defaults and warn once.

## Why Verification Matters

PICs that transcribe conversation claims without checking them cause real damage:
- "API is offline" when it's actually running behind a reverse proxy wastes a session on false urgency
- Missing a latent bug (like a CHECK constraint that will fail on the next INSERT) means the next agent hits it blind
- Listing key files that were moved or renamed sends the next agent on a scavenger hunt

The cost of verification is minutes. The cost of an inaccurate PIC is hours of wasted work in the next session. Always verify.

## Inputs

This skill needs two things:

1. **Topic** — what work needs a pickup (from the conversation, from closeout, or from the user)
2. **Project** — which vault project this belongs to (ask if ambiguous)

If called from `/closeout`, these are provided. If called directly, extract them from the conversation or ask.

## Step 0: Check for Existing Open PICs

**Before creating a new PIC**, search for open PICs in the same project:

```bash
# Glob for PICs in the target project's pickups directory
```

Read the frontmatter of each match. If any PIC has `status: open` or `status: picked-up` and covers the same domain or system:

1. Read its content
2. Ask the user: "There's an open PIC that covers this area: [[PIC - Name]]. Update it with the new context, or create a separate PIC?"
3. If updating, merge the new information into the existing PIC (add to Current State, append to Next Steps, update Key Files). Preserve what's already there -- don't overwrite prior context.

**Only create a new PIC when:**
- No open PIC exists for this project/domain
- The user explicitly wants a separate PIC (different workstream, different scope)
- The existing PIC is `status: closed` or `status: parked`

Fragmenting related work across multiple PICs loses context and creates triage overhead. One PIC per active workstream.

## Step 0.5: PJL Entry Gate (MANDATORY)

Before gathering claims or writing anything, verify that a PJL entry exists for this project and today's date.

1. Find the PJL file: `02_Projects/<project>/PJL - <Project Name>.md`
2. If the PJL exists, check for a `## YYYY-MM-DD` heading matching today
3. **If no PJL entry exists for today: STOP.** Do not create the PIC.
   - Tell the agent/user: "Cannot create PIC for [project] -- no PJL entry exists for today. Run `/log-work` first to record what was done, then retry `/create-pickup`."
   - This is a hard gate, not a warning. PICs without PJL entries mean the next agent gets handoff context (what to do next) but no implementation record (what was done). Both layers are required.
4. If the PJL entry exists, proceed to Step 1.

**Exception:** If the PIC is for work that has no project (e.g., a cross-cutting process improvement or a one-off investigation), skip this gate. The gate applies to project-scoped PICs where a PJL should exist.

## Step 1: Gather Raw Claims

Scan the conversation (or accept input from closeout) and collect:

- What was worked on and what's done
- What needs to happen next
- What the current system state is (services, DB, deployments)
- Any blockers, decisions, or preferences expressed
- Key files referenced

Don't write anything yet — this is raw material that needs verification.

### Cross-reference Project Log

If a PJL exists at `02_Projects/<project>/PJL - <Project Name>.md`, read the most recent date section. This helps you:
- Avoid duplicating context already captured in the PJL
- Ensure the PIC's "What Was Done" is consistent with what the PJL records
- Link the PJL in the Key Files section

## Step 2: Verify Claims

This is the step that separates a good PIC from a bad one. For each factual claim about system state, verify it against the live system before writing it into the PIC.

### What to Verify (by work type)

**Infrastructure / VPS / Docker:**
- Container status claims ("service X is running/down") — check `docker ps` via SSH
- Port/endpoint claims ("API on port 8000") — check if it's host-mapped or Docker-internal only
- Health claims — actually curl the health endpoint, don't assume
- Deploy claims ("deployed to production") — verify the container is running the expected version

**Database migrations:**
- Schema claims ("table X was created/dropped") — run `\dt` or equivalent
- Row count claims ("migrated N rows") — run `SELECT count(*)`
- Constraint claims ("CHECK updated") — inspect the actual constraint
- Side effects — check for orphaned references, default value conflicts, dangling FKs

**Code changes:**
- Commit claims ("changes are committed") — check `git status` and `git log`
- File existence claims — verify key files exist at the paths listed
- Deploy status — is the committed code actually deployed, or just local?

**Feature work:**
- "Feature is live" — actually visit/test it
- "Tests pass" — check recent test output or re-run

### How to Verify

Use the appropriate tools:
- SSH + Docker commands for VPS state
- Git commands for repo state
- Curl/HTTP for endpoint state
- File reads for local state

If verification reveals a discrepancy, **record what's actually true**, not what the conversation claimed. Add a note in Session Notes explaining the discrepancy so the next agent understands the context.

### What NOT to Verify

Don't over-verify. Skip verification for:
- Decisions and preferences (these are inherently conversational)
- Plans and specs (they exist as documents — just confirm the file exists)
- Opinions about approach or architecture
- Things that are obviously true from the conversation flow (e.g., "we discussed X")

The rule: verify **system state claims**. Trust **human intent claims**.

## Step 3: Completeness Check

Before writing, run through this checklist:

1. **Known issues** — Did any bugs, warnings, or edge cases surface during the work that aren't in the next steps? Even small things like "this default value will fail on insert" matter.
2. **Partial work** — Is anything half-done that could cause confusion? (e.g., "table renamed but code still uses old name")
3. **Orphaned state** — Did the work leave anything in an inconsistent state? (e.g., "entity_signal_links still has entity_type='blocker' entries pointing to dropped table")
4. **Unasked questions** — Are there decisions the next agent will need that weren't resolved? Flag them explicitly rather than letting the agent discover them mid-work.
5. **Prerequisites for next steps** — Do the listed next steps have preconditions that might not be met? (e.g., "resume /implement" assumes the plan file exists and Plane project is set up)

For each item found, decide: does it go in "What Needs to Happen Next", "Blockers or Dependencies", or "Session Notes"?

## Step 4: Write the PIC

### File Location

```
{vault_root}/{paths.projects}/<project>/pickups/YYYY-MM-DD/PIC - Topic Name.md
```

Use today's date. Create directories if needed. If the work spans multiple projects, pick the primary one. If truly cross-cutting, use `{vault_root}/{paths.pickups}/YYYY-MM-DD/`.

### Frontmatter

```yaml
---
date created: YYYY-MM-DD
tags: [pickup, <project-tag>]
category: Pickup
status: open
project: "<project name>"
pickup_date: "YYYY-MM-DD"
---
```

`pickup_date` = next workday (skip weekends: Friday -> Monday).

### Body

```markdown
# PIC - [Topic Name]

## Context
[2-3 sentences: what project, what the user was working on, why it matters.
Frame for someone with zero prior context.]

## What Was Done
[Bullet list of completed work. Each claim should be verified.
Include concrete evidence: row counts, commit hashes, test results.
Mark anything unverified with "(unverified)" so the next agent knows to check.]

## What Needs to Happen Next
[Numbered list of specific, actionable steps.
Bad: "Continue working on the API"
Good: "Run P1.1: grep monorepo for all references to `issues` table — produce audit report categorized by must-change-now vs can-defer"
Each step should be executable without reading the full conversation history.]

## Known Issues
[Bullet list of bugs, edge cases, or inconsistencies discovered during the work
that aren't blocking but need attention. Include enough detail to reproduce.
If none, write "None identified."
Example: "work_items.status column default is 'open' but CHECK constraint
only allows pending|in_progress|blocked|done|superseded — any INSERT
without explicit status will fail"]

## Key Files
[Wikilinks and paths to essential context files. Only list files you've
confirmed exist. Group by type:]
- Specs/Plans: [[SPC - Name]], [[PL - Name]]
- Code: `~/Repos/flora-monorepo/path/to/file.py`
- Reports: [[RE - Name]]
- Project context: `agents.md`, `lessons.md` paths

## Blockers or Dependencies
[Concrete blockers with enough context to resolve them.
Distinguish between:
- Hard blockers (cannot proceed without X)
- Soft blockers (would be better to have X first, but can work around)
- External dependencies (waiting on a person, a service, a decision)
If none: "None identified."]

## Operational Dependencies
[Config, env vars, feature flags, or runtime state that the deployed work
relies on. These are the things that silently break when containers rebuild,
services restart, or someone deploys without checking preconditions.

For each dependency:
- **What**: the specific setting (e.g., `MIP_ENABLED=true`)
- **Where**: where it's configured (e.g., `docker-compose.yml`, env var, DB config table)
- **Survives rebuild?**: Yes (in compose/code) or No (set via docker exec, runtime only)
- **How to verify**: the command to check it's still set

Example:
- `MIP_ENABLED=true` in docker-compose.yml transcription-pipeline service (survives rebuild). Verify: `docker exec transcription-pipeline printenv MIP_ENABLED`
- Prompt template id=43 updated with Chris Whaley (DB-stored, survives rebuild). Verify: `SELECT content FROM prompt_templates WHERE id=43` and grep for 'Chris Whaley'

If the work didn't involve deployment or infrastructure, omit this section.
This section exists because lost env vars and feature flags are a top cause
of "it worked last week but broke" investigations — see L18 in Agent Lessons.]

## Verified State
[Quick summary of what was verified and when. This tells the next agent
which claims they can trust vs which might have drifted.
Example:
- "Container flora-api: healthy, 0 restarts (verified 2026-03-28 15:30)"
- "activities table: 1,226 rows, 332 with type='issue' (verified 2026-03-28 15:30)"
- "entity_links table: 13 rows (verified 2026-03-28 15:30)"
If no system state was relevant to verify, omit this section.]

## Session Notes
[Context that wouldn't be obvious from files alone:
- User preferences expressed during the session
- Decisions made verbally and their rationale
- Gotchas the next agent should know about
- Discrepancies found during verification (what was claimed vs what's true)]
```

### Section Guidelines

**"Known Issues" is new and critical.** The old PIC format lacked this, which meant side-effects and edge cases discovered during work were silently dropped. Every bug, warning, or inconsistency that surfaced — even if it seems minor — goes here. The next agent can decide whether to fix it; but they can't decide if they don't know about it.

**"Verified State" is new and important for infra/DB work.** It tells the next agent which claims are ground truth (with timestamps) vs which are carried forward from conversation. For pure code/design work where there's no system state to verify, omit this section entirely.

**"What Needs to Happen Next" must be specific.** Each item should be a concrete action, not a vague direction. Include command paths, file paths, plan task IDs, or Plane issue references where relevant. The test: could a competent agent execute this step with only the PIC and the linked files?

**"Key Files" must be confirmed.** Before listing a file, verify it exists. Use Glob to check vault files, `ls` to check repo files. Don't list files from memory — they may have been moved or renamed.

## Step 5: Confirm with User

Present a **brief summary** — not the full PIC. The user doesn't want to read 80 lines of markdown they'll never look at again. Show:

```
PIC: [Topic Name]
Path: [file path]
Next steps: [count] items, starting with [first item summary]
Known issues: [count] or "none"
Verified: [key facts, one line]
```

Ask: "Good to write, or adjust?"

The user can ask to see the full content if they want, but don't dump it by default. The PIC is for the *next agent*, not for the user to proofread right now.

If called from `/closeout` with multiple PICs, show all summaries in a compact list and confirm once.

## Step 6: Write and Report

Write the file. Confirm: "Created [[PIC - Topic Name]] at `<path>`."

If this PIC supersedes an older PIC on the same topic, ask: "This covers the same ground as [[PIC - Older Topic]]. Should I close that one as superseded?"

## Step 7: Log to Project Log

Append a session-end entry to the project's PJL under today's date heading (create the heading if needed, newest on top):

```markdown
- **Session end** — created [[PIC - Topic Name]]; {1-line summary of what was accomplished this session}
```

If no PJL exists yet, create one at `02_Projects/<project>/PJL - <Project Name>.md` with standard frontmatter:

```yaml
---
date created: YYYY-MM-DD
tags: [project-log, <project-tag>]
category: Project Log
project: "<project name>"
---
```

Also ensure the PIC's Key Files section includes a link to the PJL: `- Project log: [[PJL - <Project Name>]]`
