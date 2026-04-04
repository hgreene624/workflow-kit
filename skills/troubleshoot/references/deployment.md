# Git / Deployment Diagnostics

## Deployment Patterns

### Pattern 1: Local → Push → Pull → Rebuild (most apps)

```bash
# Local: commit and push
git add <files> && git commit -m "message" && git push origin main

# VPS: pull and rebuild
ssh <YOUR_VPS> "cd <source-path> && git pull && docker compose -f <compose-file> up -d --build <service>"
```

**Apps:** <YOUR_GATEWAY_APP>, <YOUR_ADMIN_APP>, <APP_1>, <APP_2>, reservations-dashboard, <SIGNAL_ENGINE>

### Pattern 2: VPS Direct Push

```bash
ssh <YOUR_VPS> "cd <source-path> && git add <files> && git commit -m 'message' && git push"
```

**Apps:** inbox-triage, dossier-builder, reservation-scraper, {{ORG_LOWER}}-kb, {{ORG_LOWER}}-email-portal

### Pattern 3: Commit Inside Container (IK Buckets)

```bash
# Commit inside container (where app.py and templates/ live)
ssh <YOUR_VPS> "docker exec ik-buckets sh -c 'cd /app && git add -A && git commit -m \"message\"'"

# Push from host (where SSH keys exist)
ssh <YOUR_VPS> "cd /docker/{{ORG_LOWER}}/ik-buckets && git push"
```

**Only IK Buckets uses this pattern.** `.git`, `briefs/`, `db/` are bind-mounted; `app.py` and `templates/` are COPY'd into the container.

## Diagnostic Checklist

### 1. Verify the deploy actually happened

```bash
# Check latest commit on VPS
ssh <YOUR_VPS> "cd <source-path> && git log --oneline -3"

# Check container build time
ssh <YOUR_VPS> "docker inspect <container> --format '{{.Created}}'"

# Check if container is running the new code
ssh <YOUR_VPS> "docker exec <container> grep -r '<unique-string>' /app/"
```

### 2. Check for unstaged files after committing

```bash
ssh <YOUR_VPS> "cd <source-path> && git status"
```

**Cross-ref:** Agent L16 (git status catches unstaged stragglers)

### 3. Verify the service name matches compose

```bash
# List service names in a compose file
ssh <YOUR_VPS> "docker compose -f <compose-file> config --services"
```

Common mistake: using container name (e.g., `{{ORG_LOWER}}-kb`) instead of service name (e.g., `kb`).

### 4. Check if rebuild is actually needed

```bash
# Is the file bind-mounted (no rebuild needed) or COPY'd (rebuild required)?
ssh <YOUR_VPS> "docker inspect <container> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'"
```

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| Change not visible after deploy | Container not rebuilt | `docker compose up -d --build <service>` | VPS L2, L15 |
| File left out of commit | Multi-file fix with explicit `git add` | Run `git status` after committing | Agent L16 |
| Build fails with syntax error | File corrupted by shell escaping | Write locally, scp to VPS | VPS L4, Agent L14 |
| Wrong service name | Container name ≠ service name | Check `docker compose config --services` | — |
| Local build wasted time | Docker builds on VPS, not locally | Skip local build for Docker-deployed apps | VPS L14 |
| Deploy key permission denied | Wrong SSH config alias | Check `~/.ssh/config` on VPS | — |

## Deploy Key Reference

Each repo has its own deploy key on VPS. SSH config aliases are in `/root/.ssh/config`.

```bash
# Test a deploy key
ssh <YOUR_VPS> "ssh -T github-<alias> 2>&1"
```

## Git Repo → VPS Path Map

| Local Path | VPS Path | Compose Service |
|-----------|----------|-----------------|
| `~/Projects/<YOUR_GATEWAY_APP>/` | `/docker/{{ORG_LOWER}}/<YOUR_GATEWAY_APP>/` | `<YOUR_GATEWAY_APP>` |
| `~/Projects/<YOUR_ADMIN_APP>/` | `/docker/{{ORG_LOWER}}/<YOUR_ADMIN_APP>/` | `<YOUR_ADMIN_APP>` |
| `~/Projects/<APP_1>/` | `/docker/{{ORG_LOWER}}/<APP_1>/` | `<APP_1>` |
| `~/Projects/<APP_2>/` | `/docker/{{ORG_LOWER}}/<APP_2>/` | `<APP_2>` |
| `~/Projects/<SIGNAL_ENGINE>/` | `/docker/{{ORG_LOWER}}/<SIGNAL_ENGINE>/` | `fwis-api` |
| `~/Projects/reservations-dashboard-next/` | `/docker/reservations-dashboard/` | `reservations-dashboard` |

## Worktree Agent Rules

- **Worktree agents MUST commit before finishing** — worktrees are auto-cleaned (Agent L1)
- **Don't parallelize overlapping file changes** — corrupts git index
- **Force checkpoints before context fills** — agents killed at compaction lose uncommitted work (Agent L4)

## Post-Deploy Verification — QA Suite

After deploying, verify with the Playwright QA suite at `~/Repos/{{MONOREPO_NAME}}/tests/qa/`:

```bash
cd ~/Repos/{{MONOREPO_NAME}}

# Quick check — all services still up? (~7s)
npx playwright test --config tests/qa/playwright.config.ts --project=smoke

# Full route validation — any broken links from the deploy?
npx playwright test tests/qa/navigation.spec.ts --config tests/qa/playwright.config.ts
```

If a deploy intentionally changed UI, update visual baselines afterward:
```bash
npx playwright test tests/qa/visual-regression.spec.ts --config tests/qa/playwright.config.ts --update-snapshots
```

Requires valid auth state (`tests/qa/.auth-state.json`). Regenerate with `./scripts/qa-auth-setup.sh` if expired.

## Key Gotchas

- **Never `npm run build` locally for VPS-deployed apps** — Docker builds inside the container on VPS (VPS L14)
- **IK Buckets is the only commit-inside-container app** — everything else commits on host
- **Subagents writing VPS files: write locally, scp** — never through ssh heredocs (Agent L14)
- **After context compaction, verify actual repo state** before re-dispatching (Agent L4)

## Lessons Files
- `01_Work/03_Projects/VPS/lessons.md` — L1, L2, L14, L15
- `04_ Tools/Reference/REF - Agent Lessons.md` — L1, L4, L14, L16
