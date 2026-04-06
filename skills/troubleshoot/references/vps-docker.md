# VPS / Docker / Traefik Diagnostics

## Architecture Overview

- **VPS:** Single Hetzner server, all services containerized
- **Reverse proxy:** Traefik v3.5 at `/docker/traefik-n8n/docker-compose.yml`
- **Networks:** `root_default` (Traefik/public), `flora_flora-internal` (postgres/inter-service)
- **Compose projects:** Flora (main), Flora KB, DocGen, OpenClaw, Plane, Reservations, Tools, Monitoring
- **Auth:** ForwardAuth via `<YOUR_GATEWAY_APP>` gateway — protected services get `X-Flora-*` headers

## Diagnostic Checklist

### 1. Which container serves this URL?

**This is the #1 cause of stuck debugging.** Always verify before editing code.

```bash
# Check Traefik labels for a specific path
ssh <YOUR_VPS> "grep -r 'PathPrefix\|rule=' /docker/*/docker-compose.yml /root/*/docker-compose.yml 2>/dev/null | grep -i '<path>'"

# Or inspect a specific container's routing
ssh <YOUR_VPS> "docker inspect <container> --format '{{json .Config.Labels}}' | python3 -m json.tool | grep traefik"
```

**Remember:** Traefik uses MOST SPECIFIC prefix match. `/kb/sales` beats `/kb/`. See `routing-map.md` for the full URL→container map.

**Cross-ref:** VPS L21, FWIS L8, Agent L21

### 2. Is the file bind-mounted or COPY'd?

```bash
ssh <YOUR_VPS> "docker inspect <container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'"
```

- **Bind-mounted:** Edits on VPS host take effect immediately (or after server restart)
- **COPY'd:** Edits on host are invisible until `docker compose up -d --build`

**Cross-ref:** VPS L2, VPS L15

### 3. Is the container running the latest code?

```bash
# When was it built?
ssh <YOUR_VPS> "docker inspect <container> --format '{{.Created}}'"

# What's the latest commit in the source?
ssh <YOUR_VPS> "cd <source-path> && git log --oneline -1"

# Does the running code contain your change?
ssh <YOUR_VPS> "docker exec <container> grep -r '<your-change>' /app/"
```

### 4. Container logs

```bash
ssh <YOUR_VPS> "docker logs <container> 2>&1 | tail -30"
ssh <YOUR_VPS> "docker logs <container> 2>&1 | grep -i error | tail -10"
```

### 5. Is the container healthy?

```bash
ssh <YOUR_VPS> "docker ps --filter name=<container> --format '{{.Status}}'"
ssh <YOUR_VPS> "docker compose -f <compose-file> ps"
```

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| Edited file but no change | COPY'd, not bind-mounted | Rebuild container | VPS L2, L15 |
| Wrong page served | Wrong container for URL path | Check Traefik labels | VPS L21 |
| "Request Header Too Large" | ForwardAuth adds headers | Increase header limits | VPS L9 |
| Container in restart loop | Bad file pushed (syntax error) | Check logs, fix file | VPS L14 |
| Two containers on same host | Old service not stopped | Stop conflicting router | VPS L7 |
| Service shows stale content | Container not rebuilt after push | `docker compose up -d --build` | VPS L14 |

## Shell Escaping Rules

**Never pass complex commands through `ssh + docker exec` inline.** Nested quotes get mangled.

Pattern:
```bash
# Write locally, scp, run
scp /tmp/fix.py vps:/tmp/fix.py
ssh <YOUR_VPS> "docker cp /tmp/fix.py CONTAINER:/tmp/fix.py && docker exec CONTAINER python3 /tmp/fix.py"
```

**Cross-ref:** VPS L4 (shell escaping), L16 (heredocs over ssh), L17 (python3 -c in double quotes), L18 (pipe + heredoc conflict)

## Key Gotchas

- **IK Buckets:** `app.py` and `templates/` live ONLY in container. Commit inside container, push from host. `.git`, `briefs/`, `db/` are bind-mounted.
- **Flask caching:** Editing a Flask template inside a container requires container restart (`docker restart <name>`) for changes to take effect.
- **Standalone Next.js:** No `curl`, `wget`, or bash utils inside standalone containers. Test from VPS host using container IP.
- **Container IPs change on restart.** Always query: `docker inspect <container> --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'`

## Compose File Locations

| Project | Path |
|---------|------|
| Flora (main) | `/docker/flora/docker-compose.yml` |
| Flora KB | `/root/flora-kb/docker-compose.yml` |
| DocGen | `/docker/docgen/docker-compose.yml` |
| OpenClaw | `/docker/openclaw/docker-compose.yml` |
| Traefik + n8n | `/docker/traefik-n8n/docker-compose.yml` |
| Plane | `/docker/plane/docker-compose.yaml` |
| Reservations | `/docker/reservations-dashboard/docker-compose.yml` |
| Tools | `/docker/dossier-builder/docker-compose.yml` |
| Monitoring | `/docker/uptime-kuma/docker-compose.yml` |

## Post-Deploy Verification — QA Suite

After any container rebuild or service restart, run the Playwright smoke tests from `~/Repos/{{MONOREPO_NAME}}/`:

```bash
npx playwright test --config tests/qa/playwright.config.ts --project=smoke
```

This checks all 7 services load correctly (~7s). If a specific service is suspect, the navigation crawl can check all its routes:

```bash
npx playwright test tests/qa/navigation.spec.ts --config tests/qa/playwright.config.ts
```

Requires valid auth state at `tests/qa/.auth-state.json`. Regenerate with `./scripts/qa-auth-setup.sh`.

## Lessons Files
- `01_Work/03_Projects/VPS/lessons.md` — all VPS-specific lessons (L1–L21)
