# Smoke Checks

Run these inline after each phase completion or deploy. You (the orchestrator) run them directly — no separate agent. Binary pass/fail output. If anything fails, tell the worker what broke.

## Build Check

```bash
pnpm --filter <app> build
```

PASS = zero errors. FAIL = any error. Don't proceed until build is clean.

## Route Check (after deploy)

For each key route the phase touched, curl it:

```bash
# Health
curl -sf https://YOUR_DOMAIN/<app>/api/health && echo "PASS: health" || echo "FAIL: health"

# Key pages (adjust per phase)
curl -sf -o /dev/null -w "%{http_code}" https://YOUR_DOMAIN/<app>/ | grep -q "200\|308" && echo "PASS: index" || echo "FAIL: index"

# Auth-protected routes should return 302 (redirect to login)
curl -sf -o /dev/null -w "%{http_code}" https://YOUR_DOMAIN/<app>/admin | grep -q "302" && echo "PASS: admin auth" || echo "FAIL: admin auth"
```

Customize the routes per phase. Check what the phase actually built.

## Diff Check

```bash
# No secrets in staged changes
git diff --cached | grep -iE "(api_key|secret|password|token)\s*[:=]" && echo "FAIL: possible secret in diff" || echo "PASS: no secrets"

# No console.log left behind
git diff --cached -- '*.ts' '*.tsx' | grep "+.*console\.log" && echo "WARN: console.log in diff" || echo "PASS: no console.log"
```

## Schema Check (if migration was applied)

```bash
# Migration file has a down/rollback method
grep -l "down\|rollback\|revert" <migration_file> && echo "PASS: rollback exists" || echo "WARN: no rollback method"
```

## Container Check (after VPS deploy)

```bash
ssh vps "docker inspect <container> --format '{{.State.Health.Status}}'" | grep -q "healthy" && echo "PASS: container healthy" || echo "FAIL: container unhealthy"

ssh vps "docker inspect <container> --format '{{.Created}}'" 
# Verify timestamp is AFTER your push
```

## Reporting

Print results as a compact block:

```
Smoke check — Phase 2 (Auth Rewrite)
PASS: build clean
PASS: /owners/ returns 308
PASS: /owners/admin returns 302
PASS: /owners/api/auth/login returns 405
FAIL: /owners/privacy returns 302 (expected 200)
Result: 1 FAIL — worker needs to add /privacy to PUBLIC_PATHS
```

One failure line = one action item for the worker. No multi-page analysis needed.
