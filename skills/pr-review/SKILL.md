---
name: pr-review
description: >-
  Post-implementation code review — reviews changed files, checks for quality issues,
  generates a review artifact. Use after /implement completes or when the user wants a
  code review. Trigger on "review the code", "PR review", "code review", "check the
  implementation", "review what was built", or at the end of an /implement sprint.
  Do NOT use this for spec review (use /review-spec) or planning (use /create-plan).
---

# PR Review Skill

You review code produced by an implementation sprint and generate a review artifact. This is the final quality gate before work is considered done.

**Arguments:** $ARGUMENTS — Plan path, git ref range (e.g. `main..feature-branch`), or nothing (will infer).

## Step 1 — Determine Scope

1. If a plan path is provided, read it — extract the project name and list of changed/created files from completed tasks.
2. If a git ref range is provided, use it directly.
3. If neither, infer scope: run `git log --oneline -20` to find the most recent implementation commits, then determine the base ref (look for the merge-base with `main` or the branch point).
4. Run `git diff --name-only {base}...HEAD` to get the full list of changed files.
5. Filter out non-code files (markdown docs, config that wasn't part of the implementation, lock files).

## Step 2 — Read Context

1. If a plan path was provided or can be found, read the plan to understand **intent** — what was the code supposed to do?
2. Read the project's `CLAUDE.md` and `lessons.md` if they exist — these contain project-specific patterns and known pitfalls.
3. Note the languages and frameworks in use from the file extensions and imports.

## Step 3 — Review Each File

For each changed file, read the full file and evaluate:

- **Code quality:** Duplication, dead code, naming inconsistency, unnecessary complexity, functions that are too long.
- **Security:** Injection risks (SQL, command, XSS), hardcoded credentials or secrets, missing input validation at system boundaries, insecure defaults.
- **Consistency:** Does the code follow existing patterns in the codebase? Check neighboring files for conventions (naming, error handling, logging style).
- **Test coverage:** Are there tests for the new code? If the project has tests, are the new paths covered? Flag untested public functions.
- **Documentation:** Do public APIs and exported functions have clear interfaces? Are complex algorithms explained?

Mark each issue with a severity:
- **Critical (C):** Security vulnerability, data loss risk, or logic bug that will cause failures.
- **Warning (W):** Code smell, missing test, or inconsistency that should be fixed but won't break anything.
- **Info (I):** Style nit, minor improvement, or suggestion — fix if convenient.

## Step 4 — Generate Review Artifact

Create the review artifact at `{project_reviews_dir}/ARE - {Plan Name} Code Review.md` with this structure:

```yaml
---
date created: {today}
tags: [code-review, {project-tag}]
category: Report
status: complete
plan: "[[{plan filename}]]"
---
```

Sections:
1. **Summary** — One paragraph: what was built, how many files changed, overall quality assessment.
2. **Files Reviewed** — Table: filename, lines changed, issue count by severity.
3. **Issues** — Numbered list grouped by severity (Critical first, then Warning, then Info). Each issue: file, line range, description, suggested fix.
4. **Positive Notes** — Call out things done well: good patterns, solid test coverage, clean abstractions.
5. **Verdict** — One of: `Ready to merge`, `Merge after fixes`, `Needs rework`. With a one-line explanation.

## Step 5 — Present Summary

Show the user:
- Total files reviewed
- Issue counts by severity (C/W/I)
- The verdict
- Link to the review artifact

If there are Critical issues, list them inline — don't make the user open the file.

## Step 6 — Offer Fixes

If there are non-controversial fixes (dead imports, unused variables, naming inconsistencies, missing type annotations):
1. Group them and present via `AskUserQuestion` with `multiSelect: true`: "I can auto-fix these. Select which to apply:"
2. Apply selected fixes directly to the code files.
3. Update the review artifact's Issues section to mark applied fixes as `[FIXED]`.

Do NOT auto-fix logic changes, architectural decisions, or anything that changes behavior. Those require human judgment.
