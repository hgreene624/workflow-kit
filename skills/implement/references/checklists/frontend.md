# Frontend Checklist

Inject into worker prompt when task touches Next.js UI, AG Grid, or basePath apps.

## Next.js basePath Rules

Apps with `basePath` configured (e.g., `/owners`, `/fwis`, `/kb`):

| API | basePath behavior |
|-----|-------------------|
| `<Link href="...">` | Auto-prepends. Do NOT include basePath. |
| `router.push("...")` | Auto-prepends. Do NOT include basePath. |
| `fetch("...")` | Does NOT prepend. You MUST include basePath. |
| `<a href="...">` | Does NOT prepend. You MUST include basePath. |
| `NextResponse.rewrite(url)` | Does NOT prepend. You MUST include basePath. |

Double-prefix (`/owners/owners/...`) = you included basePath where Next.js auto-prepends.
Missing prefix (404) = you forgot basePath where `fetch` or `<a>` needs it.

Test ALL of these after deploying. Check Network tab for 404s.

## AG Grid

1. Use `modules` prop on `<AgGridReact>`, NOT `ModuleRegistry.registerModules()`. Include `ClientSideRowModelModule`.
2. Version pin `ag-grid-community` to `^32.3.0`. Mismatch with `ag-grid-react` = silent 0-row grids.
3. Cell renderers: React JSX components, NEVER HTML strings.
4. Date serialization: convert PostgreSQL Date objects to ISO strings in query layer (not JSON-serializable in RSC).
5. Enterprise modules: import only in browser context (`if (typeof window !== 'undefined')`).

## Rendering Verification

After deploying, test with REAL data (not just health checks):

1. Pick 3 representative content items from DB
2. Verify tables render as tables (not pipe chars), headings sized correctly, lists indented
3. Check browser Network tab — all fetches returning 200?
4. Check browser console — JS errors?
5. Run Playwright QA screenshots if available: `./scripts/qa-screenshots.sh <service>`

"It compiled" and "health check passes" are NOT verification. Content must be visually correct.

## Scaffold Checklist (new apps/pages)

1. Content container with max-width (list: max-w-5xl, detail: max-w-4xl)
2. Viewport fill: `h-screen flex flex-col` with `flex-1 overflow-auto` on main content
3. `public/` directory with `.gitkeep` — Dockerfile expects `COPY public/ ./public/`. Missing = build failure. Has caused 4 consecutive deploy failures.

## API Response Safety

```tsx
// Always use defensive access on API responses:
const items = response?.items ?? [];
const total = response?.total ?? 0;
```

Especially for {{SIGNAL_ENGINE}} endpoints (may be stubs), `Promise.allSettled` results, and endpoints with different shapes for empty vs populated responses.
