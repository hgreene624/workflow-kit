# Authentication / Authorization Diagnostics

## Auth Architecture

```
Browser → Traefik → ForwardAuth middleware (<YOUR_GATEWAY_APP> gateway) → Downstream container
                                    ↓
                    Microsoft Entra ID (Azure AD) OAuth
```

### Two Entra App Registrations

| App ID | Purpose | Flow |
|--------|---------|------|
| `a79fcf06` | Web sign-in (user-facing) | Authorization code flow |
| `4935ad02` | Graph API (server-to-server) | Client credentials — NO user sign-in |

**Always verify which app ID a service uses.** The Graph API app will never work for user-facing OAuth.

**Cross-ref:** VPS L3

### ForwardAuth Flow

1. Request hits Traefik
2. Traefik calls `<YOUR_DOMAIN>/auth/verify` (ForwardAuth middleware)
3. Gateway checks session cookie → if valid, returns 200 + `X-{{ORG}}-*` headers
4. If invalid → returns 302 redirect to `/auth/signin?returnTo=...`
5. User completes MS login → redirected back with session cookie
6. Downstream containers receive headers: `X-{{ORG}}-User-Id`, `X-{{ORG}}-Email`, `X-{{ORG}}-Name`, `X-{{ORG}}-Role`

### Services with/without auth

| Auth Type | Services |
|-----------|----------|
| ForwardAuth (`flora-auth`) | {{ORG}} Hub, Portal, IK Buckets, Inbox Triage, Email Portal, KB, DocGen, Admin |
| Basic auth | {{SIGNAL_ENGINE}} API (`api.<YOUR_DOMAIN>`), Dossier Builder, Chawdys |
| MS Entra (oauth2-proxy) | Uptime Kuma (`status.<YOUR_DOMAIN>`) |
| No auth | `/ai/widget.js` (public), Plane (`projects.<YOUR_DOMAIN>`) |

## Diagnostic Checklist

### 1. Check if auth is blocking the request

```bash
# -L follows redirects, -v shows redirect chain
ssh <YOUR_VPS> "curl -svL https://<YOUR_DOMAIN>/<path> 2>&1 | grep -E 'HTTP|Location'"
```

If you see `302` → `auth/signin`, auth is blocking.

### 2. Verify ForwardAuth header forwarding

```bash
# Check what headers Traefik is configured to forward
ssh <YOUR_VPS> "docker inspect <YOUR_GATEWAY_APP> --format '{{json .Config.Labels}}' | python3 -m json.tool | grep authresponseheaders"
```

Headers must be listed in `authresponseheaders` or they're silently dropped.

**Cross-ref:** VPS L20 (header name mismatch — singular vs plural)

### 3. Check downstream header limits

```bash
# Gunicorn (Flask apps)
ssh <YOUR_VPS> "docker exec <container> ps aux | grep gunicorn"
# Look for --limit-request-field_size

# Test with verbose curl
ssh <YOUR_VPS> "curl -sv http://<container-ip>:<port>/ 2>&1 | grep -i 'header\|413\|431'"
```

**Cross-ref:** VPS L9 (ForwardAuth adds headers that exceed backend limits)

### 4. Verify redirect URIs are registered

New services require their callback URI added to the Entra app registration (`a79fcf06`) in Azure portal. Can't be automated — Graph API app lacks `Application.ReadWrite.All`.

**Cross-ref:** VPS L6

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| Blank page on protected route | ForwardAuth returns 401 instead of 302 | Change to 302 redirect | VPS L4 |
| Infinite redirect loop | hooks.server.ts and layout.server.ts disagree | Sync auth exclusions | VPS L5 |
| AADSTS50011 error | Wrong Entra app ID | Check working service env vars | VPS L3 |
| "Request Header Too Large" | Backend rejects ForwardAuth headers | Increase header limits | VPS L9 |
| User gets wrong role/permissions | Header name mismatch in Traefik config | Verify `authresponseheaders` | VPS L20 |
| `/ai/widget.js` blocked by auth | Wrong path or Traefik rule | Widget path has NO auth — verify routing | (routing-map.md) |
| Account disabled side effects | Entra disables strip Teams memberships | Audit ALL side effects first | Agent L19 |

## IK Buckets Auth (Separate System)

IK Buckets has its OWN auth layer (MSAL OAuth, NOT ForwardAuth), with an `allowed_users` email whitelist in SQLite:

```bash
ssh <YOUR_VPS> "docker exec ik-buckets sqlite3 /app/db/search.db 'SELECT * FROM allowed_users'"
```

Admin UI at `/admin/users` or seed list in `app.py`.

## OpenClaw/Chawdys Auth

- Basic auth via Traefik (`chawdys.<YOUR_DOMAIN>`)
- Teams Bot endpoint (`bot.<YOUR_DOMAIN>`) — separate auth flow
- Internal service calls use env vars for {{SIGNAL_ENGINE}} API basic auth

## Key Gotchas

- **ForwardAuth must return 302, not 401** — browsers show blank on 401 (VPS L4)
- **Two shell layers corrupt auth tokens:** Cookie strings with special chars break through `ssh + docker exec`. Write scripts locally and scp.
- **Disabling an Entra account strips ALL private Teams channel memberships** — they don't restore on re-enable (Agent L19)
- **oauth2-proxy for Uptime Kuma** is a separate auth proxy, not ForwardAuth

## Lessons Files
- `01_Work/03_Projects/VPS/lessons.md` — L3-L6, L9, L20
- `04_ Tools/Reference/REF - Agent Lessons.md` — L19
