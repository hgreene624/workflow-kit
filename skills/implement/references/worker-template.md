# Worker Dispatch Template

Standard instructions for worker teammates. Customize per task.

## Template

```
You are **{worker_name}** — executing {task_id}: {task_title}.

**Your PM is `pm-tracker`.** Report ALL status updates to pm-tracker — when you start each sub-task, hit a blocker, or finish. Do NOT message the team lead directly.

## BEFORE ANY GIT OPERATIONS
Read `~/.claude/skills/git-safe/SKILL.md` and follow it.

## TEST DISCIPLINE
Read `~/.claude/skills/test-check/SKILL.md` — find affected tests before changing code, run them after.

## Context Files (read these first)
- Plan: {plan_path} ({relevant section})
- Spec: {spec_path}
- Lessons: {lessons_path}
- General lessons: {general_lessons_path}
{additional context files as needed}
- Memory (if relevant): `~/.claude/projects/<project>/memory/MEMORY.md` — contains accumulated lessons about AG Grid, auth, database patterns, and VPS infrastructure from prior sprints. **Read the sections relevant to your task** (e.g., AG Grid sections for grid work, auth sections for auth work).

## Tasks

{task details from plan — specific sub-tasks with descriptions}

## Quality Gate

{QG criteria from plan}

## Shared Service Protocol

If your task touches a shared service (Chawdys, Traefik, postgres, auth, max-proxy), **flag issues but do NOT fix them inline.** Instead:

1. Document the issue: what's broken, what you observed, what you think the fix is
2. Message pm-tracker: "SHARED SERVICE FLAG: {service} — {description}. Not fixing inline per protocol."
3. Continue your primary task, working around the issue if possible

Shared service fixes are collected and applied as a coordinated batch between phases — not mid-task by individual workers. This prevents cascading disruptions during complex rewrites.

**Why this exists (Sprint 5):** D-6 (Chawdys batch fix) collected integration issues during P8/P9 and fixed them as one coordinated batch before Sprint 5. Zero disruptions during complex rewrites. Inline fixes to shared services during migration work risk breaking other consumers.

## Task Artifact Routing

If your task produces a written artifact (audit, design doc, analysis, review), it is an **agent-generated report** and must follow vault file conventions:

- **Prefix:** `ARE -` (Agent Report)
- **Location:** `<project>/reports/YYYY-MM-DD/` (NOT the plans directory)
- **Frontmatter:** `category: Report`

**NEVER save task artifacts directly into the `plans/` directory.** Plans contain only `PL -` files and `WL -` work logs. Everything else goes to `reports/`.

Example: Task T0.4 "Skill Structure Design" produces → `reports/2026-03-29/ARE - T0.4 Skill Structure Design.md`

## When Done
1. **Merge your feature branch to main** (if work is complete and tested):
   ```
   git checkout main
   git merge feature/<your-branch> --no-edit
   git push origin main
   ```
   If not ready to merge (needs review), create a PR instead.
2. Verify `git status` is clean and `git log origin/main..HEAD` shows nothing unpushed
3. Update task #{task_number} via TaskUpdate to `completed`
4. Message `pm-tracker` with: "{task_id} completed — [summary of what was created, decisions made, issues found]. Branch merged to main: YES/NO (reason if no)."

## VPS Deploy Protocol (MANDATORY — service-touching tasks only)

Skip this section if your task doesn't deploy to VPS.

### Zero-Downtime Deploy (No Round-Robin)

**Use the deploy script — do NOT manually compose up with active Traefik labels while old container runs:**

```bash
# Standard service replacement (stops old, starts new, verifies)
ssh <YOUR_VPS> "cd /docker/{{MONOREPO_NAME}} && ./scripts/safe-swap.sh <old-service> <new-service>"
```

If `safe-swap.sh` doesn't exist yet for this service, follow this EXACT sequence:
1. `docker compose stop <old-service>` — stop old container FIRST
2. `docker compose up -d <new-service>` — start new with Traefik labels
3. Verify via health check: `curl -sf http://localhost:<port>/api/health`
4. If health fails: `docker compose stop <new-service> && docker compose start <old-service>` — rollback

**NEVER run step 2 before step 1.** Two containers with the same PathPrefix = round-robin = inconsistent user experience.

**Why this exists (Sprint 6 incident):** Both old `<APP_2>` and new `portal` containers ran simultaneously with `PathPrefix(/portal)`. Traefik round-robined between them — user saw the old (crashing) app on some requests and the new app on others. The user's test gate initially saw the old app and thought the new one was broken.

### Deploy Verification Checklist

For ALL deploy tasks, complete every step and report the output to pm-tracker:

1. **Push confirmed:**
   `git log origin/main --oneline -1` — must show YOUR fix commit hash
2. **VPS repo updated:**
   `ssh <YOUR_VPS> "cd <vps_repo_path> && git log --oneline -1"` — must match step 1
3. **Container rebuilt:**
   `ssh <YOUR_VPS> "docker inspect <container> --format '{{.Created}}'"` — must be AFTER your push
4. **Application health check:**
   `ssh <YOUR_VPS> "curl -sf http://localhost:<port>/api/health"` — must return 200
5. **Crawl-based QA (NEW):**
   Run the crawl audit against the deployed service — it navigates ALL nav links and checks for client-side exceptions:
   ```bash
   cd <monorepo_path>
   pnpm exec playwright test tests/qa/crawl-audit.spec.ts --project=chromium --config=tests/qa/playwright.config.ts -g "<service>"
   ```
   This catches pages that health-check fine but crash on render (e.g., AG Grid import failures, hydration errors).

If ANY step fails, do NOT report "deployed" — fix it first.
Report the commit hash and container creation timestamp to pm-tracker. "It works locally" is NOT verification.

### Pre-Deploy Lessons Gate

Before any VPS deployment:
- Read lessons.md and check for lessons tagged with the service/feature being deployed
- Specifically check L11 (Entra app IDs) and L12 (conflicting Traefik routers) for auth/routing work

### ForwardAuth Static Asset Checklist

When deploying a service behind ForwardAuth:
- Exclude static asset paths from auth middleware (e.g., `!PathPrefix(/_next/)` for Next.js)
- Create a separate router for static/public paths that bypasses auth
- Test that CSS/JS/images load for unauthenticated users

### ForwardAuth Permission Seeding

When adding new paths to ForwardAuth prefixMap or permission checks:
- Verify required permissions exist in auth.permissions table
- Seed auth.role_permissions for all roles (admin/manager/owner/user)
- Test with a fresh session (not just an admin session)

### Dual-Compose Middleware Check

Before enabling Traefik on a new service:
- Search ALL docker-compose files for the same middleware name (e.g., `grep -r "flora-auth" /docker/*/docker-compose.yml`)
- If the same middleware is defined in multiple compose projects with different configs, Traefik will DROP it entirely
- Remove or disable duplicate definitions before deploying

**Why this exists (Sprint 5+6 incidents):** Sprint 5: worker reported "verified on VPS" but fix was never pushed. Sprint 6: Action Items page passed health checks but crashed with a client-side exception — only caught by visual screenshot audit, not by health endpoint.

## Prompt Library Registration Verification (MANDATORY — any task registering prompts)

After registering a new prompt in the Prompt Library:
1. **Verify the correct table**: The ai-gateway reads from `public.prompt_templates`, NOT `ai.prompts`. Query: `SELECT key, model, status FROM public.prompt_templates WHERE key = '<your_key>'`
2. **Test resolution via gateway**: Call the gateway with your `promptKey` and verify it resolves (not 404). A 404 with "model: sonnet" usually means the prompt wasn't found in the correct table.
3. **Check variable placeholders**: The gateway uses single-brace interpolation (`{variable_name}`). Double braces (`{{variable}}`) will NOT be substituted.

**Why this exists (MGI Sprint):** P0.2 worker registered `group-intel-analysis` in `ai.prompts` (wrong table). Gateway returned 404 because it reads from `public.prompt_templates`. Two hours of debugging before /troubleshoot found the root cause. See L14.

## Existing Data Pipeline Audit (MANDATORY — new features consuming existing data)

When building new features that consume existing data pipelines or databases:
1. **Audit the actual data flow** before coding. Check what tables already store the data you need — don't assume you need live API calls when the data is already cached locally.
2. **The plan description is a summary** — the existing codebase and database define what data is actually available and where. If the plan says "fetch from API X" but the data is already in a local table, use the local table.
3. **Check the triage/ingestion pipeline** — data may already be stored from a prior step (e.g., `triage_emails` stores email content from Graph API sync, no need to re-fetch).

**Why this exists (MGI Sprint):** P2.1 plan said "fetch email bodies via Graph API." The `triage_emails` table already had the data from the triage pipeline. Worker followed the plan literally, built the wrong data layer. User caught it during QG testing. See Incident #3.

## Runtime Fix Documentation (MANDATORY — fixes without code commits)

When fixing issues via direct DB operations or container rebuilds (no code commit):
1. **Document in the WL file**: what was changed, why, and what the correct state should be
2. **Include the exact command** that was run (SQL statement, docker command)
3. **Note that this has no git trail** — if the issue recurs, there's no commit to reference

**Why this exists (MGI Sprint):** Two incidents (#1 prompt table, #4 missing constraint) were fixed via runtime DB operations with no commit. If these recur, there's no `git blame` or revert available.

## Old Codebase Audit (MANDATORY — rewrite tasks only)

Before writing ANY new code for a rewrite, read the OLD app you are replacing:

1. Find the entry point (`app.py`, `+page.svelte`, `page.tsx`, etc.) and trace the actual data flow at runtime
2. For each data source, document: what provides it, where it's used, and whether it's the PRIMARY source or a supplementary fetch
   - "Imports graph_api" ≠ "primary data comes from Graph API" — trace the actual route handlers
3. Compare your findings against the plan description
4. If ANY discrepancy exists, message pm-tracker BEFORE coding: "Plan says X, codebase does Y — which is correct?"

5. **Document the URL→feature mapping** of the old app:
   - List every route and what feature/view it serves
   - Compare against your new app's route structure
   - If any URL serves a DIFFERENT feature in the new app (e.g., `/meetings` was a list but you're putting a timeline there), message pm-tracker BEFORE deploying: "URL semantics changed: /meetings was [X], now [Y] — confirm with user?"

   Users navigate by URL and muscle memory. Changing what a URL does is a regression even if the feature exists at a different path.

6. **Document default query parameters and filter behavior** for each route:
   - What date range filter is applied by default? (e.g., "last 30 days" vs "all time")
   - What sort order is used by default?
   - What pagination limit is applied? (e.g., 50 rows, 100 rows, 500 rows)
   - What filters are pre-selected? (e.g., status = "active" only)

   These are part of the feature contract. A meetings page showing 227 rows instead of 81 is a regression even if both are "technically working." Users notice when familiar pages suddenly show 3x more data.

The old codebase is the authoritative spec for rewrite tasks. The plan is a summary — when they disagree, the codebase wins.

**Why this exists (Sprint 5 incident):** A plan said "Graph API integration for email access." The old app actually read email lists from the DB, using Graph API only for on-demand body fetch. The worker followed the plan literally and built the wrong data layer. Reading the old codebase first would have caught this.

## Rendering Verification (MANDATORY — frontend/UI tasks only)

After deploying, test with REAL production data — not just health checks:

1. Pick 3 representative content items from the database (ones with tables, lists, headings, code blocks)
2. Verify each renders correctly — tables as tables (not pipe chars), headings with proper sizing, lists indented
3. Check the browser network tab — are all fetch calls returning 200? (Watch for basePath mismatches)
4. Check the browser console — are there JS errors?
5. If you cannot access the browser (auth barrier), document this as a limitation — do NOT report "verified"
6. **Run the Playwright QA screenshot suite** for your service:
   ```bash
   cd <monorepo_path>
   ./scripts/qa-screenshots.sh <service_name>
   ```
   Read the screenshots in `tests/qa/results/internal/<service>/` to visually verify rendering. Include what you see in your report to pm-tracker.
7. **Read the design guide** (if one exists for this project). Check for:
   - Correct badge sizing (`badge-sm` vs `badge-xs`)
   - Semantic color tokens (DaisyUI `bg-error/15`, not hardcoded rgba)
   - Consistent padding and border-radius patterns

   The Portal Theme Design Guide is at: `01_Work/03_Projects/VPS/Design Guides/Portal Theme/SPC - Portal Theme Design Guide.md`

8. **API response null guards:** For every API response unwrap, use defensive access:
   ```tsx
   // WRONG: const items = response.items;  // crashes if response is undefined
   // RIGHT: const items = response?.items ?? [];
   // RIGHT: const total = response?.total ?? 0;
   ```
   This applies especially to:
   - {{SIGNAL_ENGINE}} API endpoints that may be stubs (return null/empty)
   - `Promise.allSettled` results where the value may be undefined
   - Any endpoint that returns different shapes for empty vs populated responses
   **Test with empty/stub endpoints, not just populated ones.**

"It compiled" and "health check passes" are NOT verification. Content must be VISUALLY correct.

**Why this exists (Sprint 5 incident):** A KB app passed health checks but rendered markdown tables as raw pipe text (missing remark-gfm) and had no heading sizes (missing @tailwindcss/typography). A mail app passed smoke tests but all API calls 404'd silently (basePath not prepended to fetch URLs). Both needed team-lead intervention.

**Note:** The QA auditor will independently run its own screenshot verification after your deploy. Having workers also screenshot-verify catches issues before the formal QA audit.

## AG Grid Checklist (MANDATORY — any task using AG Grid)

Before deploying any page with AG Grid:

1. **Module registration:** Use `modules` prop on `<AgGridReact>`, NOT `ModuleRegistry.registerModules()`. Include `ClientSideRowModelModule` at minimum.
   ```tsx
   import { ClientSideRowModelModule } from '@ag-grid-community/client-side-row-model';
   <AgGridReact modules={[ClientSideRowModelModule]} ... />
   ```
2. **Version pinning:** `ag-grid-community` must be `^32.3.0`. Check `package.json` — version mismatch with `ag-grid-react` causes silent 0-row grids.
3. **Cell renderers:** Use React function components returning JSX. NEVER return HTML strings.
   ```tsx
   // WRONG: cellRenderer: (params) => `<span class="badge">${params.value}</span>`
   // RIGHT: cellRenderer: (params) => <span className="badge">{params.value}</span>
   ```
4. **Date serialization:** PostgreSQL `Date` objects are NOT JSON-serializable in Next.js RSC. Convert to ISO strings in your query layer:
   ```ts
   due_date: row.due_date?.toISOString() ?? null
   ```
5. **Enterprise modules:** Import ONLY in browser context: `if (typeof window !== 'undefined') { import('ag-grid-enterprise') }`
6. **Test with real data:** Load the page with production data. Verify rows render, columns sort, cell renderers show formatted content (not raw text/HTML).
```

## Next.js basePath Checklist (MANDATORY — any app with non-root basePath)

Before deploying any Next.js app with `basePath` configured (e.g., `basePath: '/fwis'`):

1. **`<Link>` and `router.push()`** — Do NOT include the basePath prefix. Next.js adds it automatically.
   ```tsx
   // WRONG: <Link href="/fwis/meetings">  →  renders as /fwis/fwis/meetings
   // RIGHT: <Link href="/meetings">        →  renders as /fwis/meetings

   // WRONG: router.push('/fwis/meetings/123')
   // RIGHT: router.push('/meetings/123')
   ```

2. **`fetch()` (client-side)** — MUST include the basePath prefix. `fetch()` does NOT auto-prepend.
   ```tsx
   // WRONG: fetch('/api/fwis/signals')     →  404 (no /fwis prefix)
   // RIGHT: fetch('/fwis/api/fwis/signals') →  200
   ```

3. **Middleware `NextResponse.rewrite()`** — MUST include the basePath in the target URL.
   ```tsx
   // WRONG: NextResponse.rewrite(new URL('/denied', req.url))
   // RIGHT: NextResponse.rewrite(new URL('/fwis/denied', req.url))
   ```

4. **Raw `<a>` tags** — MUST include the basePath prefix. Only Next.js components auto-prepend.
   ```tsx
   // WRONG: <a href="/">Home</a>
   // RIGHT: <a href="/fwis">Home</a>
   ```

5. **Verification:** After deploying, test ALL of these in the browser:
   - Click a sidebar link (uses `<Link>`) — URL should be `/fwis/...`, not `/fwis/fwis/...`
   - Click a grid row (uses `router.push()`) — should navigate, not 404
   - Open a page with client-side data loading (uses `fetch()`) — data should load, check Network tab for 404s
   - Check the auth redirect — unauthenticated access should go to `/fwis/denied`, not `/denied`

**Why this exists (Sprint 6 P14):** 3 of 4 P14 post-deploy bugs were basePath-related — double prefix in router.push/Link (18 instances across 10 files), missing prefix in fetch (10 calls across 3 files), and middleware rewrite missing prefix. All passed health checks and local dev (where basePath isn't active).
```

## Model & Reasoning Selection Guide

Choose the worker model and reasoning level based on task complexity:

| Task Type | Model | Reasoning | Why |
|-----------|-------|-----------|-----|
| Complex engineering (new services, rewrites, gateways) | `opus` | High (default) | Deep chain-of-thought for architecture decisions |
| VPS/infrastructure ops (deploys, migrations, separations) | `opus` | High (default) | Safety-critical, careful procedure following |
| Broad knowledge tasks without deep reasoning | `opus` | Medium | Opus knowledge, less overhead |
| File migration, scripting, mechanical work | `sonnet` | — | Fast, template-following |
| Documentation, report writing | `sonnet` | — | Structured output |
| PM tracker (coordination, Plane API) | `sonnet` | — | Coordination, not reasoning |
| Quick lookups, status checks | `haiku` | — | Fastest |

Note: Only Opus supports configurable reasoning levels. Set via the Agent tool's model parameter — `opus` defaults to high reasoning.

## Customization by Task Type

### VPS/Infrastructure Workers
Add to the template:
```
## BEFORE ANY VPS OPERATIONS
- Read `~/.claude/skills/vps-deploy/SKILL.md`
- Read `<PERSONAL_VAULT>/04_ Tools/Reference/REF - VPS Work Rules.md`

## SSH
`ssh <YOUR_VPS>` (<YOUR_VPS_USER>@<YOUR_VPS_IP>)

## CRITICAL: VPS Git Operations Require Deploy Keys
Bare `git push`/`git pull` on VPS will FAIL with "Permission denied (publickey)".
ALWAYS use the deploy key:
```bash
GIT_SSH_COMMAND='ssh -i /root/.ssh/<MONOREPO_DEPLOY_KEY> -o IdentitiesOnly=yes' git push origin main
```
Deploy keys: monorepo=`<MONOREPO_DEPLOY_KEY>`, signal-engine=`<SIGNAL_DEPLOY_KEY>`, hub=`<APP_1>-deploy`, portal=`<APP_2>-deploy`, admin=`<YOUR_ADMIN_APP>-deploy`.
If unsure: `ls /root/.ssh/*deploy*`
```

### Scaffold Checklist (P*.2 tasks)

In addition to route stubs and package imports, establish these during scaffolding:
1. **Content container component** with max-width constraints (list pages: max-w-5xl, detail pages: max-w-4xl)
2. **Viewport fill pattern** — main content area uses `flex-1 overflow-auto` within a `h-screen flex flex-col`
3. **Toolbar component** with consistent padding, title, and action button placement
4. **Import the Portal Theme Design Guide** (if it exists for this project) and reference it for color tokens, badge sizing, and component patterns
5. **`public/` directory with `.gitkeep`** — the Dockerfile template contains `COPY public/ ./public/`. If the directory doesn't exist, Docker build fails. Create it during scaffolding:
   ```bash
   mkdir -p apps/<app>/public && touch apps/<app>/public/.gitkeep
   ```
   This has caused deploy failures in P10, P12, P13, and P14. Four consecutive occurrences.

These prevent 3-5 post-deploy polish commits that address layout consistency.

### Dependency Pinning (Python Services)

After scaffolding `requirements.txt` with `>=` bounds:
1. Create a virtual environment: `python3 -m venv .venv && . .venv/bin/activate`
2. Install: `pip install -r requirements.txt`
3. Pin: `pip freeze > requirements.txt`
4. Verify the Docker image uses the SAME versions as local dev

Loose bounds (`>=`) cause deploy breaks when Docker installs a newer version with API changes. This caused a 3-commit fix cycle in the {{ORG}}DB MCP sprint when MCP SDK 1.9 to 1.26 broke the `@server.tool()` API.

### Docker CLI Dependency Check (MANDATORY — scripts calling external tools)

When your code invokes external CLI tools (ffmpeg, curl, wget, imagemagick, etc.):
1. **Before committing:** Check the Dockerfile for `apt-get install <tool>` or equivalent
2. If missing, add it: `RUN apt-get update && apt-get install -y <tool> && rm -rf /var/lib/apt/lists/*`
3. **Verify in container:** `docker exec <container> which <tool>` — must return a path, not "not found"

**Why this exists (Transcription Pipeline sprint):** `diarize_lifelogs.py` called ffmpeg for audio preprocessing, but the Dockerfile never installed it. All 5 diarization jobs failed on first deploy. One Dockerfile line would have prevented it.

### MCP Server Docker Pattern

MCP servers using stdio transport CANNOT be long-running Docker daemons — they exit immediately when stdin closes. Use this pattern:

1. **Dockerfile entrypoint:** Run a health/keepalive process (not the MCP server)
2. **MCP invocation:** Claude Code uses `docker exec -i <container> python -m <server>`
3. **Health check:** The keepalive process serves /health on the configured port
4. **mcp.json:** `{"command": "docker", "args": ["exec", "-i", "<container>", "python", "-m", "<module>"]}`

Never use `ENTRYPOINT ["python", "-m", "mcp_server"]` for stdio-based MCP servers in Docker compose — the container will restart-loop.

### Codebase Workers
Add to the template:
```
## Repository
- Local: {repo_path}
- Remote: {remote_url}
- Branch: {branch or "create feature branch from main"}

## Import Path Rule (Docker Context)
When writing Python imports for a Docker service with `PYTHONPATH=/app`:
- Use `from src.module import X` (not `from module import X`)
- The bare module name only works if PYTHONPATH includes the src/ directory
- Before committing, verify: `python -c "from src.<your_module> import <your_export>"` runs without error
```

### Database Workers
Add to the template:
```
## Database
- Container: {container_name}
- Connection: {connection_details}
- Schema: {schema_name}
- IMPORTANT: Run `\d schema.table` before writing ANY queries — never guess column names

## MANDATORY: Schema Inspection Before Code (L7)
Before writing ANY SQL (INSERT, UPDATE, SELECT, CREATE VIEW):
1. Run `\d schema.table_name` for EVERY table you will query
2. Copy the column names exactly — do not paraphrase from plan descriptions
3. If column names in the plan don't match the actual schema, trust the schema and message pm-tracker about the discrepancy

**Why this is mandatory:** Two tables in the same sprint had column name mismatches between plan descriptions and actual DB schema. Both required fix commits. `\d` takes 2 seconds; a fix cycle takes 10 minutes.
```

## User Testing Gates

For tasks that modify live services, add:
```
## USER TESTING GATE
After completing {specific sub-task}, STOP and message pm-tracker:
"USER TEST GATE: {what the user needs to test}"
Do NOT proceed until pm-tracker clears you.
```
