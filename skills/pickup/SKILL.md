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

### Step 1: Find All Open PICs

1. Glob for `**/PIC - *.md` under `Work Vault/02_Projects/` and `Work Vault/01_Notes/`
2. Read each PIC's frontmatter and filter to `status: open` and `status: picked-up`
3. Report the count: "Found N open pickups (and M in-progress)."

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

Present two views:

**Project Cluster View** (for multi-PIC projects):

```
| Project | PICs | Complexity Mix | Batch Verdict |
|---------|------|---------------|---------------|
```

**Ranked List** (all PICs, grouped by complexity):

```
### Quick Wins (LOW)
| # | PIC | Project | Created | Summary | Blockers |

### Medium Effort
| # | PIC | Project | Created | Summary | Blockers |

### Heavy Lifts (HIGH)
| # | PIC | Project | Created | Summary | Blockers |
```

**Recommended Session Order:**
1. Superseded PICs first - close with no work
2. Standalone quick wins (LOW, no batch)
3. Batch clusters with a LOW member - enter via the quick win
4. Batch clusters, all MEDIUM
5. Solo MEDIUMs
6. Solo HIGHs
7. Blocked PICs last

Within each tier, prefer older PICs and PICs aligned with current priorities (check SOD if loaded).

Then ask which PIC or cluster the user wants to start with.

---

## Load and Work

Once a PIC is selected (from triage or directly):

### Load Context

1. Read the full PIC document
2. Read every file listed in `## Key Files` - these are essential context from the previous session
3. Read the project's `agents.md` and `lessons.md` if they exist
4. If the PIC references a spec or plan, read those too

Build understanding of: project scope, what was done, concrete next steps, blockers, and any user preferences from the previous session.

### Mark as Picked Up

Update the PIC's frontmatter immediately:
- Change `status: open` to `status: picked-up`
- Add `picked_up_date: YYYY-MM-DD`

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

Update the daily note: add a brief entry under `## Worked on` noting the PIC closure and outcome.

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
