---
name: create-spec
description: >
  Create or update a spec document (SPC - *.md) through a guided workflow. For new ideas, runs a full
  interview, determines vault placement, drafts all 11 sections, and gates with review-spec. For existing
  specs, triages whether the idea belongs under an existing spec and handles surgical updates — appending
  new FRs, expanding scope, and propagating changes to downstream plans and Plane projects.
  MUST trigger whenever the user wants to create, write, draft, or update a spec — including phrases like
  "spec this out", "turn this into a spec", "I have an idea for", "let's spec", "new spec for",
  "write a spec", "create a spec", "can we write a spec for", "I want to spec out", "add this to the spec",
  "update the spec with", or describes a feature/system they want to formalize before building. Also trigger
  when the user says they want to "formalize" an idea, "define requirements" for something new, or asks to
  "document what we want to build". Even casual requests like "ok so dad wants X, can we spec that?" should
  trigger this skill. Does NOT trigger for reviewing existing specs without changes (use review-spec) or
  planning from specs (use plan-spec). Also works in agent mode when another agent passes structured
  requirements.
---

# Spec Creator (Router)

This skill routes between two sub-flows based on whether the user is creating a new spec or updating an existing one. The user-facing command is always `/create-spec`.

## Step 0 — Orient

1. Run `date` for a fresh timestamp
2. Read the vault-root `AGENTS.md` to understand current vault conventions
3. If the user mentioned a project or you can infer one from context, read that project's `agents.md` and `lessons.md` if they exist

## Step 1 — Detect Audience

- **Interactive mode**: The user is talking to you directly. Use `AskUserQuestion` for every question. One question at a time, numbered options.
- **Agent mode**: Invoked programmatically with structured purpose, requirements, and constraints. Skip the interview. If the agent specifies a target spec to update, route to Update; otherwise route to Create.

If unsure, default to interactive.

## Step 2 — Route: Create or Update?

### Routing Manifest

Write a manifest to `/tmp/routing-manifest-create-spec-{timestamp}.json`:
```json
{
  "router": "create-spec",
  "expected": ["create"],
  "completed": [],
  "timestamp": "..."
}
```
Set `expected` to `["create"]` or `["update"]` based on the routing decision below. On sub-flow completion, append the flow name to `completed`. On chain end, verify `expected` matches `completed` — alert if any sub-flow was skipped. Delete the manifest on success.

### Auto-Route (skip triage)

- **User explicitly said "new spec"** → Create flow
- **User explicitly said "add to" or "update" a named spec** → Update flow
- **Agent mode with no target spec** → Create flow
- **Agent mode with target spec specified** → Update flow

### Triage (interactive mode, ambiguous intent)

1. Infer the project area from what the user described
2. Search for existing specs: `Glob: 01_Work/03_Projects/<inferred project>/**/SPC - *.md`
3. If no specs found → Create flow
4. If specs found, read each one's `## 1) Purpose / Objectives` and `## 2) Scope` (just enough to assess)
5. Present options via `AskUserQuestion`:
   > "I found these existing specs. Does your idea fit under one, or is it new?"
   > 1. SPC - [Name] — [one-line summary]
   > 2. SPC - [Name] — [one-line summary]
   > 3. None — this is a new spec
6. User picks existing spec → **Update flow**. User picks "new" → **Create flow**.

### Dispatch

- **Create** → continue to Step 3 below (Create flow is inline)
- **Update** → read `references/update-spec.md` and follow it from Step U1

---

# Create Flow

## Step 3 — Interview (Interactive Mode Only)

Agent mode: skip to Step 4.

### Phase A: What and Why

**Q1: What is this spec for?** Ask the user to describe the feature/system. If they already described it before invoking the skill, confirm rather than re-asking.

**Q2: What does success look like?** Ask for measurable outcomes with relevant examples.

### Phase B: Scope and Constraints

**Q3: What's explicitly OUT of scope?** Offer educated guesses:
> "Based on what you described, which of these are OUT?"
> - Option A: [exclusion]
> - Option B: [exclusion]
> - Option C: All in scope
> - Option D: Different exclusions

**Q4: Any hard constraints?** Pre-populate known constraints from project context.

### Phase C: Requirements Deep-Dive

Walk down the design tree one branch at a time — explore dependencies, edge cases, integration points, and user experience decisions until you can confidently draft all 11 spec sections. One question at a time, adapting based on answers. If a question can be answered by exploring the codebase or project context, do that instead of asking. Stop when you have enough to draft, not after an arbitrary count.

### Phase D: Confirm Understanding

Give a 3-5 bullet summary, then `AskUserQuestion`:
1. Looks good, draft it
2. I want to adjust something

## Step 4 — Research Isolation (FR-16-18)

Before drafting, if you need to research external systems, APIs, schemas, or prior art:

1. **Generate research questions** based on the interview/input — specific, factual queries (e.g., "What columns exist in signals.signals?", "What API endpoints does the portal expose?")
2. **Dispatch a research agent** that receives ONLY the list of questions. The research agent must NOT receive: the spec content, the feature description, the user's answers, or any draft material. It gets questions and returns facts.
3. **Receive facts back** and incorporate them into the draft. This isolation prevents the research agent from being biased by the spec's framing.

Skip research isolation if: the spec is purely conceptual (no external system references), or the agent-mode caller already provided verified facts.

## Step 5 — File Placement

### Placement Logic

1. Check if a project already exists under `01_Work/03_Projects/`
2. If project exists: sub-system → sub-project root; otherwise → project root. Check for overlapping specs.
3. If project doesn't exist: create the directory. Spec goes at its root. Don't create sub-projects preemptively.
4. Naming: `SPC - <Descriptive Name>.md` — Title Case, concise but specific

### Confirm (Interactive)

Show the planned path via `AskUserQuestion`:
1. Yes, that's right
2. Different location

### Confirm (Agent)

Use the caller's path if specified; otherwise apply placement logic and proceed.

## Step 6 — Draft the Spec

Read the template at `references/spec-template.md`.

### Drafting Rules

1. **Fill every section.** All 11 sections must appear. Empty sections signal gaps for the review gate.
2. **Use IDs for everything trackable.** FR-1, NFR-1, A-1, SAT-1, etc.
3. **Frontmatter is mandatory:**
   ```yaml
   ---
   category: Spec
   date created: {today}
   date modified: {today}
   status: Draft v1
   project: "[[{Project Name}]]"
   source: "{what spawned this}"
   ---
   ```
4. **Keep implementation out.** No build phases, deployment steps, or effort estimates.
5. **Entity boundaries.** If the spec processes people/contacts/entities, define inclusion/exclusion rules.
6. **Verify external references.** Check schema, docs, actual systems — don't assume from memory.
7. **Golden examples for quality features.** Embed concrete input → expected output → threshold examples for quality-dependent SATs.
8. **Open Decisions need recommendations.** Never leave the recommendation column blank.

Write the file. Add today's daily note entry under `## Worked on` with a wiki-link to the new spec.

## Step 7 — Review Gate

**Immediately** invoke `/review-spec {spec_path}` — no confirmation needed. This is a mandatory gate. The review-spec skill dispatches 3 agents (Scope Analyst, Context Researcher, Critical Reviewer), presents findings, and applies approved changes. Let it run to completion.

## Step 8 — TLDR & Handoff

1. **TLDR** — 3-5 bullets:
   > - **What:** [one-line purpose]
   > - **Key FRs:** [2-3 most important]
   > - **Scope:** [in/out highlights]
   > - **Open decisions:** [count or "all resolved"]
   > - **Review verdict:** [from review]

2. **Offer plan-spec handoff** via `AskUserQuestion`. Plan-spec now includes built-in design exploration and structure verification — no need to run `/design` or `/structure` separately.
   1. Yes, run /plan-spec now (Recommended)
   2. Not yet — more changes first
   3. Done for now

---

## Error Handling

- **Duplicate spec detected:** If you find an existing spec with overlapping scope during Create, suggest switching to Update instead.
- **Project directory ambiguous:** Present options, let the user decide.
- **Review gate finds critical issues:** Present them honestly — the gate exists to catch problems early.
- **Plan conflict with completed work:** Always flag rework implications before applying changes (Update flow only).

## Checklist — Create Mode

- [ ] All 11 sections present
- [ ] Frontmatter complete (category, dates, status, project, source)
- [ ] IDs on all requirements, assumptions, acceptance criteria
- [ ] No implementation phases or build order in the spec
- [ ] Entity boundaries defined (if applicable)
- [ ] External references verified (if applicable)
- [ ] Golden examples included (for quality-dependent SATs)
- [ ] Open decisions have recommendations
- [ ] File placed at correct project/sub-project root
- [ ] Daily note updated with wiki-link
- [ ] Review gate passed
- [ ] Research isolation used (if external research was needed)

## Checklist — Update Mode

- [ ] New IDs continue from highest existing (no gaps, no reuse)
- [ ] Frontmatter version bumped and date modified updated
- [ ] Change Log entry added with date, version, description, source
- [ ] Contradictions flagged and resolved with user
- [ ] Superseded FRs struck through (not deleted) with reference to replacement
- [ ] Delta review passed
- [ ] Plan updated (if exists): new phase or superseded items cancelled
- [ ] Plane updated (if exists): new issues created, cancelled issues marked
- [ ] Daily note updated with wiki-link noting the update
