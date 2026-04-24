---
name: design
description: >-
  Produce a Design Discussion (DD) document that externalizes human-agent alignment
  before implementation. Reads the spec and review artifacts, then generates a ~200-line
  document covering current state, desired state, patterns, approach options, and open
  questions. Use after /review-spec and before /structure. Trigger on "design discussion",
  "let's discuss the design", "DD for this spec", "alignment check", or when review-spec
  completes and the implementation is estimated at >500 LOC.
---

# Design Discussion Skill

You are producing a Design Discussion (DD) document — the human-agent alignment artifact from CRISPY. This forces you to externalize your understanding of what's being built BEFORE any code or detailed planning happens.

## Invocation

```
/design <path-to-spec>
```

If no path is given, ask the user which spec to work from.

## Instructions

1. Read the spec file at the provided path. Extract the spec name and project directory from its location in the vault tree (`01_Work/03_Projects/<Project>/` or `02_Projects/<Project>/`).

2. Check for review artifacts in the project's `reviews/` directory (any dated subdirectory). Read `scope-analysis.md`, `context-brief.md`, and `spec-review.md` if they exist — these contain prior analysis you should incorporate.

3. Read the project's `agents.md` and `lessons.md` if they exist. Read the vault-root `AGENTS.md` as well.

4. **Oracle check:** Read the project's PJL frontmatter for `oracles:`. If an oracle exists, query it: "What does the industry consider best practice for {design area}? What are proven patterns and common pitfalls?" Surface as a proposition when writing the Desired End State section. If no oracle exists, prompt: "This project has no oracle. Want to create one with `/oracle-create` for domain grounding?" If declined, proceed without. See [[SD - Oracle System]].

5. If `agents.md` specifies a repo path, explore the codebase until you can confidently fill the Current State and Patterns Found sections. Don't limit yourself to files the spec explicitly mentions — adjacent modules, shared utilities, and existing patterns in the same domain all matter. If a question about current behavior can be answered by reading the code, read the code instead of leaving it as an Open Question.

6. Estimate the implementation LOC. If under 500 LOC, inform the user: "This implementation is estimated at ~{N} LOC. Design discussions are optional under 500 LOC, skipping to `/structure`." and proceed directly to `/structure`. If >=500 LOC, continue with the DD.

7. Read the DD template from `~/.claude/skills/design/references/dd-template.md`.

8. Generate the DD document (~200 lines) filling all six sections:
   - **Current State** — what exists today, based on codebase exploration
   - **Desired End State** — concrete target behavior from the spec
   - **Patterns Found** — table of relevant patterns from the codebase
   - **Approach Options** — at least 2 options with tradeoffs and effort estimates, plus a recommendation
   - **Resolved Decisions** — decisions already locked in from the spec or review
   - **Open Questions** — questions that will change the implementation approach

9. For each Open Question, present it to the user one at a time via AskUserQuestion. Include the question, its impact, and the default if unanswered.

10. Record each answer in the Resolved Decisions table. Move the question from Open Questions and add a new DD-N row with the decision and rationale.

11. After all questions are resolved (or the user defers them), save the DD document to: `02_Projects/<project>/designs/{today}/DD - {Spec Name}.md` — create the directory if needed. Set frontmatter fields: today's date, category "Design Discussion", source wikilink to the spec, and status "Draft".

12. Print the path to the saved DD document and end with: "Design discussion complete. Ready for `/structure` to create the implementation outline."
