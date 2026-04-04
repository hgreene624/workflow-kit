# Theme CSS Template

Use this exact structure when creating a new theme CSS file. Replace all `<placeholders>` with actual values from the scraped data.

```css
/*
 * <Theme Label> Theme
 * ========================
 * Scraped from <source-url> — <short aesthetic description>.
 *
 * Design language:
 *   - <key trait 1, e.g., "Serif body text (editorial feel), sans-serif headings">
 *   - <key trait 2, e.g., "Near-zero border-radius, no box-shadows">
 *   - <key trait 3, e.g., "Warm off-white and near-black palette">
 *   - <key trait 4, e.g., "Generous vertical rhythm (96px section padding)">
 *   - <key trait 5, e.g., "Top-border section dividers using muted gray">
 */

/* ───── Light variant ───── */
@plugin "daisyui/theme" {
  name: "<id>-light";
  default: false;
  color-scheme: light;

  /* Surfaces */
  --color-base-100: <lightest-bg>;
  --color-base-200: <subtle-bg>;
  --color-base-300: <border-color>;
  --color-base-content: <primary-text>;

  /* Brand */
  --color-primary: <primary-brand-or-cta>;
  --color-primary-content: <text-on-primary>;
  --color-secondary: <secondary-or-muted>;
  --color-secondary-content: <text-on-secondary>;
  --color-accent: <accent-highlight>;
  --color-accent-content: <text-on-accent>;

  /* Neutral */
  --color-neutral: <dark-surface>;
  --color-neutral-content: <text-on-dark>;

  /* Semantic */
  --color-info: <info-blue>;
  --color-info-content: #FFFFFF;
  --color-success: <success-green>;
  --color-success-content: #FFFFFF;
  --color-warning: <warning-amber>;
  --color-warning-content: #000000;
  --color-error: <error-red>;
  --color-error-content: #FFFFFF;
}

/* ───── Dark variant ───── */
@plugin "daisyui/theme" {
  name: "<id>-dark";
  default: false;
  color-scheme: dark;

  /* Surfaces — invert the light palette */
  --color-base-100: <darkest-bg>;
  --color-base-200: <dark-subtle>;
  --color-base-300: <dark-border>;
  --color-base-content: <light-text>;

  /* Brand */
  --color-primary: <primary-on-dark>;
  --color-primary-content: <text-on-primary-dark>;
  --color-secondary: <secondary-on-dark>;
  --color-secondary-content: <text-on-secondary-dark>;
  --color-accent: <accent-on-dark>;
  --color-accent-content: <text-on-accent-dark>;

  /* Neutral */
  --color-neutral: <dark-neutral>;
  --color-neutral-content: <light-text>;

  /* Semantic */
  --color-info: <info-blue-bright>;
  --color-info-content: #FFFFFF;
  --color-success: <success-green-bright>;
  --color-success-content: #FFFFFF;
  --color-warning: <warning-amber-bright>;
  --color-warning-content: #000000;
  --color-error: <error-red-bright>;
  --color-error-content: #FFFFFF;
}

/* ───── Theme-specific design tokens (both variants) ───── */
[data-theme="<id>-light"],
[data-theme="<id>-dark"] {
  /* Typography */
  --theme-font-heading: '<heading-font>', <heading-fallback>;
  --theme-font-body: '<body-font>', <body-fallback>;
  --theme-font-mono: '<mono-font>', ui-monospace, monospace;

  /* Heading scale */
  --theme-h1-size: <h1-size>;       /* e.g., 3.25rem */
  --theme-h1-weight: <h1-weight>;   /* e.g., 700 */
  --theme-h1-lh: <h1-lh>;           /* e.g., 1 */
  --theme-h2-size: <h2-size>;
  --theme-h2-weight: <h2-weight>;
  --theme-h2-lh: <h2-lh>;
  --theme-h3-size: <h3-size>;
  --theme-h3-weight: <h3-weight>;
  --theme-h3-lh: <h3-lh>;

  /* Body */
  --theme-body-size: <body-size>;
  --theme-body-lh: <body-lh>;
  --theme-body-ls: <body-ls>;        /* letter-spacing */
  --theme-prose-size: <prose-size>;   /* paragraph text if different */
  --theme-prose-lh: <prose-lh>;

  /* Nav */
  --theme-nav-font-size: <nav-size>;
  --theme-nav-font-weight: <nav-weight>;
  --theme-nav-ls: <nav-ls>;

  /* Spacing */
  --theme-section-py: <section-top-padding>;
  --theme-section-py-sm: <section-bottom-padding>;
  --theme-section-gap: <gap-between-sections>;
  --theme-content-gap: <gap-within-grids>;

  /* Shape */
  --theme-radius: <border-radius>;
  --theme-radius-sm: <small-radius>;
  --theme-radius-lg: <large-radius>;
  --theme-card-shadow: <shadow-or-none>;
  --theme-card-border: <border-or-none>;
  --theme-card-bg: <card-bg-or-transparent>;

  /* Images */
  --theme-img-radius: <img-radius>;
  --theme-img-hero-ratio: <hero-aspect-ratio>;
  --theme-img-thumb-ratio: <thumb-aspect-ratio>;

  /* Borders & Dividers */
  --theme-divider-width: <divider-width>;
}

/* Light-specific muted colors */
[data-theme="<id>-light"] {
  --theme-divider-color: <light-divider>;
  --theme-text-muted: <light-muted>;
  --theme-text-faint: <light-faint>;
}

/* Dark-specific muted colors */
[data-theme="<id>-dark"] {
  --theme-divider-color: <dark-divider>;
  --theme-text-muted: <dark-muted>;
  --theme-text-faint: <dark-faint>;
}
```
