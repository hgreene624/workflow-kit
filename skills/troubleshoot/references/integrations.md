# Third-Party Integrations Diagnostics

## Integrations in the Stack

| Integration | Used By | Protocol | Key Details |
|-------------|---------|----------|-------------|
| Microsoft Graph API | {{SIGNAL_ENGINE}}, Inbox Triage, Chawdys | REST + OAuth | App ID `4935ad02` (client_credentials) |
| Microsoft Entra ID | All ForwardAuth services | OAuth 2.0 | App ID `a79fcf06` (authorization code) |
| Telegram Bot | Chawdys, cron alerts | Bot API | `TELEGRAM_TARGET` in config.py |
| 7rooms | Reservation Scraper | Playwright scrape | **Currently broken** (auth failing since 2026-03-04) |
| OpenTable | Reservation Scraper | Playwright scrape | Part of reservation-scraper container |
| Anthropic API | MyArroyo Admin, pipeline | REST | SSE streaming, Max Proxy fallback |
| Limitless API | Limitless Sync | REST | Lifelog ingestion every 30 min |
| SharePoint | VPS backup | Graph API | Offsite backup at 3:30 AM |

## Diagnostic Checklist

### 1. Microsoft Graph API issues

```bash
# Test Graph API connectivity
ssh <YOUR_VPS> "docker exec {{API_CONTAINER}} python3 -c 'from graph_client import get_access_token; print(get_access_token())'"

# Check token expiry
ssh <YOUR_VPS> "docker exec {{API_CONTAINER}} python3 -c '
from graph_client import get_access_token
import json, base64
token = get_access_token()
payload = json.loads(base64.b64decode(token.split(\".\")[1] + \"==\"))
print(\"Expires:\", payload.get(\"exp\"))
'"
```

**App ID `4935ad02`** = client_credentials (Graph API, server-to-server)
**App ID `a79fcf06`** = authorization code (user sign-in)

Never use the Graph API app for user-facing OAuth, or vice versa.

### 2. Telegram notifications

```bash
# Test Telegram delivery
ssh <YOUR_VPS> "docker exec {{API_CONTAINER}} python3 -c '
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_TARGET
import requests
r = requests.post(f\"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage\",
    json={\"chat_id\": TELEGRAM_TARGET, \"text\": \"Test from diagnostics\"})
print(r.status_code, r.json().get(\"ok\"))
'"
```

**Disable during bulk operations:** Set `TELEGRAM_TARGET=""` in config.py to avoid spam.

**Cross-ref:** {{SIGNAL_ENGINE}} L2

### 3. Reservation Scraper (currently broken)

```bash
# Check scraper status
ssh <YOUR_VPS> "docker logs reservation-scraper 2>&1 | tail -20"

# Known issue: 7rooms login auth failing since 2026-03-04
# Container is in restart loop
ssh <YOUR_VPS> "docker ps --filter name=reservation-scraper --format '{{.Status}}'"
```

### 4. Limitless Sync

```bash
# Check recent sync
ssh <YOUR_VPS> "docker exec {{DB_CONTAINER}} psql -U flora -d {{PROJECT_DB}} -c \"SELECT id, created_at FROM limitless_lifelogs ORDER BY created_at DESC LIMIT 5\""

# Check sync logs
ssh <YOUR_VPS> "cat /var/log/limitless-sync.log | tail -20"
```

Runs every 30 min (7 AM–9 PM Mazatlán). Pipeline: `sync_lifelogs.py` → `consolidate_lifelogs.py` → `generate_meeting_notes.py`.

### 5. Anthropic API / AI Chat

```bash
# Check AI chat connectivity
ssh <YOUR_VPS> "curl -s http://$(docker inspect <YOUR_ADMIN_APP> --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' | head -c 15):3000/api/ai/health"

# Check session count
ssh <YOUR_VPS> "docker exec {{DB_CONTAINER}} psql -U flora -d {{PROJECT_DB}} -c \"SELECT COUNT(*) FROM chat_sessions\""
```

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| Graph API 401 | Token expired or wrong app ID | Refresh token, verify app ID | VPS L3 |
| Graph API 401 on SharePoint REST | Graph token != SharePoint token | Add SharePoint API permissions to app registration | 2026-03-27 |
| Telegram flood | Bulk operation without disabling target | Set `TELEGRAM_TARGET=""` | {{SIGNAL_ENGINE}} L2 |
| Scraper in restart loop | 7rooms auth changed | Check login flow, update selectors | — |
| Meeting sync empty | Graph API permissions changed | Check app permissions in Azure | — |
| Email misattribution | Wrong email from name guess | Query `monitored_mailboxes` to verify | {{SIGNAL_ENGINE}} L1 |
| Entra account side effects | Disabling strips Teams memberships | Audit ALL side effects before admin ops | Agent L19 |
| API returns 0 results but data exists | **Identity mismatch** — wrong ID format, wrong user context, or stale ID | See checklist below | 2026-03-27 |
| API returns 404 for known resource | Meeting/call ID in DB doesn't match Graph's expected ID | Resolve via `joinWebUrl` instead of stored ID | 2026-03-27 |

### Identity Mismatch Diagnostic Checklist

This failure mode cost hours on 2026-03-27 when Graph returned 0 transcripts for meetings that definitely had transcripts visible in the UI. The root cause: the meeting IDs stored in the database were from calendar events, not from the `onlineMeetings` API — they looked valid but didn't match what Graph expected.

**When an API returns empty/404 for something you know exists:**

1. **Find a known-good.** Pick ONE resource you can verify exists (e.g., a meeting with a confirmed transcript). Query it with your exact pattern. If it also fails, the problem is your query — not the data.

2. **Compare IDs.** Print the ID you're using alongside what the API returns for the same resource resolved a different way. On 2026-03-27: DB stored `MSpmODQw...ZGRjTlRJ...` but Graph returned `MSpmODQw...Namd6WXpG...` for the same meeting — similar prefix, completely different suffix.

3. **Try a different resolution path.** If direct ID lookup fails, try resolving via an indirect key:
   - `joinWebUrl` filter on `/onlineMeetings`
   - `externalId` from driveItem `source` field
   - Chat message `eventDetail.callId` → call record → `joinWebUrl`

4. **Check user context.** The same resource accessed via `/users/A/onlineMeetings/{id}` vs `/users/B/onlineMeetings/{id}` returns different results. The user must match who organized/created the resource.

5. **Check API version.** Some fields only exist in `/beta` (e.g., driveItem `source` field). Try both `v1.0` and `beta`.

6. **Check token audience.** Graph tokens (`https://graph.microsoft.com`) cannot access SharePoint REST endpoints (`/_api/`). They are separate permission systems even though both use Azure AD.

## Chawdys (OpenClaw)

- **Container:** `chawdys` in `/docker/openclaw/docker-compose.yml`
- **Image:** Pre-built `ghcr.io/hostinger/hvps-openclaw`
- **Volumes:** Mount from `/docker/flora/data/` (`.openclaw`, `.bun`, `.npm`, etc.)
- **Network:** `root_default` (reaches app services via Traefik)
- **Env vars:** `{{SIGNAL_ENGINE}}_API_URL`, `INBOX_TRIAGE_URL`, `IK_BUCKETS_URL`
- **Internal crons:** Managed via `openclaw cron list/enable/disable` inside container
- **MS Graph tools:** `/data/.openclaw/workspace/projects/ms-teams-planner/`

```bash
# Check Chawdys health
ssh <YOUR_VPS> "docker exec chawdys openclaw health"

# List internal crons
ssh <YOUR_VPS> "docker exec chawdys openclaw cron list"
```

## Email Safety

**ALWAYS verify emails against `monitored_mailboxes` table** before use:
- `admin@YOUR_DOMAIN` = Patrick (owner/executive)
- `consultant@YOUR_DOMAIN` = Pablo de la Garza (Odoo consultant, NOT Patrick)

```bash
ssh <YOUR_VPS> "docker exec {{DB_CONTAINER}} psql -U flora -d {{PROJECT_DB}} -c 'SELECT email, display_name FROM monitored_mailboxes'"
```

**Cross-ref:** {{SIGNAL_ENGINE}} L1

## Lessons Files
- `{{PROJECT_PATH}}/{{INTELLIGENCE_PROJECT}}/lessons.md` — L1 (email verification), L2 (Telegram)
- `01_Work/03_Projects/VPS/lessons.md` — L3 (Entra app IDs)
- `04_ Tools/Reference/REF - Agent Lessons.md` — L19 (admin operation side effects)
