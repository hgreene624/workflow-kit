---
name: pdf-cuartilla
description: Generate a one-page (cuartilla) PDF summary from any content — meeting notes, diagnostic summaries, briefings, technical fact-sheets, Soltein ticket drafts, executive memos. Output is a Letter-size single-page PDF built from inline HTML+CSS converted via headless Microsoft Edge (no external dependencies). Three style variants — tecnico (dense table layout with code blocks for IDs/codes), ejecutivo (more whitespace, larger callouts), ticket-soltein (Status Shadai header + TFLO1 prefix conventions). Trigger on "hazme un PDF de una cuartilla", "PDF de una hoja", "one-pager PDF", "resumen en PDF", "ficha técnica PDF", "briefing PDF", or /pdf-cuartilla. Use this skill — not ad-hoc HTML writing — whenever the user asks for a polished single-page PDF deliverable.
---

# pdf-cuartilla — One-page PDF deliverables for Windows

This skill reproduces the diagnóstico-Tucson-2011 style: a polished, single-page Letter PDF that fits a complete topic on one sheet. Built on Windows 11 with zero external dependencies (uses Microsoft Edge headless, already installed).

## When to use

Invoke when the user wants a **shareable single-page PDF** for an external audience (mechanic, doctor, contractor, Soltein support, executive). Signals:

- "una cuartilla", "una hoja", "one-pager", "ficha", "resumen para [persona externa]"
- The user wants something they can print or send as attachment
- The content has a definable structure: symptoms → causes → action plan, or problem → options → recommendation

**Don't use for:** interactive dashboards (use `analytics-report`), multi-page reports, raw markdown notes (just write the `.md`), or anything that lives in the vault as working memory.

## Workflow

### Step 1 — Confirm variant and audience

Ask the user (if not obvious from request):

1. **Variant** — `tecnico` / `ejecutivo` / `ticket-soltein` (default `tecnico` if the content has tables, codes, or specific IDs).
2. **Output path** — default `C:\Users\Shadai Hernandez\Desktop\<slug>.pdf`. Offer vault location if content is project-related (`G:\Mi unidad\Vaults\02_Projects\<project>\<slug>.pdf`).
3. **Title** — short, ≤60 chars.
4. **Subtitle** — context line (date + audience, e.g., "Resumen para conversación con mecánico · 16 mayo 2026").

Use sensible defaults; only ask if genuinely ambiguous.

### Step 2 — Structure the content

Pick one of these spines based on the topic:

| Spine | Sections |
|---|---|
| **Diagnóstico** (vehicle, health, IT) | Síntomas → Causas probables (tabla rankeada) → Guion citable → Plan de acción + costos → Bandera roja |
| **Decisión** (which option to pick) | Contexto → Opciones (tabla comparativa) → Recomendación → Riesgos → Próximos pasos |
| **Briefing** (catch someone up) | TL;DR → Estado actual → Bloqueadores → Pendientes → Próxima decisión |
| **Ticket Soltein** | Síntoma observado → Pasos para reproducir → Impacto → Logs/evidencia → Solicitud específica |

If the content doesn't fit, design ad-hoc but keep ≤6 sections and use the same H2 styling.

### Step 3 — Write the HTML

Use the template at `template.html` in this skill folder as the base. Critical CSS conventions:

- `@page { size: Letter; margin: 1.5cm 1.8cm; }` — forces single Letter page, tight margins so a full topic fits.
- Font stack: `"Segoe UI", Calibri, Arial, sans-serif`. Body 10.5pt, line-height 1.35 — dense but readable when printed.
- Color palette: **#0b3d91** (azul) for titles + borders, **#fffceb / #d4a017** (amarillo) for citable quote blocks, **#fdecea / #c0392b** (rojo) for warnings/red flags, **#e8eef9** for table headers.
- Tables: `border-collapse: collapse`, headers in azul, `td.num` centered 22px for ranking columns.
- Quote block (`.quote`): yellow background with left border — used for the verbatim phrase the user will read to the third party.
- Warning block (`.warn`): red background with left border — used for the single most important caveat.

**Density rules** (so it fits on one page):
- `tecnico`: body 10.5pt, `h2` 11.5pt, table font 9.5pt
- `ejecutivo`: body 11pt, `h2` 13pt, table font 10pt, doubled vertical margins on headings
- `ticket-soltein`: same as `tecnico` but prefix the title with `[TFLO1-NNNN]` placeholder and include "💬 Status Shadai YYYY-MM-DD:" line in the subtitle area

### Step 4 — Convert HTML → PDF

Run this PowerShell snippet (the user has Edge at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`):

```powershell
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$html = "<absolute path to .html>"
$pdf  = "<absolute path to .pdf>"
& $edge --headless --disable-gpu --no-pdf-header-footer `
        --print-to-pdf="$pdf" "file:///$($html -replace '\\','/')" 2>&1 | Out-Null
if (Test-Path $pdf) { "OK -> $pdf ($((Get-Item $pdf).Length) bytes)" } else { "FAILED" }
```

Flags explained:
- `--headless --disable-gpu` — runs without UI
- `--no-pdf-header-footer` — strips browser-default URL/date footer (without this, every PDF shows "file:///..." in the corner — looks unprofessional)
- `file:///` URL with forward slashes — Edge requires URL format, not Windows paths

### Step 5 — Verify and report

- Confirm the PDF exists and report its size (typical ~80–120 KB).
- Don't open it automatically — the user will inspect on Desktop.
- Keep the `.html` source alongside the `.pdf` so they can edit and regenerate.
- If the user is following `feedback_vault_loop` and the topic deserves persistence, suggest also dropping a `.md` copy of the content in `04_Reference/`.

## Anti-patterns

- **Don't** install pandoc/wkhtmltopdf/Puppeteer/Chromium — Edge is already there.
- **Don't** force content onto two pages. If it won't fit, drop sections or use `ejecutivo` variant with smaller font; never let it spill 2 lines onto page 2.
- **Don't** add a generated-by-Claude footer. The user is presenting this as their own work to a third party.
- **Don't** use emoji decorations in headings (the warning ⚠ inside the warn block is fine; otherwise keep it clean for print).
- **Don't** include hyperlinks that won't be clickable on paper — if you reference a source, cite it inline as "(Edmunds foro)" not a URL.

## Example invocation

User: *"Hazme un PDF de una cuartilla sobre cómo cuidar la batería de litio del taladro Makita."*

1. Variant: `tecnico` (has specs and do/don't lists).
2. Path: Desktop, `cuidado_bateria_makita.pdf`.
3. Sections: Resumen 30s → Qué hacer (tabla) → Qué evitar (tabla con códigos de comportamiento) → Señales de batería muerta → Cuándo reemplazar.
4. Generate HTML → Edge → done in one round.
