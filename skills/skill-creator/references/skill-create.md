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

## Design Principles

Apply these when writing the skill. They come from empirical observation of what makes skills effective vs bloated.

**Constraint-based > procedure-based.** Tell the agent *what to achieve*, not *every step to take*. "Interview the user relentlessly until you can draft all sections" outperforms a 50-step interview script. Constraints adapt to context; procedures break when the situation deviates. Reserve step-by-step procedures only for sequences where order truly matters (deploy checklists, safety protocols).

**Deep module pattern.** A skill should have a simple interface (short trigger, minimal parameters) and complex behavior (rich internal logic driven by exploration and judgment). The `grill` skill is 3 sentences and drives 50-question design interviews. If your skill needs 2,000 tokens to explain what it does, the design is wrong.

**Examples and reference material belong in `references/`.** The SKILL.md should contain operational instructions — the minimum the agent needs to act. Examples, templates, incident history, and edge case catalogs lazy-load from `references/` only when needed. This keeps the per-invocation token cost low.

**Explore the codebase instead of asking.** When a skill needs context about existing code, infrastructure, or project state, instruct the agent to read the relevant files rather than asking the user. The user shouldn't have to describe their own codebase to the agent.

**Every skill should hand off clearly.** After completing its work, a skill should tell the user what the natural next step is and offer to invoke it. Broken handoff chains mean capabilities get skipped.

**Token budget is a design constraint.** Measure the SKILL.md in approximate tokens (1 token ≈ 4 chars). Under 1,500t is excellent. Under 3,000t is acceptable. Over 4,000t needs justification — consider whether content should move to references/.

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

### Token Budget Lint

17b. Estimate SKILL.md token count (file size in bytes ÷ 4).
    - **GREEN** (<1,500t): Excellent — lean and focused.
    - **YELLOW** (1,500-3,000t): Acceptable. Check if any content could move to references/.
    - **RED** (>3,000t): Heavy. Flag specific sections that could be extracted (examples, edge cases, templates, incident history).
    Display: "SKILL.md is ~{N}t. {status}."

### Constraint vs Procedure Check

17c. Scan for procedural patterns that could be constraint-based: numbered step sequences with >5 steps where the order doesn't strictly matter, fixed question counts ("ask 3 questions"), or rigid caps that prevent adaptive behavior. Flag them: "Steps X-Y look procedural — could a constraint achieve the same result with more flexibility?"

### Control Flow Detection

18. Scan the generated SKILL.md for natural-language conditionals: "if", "when", "unless", "in case of", "depending on" (as control flow markers, not incidental uses in explanations).
19. Count conditional branches.
20. If 3+ conditional branches: warn "This skill has {N} conditional branches. Consider splitting into separate skills with deterministic routing instead."
21. Suggest the router pattern from `~/.claude/skills/implement/references/routing-manifest.md` — a router SKILL.md that classifies the request and dispatches to the appropriate sub-skill reference file.

## Phase 5: Handoff

22. After post-generation checks pass (or user overrides), present the skill to the user.
23. If the user wants to run evals, hand off to the eval flow (the router will load `skill-eval.md`).
24. If the user is satisfied, proceed to backup via `/update-skills push <skill-name>`.
