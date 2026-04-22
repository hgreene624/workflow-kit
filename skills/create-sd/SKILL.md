# Create System Definition

Create or update a System Definition (SD) document. SDs are constitutional, living references that define what a system is, how it works, and what principles govern it. They sit above specs: when a spec conflicts with the SD, the SD wins.

Use this skill when the user says "create SD", "system definition", "write an SD", or when starting foundational design work for a new system, skill framework, or workflow concept.

**SD vs SPC decision:** If the deliverable is defining how a system behaves (principles, constraints, boundaries, conceptual model), write an SD. If the deliverable is defining what to build (concrete requirements, acceptance criteria, implementation scope), write a spec. Skill frameworks, workflow patterns, and agent behavior systems are SDs. Apps, services, and infrastructure are SPCs.

## Path Resolution

Read `~/.claude/wfk-paths.json` to resolve the vault root and project paths. The SD lives at the project root:
```
{vault_root}/{paths.projects}/<project>/SD - <System Name>.md
```

## Mandatory Frontmatter

```yaml
---
date created: YYYY-MM-DD
tags: [<system-tag>, system-definition, architecture, canonical]
category: System Definition
status: Living Document
date modified: YYYY-MM-DD
version: 1
---
```

`category: System Definition` is required for Obsidian views to pick up the file. Do not use `Reference` or any other category.

## Required Structure

Every SD follows this structure. Sections can be reordered slightly for flow, but all must be present.

### 1. Opening Declaration

Two paragraphs, always:

> This is the definitive reference for what [System Name] is, how it works, and what it does. Every spec, design discussion, and implementation that touches [System Name] must conform to this document. When there is a conflict between this document and a spec, this document wins.
>
> This is not a technical specification. It contains no database schemas, API endpoints, or container names. Those live in specs. This document defines the conceptual structure, principles, and boundaries that specs implement.

If the SD was informed by research (NLM oracle, research report), add a source reference line:
> Source research: [[RE - Research Report Name]].
> Oracle resource (NLM notebook): `<notebook_id>` (<N> sources on <topic>).

### 2. What [System Name] Is

Define the system's purpose and identity. What does it exist to do? Frame as 2-3 clear functions. Use "it exists to do [N] things" when there are multiple purposes.

Write in active present tense. The system "is," "does," "serves." Never "will be" or "should."

### 3. How It Works

The conceptual model. Define the core concepts, entities, processes, and relationships. Use subsections for distinct aspects.

**Rules:**
- Name concepts, not implementations. "Signals" not "the signals table." "Observation boundary" not "the email scraping cron."
- Entities are conceptual. "Six entities define the system. They are conceptual - schema details live in specs."
- Processes are described as flows, not as code paths.
- If the system has a theoretical model (OODA, VSM, SECI, etc.), introduce it here.

### 4. How It Changes How We Work

Business impact. How does this system change what people do today? Write from the user's perspective, not the builder's. Use "Today... With [System Name]..." contrast pairs for each stakeholder.

### 5. What [System Name] Is Not

Explicit boundaries. List 4-6 things the system is NOT, each with a one-line explanation. This prevents scope creep by making exclusions visible.

Format: **Not a [thing].** [One sentence explaining why this is excluded or where it lives instead.]

### 6. Core Principles

Numbered, non-negotiable constraints. These apply to every spec, design, and implementation decision.

Open with: "These are non-negotiable. They apply to every spec, design, and implementation decision."

Each principle: **N. Title.** Then 2-4 sentences explaining the constraint, why it exists, and what violating it looks like. Principles describe constraints, not implementations.

### 7. Theoretical Grounding

List the established frameworks the system draws on. Each entry: framework name, author/year, and one sentence on what it contributes to this system's design.

### 8. Future Direction (optional)

Vision for what the system becomes beyond v1. Framed as possibilities, not commitments. Close with "None of this is in v1. The architecture is designed so each is additive, not disruptive."

### 9. Change Log

Table tracking every revision:

```markdown
| Date | Change | Author |
|---|---|---|
| YYYY-MM-DD | Initial version. [Brief description.] | [Name] |
```

## Optional Sections

Add these when relevant:

- **Relationship to Adjacent Systems** - When the system touches other systems, define scope boundaries explicitly. Who owns what.
- **Anti-Patterns** - Failure modes observed during design or development. Each was encountered and resolved. Documented as active constraints.
- **The Oracle Resource** - If an NLM notebook was created for this system's domain, document its ID, source count, and when to query it.

## Writing Rules

These are the most important constraints. Violating them produces a spec disguised as an SD.

1. **Active present tense only.** "The system does X." Never "the system will do X" or "the system should do X." Implementation status belongs in specs and plans, not SDs.
2. **No implementation detail.** No database schemas, table names, column names, API endpoints, container names, file paths, function names, SQL queries, or config values. If you catch yourself writing a specific technical name, you've dropped from SD level to spec level. Lift back up.
3. **Principles describe constraints, not implementations.** "History is immutable" is a principle. "Use SCD Type 2 with valid_from/valid_to columns" is implementation.
4. **No hedging.** The system "does" or "does not." Never "likely," "probably," "should," "might."
5. **No em dashes.** Use commas, periods, or parentheses.
6. **Tight spacing.** No double blank lines.

## Oracle Prompt (Step 0)

Before writing the SD, check if the project has an oracle (NLM notebook) registered in its PJL frontmatter. If one exists, query it for domain grounding. If none exists, suggest creating one:

> "This project has no oracle for domain grounding. Want to research real-world approaches to [domain] before writing the SD? The oracle will gather established patterns, industry standards, and theoretical frameworks so the SD builds on informed principles."

This is a prompt, not a gate. The user can skip it.

## Workflow

1. **Check for oracle** (Step 0 above)
2. **Read existing context** - project agents.md, related specs, any existing SD fragments
3. **Draft v1** - Write the full SD following the structure above
4. **Present to user** - The user reviews and provides feedback
5. **Iterate** - Apply changes, bump version and date modified
6. **Lock** - When the user confirms, the SD becomes the governing document for all future work on this system
