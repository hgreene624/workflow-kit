# Skill Create — Reference

Instructions for creating a new skill from scratch. You were routed here by the skill-creator router.

## Phase 1: Capture Intent

1. Understand the user's intent. If the current conversation already contains a workflow to capture, extract answers from the conversation history first — tools used, step sequence, corrections made, input/output formats observed.
2. Determine answers to these four questions (ask the user to fill gaps):
   - What should this skill enable Claude to do?
   - When should this skill trigger? (what user phrases/contexts)
   - What's the expected output format?
   - Should we set up test cases? Suggest the appropriate default based on skill type (objective outputs benefit from tests; subjective outputs often don't), but let the user decide.
3. Proactively ask about edge cases, input/output formats, example files, success criteria, and dependencies. Wait to write test prompts until this is ironed out.
4. Check available MCPs — if useful for research, research in parallel via subagents if available, otherwise inline.

## Phase 2: Write the SKILL.md

5. Fill in these components based on the user interview:
   - **name**: Skill identifier
   - **description**: When to trigger, what it does. This is the primary triggering mechanism — include both what the skill does AND specific contexts. Make descriptions a little "pushy" to combat undertriggering. Example: instead of "How to build a dashboard", write "How to build a dashboard to display data. Use this skill whenever the user mentions dashboards, data visualization, metrics, or wants to display data, even if they don't explicitly ask for a 'dashboard.'"
   - **compatibility**: Required tools, dependencies (optional, rarely needed)
   - **the rest of the skill**

6. Follow progressive disclosure — three-level loading:
   - Metadata (name + description) — always in context (~100 words)
   - SKILL.md body — in context when skill triggers (<500 lines ideal)
   - Bundled resources — loaded as needed (unlimited, scripts can execute without loading)

7. Keep SKILL.md under 500 lines. If approaching this limit, add hierarchy with clear pointers about where to go next. Reference files clearly from SKILL.md with guidance on when to read them.

8. For multi-domain skills, organize by variant with separate reference files per domain. Claude reads only the relevant reference file.

9. Use the imperative form in instructions. Explain the **why** behind instructions instead of heavy-handed MUSTs. Use theory of mind — make the skill general, not narrow to specific examples.

10. Include examples where useful:
    ```markdown
    ## Commit message format
    **Example 1:**
    Input: Added user authentication with JWT tokens
    Output: feat(auth): implement JWT-based authentication
    ```

11. Skills must not contain malware, exploit code, or security-compromising content. Don't create misleading skills or skills for unauthorized access.

12. Write a draft, then review it with fresh eyes and improve it before presenting.

## Phase 3: Test Cases

13. After writing the skill draft, create 2-3 realistic test prompts — things a real user would actually say. Share with the user for confirmation.

14. Save test cases to `evals/evals.json` with this structure (don't write assertions yet — just prompts):
    ```json
    {
      "skill_name": "example-skill",
      "evals": [
        {
          "id": 1,
          "prompt": "User's task prompt",
          "expected_output": "Description of expected result",
          "files": []
        }
      ]
    }
    ```
    See `references/schemas.md` for the full schema including the `assertions` field (added later).

## Phase 4: Post-Generation Checks

### Instruction Budget Lint

15. Count distinct imperative instructions in the generated SKILL.md.
16. Display the count with budget status:
    - **GREEN** (<30 instructions): Good to go.
    - **YELLOW** (30-40 instructions): Approaching budget. Consider whether any instructions can be consolidated.
    - **RED** (>40 instructions): Over budget. Warn the user and suggest splitting into sub-skills with a router pattern.
17. If >60 instructions: refuse to save without explicit user override — display: "This skill has {N} instructions. The CRISPY budget is 40. Split into sub-skills or confirm override."

### Control Flow Detection

18. Scan the generated SKILL.md for natural-language conditionals: "if", "when", "unless", "in case of", "depending on" (as control flow markers, not incidental uses in explanations).
19. Count conditional branches.
20. If 3+ conditional branches: warn "This skill has {N} conditional branches. Consider splitting into separate skills with deterministic routing instead."
21. Suggest the router pattern from `~/.claude/skills/implement/references/routing-manifest.md` — a router SKILL.md that classifies the request and dispatches to the appropriate sub-skill reference file.

## Phase 5: Handoff

22. After post-generation checks pass (or user overrides), present the skill to the user.
23. If the user wants to run evals, hand off to the eval flow (the router will load `skill-eval.md`).
24. If the user is satisfied, proceed to backup via `/update-skills push <skill-name>`.
