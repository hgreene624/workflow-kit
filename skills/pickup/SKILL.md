---
name: pickup
description: >-
  Load pickup documents (PICs) and resume work. Handles both single-PIC loading and
  full backlog triage. Use this skill when the user says "pickup", "pick up", "start
  of day", "what's on my plate", "what do I need to do", "get started", "load the
  pickup", "continue where I left off", "resume work", "triage pickups", "which
  pickups are easiest", "work through my pickups", "clear out pickups", "pickup
  backlog", "how many open pickups", "rank my pickups", "what's the quickest pickup
  to close", "batch my pickups", "group pickups by project", or points at a specific
  PIC document. Also trigger when the user opens a new session and says something like
  "ok what am I doing today" or "what was I working on".
---

# Pickup

Resume work by loading context from pickup documents. Routes automatically: if the user points at a specific PIC, load it directly. Otherwise, triage all open PICs and help the user choose.

## Pre-flight: Orient Check

Before doing anything else, check whether `/orient` has been run in this session. Look for evidence in the conversation history - if you've already read the SOD, vault agents.md, and lessons.md earlier, orient has been done.

If orient has NOT been run yet, run `/orient` first (invoke the Skill tool with skill: "orient"). Do not skip this - pickup without orient means you'll miss project rules and lessons.

## PIC Lifecycle

PICs have three statuses:
- **`open`** - created by closeout, waiting to be picked up
- **`picked-up`** - actively being worked on in a session
- **`closed`** - work is complete

You are responsible for managing these transitions throughout the session.

---

## Route A: Specific PIC Given

If the user pointed at a specific PIC file or named one explicitly, skip triage and go directly to **Load and Work** below.

## Route B: Triage (No Specific PIC)

### Step 0: Check for Cached Triage (TRI)

Before scanning PICs, check for an existing triage report:

1. Look for `Work Vault/01_Notes/Reports/Triage/TRI - {today}.md`
2. **If today's TRI exists:** load it, then run a **light scan** (Step 0a) to catch changes since it was written. Skip to Step 5 (Present the Triage) with the updated data.
3. **If today's TRI is missing:** check for the most recent `TRI - *.md` in the same directory.
   - **If a previous TRI exists:** use it as a seed. Carry forward assessments (complexity, summary, batch verdicts) for PICs that are still open. Only run the full scan (Steps 1-4) on PICs that are **new** since that TRI was written (no matching entry in the previous report). Merge results and write today's TRI.
   - **If no TRI exists at all:** run the full scan (Steps 1-5), then write today's TRI.

#### Step 0a: Light Scan (TRI refresh)

When loading a cached TRI, validate it against current PIC state:

1. **Find ALL open and picked-up PICs using Grep, not Glob.** Glob truncates results when there are many PIC files, which causes missed PICs. Instead, run these two Grep calls in parallel with `head_limit: 0` (unlimited results) to guarantee complete coverage:
   - `Grep pattern="^status: open" glob="**/PIC - *.md" path="Work Vault/" output_mode="files_with_matches" head_limit=0`
   - `Grep pattern="^status: picked-up" glob="**/PIC - *.md" path="Work Vault/" output_mode="files_with_matches" head_limit=0`
2. For each PIC listed in the TRI, check whether it appears in the grep results (still open/picked-up) or is absent (now closed).
3. Update the cached triage data:
   - PICs that no longer appear in grep results: mark as closed in the triage (confirm by reading frontmatter if unsure)
   - PICs found in grep results but not listed in the TRI (filter to files whose basename starts with `PIC - ` -- discard IRs, delegated tasks, templates): these are **new** -- run the full assessment (Step 2) on just those PICs and add them
   - PICs in the TRI that no longer exist on disk: remove them
4. Report changes: "TRI loaded from {time}. Changes since then: N closed, M picked up, P new."

This light scan uses grep to find open PICs by content rather than globbing all files, so it completes in seconds and never misses PICs due to truncation.

### Step 1: Find All Open PICs

1. **Use Grep, not Glob, to find PICs by status.** Glob truncates results when there are many PIC files (50+), which silently drops PICs from the triage. Run these two Grep calls in parallel with `head_limit: 0`:
   - `Grep pattern="^status: open" glob="**/PIC - *.md" path="Work Vault/" output_mode="files_with_matches" head_limit=0`
   - `Grep pattern="^status: picked-up" glob="**/PIC - *.md" path="Work Vault/" output_mode="files_with_matches" head_limit=0`
2. From the results, keep only files whose basename starts with `PIC - `. The grep may also match IRs, delegated tasks, or templates that share the `status: open` frontmatter pattern -- discard those.
3. The filtered results ARE the complete set of open/picked-up PICs.
4. Report the count: "Found N open pickups (and M in-progress)."

If there are no open PICs, tell the user: "No open pickups found. Starting fresh - what would you like to work on?"

If there's exactly one open PIC, confirm: "One open pickup: [topic]. Want me to load it?" Then proceed to Load and Work.

### Step 2: Assess Each Open PIC

For each open PIC, read the full file and extract:

- **Project**: from `project` frontmatter or inferred from file path
- **Created**: from `date created` frontmatter
- **Summary**: one sentence from the `## Context` section
- **Next steps count**: items in `## What Needs to Happen Next`
- **Has blockers**: whether `## Blockers or Dependencies` lists anything substantive
- **Complexity**: LOW / MEDIUM / HIGH

**LOW** - Under 30 minutes: single file change, config tweak, running a documented script, closing stale issues, investigation with clear diagnostic steps.

**MEDIUM** - Meaningful but self-contained: changes across 2-5 files, migrating code to an existing pattern, setting up a documented integration, multi-step diagnostics.

**HIGH** - Multi-system or architectural: cross-service changes, multiple repos/deployment targets, requires user decisions or external input, phase 2+ of a multi-phase plan, large data migrations.

### Step 3: Supersession Check

When multiple PICs exist for the same project area:
- Check if a newer PIC's "What Was Done" covers what an older PIC's "What Needs to Happen Next" listed
- If so, recommend closing the older PIC as superseded
- Flag these explicitly - closing stale PICs is a quick win

### Step 4: Project Clustering

Group PICs by project. For clusters with 2+ PICs, evaluate batch compatibility:

1. **Shared context?** Same codebase, database, or deployment target - loading context once saves ramp-up time
2. **Shared workstream?** Sequential phases or subtasks of the same effort
3. **Compatible complexity?** LOW + MEDIUM batches well. Two HIGHs risk fatigue.
4. **Containment?** Does one PIC's next-steps include the other? Work the parent, close both.

Assign batch verdicts:
- **BATCH** - shared context makes working them together faster
- **PARTIAL BATCH** - some PICs in the cluster batch, others don't
- **SPLIT** - same project label but independent workstreams

### Step 5: Present the Triage

**Presentation rules (mandatory):**
- Present ONE grouped-by-cluster table — not three separate views.
- Clusters are themes (e.g. "FWIS / Signal Engine", "DocGen / Patrick-facing", "Admin / Infra", "Restaurant Ops / Tourism (blocked)"). Pull the theme from the SOD priorities when possible.
- A "Validate first" cluster always comes first if there are picked-up PICs flagged in the SOD.
- Within each cluster, order PICs **low → high effort** (LOW → MED → HIGH). Blocked PICs sink to the bottom of their cluster.
- Cluster order: validate-first → SOD priority order → blocked clusters last.
- Every PIC gets a global selection number (`#`), assigned by walking the clusters top-to-bottom so #1 is the top of the first cluster.
- Use a single table with cluster headers as separator rows, OR one small table per cluster — either is fine, but no separate "by complexity" or "session order" tables.

**Format:**

```
### ⚠ Validate first (if applicable)
| # | PIC | Tier | Blockers | Note |
|---|-----|------|----------|------|

### {Cluster 1 — e.g. FWIS / Signal Engine}
| # | PIC | Tier | Blockers | Note |
|---|-----|------|----------|------|

### {Cluster 2 — e.g. DocGen / Patrick-facing}
...

### {Blocked cluster, last}
...
```

The `Note` column is one short phrase: SOD priority, batch hint, or blocker reason. Skip the Project column — the cluster header makes it redundant.

End with: "Pick a number to load, or tell me which cluster to batch."

### Step 6: Write the TRI

After completing triage (whether full scan or seeded), write the results to `Work Vault/01_Notes/Reports/Triage/TRI - {today}.md`. See the TRI format specification below.

**When to update the TRI during the session:**
- When a PIC is picked up: update its status row to `picked-up` and add the agent/session that claimed it
- When a PIC is closed: update its status row to `closed`
- When a new PIC is created (via closeout): add it to the appropriate complexity tier

This keeps the TRI as a live document that other agents can read for current state.

---

## TRI File Format

```yaml
---
date created: YYYY-MM-DD
tags: [report, triage]
category: Report
type: TRI
scan_time: "HH:MM"
total_scanned: N
seeded_from: "TRI - YYYY-MM-DD.md"  # or "full scan" if no seed
---
```

```markdown
# TRI - Day, Month DD, YYYY

## Triage Summary
- **Open:** N | **Picked-up:** M | **Parked:** P | **Closed since last TRI:** C
- **New since last TRI:** list of new PIC names (or "none" / "first scan")

## Recommended Session Order
| # | PIC | Project | Tier | Blockers | Why this order |
|---|-----|---------|------|----------|----------------|

> Numbers in this table are the canonical selection IDs. Reuse them in every other table below.

## Project Clusters
| Cluster | PIC #s | PICs | Complexity Mix | Batch Verdict |
|---------|--------|------|----------------|---------------|

## Supersession Findings
- [list, or "None detected"]

## Quick Wins (LOW)
| # | PIC | Project | Created | Summary | Blockers | Status |
|---|-----|---------|---------|---------|----------|--------|

## Medium Effort
| # | PIC | Project | Created | Summary | Blockers | Status |
|---|-----|---------|---------|---------|----------|--------|

## Heavy Lifts (HIGH)
| # | PIC | Project | Created | Summary | Blockers | Status |
|---|-----|---------|---------|---------|----------|--------|

## Claim Log
| Time | PIC | Agent/Session | Action |
|------|-----|---------------|--------|
```

The Claim Log tracks which agent picked up which PIC and when, so other agents can see what's already being worked on without re-reading PIC frontmatter.

---

## Load and Work

Once a PIC is selected (from triage or directly):

### Pre-flight: Log Previous Work

Before loading the new PIC, check whether there's unlogged work from earlier in this session. This matters when the user finishes one PIC and immediately picks up the next without running `/closeout` or `/log-work` in between.

**Check for unlogged work:**
1. Scan the conversation for completed tasks, file edits, deploys, or decisions since the last `/log-work` or `/closeout` invocation
2. Check if a PIC was being worked on earlier in this session (look for a PIC that was marked `picked-up` by this session)

**If unlogged work exists:**
- Tell the user: "You have unlogged work from [previous topic]. Want me to log it before picking up the next one?"
- If yes: invoke `/log-work` with the previous work context (this handles DN + PJL updates), then ask if the previous PIC should be closed or if it needs a new PIC via `/create-pickup`
- If no: continue to Load Context. The work can still be captured at closeout.

**If this is the first pickup of the session** (no prior work), skip this step.

### Verify Project Structure

If the PIC's `project` frontmatter maps to a vault project under `02_Projects/`, verify the project folder is properly set up before loading context:

1. Check that the project directory exists (e.g., `02_Projects/Flora Intelligence/signal-engine/`)
2. Check for `agents.md` at the project root. If missing, create it with a minimal stub:
   ```markdown
   # Agent Context - {Project Name}
   
   Read root `agents.md` first.
   
   ## Scope
   
   {one-line project description}
   ```
3. Check for `lessons.md` at the project root. If missing, create it with:
   ```markdown
   # Lessons - {Project Name}
   
   See root `lessons.md` for cross-project lessons.
   ```
4. Check for the PJL file at `02_Projects/<project>/PJL - <Project Name>.md`. If missing, it will be created in the "Log to Project Log" step below.

Do NOT create empty subdirectories (`specs/`, `plans/`, `reports/`). Those are created by the skills that write to them (`/create-spec`, `/create-plan`, `/log-work`). This step only ensures the project root and its config files exist.

### Load Context

1. Read the full PIC document
2. Read every file listed in `## Key Files` - these are essential context from the previous session
3. Read the project's `agents.md` and `lessons.md` (created above if they didn't exist)
4. If the PIC references a spec or plan, read those too
5. **Read the Project Log** if one exists at `02_Projects/<project>/PJL - <Project Name>.md`. Read the most recent 2-3 date sections (newest entries). This gives you the project's recent history -- what was built, what decisions were made, what failed, what's deployed. Don't read the entire PJL if it's large; the recent entries are what matter for context loading.

Build understanding of: project scope, what was done, concrete next steps, blockers, and any user preferences from the previous session.

### Environment Declaration (MANDATORY for Flora-touching PICs)

If the PIC's project is a Flora app (KB, admin, portal, mail, fwis-viewer, home, reservations, mailbox-viewer, revenue-dashboard, culinary-cottages, or anything in `~/Repos/flora-monorepo/`), declare the target environment in your "Present the Plan" output. Three valid forms:

```
Environment: LOCAL          → iterating at localhost:3001-3011 via flora-dev, no production change expected
Environment: REMOTE         → updating myarroyo.com/<app>/, will run flora-deploy <service> after the fix
Environment: BOTH           → iterate locally first, then deploy to production
```

Read the PIC's `## What Was Done` and `## What Needs to Happen Next` to determine which one applies. If the PIC's next steps include a `flora-deploy` or `safe-build` command → REMOTE or BOTH. If the next steps are pure code iteration with no deploy command → LOCAL. **If unclear, ASK the user via AskUserQuestion before starting.** Don't guess.

**Verify the PIC's deployment-state claims before acting on them.** A PIC carrying "deployed KB hydration fix" in its `## What Was Done` is unverified hearsay until you confirm. Run:
- `gh run list --repo hgreene624/flora-monorepo --limit 5` — confirm the GHA workflow ran
- `curl -sf https://myarroyo.com/<app>/<path>` — confirm the live URL behaves as expected

PICs carry false "deployed" claims forward when the prior session pushed without running `flora-deploy`. See L25.

### Mark as Picked Up

Update the PIC's frontmatter immediately:
- Change `status: open` to `status: picked-up`
- Add `picked_up_date: YYYY-MM-DD`

### Log to Project Log

If a PJL exists for this project, append a session-start entry under today's date heading (create the date heading if it doesn't exist, newest on top):

```markdown
- **Session start** — picked up [[PIC - Topic Name]], targeting: {first 1-2 next steps from PIC}
```

If no PJL exists yet, create one at `02_Projects/<project>/PJL - <Project Name>.md` with standard frontmatter and this first entry. The PJL will accumulate as work is logged via `/log-work` and `/create-pickup`.

Do this before presenting the plan.

### Present the Plan

1. **One-line context** - what project, what we're continuing
2. **Where we left off** - key outcome from the previous session (1-2 sentences)
3. **Today's plan** - the numbered next steps from the PIC
4. **Blockers** - anything that might get in the way (or "none")

Then ask: "Ready to start, or do you want to adjust the plan?"

Once confirmed, begin working on the first step.

---

## Closing PICs

As you work through a PIC's next steps, track progress. When all steps are complete (or the user says they're done), ask:

"The work from [PIC topic] looks complete - [brief summary]. Can I close this pickup?"

If confirmed, update frontmatter:
- Change `status: picked-up` to `status: closed`
- Add `closed_date: YYYY-MM-DD`

Append a closing update:

```markdown
## Closing Update
**Closed:** YYYY-MM-DD
**Outcome:** [1-2 sentences: what was accomplished]
**Artifacts:** [wikilinks to anything produced]
**Carry-forward:** [Anything not completed that needs a new PIC, or "None - fully resolved"]
```

**Log work (MANDATORY before closing).** Invoke `/log-work` with the PIC's closing context before writing the closing update. Log-work writes to both the daily note AND the project log (PJL). Pass it: the project name, what was done (from the Closing Update), and any artifacts. Do not manually write to the daily note or PJL - let log-work handle both layers so formatting stays consistent. The PIC cannot be closed until log-work has created the PJL entry for today.

### Batch Continuation

If the user chose a batch cluster and just finished one PIC, prompt: "Context is still warm for [next PIC in cluster]. Continue with that, or switch to something else?"

After each PIC closure, update the running tally: "Closed N/M pickups this session. X remaining."

### Lingering PIC Detection

If during a session you notice PICs in `picked-up` status that haven't been actively worked on, proactively ask before the session ends: "[[PIC - Topic]] is still marked as picked-up. Should I close it, carry it forward, or leave it for next session?"

Don't let PICs accumulate in `picked-up` status across multiple sessions.

## Tips

- Some PICs may be closeable just by verifying work was already done in a later session. Check git history or current state before assuming work is needed.
- If a PIC's next steps have been partially completed, note which items remain.
- Ask one question at a time when clarifying with the user.
- Don't force batching - if the user wants to cherry-pick across projects, that's fine. Batch analysis is a recommendation, not a constraint.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
