# Frontend / UI Diagnostics

## Frameworks in the Stack

| App | Framework | Base Path | Key Gotchas |
|-----|-----------|-----------|-------------|
| {{ORG}} Hub | SvelteKit (Svelte 5) | `/hub` | Hydration timing, `base` config |
| {{ORG}} Portal | SvelteKit (Svelte 5) | `/portal` | Same hydration concerns |
| MyArroyo Gateway | SvelteKit | `/` | Auth gateway, ForwardAuth provider |
| {{ORG}} KB | SvelteKit | `/kb` | Widget loading needs delayed init |
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

### 2b. Authenticated Browser Simulation (MANDATORY for ForwardAuth-protected apps)

**The container-direct screenshot (step 2) bypasses auth entirely. It proves the app renders but NOT that the user can access it.** You MUST also test through the real Traefik + ForwardAuth path.

**Method: Playwright with session cookie through the real URL**

```bash
# 1. Get a valid session from the DB
SESSION=$(ssh vps "docker exec {{DB_CONTAINER}} psql -U {{DB_USER}} -d {{PROJECT_DB}} -t -c \"SELECT id FROM auth.sessions WHERE user_id = (SELECT id FROM auth.users WHERE email = 'user@YOUR_DOMAIN') AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1;\"" | tr -d ' \n')

# 2. Write a Playwright script that uses the session cookie
ssh vps "cat > /tmp/auth-screenshot.mjs << 'SCRIPT'
import { chromium } from '/docker/{{MONOREPO_NAME}}/node_modules/playwright/index.mjs';
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  extraHTTPHeaders: { 'Cookie': '{{SESSION_COOKIE}}=SESSION_PLACEHOLDER' }
});
const page = await context.newPage();

// Collect console errors and network failures
const errors = [];
page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
page.on('requestfailed', req => errors.push('NETWORK FAIL: ' + req.url() + ' ' + req.failure().errorText));

// Track 403s and 302s on sub-resources
const blocked = [];
page.on('response', res => {
  if (res.status() === 403) blocked.push('403: ' + res.url());
  if (res.status() === 302 && !res.url().includes('/auth/')) blocked.push('302: ' + res.url());
});

await page.goto('https://YOUR_DOMAIN/PATH_PLACEHOLDER', { waitUntil: 'networkidle', timeout: 30000 });
await page.waitForTimeout(3000);
await page.screenshot({ path: '/tmp/auth-debug.png' });

console.log('=== BLOCKED RESOURCES ===');
blocked.forEach(b => console.log(b));
console.log('=== CONSOLE ERRORS ===');
errors.forEach(e => console.log(e));
console.log('=== SCREENSHOT SAVED ===');
await browser.close();
SCRIPT
"

# 3. Replace placeholders and run
ssh vps "sed -i 's/SESSION_PLACEHOLDER/${SESSION}/' /tmp/auth-screenshot.mjs && sed -i 's|PATH_PLACEHOLDER|<path>|' /tmp/auth-screenshot.mjs && cd /docker/{{MONOREPO_NAME}} && node /tmp/auth-screenshot.mjs 2>&1"

# 4. Download and show the user
scp vps:/tmp/auth-debug.png /tmp/auth-debug.png && open /tmp/auth-debug.png
```

**What this catches that container-direct misses:**
- 403 from missing permissions (white screen)
- 302 on static assets from ForwardAuth blocking CSS/JS (white screen)
- 404 on fetch() calls missing basePath prefix (page loads, no data)
- CORS or cookie issues through Traefik

**If Playwright ESM import fails** (no node_modules context), use the CLI:
```bash
ssh vps "cd /docker/{{MONOREPO_NAME}} && npx playwright screenshot --browser chromium --wait-for-timeout 5000 'http://CONTAINER_IP:3000/<path>' /tmp/debug.png"
```
Note: this bypasses auth. Only use as fallback when the authenticated method fails.

**Rule: Never declare a fix verified unless you've tested through Traefik with auth.** Container-direct tests are useful for isolating whether the issue is in the app vs the routing/auth layer, but they are NOT proof the user can see it.

**Cross-ref:** Agent L21 (verify visually), FWIS L9 (browser-level verification), {{ORG_LOWER}}-app debug-checklist.md

### 2c. Capture Client-Side JS Errors (MANDATORY for "Application error" screens)

**Server-side tests (wget, curl, docker exec) cannot detect client-side JS crashes.** A Next.js page can return HTTP 200 with valid HTML while the client-side React app crashes during hydration, showing a black "Application error" screen. The ONLY way to detect this is with a real browser.

**Use Playwright with `pageerror` event capture:**

```bash
SESSION=$(ssh vps "docker exec -i {{DB_CONTAINER}} psql -U {{DB_USER}} -d {{PROJECT_DB}} -t -A -c \"SELECT id FROM auth.sessions WHERE expires_at > NOW() AND deleted_at IS NULL ORDER BY last_active_at DESC LIMIT 1;\"")

ssh vps "cd /tmp && node -e \"
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--ignore-certificate-errors'] });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addCookies([{ name: '{{SESSION_COOKIE}}', value: '${SESSION}', domain: '.YOUR_DOMAIN', path: '/' }]);
  const pg = await ctx.newPage();
  const errors = [];
  pg.on('pageerror', (err) => errors.push(err.message.slice(0, 500)));

  await pg.goto('https://YOUR_DOMAIN/fwis/<path>', { waitUntil: 'networkidle', timeout: 25000 });
  await pg.waitForTimeout(3000);
  await pg.screenshot({ path: '/tmp/debug.png', fullPage: false });
  const hasAppError = await pg.locator('text=Application error').count();
  console.log(hasAppError > 0 ? 'APP_ERROR' : 'OK');
  if (errors.length > 0) errors.forEach(e => console.log('JS ERROR: ' + e));
  await browser.close();
})();
\""
```

**Why this works when other tests don't:**
- `pageerror` captures the EXACT JS exception message the browser throws
- This caught "AG Charts - No modules have been registered" and "Unknown chart type" -- errors invisible to any server-side test
- The screenshot proves what the user actually sees (not what the server renders)

**Critical: verify the cookie name from source FIRST.** Read the app's cookie utility to get the exact name. Using the wrong name makes all pages show the login screen with HTTP 200, and text checks report "OK" because the login page doesn't contain "Application error". (See L45.)

**Cookie name lookup:**
```bash
ssh vps "grep 'COOKIE_NAME' /docker/{{MONOREPO_NAME}}/apps/home/src/lib/server/cookie.ts"
# Returns: const COOKIE_NAME = '{{SESSION_COOKIE}}';
```

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
| Black "Application error" screen | Client-side JS crash during hydration | Capture `pageerror` event via Playwright | L44, L45 |
| All pages show 200 but user sees error | Server renders HTML fine, client JS crashes | Server-side tests (wget/curl) cannot catch client-side errors | L44 |
| AG Charts "No modules registered" | Missing `AgChartsEnterpriseModule.setup()` | Call setup() synchronously at module scope | L44 |
| Playwright tests all pass but user sees errors | Wrong auth cookie name | Read cookie.ts source, verify with screenshot | L45 |

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

## Widget Loading ({{ORG}} AI Chat)

The `<{{ORG_LOWER}}-chat>` web component loads from `/ai/widget.js` (served by <YOUR_ADMIN_APP>, NO auth). To embed in any app:

```html
<script>
window.__{{ORG_LOWER}}Chat_skipAutoInit = true;
var s = document.createElement("script");
s.src = "/ai/widget.js";
s.onload = function() {
    var chat = document.createElement("{{ORG_LOWER}}-chat");
    chat.setAttribute("data-app", "<instance-id>");
    document.body.appendChild(chat);
};
document.head.appendChild(s);
</script>
```

## Playwright QA Suite

A validated test suite at `~/Repos/{{MONOREPO_NAME}}/tests/qa/` can quickly isolate frontend issues. All commands run from the monorepo root.

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
- `01_Work/03_Projects/{{ORG}} Work Intelligence System/lessons.md` — L8-L11
- `01_Work/03_Projects/VPS/lessons.md` — L2, L15, L19
