# Zero-Downtime Deploy Protocol (No Round-Robin)

**CRITICAL: Never run two containers with the same Traefik PathPrefix simultaneously.** This causes Traefik to round-robin between old and new containers, giving users inconsistent responses.

## Correct Deploy Sequence

1. Deploy new container **without Traefik labels** (use `traefik.enable=false` in VPS override)
2. Verify via SSH tunnel or direct container IP
3. Run crawl-based QA audit against the container via tunnel
4. **Atomically swap:** stop old container + enable Traefik labels on new container in ONE `docker compose up -d` call
5. Verify via public URL

## Why This Exists

Sprint 6: Both old `<APP_2>` and new `portal` ran simultaneously with `PathPrefix(/portal)`. User's test gate saw the old (crashing) app on first load, new app on refresh. Round-robin made the deploy appear broken when it wasn't.
