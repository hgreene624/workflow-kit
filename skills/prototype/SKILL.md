---
name: prototype
description: >-
  Ingest a spec and produce a Prototype Design Discussion (DD) optimized for
  Claude Design (claude.ai/design). Extracts user flows, screen inventory,
  component inventory, data model summary, and interaction patterns from the
  spec into a single document that can be fed directly to Claude Design for
  UI prototyping. Use when the user says "prototype", "prototype this spec",
  "design doc for prototyping", "claude design prep", or wants to create
  mockups from a spec.
---

# Prototype Skill

Produce a Prototype Design Discussion (DD) from a spec. The DD is a self-contained document optimized for feeding into Claude Design (claude.ai/design) to generate interactive UI prototypes.

The goal is not implementation alignment (that's `/design`). The goal is visual/UX clarity: every screen, every interaction, every piece of data displayed, laid out so Claude Design can produce accurate mockups without needing the full spec.

## Invocation

```
/prototype <path-to-spec>
```

If no path is given, ask the user which spec to prototype.

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{vault_root}/{paths.projects}/`). If the file doesn't exist, use defaults and warn once.

## Instructions

1. **Read the spec.** Extract the spec name, project directory, and all functional requirements. Also read the PD (Product Definition) if one exists in the project's `concepts/` directory, as it often contains user-facing context the spec doesn't.

2. **Read the template** from `~/.claude/skills/prototype/references/prototype-dd-template.md`.

3. **Extract and generate six sections:**

   ### Section 1: Product Context
   One paragraph. What this product is, who uses it, and what problem it solves. Written for a designer who has never seen the spec. Pull from the PD's vision section if available, otherwise synthesize from the spec's Purpose/Objectives.

   ### Section 2: User Flows
   Every distinct user journey through the product, end to end. Each flow is a numbered sequence of steps with the format:

   ```
   Flow: {Flow Name}
   Actor: {who is doing this}
   1. {action} -> {what happens / what they see}
   2. {action} -> {what happens / what they see}
   ...
   ```

   Extract flows from FRs, use cases, and architecture data flows. Common flows to look for: creation/setup flows, consumption/viewing flows, management/admin flows, authentication flows. Include error and edge case flows where the spec defines them.

   ### Section 3: Screen Inventory
   Every distinct screen/page/view the product needs. For each screen:

   ```
   Screen: {Screen Name}
   Route: {URL path if specified in spec}
   Actor: {who sees this screen}
   Purpose: {what the user does here, one line}
   Entry points: {how the user gets here}
   Key content: {bullet list of what's displayed}
   Key actions: {bullet list of what the user can do}
   ```

   Derive screens from the spec's deliverables, API routes, and functional requirements. If the spec mentions a "listing page," "detail page," "creation wizard," etc., each is a screen. If a screen has distinct states (empty, loading, populated, error), note them.

   ### Section 4: Component Inventory
   Reusable UI components that appear across multiple screens or are complex enough to warrant explicit design. For each:

   ```
   Component: {Component Name}
   Used in: {which screens}
   Description: {what it looks like and does}
   States: {variants, empty/loading/error states}
   Data: {what data it displays or accepts}
   ```

   Look for: navigation elements, data tables, forms, cards, progress indicators, assessment interfaces, media players, auth flows, status badges, modals/overlays.

   ### Section 5: Data Model Summary
   What data is displayed where, written for a designer not a developer. No SQL, no schema. For each major entity:

   ```
   Entity: {Entity Name}
   Displayed as: {how users see this - card, row, detail page, etc.}
   Key fields shown to user: {list of visible fields with example values}
   Relationships: {what other entities it connects to visually}
   ```

   ### Section 6: Interaction Patterns
   How the product responds to user actions. Focus on patterns that affect visual design:

   - **Navigation model**: how users move between screens (tabs, sidebar, breadcrumbs, back buttons)
   - **Creation flows**: wizard vs. single page, progressive disclosure, step indicators
   - **Async operations**: what happens during long-running processes, polling indicators, return-to-completed states
   - **Mobile vs. desktop**: which screens are mobile-first, which are desktop-only, responsive breakpoints
   - **Auth transitions**: how the UI changes between manager and learner views
   - **Bilingual**: how language switching works in the UI
   - **Feedback patterns**: success/error states, toast notifications, inline validation
   - **Data tables**: sorting, filtering, pagination

4. **Check for existing design context.** If the project has a `designs/` directory with prior DDs, read them and note any established patterns or decisions. If a design system document exists, reference it.

5. **Save the DD** to: `{vault_root}/{paths.projects}/<project>/designs/{today}/DD - {Spec Name} Prototype.md`. Create the directory if needed. Set frontmatter: today's date, category "Design Discussion", source wikilink to the spec, status "Draft", and add tag `prototype`.

6. **Present the output.** Summarize what was generated (number of flows, screens, components) and tell the user: "This DD is ready to paste into Claude Design (claude.ai/design). Copy the full document or specific sections to generate prototypes."

## Quality Checks

Before saving, verify:
- Every FR that implies a user-visible element has a corresponding screen or component
- Every screen has at least one entry point (no orphan screens)
- Every flow ends (no open-ended sequences)
- Data entities match what's actually displayed on screens (no phantom fields)
- Mobile-specific screens are flagged as mobile
- Data tables specify their grid/table component (if a project-level standard exists)

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
