# Handoff Report Template

Generate this report at sprint completion OR when a session ends mid-sprint. The next session cannot resume efficiently without it.

**Why this exists (Sprint 5):** The Sprint 5 handoff report had everything needed for smooth session resumption: Plane UUIDs, task states, carry-forwards, active worker positions, and user test gate instructions. Making this templated and automatic ensures every sprint gets the same quality handoff.

## Template

Save as: `HAN - {Project Name} - {Sprint} {Phase}.md` in the project's vault directory. No date suffix, no "Handoff Report" — the `HAN` prefix is self-evident.

```markdown
---
category: Report
date created: {today}
date modified: {today}
tags: [sprint-handoff, {project-tag}, {sprint-tag}]
---

# HAN - {Project Name} - {Sprint} {Phase}

## Sprint Outcome: {COMPLETE / IN PROGRESS / BLOCKED}

{1-2 sentence summary of where things stand.}

| Milestone | Status | Notes |
|-----------|--------|-------|
| {milestone} | {status} | {notes} |

**Plan progress: {N}/{total} tasks done** (up from {prev}/{total} at previous close)

---

## Task Status

### Completed This Session

| Task | Description | Status |
|------|-------------|--------|
| {task_id} | {description + key commit hashes} | Done |

### In Progress

| Task | Description | Status |
|------|-------------|--------|
| {task_id} | {description} | {AT USER TEST GATE / In Progress} |

{For each in-progress task, include sub-task state table if applicable.}

### Pending

| Task | Description | Status |
|------|-------------|--------|
| {task_id} | {description} | {Pending — blocked on X} |

---

## Active Workers at Session End

{For each active worker: name, what they're doing, whether they're waiting on a gate.}

{If a user test gate is pending, include:}

**USER TEST GATE — {task_id}:**
- {URL 1} — {what to check}
- {URL 2} — {what to check}

**On user PASS:** {Exactly what to do next — cascade in Plane, dispatch next worker, etc.}
**On user FAIL:** {Keep in progress, relay feedback to worker.}

---

## Infrastructure Changes (This Session)

| # | Change | Impact |
|---|--------|--------|
| {n} | {what changed} | {effect} |

---

## Carry-Forwards

### Immediate (Next Session Start)

| # | Item | Action |
|---|------|--------|
| {n} | {item} | {what to do} |

### Sprint Remaining

| # | Item | Blocked On |
|---|------|-----------|
| {n} | {item} | {blocker} |

### Shared Service Issues (Flagged, Not Fixed)

{From PM's carry-forward list. Include service, description, reporter, severity.}

| # | Service | Issue | Severity | Reporter |
|---|---------|-------|----------|----------|
| {n} | {service} | {description} | {H/M/L} | {worker} |

### Infrastructure / Technical Debt

| # | Item | Priority |
|---|------|----------|
| {n} | {item} | {priority} |

### QA Tooling State

- **Playwright auth state**: {fresh / expired / not set up}. If expired, next session must run `./scripts/qa-auth-setup.sh` before QA auditor can do authenticated screenshot verification.
- **Last QA screenshot run**: {date + services tested, or "none this session"}

---

## Plane State Reference

### Projects

| Project | ID |
|---------|-----|
| {name} | {uuid} |

### State UUIDs (per project)

{One table per project with State → UUID mapping.}

### Issue IDs (for next PM)

{Full or partial UUIDs for all issues the next PM will need to touch.}

> **CRITICAL:** Plane API requires **full UUIDs** in PATCH requests. Partial 8-char prefixes return empty responses and silently fail.

---

## Plane API Reference

- **Base URL**: {url}
- **Auth**: `x-api-key: {key}`
- **PATCH state**: `PATCH /projects/{project_id}/issues/{full-uuid}/` with `{"state": "<full-state-uuid>"}`

---

## Plans

- {Plan name}: {absolute path}
- Daily note: {absolute path}

---

## Lessons Added This Session

{List any new lessons with their IDs and one-line summaries.}

---

## Key Path Changes

{Only if paths changed during this session.}

| Item | Old Path | New Path |
|------|----------|----------|
| {item} | {old} | {new} |
```

## Usage Notes

- **Every field matters.** The Sprint 5 handoff was smooth because it included Plane UUIDs, specific user test gate instructions, and exact carry-forward actions. A vague handoff forces the next session to spend 15+ minutes reconstructing state.
- **Include commit hashes** for completed work so the next session can verify VPS state.
- **Full Plane UUIDs** — partial UUIDs silently fail (L32). Include full UUIDs or at minimum the lookup instructions.
- **Shared service issues** come from the PM's carry-forward list. If none were flagged, note "None flagged this session."
