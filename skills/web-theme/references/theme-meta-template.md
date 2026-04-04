# Theme Meta Template

Use this structure for the `.meta.ts` file. The `ThemeMeta` interface is defined in `packages/ui/src/themes/types.ts`.

```typescript
import type { ThemeMeta } from './types';

/**
 * <Theme Label> theme — scraped from <source-url>.
 *
 * <1-2 sentence aesthetic description.>
 */
export const <id>Theme: ThemeMeta = {
  id: '<id>',
  label: '<Human-Readable Label>',
  description: '<Short aesthetic summary, e.g., "Editorial minimal — warm neutrals, serif body, sharp corners">',
  sourceUrl: '<url-scraped-from>',
  scrapedAt: '<YYYY-MM-DD>',

  variants: {
    light: '<id>-light',
    dark: '<id>-dark',
  },
  defaultVariant: '<id>-light',  // Use whichever matches the source site

  fonts: {
    heading: {
      family: '<Google Font name>',
      googleFonts: '<Google Fonts parameter, e.g., "Inter:wght@400;500;600;700">',
      fallback: '<fallback stack, e.g., "ui-sans-serif, system-ui, sans-serif">',
      note: '<What proprietary font this approximates>',
    },
    body: {
      family: '<Google Font name>',
      googleFonts: '<Google Fonts parameter>',
      fallback: '<fallback stack>',
      note: '<What proprietary font this approximates>',
    },
    mono: {
      family: '<Mono font>',
      googleFonts: '<Google Fonts parameter>',
      fallback: 'ui-monospace, monospace',
    },
  },

  designTokens: {
    radius: '<e.g., "0" or "0.75rem">',
    cardStyle: '<e.g., "borderless, transparent bg, no shadow">',
    sectionDivider: '<e.g., "top-border with muted gray">',
    heroImageRatio: '<e.g., "16:9">',
    thumbnailRatio: '<e.g., "1:1">',
    sectionPadding: '<e.g., "96px top / 48px bottom">',
    contentGap: '<e.g., "8px">',
  },

  palette: {
    light: {
      bg: '<base-100>',
      bgSubtle: '<base-200>',
      border: '<base-300>',
      text: '<base-content>',
      textMuted: '<muted text color>',
      textFaint: '<faintest text color>',
      // Add any other notable colors from the scraped palette
    },
    dark: {
      bg: '<dark base-100>',
      bgSubtle: '<dark base-200>',
      border: '<dark base-300>',
      text: '<dark base-content>',
      textMuted: '<dark muted>',
      textFaint: '<dark faint>',
    },
  },
};
```

## Font Mapping Cheat Sheet

Common proprietary → free Google Font mappings:

| Proprietary | Google Font Match | Category |
|---|---|---|
| StyreneA, Gilroy, Avenir, Circular | Inter, DM Sans, Space Grotesk | Geometric sans |
| Neue Haas, Aktiv Grotesk, Graphik | Inter, Plus Jakarta Sans | Neo-grotesque |
| TiemposText, Noe Text, Chronicle | Lora, Source Serif 4, Merriweather | Editorial serif |
| GT Sectra, Canela | Playfair Display, Cormorant Garamond | Display serif |
| SF Mono, Fira Code | JetBrains Mono, Fira Code | Monospace |
| Söhne, Calibre | Geist, Inter | Modern sans |
