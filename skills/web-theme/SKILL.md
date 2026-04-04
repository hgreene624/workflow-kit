---
name: web-theme
description: >-
  Scrape website styles into reusable themes, preview themes on the Flora site via Playwright
  screenshots, and manage the theme registry. Use this skill whenever the user mentions scraping
  styles from a website, capturing a site's aesthetic, theme preview, mockups, "what themes do we
  have", switching themes, "apply this theme", "scrape the theme from [url]", "show me the
  [name] theme", "preview [name]", or any request about Flora site theming. Also trigger on
  /web-theme, "new theme from [url]", "capture the look of [site]", "style guide from [url]",
  "theme list", or when the user pastes a URL and wants to extract its visual design for Flora.
  Even casual requests like "make our site look like [url]" or "I like how [site] looks" should
  trigger this skill.
---

# Web Theme — Scrape, Preview & Manage Flora Site Themes

This skill manages a theme system for the Flora monorepo. Themes are scraped from real websites using Playwright, stored as DaisyUI v5 theme definitions with custom design tokens, and previewed by injecting CSS into the running Flora app and taking screenshots — all without modifying production code.

## Key Paths

| Path | Purpose |
|------|---------|
| `~/Repos/{{MONOREPO_NAME}}` | Flora monorepo root |
| `packages/ui/src/themes/` | Theme files (CSS, meta, types, registry) |
| `packages/ui/src/themes/previews/` | Generated preview screenshots |
| `packages/ui/src/themes/types.ts` | ThemeMeta TypeScript interface |
| `packages/ui/src/themes/index.ts` | Theme registry — all themes registered here |
| `scripts/scrape-theme.mjs` | Playwright scraper — extracts computed styles from any URL |
| `scripts/preview-theme.mjs` | Playwright previewer — injects theme CSS and screenshots the Flora site |
| `tests/qa/.auth-state.json` | Saved Entra auth cookies — required for previewing authenticated pages |
| `scripts/qa-auth-setup.sh` | Re-generates auth state (opens browser for Microsoft login) |

All paths below are relative to the monorepo root unless stated otherwise.

## Three Modes

Determine which mode the user needs based on their request:

### 1. Scrape — Extract styles from a website

Trigger: URL + intent to capture styles ("scrape from", "capture the look of", "new theme from", "style guide from")

**Steps:**

1. **Run the scraper** — Execute the Playwright script against the target URL:
   ```bash
   cd "~/Repos/{{MONOREPO_NAME}}"
   node scripts/scrape-theme.mjs <url> <theme-name>
   ```
   This produces `packages/ui/src/themes/<name>-scraped.json` with computed styles (colors, fonts, spacing, layout) and `<name>-reference.png` (full-page screenshot).

2. **Show the reference screenshot** to the user so they can see what was captured.

3. **Read the scraped JSON** and analyze it to build the theme files. The JSON contains:
   - `root` — body background, text color, font-family, font-size, line-height
   - `headings` — h1-h6 font details (family, size, weight, line-height, color)
   - `paragraph` — body text styling
   - `nav` — navigation bar styles
   - `cards` — card component styles (border-radius, shadow, border, background)
   - `sections` — section padding, backgrounds, borders
   - `colorPalette` — all unique background-color, color, border-color values on the page
   - `loadedFonts` — font families loaded by the page
   - `images` — image styling (object-fit, border-radius, aspect-ratio)

4. **Map scraped values to DaisyUI tokens.** This is the creative step — use judgment to assign scraped colors to the right semantic roles:
   - The most common background color → `base-100`
   - Slightly darker/lighter variant → `base-200`
   - Border colors → `base-300`
   - Primary text color → `base-content`
   - The dominant UI/brand color → `primary`
   - Secondary muted text → `secondary`
   - Any accent/highlight color → `accent`
   - Dark footer/nav background → `neutral`
   - Light text on dark surfaces → `neutral-content`

5. **Find closest free Google Fonts** for any custom/proprietary fonts. Common mappings:
   - Geometric sans (StyreneA, Gilroy, Avenir) → Inter, Space Grotesk, or DM Sans
   - Editorial serif (TiemposText, Tiempos, Noe) → Lora, Source Serif, or Merriweather
   - Neo-grotesque (Aktiv Grotesk, Neue Haas) → Inter or Plus Jakarta Sans
   - Monospace → JetBrains Mono (usually fine as-is)

6. **Create the CSS file** — `packages/ui/src/themes/<name>.css`:
   - Two `@plugin "daisyui/theme"` blocks (light + dark variants)
   - A shared `[data-theme]` block with custom design tokens (`--theme-*` variables)
   - Variant-specific blocks for divider colors and muted text shades
   - Read `references/theme-css-template.md` for the exact format

7. **Create the meta file** — `packages/ui/src/themes/<name>.meta.ts`:
   - Import and implement the `ThemeMeta` type from `./types`
   - Include fonts, palette, design tokens, sourceUrl, scrapedAt date
   - Read `references/theme-meta-template.md` for the exact format

8. **Register in index.ts** — Add the import and entry to the `themes` map in `packages/ui/src/themes/index.ts`

9. **Offer to preview** — Ask if the user wants to see it applied to the Flora site.

### 2. Preview — Mockup a theme on the Flora site

Trigger: "preview", "show me", "mockup", "how does [name] look"

**Steps:**

1. **Determine the target app.** Default is `portal` (the richest UI). The user may specify "home", "portal", or "admin".

2. **Determine variant** — Default is light. If user says "dark" or "--dark", use dark.

3. **Always use `--external` mode with auth.** This hits the live VPS site (`YOUR_DOMAIN`) with the saved auth state, so pages render with real data. The auth state file lives at `tests/qa/.auth-state.json` — check it exists before running.

   ```bash
   # Verify auth state exists
   ls -la "~/Repos/{{MONOREPO_NAME}}/tests/qa/.auth-state.json"
   ```

   If the file is missing or older than ~24 hours, tell the user to re-run auth setup:
   ```bash
   cd "~/Repos/{{MONOREPO_NAME}}" && ./scripts/qa-auth-setup.sh
   ```

4. **Run the preview script with `--external`:**
   ```bash
   cd "~/Repos/{{MONOREPO_NAME}}"
   node scripts/preview-theme.mjs <theme-id> --external --app=<app> [--dark]
   ```

   The script supports these flags:
   - `--external` — Use live VPS URLs (`YOUR_DOMAIN`) with auth state injection
   - `--app=portal|home|admin` — Target app (determines routes + port)
   - `--dark` — Use dark variant
   - `--port=PORT` — Override port (only for local dev, not external)
   - `--routes=/path1,/path2` — Custom routes to screenshot

   Default routes per app when using `--external`:
   - **portal**: `/portal/`, `/portal/meetings`, `/portal/timeline`, `/portal/actions`
   - **home**: `/`
   - **admin**: `/admin/`

5. **Show the desktop screenshot** inline by reading the file:
   `packages/ui/src/themes/previews/<theme-id>-<variant>[-<app>]/dashboard-desktop.png` (portal)
   or `home-desktop.png` (home)

6. **Open the HTML index** for the user to browse all viewports:
   ```bash
   open "<previews-dir>/index.html"
   ```

7. **Mention** that tablet and mobile screenshots are also available in the same directory.

### 3. List — Show available themes

Trigger: "list themes", "what themes", "available themes", "which themes"

**Steps:**

1. Read `packages/ui/src/themes/index.ts` to get the registered theme IDs.
2. For each theme, read its `.meta.ts` to extract label, description, defaultVariant, and sourceUrl.
3. Present as a clean table.

## Theme File Anatomy

Each theme consists of three things:

### CSS (`<name>.css`)
```css
/* Light variant */
@plugin "daisyui/theme" {
  name: "<name>-light";
  color-scheme: light;
  --color-base-100: #FAF9F5;
  /* ... all DaisyUI color tokens ... */
}

/* Dark variant */
@plugin "daisyui/theme" {
  name: "<name>-dark";
  color-scheme: dark;
  --color-base-100: #141413;
  /* ... */
}

/* Custom design tokens (both variants) */
[data-theme="<name>-light"],
[data-theme="<name>-dark"] {
  --theme-font-heading: 'Inter', sans-serif;
  --theme-font-body: 'Lora', serif;
  --theme-radius: 0;
  --theme-card-shadow: none;
  /* ... see references/theme-css-template.md for full list */
}
```

### Meta (`<name>.meta.ts`)
```ts
import type { ThemeMeta } from './types';
export const <name>Theme: ThemeMeta = {
  id: '<name>',
  label: 'Human-Readable Name',
  description: 'Short aesthetic description',
  sourceUrl: 'https://...',
  variants: { light: '<name>-light', dark: '<name>-dark' },
  defaultVariant: '<name>-light',
  fonts: { heading: {...}, body: {...} },
  designTokens: { radius: '0', cardStyle: '...' },
  palette: { light: {...}, dark: {...} },
};
```

### Registry entry (`index.ts`)
```ts
import { <name>Theme } from './<name>.meta';
// Add to the themes map:
export const themes = { ..., <name>: <name>Theme };
```

## Important Notes

- The preview system works by injecting CSS overrides at runtime — it does NOT modify any source files. This means previews are safe and non-destructive.
- The scraper extracts computed styles from a real browser via Playwright's `page.evaluate()`, so it captures the actual rendered values, not just what's in the stylesheet.
- When creating dark variants from a light-only source site (or vice versa), invert the color relationships — lightest background becomes darkest, etc.
- The Flora monorepo uses Tailwind v4 + DaisyUI v5 with `data-theme` attribute switching.
- Custom `--theme-*` tokens extend beyond DaisyUI — they control typography, spacing, shape, and layout. The preview script injects these as `!important` overrides.
