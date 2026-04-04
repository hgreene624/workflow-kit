---
name: vps-deploy
description: >-
  Mandatory safety protocol for all Docker deployment operations on the VPS — build, up,
  restart, compose file edits, and service replacement. MUST be consulted before running
  any `docker compose build`, `docker compose up`, `docker compose restart`, `docker compose down`,
  or before editing any `docker-compose.yml` / `Dockerfile` on the VPS. Also trigger when
  deploying a new service behind Traefik, replacing an existing service, adding ports or
  route labels to a container, or running `safe-build`. This skill prevents the recurring
  issues of silent file loss from rebuilds over uncommitted work, stale restarts that don't
  pick up code changes, conflicting Traefik routers causing partial failures, and garbled
  responses from double-compressed proxies. If you are about to run ANY docker compose
  command on the VPS, consult this skill first.
---

# VPS Deploy Protocol

All {{ORG}} services use **COPY-only deploys** (ADR-003): app code is baked into Docker images via `COPY`, not bind-mounted. This means every code change requires a full rebuild — there is no edit-and-restart shortcut. The only exceptions to bind-mounting are `.env` files, credentials, and persistent data volumes.

This protocol exists because agents have repeatedly caused silent file loss, service outages, and hours of wasted debugging. Every step below prevents a real incident.

---

## Deploy Procedure

Follow these steps in order. Do not skip steps.

### Step 1: Identify the Target

```bash
ssh vps "export PATH=/root/bin:\$PATH && whichcontainer <url-path>"
```

- Show the output in your response
- Confirm the container name and compose file path match your intent
- If there's a mismatch, stop and ask the user
- Run this every time — never rely on prior knowledge

### Step 2: Pre-Deploy Assessment

```bash
# Check git state on VPS
ssh vps "cd <project-dir> && git status --short && git log --oneline origin/main..HEAD"

# Check container status
ssh vps "docker ps --filter name=<container> --format '{{.Names}}\t{{.Status}}'"
```

What you're checking:
- **Dirty tree** — uncommitted files get baked into the image, then lost on next pull
- **Unpushed commits** — local-only commits vanish if someone pulls or the disk fails
- **Container state** — know what's running before changing it

### Step 3: Build Locally First (Monorepo Deploys)

For services in the {{MONOREPO_NAME}}, **always verify the build passes locally before pushing**:

```bash
cd ~/Repos/{{MONOREPO_NAME}} && pnpm --filter @{{ORG}}/<app> build
```

This catches TypeScript errors, missing imports, and bundler issues before they fail inside Docker on the VPS (where build output is harder to read and rebuilds are slow).

### Step 4: Audit the Dockerfile for New Files

When deploying a feature that adds new directories or file types (e.g., `messages/`, `migrations/`, config files), check that the Dockerfile copies them:

```bash
# List COPY directives
ssh vps "grep COPY <project-dir>/Dockerfile"
```

If your new directory isn't listed, add a `COPY` line. This is the #1 cause of "works locally, fails in Docker" — the build context doesn't include files that aren't explicitly copied.

### Step 5: Push and Pull

**Before pulling on VPS, check for dirty state** (prevents silent overwrites):

```bash
# From local — push to remote
cd ~/Repos/{{MONOREPO_NAME}} && git push origin main

# On VPS — check clean, then pull
ssh vps "cd <project-dir> && git status --short"
# If dirty: commit or stash VPS changes BEFORE pulling
ssh vps "cd <project-dir> && git pull origin main"
```

### Step 6: Build and Deploy

Use `safe-build`, never raw `docker compose build`. It checks for uncommitted changes and unpushed commits before building.

```bash
ssh vps "cd <project-dir> && export PATH=/root/bin:\$PATH && safe-build <service>"
```

If safe-build warns about dirty files **outside** your service (unrelated changes), use `--force`. If the dirty files are **inside** your service, stop and commit them first.

After build succeeds, bring the container up:

```bash
ssh vps "cd <project-dir> && docker compose up -d <service>"
```

### Step 7: Verify (MANDATORY)

You may NOT tell the user "it's deployed" until you prove it works.

**For web apps** — curl from inside the Docker network or the container itself:
```bash
ssh vps "docker exec <container> wget -q -O- http://127.0.0.1:<port>/<path> | grep '<marker>'"
```

**For API endpoints:**
```bash
ssh vps "curl -s http://localhost:<port>/api/<endpoint> | head -20"
```

**For services behind auth** — curl from inside the container bypasses Traefik/ForwardAuth:
```bash
ssh vps "docker exec <container> wget -q -O- 'http://127.0.0.1:<port>/<path>' | grep '<marker>'"
```

**Report format:**
```
Deployed and verified:
- Container: <name> rebuilt and running
- Verification: <evidence the change is live>
- Hard refresh (Cmd+Shift+R) to bypass browser cache
```

If verification fails, diagnose and fix — do not tell the user to test.

### Step 8: Infrastructure Baseline Update (Container Add/Remove/Rename Only)

**Skip this step for routine code deploys.** Only applies when you add a new container, remove/sunset a container, or rename one.

After a container change is verified, update the VPS infrastructure baseline so nightly audits don't flag the change as drift:

1. **Update `vps-audit.sh`** — edit `EXPECTED_CONTAINERS` and `CONTAINER_COMPOSE` arrays:
   ```bash
   ssh vps "nano /root/vps-audit.sh"  # or scp a patched version
   ```

2. **Test zero drift** — run the audit and confirm no false positives:
   ```bash
   ssh vps "bash /root/vps-audit.sh"
   # Silent output = clean. Any Telegram alert = something's wrong.
   ```

3. **Update `REF - VPS Work Rules.md`** — add/remove the container from the App Location Map and Docker Compose Projects tables in the vault.

4. **Update Chawdys' infrastructure-audit skill** — the expected containers list in `/data/.openclaw/workspace/skills/infrastructure-audit/SKILL.md` must match. Use `docker cp` to push the updated file.

**Why this exists:** On 2026-03-29, Chawdys flagged 11 "missing" containers that were actually intentional renames from the Platform Redesign migration. The baseline hadn't been updated since 2026-03-09. Three separate lists (vps-audit.sh, Chawdys skill, REF doc) drifted independently for 3 weeks, causing a full day of false-positive triage. This step prevents that.

---

## Rebuild vs Restart

Getting this wrong means your changes are silently ignored:

| Change type | What to run |
|------------|-------------|
| Code files (src/, templates/) | `safe-build` then `docker compose up -d` |
| Bind-mounted config files | `docker compose restart` is sufficient |
| Environment variables (.env) | `docker compose up -d` (recreates container) |
| Dockerfile or docker-compose.yml | `safe-build` then `docker compose up -d` |

If unsure whether a file is COPY'd or mounted:
```bash
ssh vps "grep COPY <project-dir>/Dockerfile && grep -A5 'volumes:' <project-dir>/docker-compose.yml"
```

---

## Traefik Safety

### Replacing a Service

Traefik routes randomly to both old and new containers if both are running with the same route rules. Always stop the old one first:

```bash
ssh vps "cd <old-compose-dir> && docker compose stop <old-service>"
ssh vps "cd <new-compose-dir> && safe-build <new-service> && docker compose up -d <new-service>"
# Verify, then remove old container if no longer needed
```

After decommissioning a service (L41), verify the old container is actually stopped — don't just remove it from compose and assume Docker cleaned it up:
```bash
ssh vps "docker ps -a --filter name=<old-container>"
```

### Multi-Port Containers

When a container exposes multiple ports, every router needs an explicit `.service=` label. Without it, Traefik fails with "cannot be linked automatically with multiple Services" and ALL routes on that container break.

```yaml
# Every router must specify which service it uses
- "traefik.http.routers.myapp-web.service=myapp-web"
- "traefik.http.routers.myapp-api.service=myapp-api"
```

### Inner Proxy Compression

If your service runs its own reverse proxy (Caddy, nginx) behind Traefik, disable compression in the inner proxy. Traefik strips `Content-Encoding` headers, so the browser gets compressed bytes it can't decode — garbled text with no error.

| Caddy | Remove `encode zstd gzip` |
|-------|--------------------------|
| nginx | Remove `gzip on;` |
| Express | Remove `compression()` middleware |

### ForwardAuth Header Limits

Traefik's ForwardAuth adds `X-{{ORG}}-*` headers and cookies that can push total header size past 8KB. For new services:

| Gunicorn | `--limit-request-field_size 16384` |
|----------|-----------------------------------|
| nginx | `large_client_header_buffers 4 16k;` |
| Node.js | Usually fine (16KB default) |

Symptom: HTTP 431 or silently dropped requests.

---

## Compose File Safety

Before modifying any `docker-compose.yml`:

```bash
# Validate syntax
ssh vps "cd <project-dir> && docker compose config --quiet"

# Check for empty env vars
ssh vps "cd <project-dir> && docker compose config 2>&1 | grep -E '^\s+\w+:\s*$'"
```

Never hardcode secrets in compose files — always use `${VAR}` references from `.env`.

---

## When Things Break

### Snapshot first, then fix

```bash
ssh vps "cd <project-dir> && cp docker-compose.yml docker-compose.yml.pre-fix-\$(date +%Y%m%d-%H%M)"
ssh vps "cd <project-dir> && cp .env .env.pre-fix-\$(date +%Y%m%d-%H%M)"
```

If your first fix doesn't work, **restore the snapshot** instead of layering more fixes. Cascading fix attempts turn 1 problem into 5.

### Cache issues

If the user reports stale content after a deploy:
1. Check inside the container that the file is actually updated
2. Tell user: "Hard refresh (Cmd+Shift+R)" or "Clear site data in DevTools"
3. For static files without content-hash names, add `?v=<timestamp>` query params

---

## Quick Reference

```bash
# Standard monorepo deploy (most common pattern)
cd ~/Repos/{{MONOREPO_NAME}} && pnpm --filter @{{ORG}}/<app> build   # local build check
git push origin main
ssh vps "cd /docker/{{MONOREPO_NAME}} && git pull origin main"
ssh vps "cd /docker/{{MONOREPO_NAME}} && export PATH=/root/bin:\$PATH && safe-build <service> && docker compose up -d <service>"
ssh vps "docker logs --tail 20 <container>"

# Verify
ssh vps "docker exec <container> wget -q -O- 'http://127.0.0.1:<port>/<path>' | grep '<marker>'"
```

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
