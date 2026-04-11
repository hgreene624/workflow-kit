---
name: git-safe
description: >-
  Mandatory safety protocol for all git operations — pull, push, merge, commit, checkout,
  branch creation, and multi-repo coordination. MUST be consulted before ANY git operation
  that modifies repository state, especially when working across multiple repos, deploying
  to VPS, dispatching agents to write code, or doing merge/rebase operations. Also trigger
  when you see dirty working trees, merge conflicts, untracked files blocking operations,
  worktree agents, parallel git operations across repos, or any git error. This skill
  prevents the recurring issues of lost work from worktree cleanup, cascading failures
  from parallel git ops, dirty trees blocking merges, deleted files that shouldn't have
  been deleted, and branches that never reach remotes. If you are about to run ANY git
  command beyond `git status` or `git log`, consult this skill first.
---

# Git Safe — Mandatory Git Operations Protocol

This skill exists because agents have repeatedly caused data loss, corruption, and hours of wasted debugging by treating git as an afterthought. Every rule below comes from a real incident where work was destroyed or the user had to manually recover.

## The Core Problem

Agents fail at git in predictable ways:
- They run `git checkout` / `git pull` without checking for dirty trees → merge blocked or work lost
- They `rm` untracked files or `git stash` without understanding what those files are → user's work deleted
- They run parallel git operations where one failure cascades and cancels everything → 5 repos half-done
- They commit to worktrees that get cleaned up → branches never reach remotes, work vanishes
- They don't checkpoint during long tasks → context compaction kills the agent, uncommitted work gone
- They assume repo state without checking → 43 commits behind, wrong branch, missing remotes

## Rule 1: Always Assess Before Acting

Before ANY git command that modifies state, run these checks and read the output:

```bash
git status
git branch --show-current
git log --oneline -3
```

This tells you:
- **Dirty tree?** — Don't proceed until you handle it (see Rule 3)
- **Which branch?** — Don't assume you're on main
- **How far behind?** — Context for whether pull/merge is safe

Never skip this. "I just checked" from earlier in the conversation doesn't count — repo state changes constantly, especially with multiple agents.

## Rule 2: Never Run Parallel Git Operations Across Repos

**Wrong** (one failure kills all):
```
# All in parallel:
Bash(cd repo-a && git pull && git merge ...)
Bash(cd repo-b && git pull && git merge ...)
Bash(cd repo-c && git pull && git merge ...)
```

**Right** (sequential, each one verified):
```
# One at a time, check result before proceeding:
Bash(cd repo-a && git status)  # assess
Bash(cd repo-a && git pull origin main)  # act
Bash(cd repo-a && git status)  # verify

# Only after repo-a is clean, move to repo-b
Bash(cd repo-b && git status)  # assess
...
```

The reason: when parallel bash calls are used, if ANY one errors, Claude Code cancels all the others mid-operation. This can leave repos in partially-merged, partially-pulled states that are much harder to recover from than just doing them one at a time.

Exception: read-only parallel operations are fine (`git status`, `git log`, `git diff` across repos simultaneously).

## Rule 3: Dirty Working Tree — Never Destroy, Always Preserve

When `git status` shows uncommitted changes or untracked files:

### Modified tracked files
1. **Ask the user** what to do — these could be in-progress work
2. If the user says to proceed: `git stash push -m "auto-stash before [operation] $(date +%Y%m%d-%H%M)"` — always with a descriptive message
3. After the operation, remind the user about the stash: `git stash list`
4. **Never** do `git checkout -- .` or `git restore .` without explicit user approval

### Untracked files blocking a merge/pull
1. **Read the file** to understand what it is — it might be user work, a config file, or build output
2. If it's clearly build output (node_modules, .next, __pycache__, *.pyc): safe to remove
3. If it's a real file (source code, config, data): **ask the user** or move it to a temp location
4. **Never** blindly `rm` an untracked file just because git told you to

*See `references/incidents.md` → "vitest.config.ts incident" for why this rule is strict.*

## Rule 4: Worktree and Agent Work Must Be Pushed

If you are working in a git worktree (isolation mode) or as a background agent:

1. **Commit early and often** — don't wait until the task is "done"
2. **Push to remote** before your task completes — worktrees are cleaned up automatically when agents finish
3. **Name branches clearly**: `agent/<task-description>` (e.g., `agent/add-widget-to-hub`)
4. **Verify the push succeeded**: `git log origin/<branch> --oneline -1`

If you don't push, the branch exists only in the worktree's local state. When the worktree is cleaned up, everything is gone. *See `references/incidents.md` → "Worktree Migration Loss".*

### Checkpoint commits for long tasks
If your task will take more than 5 minutes or involve multiple files:
- Commit after each logical unit of work with message: `WIP: [what was done]`
- Push after each commit
- A clean history can be squashed later; lost work cannot be recovered

## Rule 5: Pull/Merge Safety Sequence

The safe sequence for updating a local repo:

```bash
# 1. Assess current state
git status
git branch --show-current

# 2. Handle dirty tree (see Rule 3)
# ... stash if needed ...

# 3. Fetch first (read-only, always safe)
git fetch origin

# 4. Check what would change
git log --oneline HEAD..origin/main  # see incoming commits
git diff --stat HEAD..origin/main     # see file changes

# 5. Pull (fast-forward preferred)
git pull origin main --ff-only

# 6. If ff-only fails — STOP HERE. Do not continue.
# Report to user: "Local main has diverged from origin/main."
# Show them the commits on each side.
# Ask: "Would you like me to rebase, merge, or investigate further?"
# Wait for their answer before doing anything.

# 7. Verify
git status
git log --oneline -3
```

**Never** use `git pull` without `--ff-only` as a first attempt. If ff-only fails, that means local and remote have diverged — this is a decision point, not something to auto-resolve.

**You must stop and ask the user.** Do not run `git rebase` or `git merge` on your own. The reason: diverged branches mean someone (possibly the user) committed locally. Rebasing rewrites their commit history. Merging creates a merge commit they may not want. Both change the repo in ways that are hard to undo. The user knows the project context — let them choose.

Show them:
```bash
git log --oneline HEAD..origin/main   # what remote has
git log --oneline origin/main..HEAD   # what local has
```
Then ask which strategy they prefer. This is not optional — even if the divergence looks trivial (1 commit each, no conflicts), the user still decides.

## Rule 6: Merge Operations

Before merging a branch:

```bash
# 1. Verify the branch exists on remote
git branch -r | grep <branch-name>

# 2. If it doesn't exist, STOP — the branch may have been:
#    - Already merged and deleted
#    - Created in a worktree that was cleaned up (never pushed)
#    - Named differently than expected

# 3. Preview the merge
git log --oneline main..<branch-name>  # what commits are coming in
git diff --stat main..<branch-name>     # what files change

# 4. Merge with --no-edit (no interactive editor)
git merge origin/<branch-name> --no-edit

# 5. If conflicts, STOP and report to user — don't auto-resolve
```

## Rule 7: Multi-Repo Deploy Coordination

When deploying changes across multiple repos (common in the Flora ecosystem):

1. **Plan the order** — identify dependencies (e.g., API must deploy before frontend)
2. **Do repos sequentially** — one at a time, verified before moving to next (Rule 2)
3. **Each repo gets the full safety sequence**: assess → fetch → preview → act → verify
4. **If any repo fails, stop** — don't continue to dependent repos with a broken upstream
5. **Track progress explicitly** — tell the user which repos are done, which remain

### The Flora repo ecosystem
These repos often need coordinated deploys:
- `<APP_1>` → `<APP_2>` → `<YOUR_ADMIN_APP>` (shared components flow downstream)
- `<SIGNAL_ENGINE>` / `fwis-api` (backend, usually independent)
- `dossier-builder` (independent, scp-based deploy)
- `inbox-triage`, `reservations-dashboard-next`, `flora-kb` (usually independent)

## Rule 8: Commit Discipline

### What to commit
- Run `git status` to see ALL changes
- Run `git diff` to review what changed
- Stage files explicitly by name — avoid `git add .` or `git add -A` which can catch secrets, large files, or unrelated changes

### After committing
- **Always** run `git status` after the commit to verify nothing was left behind
- If you fixed the same pattern across multiple files, double-check that ALL files are included. *See `references/incidents.md` → "The L16 Commit".*

### Commit messages
- End with `Co-Authored-By: Claude <model> <noreply@anthropic.com>` as required by system instructions
- Use conventional format: `fix:`, `feat:`, `chore:`, `refactor:`

## Rule 9: VPS Commits Must Be Pushed Immediately

When committing code on the VPS via SSH, **always push to the remote immediately after committing**. VPS repos are the live deployment — a commit without a push means:
- The next `docker compose build` rebuilds from the working tree, but a future `git pull` can overwrite your changes
- Container restarts that trigger rebuilds will use whatever the working tree has — which may be a stale merge
- No backup exists if the VPS disk fails

### The VPS commit sequence (mandatory)

```bash
# 1. Commit as normal
git add <files>
git commit -m "message"

# 2. Push immediately — find the deploy key for this repo
GIT_SSH_COMMAND='ssh -i /root/.ssh/<repo>-deploy -o IdentitiesOnly=yes' git push origin main

# 3. Verify
git log --oneline origin/main..HEAD  # should show nothing
```

### Deploy key lookup
Each Flora repo on VPS has a deploy key. **Always use `GIT_SSH_COMMAND` for VPS git operations** — bare `git push`/`git pull` will fail with "Permission denied (publickey)".

```bash
# Pattern for ALL VPS git operations:
GIT_SSH_COMMAND='ssh -i /root/.ssh/<repo>-deploy -o IdentitiesOnly=yes' git push origin main
```

Common deploy keys:
- **Monorepo** (`<YOUR_ORG>/<YOUR_MONOREPO>`) → `/root/.ssh/<MONOREPO_DEPLOY_KEY>`
- `<APP_1>` → `/root/.ssh/<APP_1>-deploy`
- `<APP_2>` → `/root/.ssh/<APP_2>-deploy`
- `<SIGNAL_ENGINE>` → `/root/.ssh/<SIGNAL_DEPLOY_KEY>`
- `ik-buckets` → `/root/.ssh/ik-buckets-deploy`
- `<YOUR_ADMIN_APP>` → `/root/.ssh/<YOUR_ADMIN_APP>-deploy`

If unsure: `ls /root/.ssh/*deploy*` to find the right key.

**This is the #1 VPS git error.** Every agent that does git operations on VPS hits this at least once. Always use the deploy key — never bare `git push/pull`.

*See `references/incidents.md` → "Portal Home Page Optimization Loss" for why this rule is non-negotiable.*

## Rule 10: Destructive Operations Are Banned Without Explicit Approval

These commands require the user to explicitly ask for them. Never run them proactively:

- `git reset --hard` — destroys uncommitted work
- `git push --force` / `git push -f` — rewrites remote history
- `git checkout -- .` / `git restore .` — discards all changes
- `git clean -f` — deletes untracked files permanently
- `git branch -D` — force-deletes a branch (even unmerged)
- `git rebase` on a pushed branch — rewrites shared history
- `rm` on any file that git is tracking or warning about

If you think one of these is needed, explain why to the user and ask first.

## Rule 11: Error Recovery

When a git command fails:

1. **Read the error message carefully** — git errors are usually very specific about what went wrong
2. **Don't retry the same command** — if it failed, something needs to change first
3. **Don't escalate to destructive commands** — a failed pull doesn't justify `reset --hard`
4. **Report the error to the user** with context: what you tried, what failed, what the repo state is now
5. **Suggest options** rather than picking one yourself — the user knows the project context better

### Common errors and safe responses

| Error | Wrong Response | Right Response |
|-------|---------------|----------------|
| "untracked files would be overwritten" | `rm` the files | Stash with `--include-untracked` or ask user |
| "your local changes would be overwritten" | `git checkout -- .` | `git stash` with descriptive message |
| "not a fast-forward" | `git pull --rebase` | STOP. Show commits on both sides. Ask user: "rebase, merge, or investigate?" |
| "merge conflict" | Auto-edit conflict markers | Report which files conflict, ask user |
| "branch not found on remote" | Create it or skip | Investigate — was it already merged? Never pushed? |
| "fatal: refusing to merge unrelated histories" | `--allow-unrelated-histories` | Stop — something is fundamentally wrong |

## Rule 12: Feature Branches Must Be Merged Before Session Ends

Feature branches that are "done" but not merged to main are a ticking time bomb. They get forgotten, conflict with later work, and create confusion about what's actually shipped.

**Before any agent shuts down or a session ends:**
1. If your feature branch work is complete and tested, merge it to main:
   ```bash
   git checkout main
   git merge feature/<name> --no-edit
   git push origin main
   ```
2. If it's not ready to merge (needs review, testing, etc.), create a PR and note it in the handoff report.
3. **Never leave completed feature branches unmerged.** *See `references/incidents.md` → "Sprint 3 Unmerged Feature Branches".*

**For orchestrators/PM trackers:** Verify all worker feature branches are merged as part of phase completion. Add "branches merged to main" to your phase-done checklist.

## Rule 13: Repo Routing — New Work Goes to the Monorepo

**For Flora projects:** All new work targets `<YOUR_ORG>/<YOUR_MONOREPO>` (the monorepo). Old individual repos (`<APP_1>`, `<APP_2>`, `<YOUR_ADMIN_APP>`, `flora-work-intelligence`, etc.) are **read-only for new features**. They may receive hotfixes only.

Before creating a branch or committing new work, verify the remote:
```bash
git remote -v
```

If the remote is NOT `<YOUR_ORG>/<YOUR_MONOREPO>.git`, you are in an old repo. **STOP.** The work should go in the monorepo instead.

**Exception:** Hotfixes to currently-deployed services that haven't been migrated yet. These can go to the old repo but must be noted for porting to the monorepo later. *See `references/incidents.md` → "Sprint 3 Repo Routing".*

## Rule 14: VPS Files Must Be Committed Before Modifying

Before modifying ANY file on VPS that isn't in a git repo:
1. Check if it should be in a repo — if yes, commit it first
2. If the directory has no `.git/`, flag it as an L9 violation
3. Never modify live VPS code without a git safety net

After deploying or modifying VPS files:
```bash
cd /path/to/repo
git status  # verify clean
git diff --stat  # if dirty, commit immediately
```

*See `references/incidents.md` → "VPS Uncommitted Production Code" for why this rule exists.*

## Quick Reference: The 30-Second Checklist

Before any git operation, mentally run through:

1. Did I check `git status`? → Do it now
2. Is the tree dirty? → Handle it safely (Rule 3)
3. Am I on the right branch? → Verify
4. Am I about to do this in parallel across repos? → Don't (Rule 2)
5. Am I in a worktree? → Push before finishing (Rule 4)
6. Could this command destroy work? → Ask the user first (Rule 10)
7. Did I verify after the operation? → `git status` again
8. Is my feature branch done? → Merge to main before shutting down (Rule 12)
9. Am I in the right repo? → Check remote URL, new work goes to monorepo (Rule 13)

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
