# Implement — Resume Phase

Resume a partially-complete implementation. The user can resume by pointing to a plan file, spec file, or Plane project URL/ID.

## Step R0 — Resolve Entry Point to Plan + Plane

No matter what the user gives you, you need both a plan file and a Plane project.

**Given a plan file:**
1. Read it — find the Plane project link/ID in the metadata
2. If no Plane link, search by project name in Plane registry

**Given a spec file:**
1. Search for `PL - *.md` in the same directory as the spec
2. If multiple plans exist, present them via `AskUserQuestion`
3. If no plan exists: "No plan found. Run `/plan-spec` first?"

**Given a Plane project URL/ID:**
1. Extract project ID from URL
2. Query Plane for project details
3. Search plan files for one referencing this project ID

## Step R1 — State Reconciliation

Gather state from all sources and reconcile:

1. **Read plan file** — extract phase structure and task inventory (plan is the structural reference, not the status source)
2. **Query Plane** — get all issues with current states (Plane is the authoritative status source)
3. **Check git** — uncommitted work? Recent commits?

### Reconciliation Rules (Plane vs Git Evidence)

| Plane State | Git Evidence | Action |
|-------------|-------------|--------|
| Done | Confirms | Skip — already complete |
| In Progress | No evidence | Stale — reset to Todo |
| Todo | Commits exist | Trust git — advance in Plane |
| Done | No evidence | Suspicious — verify before trusting |

## Step R2 — Present and Resume

1. Present status report to user — what's done, what's remaining, what drifted
2. Ask user where to resume
3. Fix any drift identified in reconciliation (update Plane states)
4. Re-spin PM tracker with current state
5. Continue execution

---

Resumption complete. Hand off to `implement-execute.md` for continued execution.
