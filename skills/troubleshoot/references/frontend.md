# Frontend / UI Diagnostics

## Frameworks in the Stack

| App | Framework | Base Path | Key Gotchas |
|-----|-----------|-----------|-------------|
| Flora Hub | SvelteKit (Svelte 5) | `/hub` | Hydration timing, `base` config |
| Flora Portal | SvelteKit (Svelte 5) | `/portal` | Same hydration concerns |
| MyArroyo Gateway | SvelteKit | `/` | Auth gateway, ForwardAuth provider |
| Flora KB | SvelteKit | `/kb` | Widget loading needs delayed init |
| MyArroyo Admin | Next.js 16 | `admin.<YOUR_DOMAIN>` | Standalone build, no system tools in container |
| Email Portal | Next.js | `/email` | Panel hydration mismatch, sanitization needed |
| Reservations Dashboard | Next.js + Ant Design | `reservations.<YOUR_DOMAIN>` | ALL pages must be `'use client'` |
| DocGen Frontend | Next.js | `/docgen` | ForwardAuth protected |
| IK Buckets | Flask (Jinja2) | `/kb/sales` | Single HTML template, NO framework |

## Diagnostic Checklist

### 1. Verify you're looking at the right app

**Most critical step.** Different URL paths serve different apps. See `routing-map.md`.

```bash
# Confirm which container serves the URL
ssh <YOUR_VPS> "grep -r 'PathPrefix' /docker/*/docker-compose.yml /root/*/docker-compose.yml 2>/dev/null | grep '<path>'"
```

**Cross-ref:** FWIS L8 (confirm URL before debugging), VPS L21 (identify container first)

### 2. Take a screenshot (MANDATORY for UI issues)

Use Puppeteer on VPS:
```bash
# Puppeteer is installed at /root/.cache/puppeteer/
ssh <YOUR_VPS> "node -e \"
const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({headless: true, args: ['--no-sandbox']});
  const page = await browser.newPage();
  await page.setViewport({width: 1280, height: 800});
  await page.goto('http://<container-ip>:<port>/<path>', {waitUntil: 'networkidle0'});
  await page.screenshot({path: '/tmp/debug.png', fullPage: true});
  await browser.close();
})();
\""
scp vps:/tmp/debug.png /tmp/debug.png
open /tmp/debug.png
```

**For auth-protected pages:** Use request interception to bypass ForwardAuth or serve needed resources.

**Cross-ref:** Agent L21 (verify visually), FWIS L9 (browser-level verification)

### 3. Verify the build contains your changes

```bash
# Check if the compiled output has your code
ssh <YOUR_VPS> "docker exec <container> grep -r '<unique-string>' /app/build/ /app/.next/ 2>/dev/null"

# Check when the container was last built
ssh <YOUR_VPS> "docker inspect <container> --format '{{.Created}}'"
```

### 4. Check for hydration mismatches (SSR frameworks)

SSR HTML can be correct while client hydration renders something different.

```bash
# Compare SSR output vs client render
ssh <YOUR_VPS> "docker exec <container> curl -s http://localhost:3000/<path> | grep '<target-element>'"
```

Then take a screenshot to see the client-rendered result. If they differ, it's a hydration issue.

**Cross-ref:** Frontend L4 (verify hydration, not just SSR)

### 5. Check CSS containment chain

Before adding `overflow`, `scroll`, or rendering HTML content, trace the full chain from root layout to insertion point. Nested scroll containers fight each other.

**Cross-ref:** Frontend L5 (containment chain)

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| Widget/script not appearing | Wrong app being modified | Check routing-map.md | FWIS L8 |
| Script loads in dev but not prod | Hydration strips DOM changes | Use `onMount` or delayed `window.load` | FWIS L10 |
| SSR looks right, browser looks wrong | Hydration mismatch | Screenshot the actual page | Frontend L4 |
| Styles break in opposite theme | Hardcoded dark/light colors | Use DaisyUI semantic tokens | Frontend L3 |
| Component class doesn't work | DaisyUI 5 naming change | Read the library CSS source | Frontend L1, L2 |
| Email HTML leaks global styles | `<style>` tags in dangerouslySetInnerHTML | Sanitize/scope all injected HTML | Frontend L5 |
| Panels reset to equal width | Client hydration overrides SSR layout | Verify final rendered state | Frontend L4 |
| Ant Design server component crash | Next.js standalone SSR + antd | ALL pages must be `'use client'` | (Reservations Dashboard rule) |

## SvelteKit-Specific

- **Base path:** Each SvelteKit app has a `base` in `svelte.config.js` (e.g., `/hub`, `/kb`, `/portal`). Links and assets resolve relative to this.
- **Svelte 5 hydration:** Scripts in `app.html` run before hydration. DOM elements created pre-hydration may be reconciled away. Use `onMount` in `+layout.svelte` for dynamic script loading.
- **`app.html` widget pattern:** `window.addEventListener("load")` + `setTimeout(2000)` as a fallback for scripts that must run after hydration.

## Next.js-Specific

- **Standalone containers:** No `curl`, `wget`, or bash utils. Test from VPS host.
- **`useSearchParams`:** Must wrap in `<Suspense>` or build fails.
- **Reservations Dashboard:** Uses Ant Design 6 — always override Layout colors for dark theme.

## Flask/Jinja2-Specific (IK Buckets)

- **Single template file:** `templates/app.html` (~160KB, all-in-one)
- **Template caching:** Flask caches templates — restart container after editing
- **No framework hydration:** Scripts in `<body>` run directly, no timing issues

## Widget Loading (Flora AI Chat)

The `<flora-chat>` web component loads from `/ai/widget.js` (served by <YOUR_ADMIN_APP>, NO auth). To embed in any app:

```html
<script>
window.__floraChat_skipAutoInit = true;
var s = document.createElement("script");
s.src = "/ai/widget.js";
s.onload = function() {
    var chat = document.createElement("flora-chat");
    chat.setAttribute("data-app", "<instance-id>");
    document.body.appendChild(chat);
};
document.head.appendChild(s);
</script>
```

## Playwright QA Suite

A validated test suite at `~/Repos/flora-monorepo/tests/qa/` can quickly isolate frontend issues. All commands run from the monorepo root.

```bash
# Quick health check — are all 7 services loading?
npx playwright test --config tests/qa/playwright.config.ts --project=smoke

# Visual regression — has the UI changed unexpectedly?
npx playwright test tests/qa/visual-regression.spec.ts --config tests/qa/playwright.config.ts

# Navigation crawl — any dead links or broken routes?
npx playwright test tests/qa/navigation.spec.ts --config tests/qa/playwright.config.ts
```

**When to use during troubleshooting:**
- Run **smoke** first to isolate which service is down
- Run **navigation** to check if specific routes return 404/500
- Run **visual regression** if a UI change caused unintended side effects elsewhere

**Prerequisites:** Auth state must be valid (`tests/qa/.auth-state.json`). If expired, run `./scripts/qa-auth-setup.sh`. Tests hit live VPS services.

**Key detail:** Use `--project=smoke` (not `--grep @smoke`). Dead link reports output to `tests/qa/reports/dead-links/`.

## Lessons Files
- `04_ Tools/Reference/REF - Frontend Lessons.md` — L1-L5
- `01_Work/03_Projects/Flora Work Intelligence System/lessons.md` — L8-L11
- `01_Work/03_Projects/VPS/lessons.md` — L2, L15, L19
