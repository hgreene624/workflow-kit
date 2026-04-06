# Git Safety — Incident History

These incidents explain WHY each rule exists. Read this file when you need context on a specific rule's origin or when investigating a similar failure pattern.

## The vitest.config.ts Incident (Rule 3)

An agent deleted an untracked `vitest.config.ts` just because git said "untracked working tree files would be overwritten by merge." That file existed because remote had added it — the right move was `git stash --include-untracked`, not `rm`. Lesson: never blindly delete untracked files; understand what they are first.

## Worktree Migration Loss (Rule 4)

Three parallel agents lost their migration work because they committed to worktrees but never pushed to remote. When the worktrees were cleaned up, all branches existed only in local state — everything was gone. Lesson: always push before finishing worktree work.

## The L16 Commit (Rule 8)

The same pattern was fixed across 5 files, but only 4 were committed. The deploy went out with the 5th file still broken. Lesson: always run `git status` after committing and verify ALL intended files were included.

## Portal Home Page Optimization Loss (Rule 9, 2026-03-17)

The portal home page optimization (2.3s → 260ms load time) was committed on VPS but never pushed to remote. A container rebuild triggered a `git pull` which merged remote changes on top, and the rebuild used the merged (un-optimized) code. The fix was lost and had to be re-applied the next day. Lesson: VPS commits must be pushed immediately.

## Sprint 3 Unmerged Feature Branches (Rule 12)

Sprint 3 had 3 completed feature branches (`feature/shared-packages`, `feature/mailbox-viewer`, `feature/fwis-audit`) that were pushed but never merged — main was still at the initial commit. Future agents checking out main got stale code. Lesson: merge completed branches before session ends.

## Sprint 3 Repo Routing (Rule 13, 2026-03-20 audit)

Sprint 3 work landed across 3 different repos (monorepo, signal engine, feature branches) instead of consolidating in the monorepo. The signal engine reorganization was done in the old repo because "it hadn't been copied yet" — creating a porting step and risking the work being forgotten. Lesson: new work always goes to the monorepo.

## VPS Uncommitted Production Code (Rule 14, 2026-03-20 audit)

42 modified files in the VPS signal engine had no commits. `ai-gateway/` and `limitless-sync/` directories had production code with zero git tracking. Lesson: all VPS code must be in a git repo and committed before modification.
