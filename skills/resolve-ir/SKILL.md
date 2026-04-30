# IR — Incident Report Resolution

Enforce root-cause discipline when resolving incident reports. Every IR finding must trace to a fix that prevents recurrence, not just one that cleans up the current mess. Use this skill when resolving an IR, closing a PIC triggered by an IR, or when the user says "resolve IR", "close IR", "IR resolved", "mark IR done". Auto-invoke when marking any `IR -` prefixed document as resolved.

Based on L47 in [[REF - Agent Lessons]].

## When to invoke

- Explicitly: user says "resolve IR", "close IR", "mark IR done"
- Automatically: any workflow that sets `status: resolved` on an `IR -` document
- Pre-check: when picking up work on a system that has an open or recently-resolved IR, verify deferred root causes were addressed before running the system again

## Resolution protocol

### Step 1: Load the IR

Read the full IR document. Extract every finding (sections labeled F1, F2, etc., or findings in a findings table/list).

### Step 2: Classify each fix

For each finding, determine what was done and classify it:

| Classification | Definition | Closes the finding? |
|---|---|---|
| **PREVENTIVE** | Code change, config change, prompt update, schema constraint, or validation rule that stops this class of error from being produced again | Yes |
| **PALLIATIVE** | Data cleanup, manual correction, one-time SQL fix, or any remedy that doesn't change the producing system | No (alone) |
| **DEFERRED** | Root cause identified but fix is tracked elsewhere (PIC, plan task, or backlog item) | Yes (if tracker exists) |

A finding is resolved when it has either:
- A PREVENTIVE fix (the system won't produce this error again), OR
- A PALLIATIVE fix + a DEFERRED tracker (the symptom is cleaned up AND the root cause is tracked)

A finding is NOT resolved if it has only a PALLIATIVE fix with no tracker for the root cause.

### Step 3: Build the resolution table

Present the assessment to the user:

```markdown
## Root-Cause Assessment

| # | Finding | Fix applied | Classification | Root cause addressed? | Tracker |
|---|---------|-------------|----------------|----------------------|---------|
| F1 | ... | ... | PREVENTIVE | Yes | commit abc123 |
| F2 | ... | ... | PALLIATIVE | No — needs preventive fix | — |
| F3 | ... | ... | PALLIATIVE + DEFERRED | Yes (tracked) | [[PIC - ...]] |
```

### Step 4: Gate on closure

- **All findings resolved?** IR can be marked `status: resolved`. Update the frontmatter.
- **Any finding has PALLIATIVE-only?** IR cannot be closed. Present the unresolved findings and offer two paths:
  1. Fix the root cause now (implement the preventive change)
  2. Create a tracking artifact (PIC or plan task) for the deferred root cause, then close with DEFERRED classification

Never allow "resolved" with unaddressed root causes and no tracker. This is the core discipline.

### Step 5: Pre-run check (when resuming work on a system with IRs)

Before running a pipeline, extraction, deploy, or any system operation that previously produced an IR:

1. Find IRs in the project's `reports/` directory
2. For any IR with DEFERRED findings, check whether the tracker (PIC/plan task) has been completed
3. If deferred root causes are still open, warn: "IR [name] has [N] deferred root causes still open. Running the system will reintroduce [issue]. Address [tracker] first, or acknowledge the risk."

## What this skill does NOT do

- Does not create IRs (use `/create-note IR`)
- Does not investigate issues (use `/ag-investigate` or `/troubleshoot`)
- Does not implement fixes (use `/implement`)
- Only governs the resolution gate and root-cause tracking
