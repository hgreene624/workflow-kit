---
name: review-spec
description: >
  Dispatch a team of agents to critically review a spec document (SPC - *.md). Evaluates scope
  and impact on the actual environment, loads all relevant context (lessons, references, related
  specs, agents.md), and flags issues, gotchas, and clarification needs. Use this skill whenever
  the user wants to review a spec, evaluate a spec before implementation, get critical feedback
  on a spec, or says anything like "review this spec", "evaluate this spec", "what are the risks
  in this spec", "is this spec ready". Also trigger when the user passes a SPC file path and
  wants feedback before planning. This skill focuses on review only — use /plan-spec afterward
  to produce the plan document and Plane project.
---

# Spec Review Skill

You are orchestrating a 3-agent team that critically evaluates a spec before it becomes a plan. The goal is to catch issues, surface gotchas, and get user buy-in on open questions — not rubber-stamp the spec and rush to planning.

This is the first half of a two-skill workflow:
1. **`/review-spec`** (this skill) — analyze, critique, get clarification
2. **`/plan-spec`** — produce plan document + Plane project (run after review issues are resolved)

## Invocation

```
/review-spec <path-to-spec>
```

The spec path can be relative to the vault root or absolute. If no path is given, ask the user which spec to review.

## Step 0 — Orient & Infer Project

Before dispatching the team:

1. Read the spec file to understand what's being proposed
2. Infer the project from the spec's location in the vault directory tree:
   - `01_Work/03_Projects/<ProjectName>/` → that's your project
   - Also check for sub-projects (e.g., `Flora Hub/`, `Inbox Triage/`, `Signal Engine/` under FWIS)
3. Check for `agents.md` and `lessons.md` in that project directory
4. Read the vault-root `AGENTS.md` file, then the project-level `agents.md` if one exists — these contain critical context about how work should be done in that project

## Step 1 — Dispatch the Team

Use `TeamCreate` to spin up three agents in tmux panes. The user needs to be able to monitor each agent's progress.

### Agent 1: Scope Analyst

**Purpose:** Map the blast radius of the spec — what does this change touch?

**Instructions for the agent:**

> You are the Scope Analyst. Your job is to map every system, file, service, API, database table, and infrastructure component that this spec would affect if implemented.
>
> **Read the spec at:** `{spec_path}`
>
> **Then investigate the actual environment:**
> 1. If the project has a local codebase (check `agents.md` for repo path), explore it:
>    - Which files/modules would need changes?
>    - What existing code does similar things that could be reused or would conflict?
>    - Are there tests that would need updating?
> 2. If the project involves VPS infrastructure (check `agents.md` for VPS paths), SSH in and check:
>    - Running containers and their resource usage
>    - Existing config files that would need modification
>    - Database schemas that would be affected (`\d tablename` in postgres)
>    - Available disk/RAM/CPU headroom
> 3. Map dependencies — what other systems does this touch? (APIs, external services, shared databases, Traefik routing, etc.)
>
> **Output:** Write a scope analysis to `{workspace}/ARE - {spec_name} Scope Analysis.md` with sections:
> - **Affected Components** (table: Component | Type | Impact | Notes)
> - **Resource Requirements** (disk, RAM, new containers, new domains)
> - **Dependency Map** (what this connects to, upstream and downstream)
> - **Risk Surface** (what could break during implementation)
>
> Keep it factual — no opinions on whether the spec is good, just what it touches.

### Agent 2: Context Researcher

**Purpose:** Gather all relevant context that the Critical Reviewer will need to evaluate this spec properly.

**Instructions for the agent:**

> You are the Context Researcher. Your job is to find and compile every piece of context that's relevant to evaluating this spec — lessons learned, reference docs, related specs and plans, past reports, and architectural decisions.
>
> **Read the spec at:** `{spec_path}`
>
> **Then gather context from these sources:**
>
> 1. **Lessons files** — Read `lessons.md` in the project directory AND in parent/sibling project directories. Also check `04_ Tools/Reference/REF - Project Planning Lessons.md` and `04_ Tools/Reference/REF - Agent Lessons.md`. Extract every lesson that's relevant to what this spec proposes.
>
> 2. **Reference files** — Search for `REF - *.md` files in the project directory and `04_ Tools/Reference/`. Read any that relate to the technologies, patterns, or infrastructure mentioned in the spec.
>
> 3. **Related specs and plans** — Search for other `SPC - *.md` and `PL - *.md` files in the same project. Read them to understand:
>    - What's already been specced/planned that this overlaps with
>    - What's currently in progress that could conflict
>    - What architectural decisions have already been made
>
> 4. **Past reports** — Check the project's `Reports/` directory for recent reports that provide context (audit results, incident reports, evaluation results).
>
> 5. **Workflow docs** — Read relevant workflows from `Documentation/Agent Workflows/` (Feature Development Workflow, Project Spec Workflow, Project Plan Workflow).
>
> 6. **Memory** — Check `~/.claude/projects/-Users-holdengreene-Library-Mobile-Documents-iCloud-md-obsidian-Documents-Personal-Vault/memory/` for any memory files relevant to this project.
>
> **Output:** Write a context brief to `{workspace}/ARE - {spec_name} Context Brief.md` with sections:
> - **Applicable Lessons** (lesson ID, source file, relevance to this spec)
> - **Related Specs & Plans** (file, status, overlap/conflict with this spec)
> - **Architectural Constraints** (decisions already made that this spec must respect)
> - **Historical Context** (past incidents, reports, or patterns relevant here)
> - **Key References** (files the reviewer should read directly)
>
> Prioritize — put the most impactful context first. If a lesson directly contradicts something in the spec, flag it prominently.

### Agent 3: Critical Reviewer

**Purpose:** Synthesize the scope analysis and context brief into a critical evaluation of the spec.

**This agent must wait for Agents 1 and 2 to complete before starting its main work.** It can begin by reading the spec and the project's agents.md, but should not start the review until the scope analysis and context brief are available.

**Instructions for the agent:**

> You are the Critical Reviewer. You synthesize the Scope Analyst's findings and the Context Researcher's brief into a thorough evaluation of the spec.
>
> Read:
> - The spec at `{spec_path}`
> - The scope analysis at `{workspace}/ARE - {spec_name} Scope Analysis.md`
> - The context brief at `{workspace}/ARE - {spec_name} Context Brief.md`
> - Any files flagged as "key references" in the context brief
>
> Evaluate the spec against these criteria:
>
> 1. **Completeness** — Are there gaps in the spec? Missing acceptance criteria? Undefined behavior at boundaries? Unaddressed edge cases?
> 2. **Feasibility** — Given the scope analysis, is this realistic? Are resource requirements acknowledged? Are there hidden infrastructure costs?
> 3. **Conflicts** — Does this contradict existing architectural decisions, lessons learned, or in-progress work?
> 4. **Gotchas** — Based on lessons and past incidents, what's likely to go wrong? What has gone wrong before in similar work?
> 5. **Scope creep risk** — Is the spec tightly scoped or does it invite unbounded work?
> 6. **Dependency risks** — Are there external dependencies that could block progress? Ordering constraints that aren't documented?
> 7. **Reality check** — Does the spec match the current state of the codebase and infrastructure? Are assumptions still valid? Has work already been done that the spec doesn't account for?
> 8. **Clarification needs** — What questions must the user answer before this spec can be planned? What ambiguities would lead different developers to make different choices?
>
> Write the evaluation to `{workspace}/ARE - {spec_name} Spec Review.md` with this exact structure and frontmatter:
>
> ```markdown
> ---
> category: Review
> date created: {today}
> source: "review-spec skill — Critical Reviewer"
> spec: "[[{spec_filename}]]"
> ---
>
> # Spec Review: {spec_name}
>
> ## Spec Quality Score
>
> | Criteria | Rating | Notes |
> |----------|--------|-------|
> | Completeness | {0-3} | {gaps?} |
> | Feasibility | {0-3} | {resource/scope issues?} |
> | Clarity | {0-3} | {ambiguities?} |
> | Scope Control | {0-3} | {creep risk?} |
> | **Total** | **{N}/12** | |
>
> **Gate:** {PASS (0 Critical issues, score >= 8) | CONDITIONAL (0 Critical, score 5-7, warnings to address) | FAIL (any Critical issues OR score < 5)}
>
> ## Summary Verdict
> {1-2 sentences: ready to plan? needs revision? needs clarification?}
>
> ## Clarifications Needed
> {MANDATORY section — even if empty, include it with "None — spec is clear enough to plan."}
> {These are questions whose answers will change the shape of the plan. They are NOT the same as issues.}
> {An issue is a problem with the spec. A clarification is a decision the user needs to make.}
> {Format each as: **CL-N: [question]** with 1-2 sentences of context explaining why this matters for planning.}
> {Examples:}
> {- "Should this be a gap-fill of the existing implementation or a fresh build?" (changes phase structure)}
> {- "Which auth system should new endpoints use?" (changes dependency chain)}
> {- "Is the backfill a one-time operation or recurring?" (changes whether we need a cron job)}
>
> ## Issues
> {Numbered by severity: Critical first, then Warning, then Info}
> {Each issue: ID (C1/W1/I1), title, affected spec section, description, concrete suggestion}
>
> ## Suggested Spec Improvements
> {Specific text changes or additions — not vague recommendations}
> {Number them so the user can say "apply 1, 3, and 5"}
>
> ## Gotchas & Lessons to Watch
> {Table: Lesson | Spec Section | Risk}
> {Map specific lessons from the context brief to specific spec sections}
> ```
>
> The distinction between **Clarifications** and **Issues** is important because they drive different actions: clarifications become AskUserQuestion prompts that the user answers interactively, while issues are problems the user can address by editing the spec. Don't conflate them.

## Workspace

Create a workspace for the review artifacts:

```
{project_dir}/reviews/{date}/
├── ARE - {spec_name} Scope Analysis.md      (Agent 1 output)
├── ARE - {spec_name} Context Brief.md       (Agent 2 output)
└── ARE - {spec_name} Spec Review.md         (Agent 3 output)
```

**CRITICAL — File naming:** All output files MUST use the exact `ARE - {spec_name} ...` prefix format shown above. Do NOT use slugified names like `spec-review-foo.md` or `context-brief.md`. The `ARE -` prefix is a vault-wide convention that enables Obsidian linking, search, and routing. When dispatching agents, include the full target filename in the prompt so agents write to the correct path.

## Step 2 — Present Findings & Get Clarification

Once all three agents finish:

1. Read the spec review (`ARE - {spec_name} Spec Review.md`)
2. Summarize the key findings for the user — verdict, issue count by severity, top gotchas
3. If the review found **Clarifications Needed**, present them one at a time using `AskUserQuestion`. Each clarification is a decision that changes the shape of the plan:
   - "The spec mentions a new API endpoint but doesn't specify auth. Should it use the existing JWT flow or the new unified auth?"
   - "This overlaps with the Sales Context Panel spec. Should they share a backend service or stay independent?"
4. Record the user's answers by appending a **Clarification Log** section to `ARE - {spec_name} Spec Review.md`:
   ```
   ## Clarification Log

   **CL-1:** [question]
   **Answer:** [user's answer] (2026-03-13)

   **CL-2:** [question]
   **Answer:** [user's answer] (2026-03-13)
   ```

## Step 3 — Apply Spec Improvements (L23: No Double-Confirmation)

After clarifications are resolved, apply improvements efficiently. **Do NOT re-ask the user to confirm decisions they already made.**

**Flow:**

1. **Auto-apply clarification-linked improvements.** Any improvement that directly implements a clarification answer the user already gave in Step 2 is applied immediately — no second ask. The user already decided; applying is just executing that decision.

2. **Present remaining improvements in ONE pass.** Collect all improvements NOT linked to a clarification answer. Present them in a single `AskUserQuestion` with `multiSelect: true`, grouped by severity in the description but as one list:
   > "Review found {N} additional improvements. Which should I apply?"
   > Options: each numbered improvement with its severity tag (e.g., "[W] Add rollback strategy", "[I] Fix typo in OD-5")

   If there are no remaining improvements (all were clarification-linked), skip this step entirely.

3. **Apply all approved changes** to the spec file. Record everything in `ARE - {spec_name} Spec Review.md` under an **Applied Changes** section:
   ```
   ## Applied Changes

   - [x] #1: Updated Assumption A1 (auto-applied — implements CL-1)
   - [x] #2: Added rollback strategy (auto-applied — implements CL-3)
   - [x] #4: Added confidence thresholds (user-approved)
   - [ ] #3: Add Acceptance Criteria section (skipped by user)
   ```

4. **Enforce the quality gate:**
   - **PASS** (0 Critical, score >= 8): "Spec is ready for `/plan-spec`."
   - **CONDITIONAL** (0 Critical, score 5-7): "Spec can proceed to `/plan-spec` but has warnings worth addressing. Proceed anyway?"
   - **FAIL** (any Critical issues OR score < 5): "Spec is not ready for planning. {N} Critical issues must be resolved first." Do NOT suggest proceeding to `/plan-spec`.

## What This Skill Does NOT Do

- It does not produce a plan document — that's `/plan-spec`
- It does not create Plane projects or issues — that's `/plan-spec`
- It does not implement the spec
- It does not make architectural decisions — it flags decisions that need to be made
- It does not modify the spec without user approval

## Handoff to /plan-spec

When the user is ready to plan, they run:
```
/plan-spec <path-to-spec>
```

The plan-spec skill will automatically look for review artifacts in `Reviews/{date}/` and use them to inform the plan. Clarification answers from the log directly shape phase structure, task dependencies, and risk mitigations in the plan.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
