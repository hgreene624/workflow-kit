# Log Work — Examples

Reference examples for daily note and work log formatting. Read this when unsure about format.

## Simple mode output (daily note only):

```markdown
### Vault Maintenance
- Standardized file prefixes across 12 reports — `RE -` prefix applied consistently
- Cleaned up 3 orphaned data.nosync directories
```

## Detailed mode output:

**WL file** (`WL - Flora Migration Orchestration Plan.md`):
```markdown
## 2026-03-21

### 14:30 — P13.1 Audit existing Flora Portal
- 8 routes, 17 API endpoints, 4 LLM calls (Max Proxy Sonnet), 14 tables direct-DB
- Portal is 100% direct-DB — zero FWIS API data reads (plan was wrong)
- Plan gaps: Work Themes system and AI Chat both missing from plan
- Security concern: `docker exec chawdys` for email sending — needs proper API
- Complexity: HIGH overall, 3-4 week estimate
- [[RE - Flora Portal Audit (P13.1)]]

### 15:45 — P13.2 Scaffold portal Next.js app
- `apps/portal/`: Next.js 16.1.6, basePath `/portal`, standalone output
- 8 route stubs + 3 API stubs, ForwardAuth middleware, AG Grid v32, DaisyUI 5
- Build verified: 12 routes (5 static, 7 dynamic)
- Commit: `beab5a8`
```

**Daily note:**
```markdown
### Flora Migration — [[PL - Flora Migration Orchestration Plan|Plan]]
- P13.1 portal audit — **8 routes, 17 endpoints**, 100% direct-DB, Work Themes + AI Chat missing from plan
- P13.2 scaffold — Next.js 16, 8 route stubs, ForwardAuth, AG Grid, build verified
- [[WL - Flora Migration Orchestration Plan|Full log]]
```

## BAD daily note entry (too detailed):

```markdown
### Flora Migration — [[PL - ...]]
- P14.1 Audit — 16 routes, 17 AG Grid instances...
- P14.2 Scaffold — apps/fwis-viewer/ created...
- P14.3 Meetings — AG Grid 8 cols...
- P14.4 Signal Explorer — 608-line client...
- P14.5 People Grid — dept cards...
(15 more bullets with commit hashes and component lists)
```
This is a task log, not a summary. All that detail goes in the WL file.

## Good daily note entry (same sprint — properly summarized):

```markdown
### Flora Migration — [[PL - Flora Migration Orchestration Plan|Plan]]
- Completed **Phase 14 (FWIS Viewer)** — SvelteKit → Next.js, 16 routes, 17 AG Grid instances
- **16/17 tasks Done**, 4 post-deploy fixes, build:fix ratio **73:27**
- Old portal sunset — **9.9 GB** reclaimed, M12 (Core Apps Live) achieved
- [[WL - Flora Migration Orchestration Plan|Full log]]
```
