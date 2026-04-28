# Deploy Checklist

Inject into worker prompt when task deploys to VPS. These checks are mandatory — learned from incidents.

## Before Deploying

- Read `~/.claude/skills/vps-deploy/SKILL.md` and `~/.claude/skills/git-safe/SKILL.md`
- Read project `lessons.md` for lessons tagged with the service being deployed
- Check for ForwardAuth: if deploying behind auth, exclude static asset paths (`/_next/`) and seed role_permissions

## Deploy Verification (every step, every deploy)

1. **Push confirmed:** `git log origin/main --oneline -1` shows your commit
2. **VPS updated:** `ssh vps "cd /docker/{{MONOREPO_NAME}} && git log --oneline -1"` matches step 1
3. **Container rebuilt:** `ssh vps "docker inspect <container> --format '{{.Created}}'"` is AFTER your push
4. **Health check:** `ssh vps "curl -sf http://localhost:<port>/api/health"` returns 200
5. **Live URL:** `curl -sf https://YOUR_DOMAIN/<app>/` returns expected status

If ANY step fails, do NOT report "deployed". Fix it first.

## Zero-Downtime Swap

Stop old THEN start new. Never run both simultaneously with the same PathPrefix — Traefik round-robins and users see inconsistent behavior.

```bash
docker compose stop <old-service>
docker compose up -d <new-service>
curl -sf http://localhost:<port>/api/health  # verify
# Rollback if health fails:
docker compose stop <new-service> && docker compose start <old-service>
```

## Push != Deploy

As of 2026-04-07, `git push` does NOT auto-deploy. Run `./infra/dev/flora-deploy <service>` (or `safe-build <service> --pull` on VPS) explicitly.

## Dual-Compose Middleware

Before enabling Traefik on a new service, grep ALL docker-compose files for the same middleware name. Duplicate definitions across compose projects cause Traefik to DROP the middleware entirely.

## Runtime Fixes (no code commit)

If you fix something via direct DB operation or container rebuild, document in the WL file: what changed, why, exact command. Note there's no git trail for this fix.
