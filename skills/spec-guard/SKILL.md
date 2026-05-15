---
name: spec-guard
description: "Pre-implementation spec check. Auto-invoke before building any feature on an existing system. Scans the project's specs directory, flags unimplemented specs in the same domain, blocks work until specs are acknowledged. Prevents reimplementing what's already been designed."
type: agent
---

# Spec Guard -- Pre-Implementation Spec Check

Before building anything on an existing system, verify no spec already governs the work. This skill fires BEFORE implementation, BEFORE writing code, BEFORE seeding data, BEFORE writing migrations.

## When to invoke

Auto-invoke when ANY of these are true:
- You are about to write code for a feature on a system that has a project directory under `02_Projects/`
- You are about to seed data into an existing database schema
- You are about to write a migration for an existing service
- You are about to create an import/export pipeline for an existing system
- A research subagent returned spec filenames matching your current work domain and you haven't read them

Do NOT invoke for:
- New projects with no existing specs
- Bug fixes where the fix is self-evident (typo, crash, missing null check)
- Documentation-only changes

## Step 1: Identify the target project

Determine which project directory the work targets. Map from the code path or database schema to the vault project. The mapping is project-specific, so consult your vault's `CLAUDE.md` or project index for the canonical signals. A general heuristic:

| Signal | Likely project directory |
|---|---|
| `apps/<app>/` or `<app>.*` schema | `02_Projects/.../<app>/` |
| `services/<svc>/` | `02_Projects/.../<svc>/` |
| Domain-specific subfolder (e.g. `payments/`, `auth/`) | Closest matching project dir |

If no project directory exists, skip to Step 4 (no specs possible).

## Step 2: Scan for governing documents (SD first, then specs)

**2a. System Definitions (constitutional authority).**
```
Glob: {project_dir}/**/SD - *.md
Glob: {vault_root}/02_Projects/**/SD - *.md  (broader search if project-level finds nothing)
```
SDs define principles, not implementations. If an SD exists for the domain, read it first. Its principles constrain every spec and implementation beneath it. A spec that contradicts its governing SD is wrong; the SD wins.

**2b. Product Definitions.**
```
Glob: {project_dir}/**/PD - *.md
```
PDs define what a product does at the concept level. If a PD exists, it provides context the spec may have been written against.

**2c. Specs.**
```
Glob: {project_dir}/specs/**/*.md
```

Read the frontmatter of every spec found. Extract:
- `status`: draft, reviewed, conditional, implemented, superseded
- Title (from `# SPC - ...` heading)
- Date created

Filter to specs that are NOT `status: implemented` or `status: superseded`. These are live design documents.

**Reading order:** SD first (for principles and constraints), then PD (for product context), then SPC (for implementation details). If the SD and SPC disagree, flag the disagreement to the user. The SD is authoritative for design principles; the SPC is authoritative for implementation specifics that don't contradict the SD.

## Step 3: Domain match

For each live spec, check whether its title or purpose touches the same domain as your planned work. Use keyword overlap. Generic categories:

| Your work | Spec keywords that often match |
|---|---|
| Data ingest / import / seeding | import, ingest, audit, seed, pipeline |
| Content generation | content, generation, brief, corpus |
| Auth / login changes | auth, login, SSO, password, session |
| API endpoint changes | API, endpoint, route |
| UI component changes | component, page, view, dashboard |
| Data migration | migration, schema, table |

If ANY spec matches:
1. Read the full spec (not just frontmatter)
2. Identify which functional requirements (FRs) govern your planned work
3. Check the data model section for tables, columns, or schemas the spec defines

## Step 4: Gate decision

**No matching specs found:**
Proceed with implementation. Log: "Spec guard: no governing specs found for [domain] in [project]."

**Matching spec found, status = reviewed or conditional:**
HARD GATE. Present the spec's design to the user:
- Spec name and date
- The FRs that apply to your planned work
- The data model the spec defines
- Ask: "This spec governs this work. Implement per spec, or deviate with reason?"

Do not proceed until the user responds. Do not silently deviate.

**Matching spec found, status = draft:**
SOFT GATE. Present the spec but note it's a draft:
- "Draft spec exists: [name]. It defines [summary]. Follow the draft design, or implement independently?"

**Matching spec found, your work contradicts the spec:**
HARD BLOCK. You cannot implement something that conflicts with a reviewed spec without user approval. Present the conflict clearly:
- "The spec says [X]. Your plan does [Y]. These are incompatible because [reason]."

## Step 5: Log the check

After the gate passes (either no specs found or user approved), log the result in your working context:

```
Spec guard: [PASS - no specs | PASS - spec acknowledged | PASS - user approved deviation]
Specs checked: [list of spec filenames scanned]
Governing spec: [name, or "none"]
```

This log survives in the conversation and can be referenced at closeout.

## What this prevents

1. **Reimplementing from scratch** when a data model already exists (e.g. an agent designs a feature from DB schema alone, ignoring a spec that already defines the canonical tables and routing logic)
2. **Conflicting implementations** where two sessions build the same feature differently
3. **Wasted work** that gets thrown away when the spec's design is eventually implemented
4. **Silent spec violations** where the agent doesn't know a spec exists
