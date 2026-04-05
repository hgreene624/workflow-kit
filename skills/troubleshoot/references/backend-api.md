# Backend / API Diagnostics

## APIs in the Stack

| API | Container | Framework | Port | Base URL |
|-----|-----------|-----------|------|----------|
| FWIS API | `fwis-api` | FastAPI | 8000 | `api.<YOUR_DOMAIN>` (basic auth) |
| IK Buckets | `ik-buckets` | Flask/Gunicorn | 8080 | `<YOUR_DOMAIN>/kb/sales/` |
| Inbox Triage | `inbox-triage` | Flask/Gunicorn | 5001 | `<YOUR_DOMAIN>/mail/` |
| MyArroyo Admin | `<YOUR_ADMIN_APP>` | Next.js API routes | 3000 | `admin.<YOUR_DOMAIN>/api/` |
| Flora KB API | `flora-api` | Express | 3001 | Internal only |
| Plane API | `plane-api-1` | Django | 8000 | `projects.<YOUR_DOMAIN>/api/` |

## Diagnostic Checklist

### 1. Check container logs first

```bash
ssh <YOUR_VPS> "docker logs <container> 2>&1 | tail -30"
ssh <YOUR_VPS> "docker logs <container> 2>&1 | grep -i 'error\|traceback\|500' | tail -10"
```

### 2. Test the endpoint directly

```bash
# Through Traefik (with auth headers if needed)
ssh <YOUR_VPS> "curl -sv https://<YOUR_DOMAIN>/<path> 2>&1 | head -30"

# Direct to container (bypass Traefik + auth)
ssh <YOUR_VPS> "curl -s http://<container-ip>:<port>/<path>"

# Get container IP
ssh <YOUR_VPS> "docker inspect <container> --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'"
```

### 3. Verify the exact user flow that's broken

Curling the root page and getting 200 is NOT sufficient. The broken code path may only trigger on specific user actions (selecting a mailbox, opening a thread, etc.).

**Cross-ref:** Agent L17 (test the exact broken flow)

### 4. Check if the API is returning errors vs HTML

APIs behind ForwardAuth may return login page HTML instead of JSON when auth fails:

```bash
ssh <YOUR_VPS> "curl -s https://<YOUR_DOMAIN>/<api-path> | head -5"
# If you see HTML, auth is redirecting
```

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| "d.map is not a function" | API returned error object, not array | Guard with `Array.isArray()` | FWIS L3 |
| Endpoint returns 404 | FastAPI catch-all `{key:path}` swallowed it | Declare specific routes before catch-alls | FWIS L5 |
| "Request Header Too Large" | ForwardAuth headers exceed backend limit | Increase Gunicorn `--limit-request-field_size` | VPS L9 |
| 500 on specific action | Wrong column name in SQL query | Inspect schema, audit all queries | Agent L7, L18 |
| Pipeline uses old prompt | Stale `prompts.json` cache | Regenerate from API | FWIS L6 |
| Data missing after INSERT | INSERT SQL missing column in list | Check all 4 places: signature, columns, VALUES, tuple | FWIS L7 |

## FastAPI-Specific (FWIS API)

- **Catch-all routes:** `{param:path}` greedily matches everything including `/`. Order specific sub-routes BEFORE catch-alls.
- **Pipeline CLI:** `flora_signal.py --mailbox EMAIL [--skip-fetch] [--verbose] [--dry-run] [--start-date YYYY-MM-DD --end-date YYYY-MM-DD] [--limit N]`
- **Run pipeline serially** — concurrent instances not supported
- **Basic auth** on `api.<YOUR_DOMAIN>` — not ForwardAuth
- **DB connection:** psycopg3 ConnectionPool via env vars

## Flask/Gunicorn-Specific

- **Template caching:** Flask caches templates at load. Container restart required after template edits.
- **Header limits:** Default `--limit-request-field_size 8190`. Set to `16384` for ForwardAuth.
- **IK Buckets auth:** MSAL OAuth → `allowed_users` table (email whitelist in SQLite)
- **Inbox Triage:** Flask at port 5001, handles email classification UI

## Next.js API Routes (MyArroyo Admin)

- **AI chat endpoints:** `/api/ai/*` (ForwardAuth protected)
- **Widget:** `/ai/widget.js` (NO auth — served publicly)
- **20+ admin API endpoints** for tools, sessions, profiles
- **SSE streaming** with Max Proxy + Anthropic fallback

## Django (Plane API)

- **ORM access:** `ssh <YOUR_VPS> "docker exec -i plane-api-1 python manage.py shell"`
- **REST API preferred** over Django ORM for status updates (ORM bypasses frontend cache)
- **API token:** `X-Api-Key: <YOUR_PLANE_API_KEY>`
- **Workspace slug:** `<YOUR_PLANE_WORKSPACE>`

## Prompt Library

All LLM prompts live in `public.prompt_templates` (flora_signal DB), managed at `admin.<YOUR_DOMAIN>/prompts`.

```bash
# Check a prompt exists
ssh <YOUR_VPS> "docker exec flora-postgres psql -U flora -d flora_signal -c \"SELECT key, version FROM prompt_templates WHERE key LIKE '%keyword%'\""
```

**Cross-ref:** FWIS L6 (regenerate prompts.json after DB updates)

## Lessons Files
- `01_Work/03_Projects/Flora Work Intelligence System/lessons.md` — L3-L7
- `01_Work/03_Projects/VPS/lessons.md` — L9 (header limits)
- `04_ Tools/Reference/REF - Agent Lessons.md` — L7, L17, L18
