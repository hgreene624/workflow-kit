# Log Work -- Examples

Reference examples for daily note and work log formatting. Read this when unsure about format.

## Simple mode output (daily note only):

```markdown
### Vault Maintenance
- Standardized file prefixes across 12 reports, cleaned up 3 orphaned directories
```

## Detailed mode output:

**WL file** (`02_Projects/owner-portal/work-logs/WL - Owner Portal 2026-04-08.md`):
```markdown
## 2026-04-08

### 09:30 -- Phase 0 audit + local env setup
- P0.1 DONE -- prerequisites audit PASS (3 non-blocking warnings)
- P0.2 DONE -- KB created (UUID 6dd426ea, slug owner-meetings)
- P0.3 DONE -- staging DB snapshot: 209,238 bytes, 11 v2 tables, sha256 a23a42b3
- P0.4 DONE -- local dev validated at port 3012, prod healthy
- Worktree created, env file added
- Artifacts: [[ARE - Owner Portal Phase 0 Audit]], [[ARE - Owner Portal Phase 0 Result]]

### 11:15 -- Phase 1 schema migrations
- P1.2 DONE -- owners->users rename migration (0008_rename.sql), 604 rows unchanged
- P1.3 DONE -- voting_items rename (0007_voting_items.sql), cadence enum clean
- P1.5 DONE -- auth_tokens + owner_emails tables (0006_auth.sql)
- P1.6 DONE -- ownership_lines backfill (0010_ownership.sql), 614 rows
- P1.9 DONE -- rollback round-trip PASSED, commit b3ca2bc
- Phase 1 COMPLETE

### 14:00 -- Phase 2 auth rewrite
- P2.2-P2.11 all DONE -- argon2 hashing, signup/login/reset/logout endpoints, proxy gating, UI pages, admin bulk-invite, smoke test PASS
- Raw-SQL rot patched at W-1 locations, wider rot (~12 files) in progress
- Build clean: 37 static pages, zero TS errors
- Phase 2 COMPLETE
```

**Daily note:**
```markdown
### Apps
#### Owner Portal
- **Built the full owner portal** -- authentication, ownership cards, voting flow, and admin controls all live
- Ran live UAT, caught and fixed 9 bugs during testing
- Bulk signup emails and final review still needed -- [[PJL - Owner Portal|Project log]]
```

## More daily note examples:

**Multi-workstream project (good):**
```markdown
### Intelligence
#### Signal Engine
- **Verified signal pipeline works after gateway refactor** -- fixed two bugs that were crashing email processing and meeting tracking
- Cleaned up stuck processing runs and backfilled missing staff records -- [[PJL - Signal Engine|Project log]]
```

**Light day, no WL needed:**
```markdown
### Apps
#### Admin Panel
- **Prompt library restructured** -- 20 top-level groups collapsed to 5 layers, 112 prompts remapped (deployed to production)
```

## BAD daily note entries:

**Too many headings for one project:**
```markdown
### Portal v3 Sprint -- Phase 0
- P0.1 DONE -- Audit...
### Portal v3 Sprint -- Phase 1
- P1.1 DONE -- Audit...
- P1.2 DONE -- Draft migration...
### Portal v3 Sprint -- Phase 2
- P2.1 DONE -- Audit...
### Portal -- Phases 2-6 Complete + Production Deploy
- Phases 2-6 all complete...
### Portal -- Owner Routing Deploy
- Caught silent undeployed code...
```
This is 5 headings for ONE project. Merge into a single `#### Owner Portal` with 3 summary bullets.

**Per-task breakdown in daily note:**
```markdown
### Migration -- [[PL - ...]]
- P14.1 Audit -- 16 routes, 17 AG Grid instances...
- P14.2 Scaffold -- apps/viewer/ created...
- P14.3 Meetings -- AG Grid 8 cols...
- P14.4 Signal Explorer -- 608-line client...
```
This is a task log, not a summary. All that detail goes in the WL file.
