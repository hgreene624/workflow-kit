# Traefik URL Routing Map

Traefik uses **most-specific prefix wins**. `/kb/sales` matches before `/kb/`.

## <YOUR_DOMAIN> Routes

| URL Path | Container | App Type | Port | Compose File | Auth |
|----------|-----------|----------|------|-------------|------|
| `/hub/*` | <APP_1> | SvelteKit | 3000 | /docker/flora/ | flora-auth |
| `/portal/*` | <APP_2> | SvelteKit | 3000 | /docker/flora/ | flora-auth |
| `/kb/sales*` | ik-buckets | Flask/Gunicorn | 8080 | /docker/flora/ | flora-auth |
| `/kb/*` | flora-kb | SvelteKit | 3000 | /root/flora-kb/ | flora-auth |
| `/mail/*` | inbox-triage | Flask/Gunicorn | 8080 | /docker/flora/ | flora-auth |
| `/email/*` | email-portal | Next.js | 3000 | /docker/flora/ | flora-auth |
| `/reservations/*` | reservations-dashboard | Next.js | 3000 | /docker/reservations-dashboard/ | flora-auth |
| `/ai/widget.js` | <YOUR_ADMIN_APP> | Next.js | 3000 | /docker/flora/ | NO AUTH |
| `/api/ai/*` | <YOUR_ADMIN_APP> | Next.js | 3000 | /docker/flora/ | flora-auth |
| `/*` (default) | <YOUR_GATEWAY_APP> | SvelteKit | 3000 | /docker/flora/ | (gateway) |

## Subdomains

| Host | Container | App Type | Port |
|------|-----------|----------|------|
| admin.<YOUR_DOMAIN> | <YOUR_ADMIN_APP> | Next.js | 3000 |
| api.<YOUR_DOMAIN> | fwis-api | FastAPI | 8000 |
| status.<YOUR_DOMAIN> | uptime-kuma | Uptime Kuma | 3001 |
| n8n.<YOUR_DOMAIN> | n8n | n8n | 5678 |
| novnc.<YOUR_DOMAIN> | novnc | noVNC | 6080 |

## Common Gotchas

- `/kb/sales/` → IK Buckets (Flask), NOT Flora KB (SvelteKit). These are DIFFERENT apps.
- `/ai/widget.js` has NO auth — it's served publicly by <YOUR_ADMIN_APP>
- Old subdomains (hub.<YOUR_DOMAIN>, portal.<YOUR_DOMAIN>, etc.) 308-redirect to <YOUR_DOMAIN>/path/

## Quick Lookup Command

```bash
grep -r 'PathPrefix\|rule=' /docker/*/docker-compose.yml /root/*/docker-compose.yml 2>/dev/null | grep -v redirect | grep '<path>'
```

Last updated: 2026-03-14
