---
name: bracket
description: >-
  Open any non-trivial work session by writing a printed contract that bounds the work:
  surface, success criteria, anti-scope, validation plan, handoff trigger. The contract
  is referenced at every stage gate so the agent cannot drift into scope creep without
  consciously deciding to. Use this skill at the start of any non-trivial work, when
  the user says "bracket this", "set the bracket", "scope this", "what's the bracket",
  before /implement, before any multi-step code change, when picking up a critical PIC,
  or whenever a session is about to do real work that could expand. Also trigger when
  the user says /bracket. Even casual phrasing like "scope this work" or "what are we
  actually doing here" should trigger this. The skill is the structural answer to the
  failure mode "agent read the working contract and then violated it within hours."
---

# Bracket — Scope Containment Contract

You are about to do non-trivial work. Before any code change, query, or worker dispatch, you write a printed contract that bounds the work. This is the structural fix for the failure mode where an agent reads a working contract and then drifts into scope creep within hours.

The bracket is not paperwork. It is a referenced object. Every progress check, every gate, every "should I do X next" question is answered by re-reading the bracket. Drift outside the bracket requires a conscious re-bracket, not silent expansion.

## When to bracket

REQUIRED before:
- Running `/implement` on any plan
- Picking up a PIC marked critical or carrying a "REQUIRED" working contract
- Dispatching agent teams for non-trivial work
- Any session where the proposed work touches more than one file or one DB row

OPTIONAL but recommended:
- Any work the user describes as "this is going to be tricky"
- Recovering from a prior failed session
- Architectural changes
- Anything where you find yourself drafting a spec longer than 5 FRs

NOT required for:
- Single-line edits
- Lookup queries
- Doc updates
- Reading and answering questions

If unsure, bracket. The cost is two minutes; the cost of skipping is a failed session.

## How to bracket

Walk the user through each of the five sections below. ASK ONE QUESTION AT A TIME via AskUserQuestion when you need a decision from the user. When you can infer the answer from a clearly stated PIC, plan, or spec, draft it yourself and confirm.

### 1. Surface

What exactly will change. Be specific:
- File paths, line numbers, function names
- Migration files
- DB tables and columns
- Specific prompts (DB key + version)
- Specific config values

NOT acceptable: "the entity proposer", "the API", "the auth flow." That is project name, not surface.

Acceptable: `services/api/src/engine/entity_proposer.py:415 propose_projects()`, `PROJECT_CLUSTERING_PROMPT at line 50`, `migration 043 to dissolve N WIs`.

If the surface contains more than 5 distinct items, the bracket is too large. Split into sub-brackets.

### 2. Success criteria

A single concrete observable that proves the work is done. Stated as a check, not a feeling.

NOT acceptable: "the bug is fixed", "the bug is gone", "tests pass", "looks good."

Acceptable: "3-5 hand-picked test inputs on a coherent topic, run through the target function in dry_run, produce correctly shaped output with sensible attribution and citations." That is testable, observable, and bounded.

Include the verification command or query if applicable.

### 3. Anti-scope (explicit out of bounds)

What will NOT change, even if you are tempted. Lists at least 3 items the agent might be drawn into during the work.

This section is the most important. Past failures involved specs that scope-crept from 5 FRs to 26 FRs; the anti-scope section names every one of those temptations explicitly so they cannot be added silently.

Examples:
- NO unified-pool function rewrite
- NO telemetry layer
- NO DB-config blocklist
- NO handoff payload signature change
- NO `/review-spec` invocation
- NO new SPC document

Each anti-scope item is a phrase the agent should be able to grep for and reject. If during work the agent finds itself wanting to do an anti-scope item, that is a STOP and re-bracket signal, not a "while I'm in here" extension.

### 4. Validation plan

The 3-5 input minimum reproducer that exercises the change end-to-end. Follow your pipeline QA procedure (if one exists).

Includes:
- Specific inputs (not "some examples", actual ids or values)
- Expected behavior per input (binary pass/fail)
- Live observation method (what to spot-check while it runs)
- Stop trigger if defects appear in early inputs

NOT acceptable: "test it after deploy", "run the eval suite", "smoke test it."

Acceptable: "Run signals 14721, 14722, 14723, 14724, 14725 through the target function with dry_run=True. Expected: correctly shaped output with proper attribution. Live spot-check: print the input + response for each as it returns. Stop trigger: any input returns null output, or output is shaped incorrectly."

### 5. Handoff trigger

The condition under which you stop and hand off, instead of continuing. Stated specifically. At minimum:
- N failed attempts on the same minimum repro (default: 2)
- Any STOP signal from user (see the stop signals list in your CLAUDE.md)
- Time-boxed limit if applicable (e.g., "90 min without observable progress on the surface")
- Specific defect classes that mandate halt (FK violations, hierarchy guard failures, schema mismatches)

If the agent hits a handoff trigger, the response is to compact, write a recovery PIC, and stop. Not "one more try."

## Output

Write the bracket as a chat-rendered markdown block AND save it to a session-state file at `~/.claude/state/bracket-active.md` (overwriting any prior bracket).

Format:

```markdown
# Bracket — {Task Name}

**Established:** {YYYY-MM-DD HH:MM}
**For:** {PIC name, plan name, or short description}

## Surface
- {item 1}
- {item 2}
- ...

## Success criteria
{single observable check, with verification command if applicable}

## Anti-scope
- NO {tempting item 1}
- NO {tempting item 2}
- ...

## Validation plan
{3-5 inputs, expected behavior, live observation, stop trigger}

## Handoff trigger
- {trigger 1}
- {trigger 2}
- STOP signals from user are immediate halts
```

Print this block in the conversation. Save the same content to `~/.claude/state/bracket-active.md`.

## Referencing the bracket during work

After the bracket is set:

1. **Before any non-trivial action** (file edit, DB query that modifies, deploy, worker dispatch), re-read `~/.claude/state/bracket-active.md` and answer in writing: "Is this action inside the surface? Does it advance the success criterion? Does it touch any anti-scope item?"

2. **At every progress check from the user** ("how's it going?", "where are we?"), reference the bracket: "On surface item X of N. Success criterion not yet met. No anti-scope drift."

3. **If a tempting extension surfaces** ("while I'm here, I should also..."), re-read the bracket. If the extension is in anti-scope, stop. If it is genuinely part of the surface but was missed at bracket time, propose a re-bracket. Do not silently expand.

4. **At handoff trigger**, the response is `/closeout` with the bracket attached, not "one more try."

## Re-bracketing

If during work the surface needs to change (genuine new requirement, not scope creep), re-invoke `/bracket`. The new bracket replaces the old one. The old bracket is appended to the next PIC under "Bracket history" so the carry-forward agent sees the evolution.

Do NOT re-bracket to legitimize scope creep. The test: would the original bracket have rejected this work? If yes, and the new requirement is genuine, ask the user explicitly: "The bracket needs to expand to include X. Is this in scope?" Get a yes before re-bracketing.

## Anti-patterns

Past failures where agents drifted from working contracts are the canonical failure mode this skill prevents. Specific anti-patterns:

- **Reading the bracket and then ignoring it.** An agent lesson: reading does not implant. Reference the bracket at every gate.
- **Silently expanding the surface.** Every surface addition requires re-bracketing.
- **Vague success criteria** ("the bug is fixed"). The criterion must be observable and verifiable in writing.
- **Missing anti-scope.** If the anti-scope section has fewer than 3 items, you have not thought hard enough about temptations.
- **Validation plan that runs at production scale.** An agent lesson: smoke test before scale. The validation plan is 3-5 inputs, not 195.
- **No handoff trigger.** If you cannot name when to stop, you will not stop. Default trigger: 2 failed attempts on same repro.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
