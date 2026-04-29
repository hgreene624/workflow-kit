---
name: create-note
description: >-
  Unified vault document creator. Handles SD, SPC, PIC, MN, PD, DD, SO, RE, and EB
  documents with correct frontmatter, routing, writing profiles, and type-specific
  structure. Replaces individual create-sd, create-spec, create-pickup, create-MN,
  create-concept-brief, design, and structure skills.
  Trigger: "create note", "create SD", "create spec", "create PIC", "create MN",
  "create PD", "design discussion", "structure outline", "write a report",
  "executive brief", "create EB", or any request to create a vault document by prefix.
---

# Create Note

Unified document creation for the Work Vault. One skill, all document types. The type determines frontmatter, routing, writing profile, and section structure.

## Step 1: Determine type

Parse the user's request or argument to identify the document type. Accept any of:

| Type | Triggers | Old skill |
|------|----------|-----------|
| `SD` | "create SD", "system definition" | `/create-sd` |
| `SPC` | "create spec", "spec this", "write a spec" | `/create-spec` |
| `PIC` | "create pickup", "make a PIC", "save for later" | `/create-pickup` |
| `MN` | "create MN", "meeting note", "write up the meeting" | `/create-MN` |
| `PD` | "product definition", "create PD", "I have an idea" | `/create-concept-brief` |
| `DD` | "design discussion", "DD for this spec" | `/design` |
| `SO` | "structure outline", "SO for this spec" | `/structure` |
| `RE` | "create report", "write a report" | (none) |
| `EB` | "executive brief", "exec brief", "create EB", "write a brief" | (none) |

If the type is ambiguous, ask via AskUserQuestion.

## Step 2: Shared setup

Run these for every type. This is the boilerplate that was duplicated across 7 skills.

1. **Path resolution.** Read `~/.claude/wfk-paths.json`. Use `vault_root` and `paths` to resolve all directory references. If missing, use defaults and warn once.

2. **Project context.** Read the target project's `CLAUDE.md` and `lessons.md` if they exist. If the project is ambiguous, ask.

3. **Writing profiles.** Load `WP - General.md` from `Work Vault/04_Reference/Agents/Writing Profiles/`. Then load the type-specific profile if one exists (see lookup table below). Follow both.

4. **Oracle check.** Read the project's PJL frontmatter for `oracles:`. If an oracle exists, query it for domain grounding relevant to the document being created. If none exists, offer to create one. This is a prompt, not a gate. Skip for MN and PIC (they don't benefit from oracle grounding).

5. **Frontmatter.** Set from the lookup table below. Never guess the category.

## Lookup table

This is the single source of truth for document metadata. Every field is mandatory.

| Type | Category (frontmatter) | Writing Profile | Routing |
|------|----------------------|-----------------|---------|
| `SD` | `System Definition` | `WP - SD.md` | `{project}/SD - {Name}.md` |
| `SPC` | `Spec` | `WP - SPC.md` | `{project}/specs/{date}/SPC - {Name}.md` |
| `PIC` | `Pickup` | `WP - PIC.md` | `{project}/pickups/{date}/PIC - {Name}.md` |
| `MN` | `Meeting` | `WP - MN.md` | `01_Notes/Meetings/MN - {date} ({Topic}).md` |
| `PD` | `Spec` | (General only) | `{project}/concepts/{date}/PD - {Name}.md` |
| `DD` | `Plan` | (General only) | `{project}/designs/{date}/DD - {Name}.md` |
| `SO` | `Plan` | (General only) | `{project}/structures/{date}/SO - {Name}.md` |
| `RE` | `Report` | `WP - RE.md` | `{project}/reports/{date}/RE - {Name}.md` |
| `EB` | `Report` | `WP - RE.md` | `{project}/reports/{date}/EB - {Name}.md` |

`{project}` = `02_Projects/<project-name>/`
`{date}` = today's date (YYYY-MM-DD)

Cross-cutting PICs (no project) go to `01_Notes/Pickups/{date}/`.

## Step 3: Load type template

Read the type-specific template from `templates/{TYPE}.md` within this skill directory. The template defines:
- Section structure (what sections to include and their order)
- Type-specific workflow steps (interviews, verification, codebase exploration)
- Type-specific writing rules beyond the general profile
- Reference files to read (from `references/` directory)

Follow the template instructions exactly. The template is the authority on type-specific behavior.

## Step 4: Write the file

Create the file at the routing path from the lookup table. Create directories if needed.

Standard frontmatter block (all types):

```yaml
---
date created: YYYY-MM-DD
tags: [<type-tag>, <project-tag>]
category: <from lookup table>
---
```

Types may add fields (SD adds `version`, PIC adds `status`/`goal`/`pickup_date`, SPC adds `status`/`source`). See templates for type-specific frontmatter.

## Step 5: Post-creation

After writing, perform type-specific post-steps from the template (e.g., PIC logs to PJL, MN links in daily note, SPC runs review gate). Then report the file path.

## Notes

- **Update mode.** If the user says "update the spec" or "add to the PIC", this is an update, not a create. For SPC, read `references/update-spec.md`. For PIC, merge into the existing open PIC. For other types, read the existing file and apply changes.
- **Retire old skills.** This skill replaces create-sd, create-spec, create-pickup, create-MN, create-concept-brief, design, and structure. Those skills should be removed once this one is validated.
