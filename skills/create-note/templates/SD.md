# SD Template - System Definition

## Frontmatter additions

```yaml
status: Living Document
version: 1
date modified: YYYY-MM-DD
```

Tags: `[<system-tag>, system-definition, architecture, canonical]`

## Section structure

1. **Definition** - One paragraph. What the system is and its purpose. No meta-commentary.
2. **Position** - Table or short list showing where it sits relative to neighbors.
3. **Mechanics** - How it works. Subsections by mechanism. Definition first, then rules, then boundary conditions.
4. **Principles** - Numbered, non-negotiable constraints. Bold name + 1-3 sentences.
5. **Adjacent systems** - One short paragraph per neighbor. State the interface, not the implementation.
6. **Boundaries** - What it is NOT. Bold label + 1-2 sentences. Only plausible confusions.
7. **Theoretical grounding** - (Optional) Framework name, one sentence on contribution.
8. **Future direction** - (Optional) Compact list of capabilities v1 excludes.
9. **Change Log** - `| Date | Change | Author |` table.

## Writing rules

- Active present tense. "The system routes signals" not "will route."
- No implementation detail. No table names, endpoints, container names, file paths.
- Principles describe constraints, not implementations.
- Size target: 80-120 lines of content (excluding frontmatter and changelog).

## SD vs SPC decision

If the deliverable defines how a system behaves (principles, constraints, boundaries), write an SD. If it defines what to build (requirements, acceptance criteria, implementation scope), write a spec. Skill frameworks, workflow patterns, and agent behavior systems are SDs. Apps, services, and infrastructure are SPCs.

## Workflow

1. Oracle check (from shared setup)
2. Read existing context (project CLAUDE.md, related specs, any existing SD fragments)
3. Draft v1 following section structure
4. Present to user for review
5. Iterate, bump version and date modified
