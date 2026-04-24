---
name: structure
description: >-
  Produce a Structure Outline (SO) document — a 2-page overview of module boundaries,
  key signatures, data flow, and vertical implementation phases. Like C header files:
  enough to see what the agent plans without the full implementation. Enforces vertical
  slicing — every phase must deliver a user-testable outcome. Use after /design and
  before /create-plan. Trigger on "structure outline", "implementation outline", "SO for
  this spec", "how should we structure this", or when /design completes.
---

# Structure Outline Skill

You produce a Structure Outline (SO) — a ~2-page document showing module boundaries, key signatures, data flow, and vertical implementation phases. Think of it as the "C header file" for an implementation: enough to see the plan and correct it before code gets written.

## Invocation

```
/structure <path-to-spec>
```

If no path is given, ask the user which spec to structure.

## Instructions

1. **Read the spec** at the provided path. Extract the project name and scope.

2. **Infer the project** from the spec's location (`02_Projects/<ProjectName>/`).

3. **Check for a Design Discussion (DD)** — look in `02_Projects/<project>/designs/` for a matching DD document. If one exists, read it — design decisions inform module boundaries and phase order.

4. **If no DD exists**, estimate lines of code for the spec. If >500 LOC, note that a DD is recommended and run `/design` first. If <500, proceed without.

5. **Read project agents.md** — look for `02_Projects/<project>/agents.md` to understand codebase context, conventions, and constraints.

6. **Explore the codebase** — if agents.md references a repo path, explore until you can confidently define module boundaries and key signatures. Don't limit yourself to files the spec explicitly mentions — adjacent modules, shared utilities, and existing patterns inform where new code should land.

7. **Read the SO template** from `~/.claude/skills/structure/references/so-template.md`.

8. **Generate the Structure Outline** using the template. Fill in all sections:
   - **Module Boundaries:** which modules/services/files are touched
   - **Key Signatures & Types:** new or changed interfaces, endpoints, schemas — just the shape, not logic
   - **Data Flow:** how data moves for key user-facing scenarios
   - **Phase Order:** implementation phases as vertical slices

9. **Enforce vertical slicing** — review every phase. Each phase MUST deliver a user-testable outcome. If any phase is purely horizontal (e.g., "set up all database tables", "create all API endpoints"), restructure into vertical slices where each phase delivers end-to-end functionality for a subset of features.

10. **Fill the Vertical Slice Verification table** — for each phase, confirm "Can the user do something new after this phase?" If the answer is no, restructure that phase.

11. **Present the phase order to the user** for review. They may want to reorder phases, split or merge them, or adjust scope. Wait for approval before saving.

12. **Save the SO document** to `02_Projects/<project>/structures/{today}/SO - {Spec Name}.md`. Create the directory if it doesn't exist.

13. **Handoff** — end with: "Structure outline complete. Ready for `/create-plan` to create the detailed implementation plan."
