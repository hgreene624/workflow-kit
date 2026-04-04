# Skill Optimize — Reference

Instructions for optimizing a skill's description for better triggering accuracy, packaging, and backup. You were routed here by the skill-creator router.

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Claude invokes a skill. This flow optimizes it for accuracy.

### Step 1: Generate Trigger Eval Queries

1. Create 20 eval queries — a mix of should-trigger (8-10) and should-not-trigger (8-10). Save as JSON:
   ```json
   [
     {"query": "the user prompt", "should_trigger": true},
     {"query": "another prompt", "should_trigger": false}
   ]
   ```

2. Queries must be realistic — concrete, specific, with detail (file paths, personal context, column names, company names, URLs). Mix of lengths, some lowercase/abbreviated/casual. Focus on edge cases, not clear-cut.

3. **Should-trigger queries**: Different phrasings of the same intent — formal and casual. Include cases where the user doesn't name the skill but clearly needs it. Include uncommon use cases and competitive cases where this skill should win.

4. **Should-not-trigger queries**: Near-misses that share keywords but need something different. Adjacent domains, ambiguous phrasing where naive keyword matching would false-positive. Don't make them obviously irrelevant.

### Step 2: Review with User

5. Read the template from `assets/eval_review.html`.
6. Replace placeholders: `__EVAL_DATA_PLACEHOLDER__` → JSON array, `__SKILL_NAME_PLACEHOLDER__` → name, `__SKILL_DESCRIPTION_PLACEHOLDER__` → description.
7. Write to `/tmp/eval_review_<skill-name>.html` and open it.
8. User edits queries, toggles should-trigger, adds/removes entries, clicks "Export Eval Set".
9. Check `~/Downloads/` for the most recent `eval_set.json`.

### Step 3: Run the Optimization Loop

10. Tell the user: "This will take some time — I'll run the optimization loop in the background and check on it periodically."

11. Save the eval set to the workspace, then run:
    ```bash
    python -m scripts.run_loop \
      --eval-set <path-to-trigger-eval.json> \
      --skill-path <path-to-skill> \
      --model <model-id-powering-this-session> \
      --max-iterations 5 \
      --verbose
    ```
    Use the model ID from your system prompt so triggering tests match user experience.

12. The loop splits 60% train / 40% test, evaluates current description (3x per query), calls Claude to propose improvements based on failures, re-evaluates each iteration. Selects best by test score to avoid overfitting.

13. Periodically tail output to give the user updates on iteration progress and scores.

### Step 4: Apply the Result

14. Take `best_description` from JSON output and update the skill's SKILL.md frontmatter. Show before/after and report scores.

### How Skill Triggering Works

15. Skills appear in Claude's `available_skills` list with name + description. Claude only consults skills for tasks it can't easily handle alone — simple one-step queries may not trigger even with matching descriptions. Eval queries should be substantive enough that Claude would benefit from consulting a skill.

## Package and Present

16. Check whether the `present_files` tool is available. If not, skip this step.
17. If available, package the skill:
    ```bash
    python -m scripts.package_skill <path/to/skill-folder>
    ```
18. Direct the user to the resulting `.skill` file path.

## Backup to GitHub

19. After any skill creation, modification, or description optimization, back up to GitHub using update-skills.
20. Tell the user: "I'll back up this skill to GitHub now."
21. Invoke `/update-skills push <skill-name>`.
22. If push succeeds, confirm. If it fails, report the error and let the user decide.
23. This step is automatic — don't ask. Skip only if the user explicitly says not to push.

## Updating an Existing Skill

24. Preserve the original name — use the existing directory name and `name` frontmatter field unchanged.
25. Copy to a writeable location before editing if the installed path is read-only. Stage in `/tmp/` first if needed.
