---
name: orient
description: >-
  Get oriented in the current project or Obsidian vault — read agent configs, guardrails,
  vault structure, and lessons learned. Use this skill at the start of any new session,
  after context compaction, when entering an unfamiliar project directory, or when the user
  says "orient", "get oriented", "what's the context here", "read the agents file", or
  "start up". Also trigger on /orient with no arguments. Even continued sessions count as
  new starts after compaction — always re-read the config chain.
---

# Orient — Session Startup & Context Loading

Load the configuration files that tell you how to behave in this workspace. Without this step, you'll miss project-specific rules, interaction preferences, and lessons that prevent repeated mistakes.

This matters because agent config files form a chain — root AGENTS.md may reference project-level agents.md files, which reference lessons files. Missing any link means you'll violate rules you didn't know existed or repeat mistakes that were already captured.

## Steps

Do all of these before responding to the user:

1. **Date/time** — Run `date` to anchor your context temporally

2. **Root agent config** — The workspace root config is `CLAUDE.md` (loaded automatically by Claude Code). Read `Work Vault/agents.md` for vault-wide behavioral rules (daily note formatting, pickup verification, closeout and EOD procedures) and `Work Vault/CLAUDE.md` for vault structure and routing. Follow any directives they contain.

3. **Style guardrails** — Read whatever interaction preference files are referenced (e.g., `04_Reference/Agents/General Style Guardrails.md`). These contain mandatory interaction rules (question format, response style, tool usage patterns), not optional suggestions.

4. **Vault/project structure** — Read the vault structure and routing table in `Work Vault/CLAUDE.md` to understand the file tree and folder purposes. This prevents you from creating files in wrong locations or missing existing work.

5. **Project agent configs** — Discover project-specific agents.md files:
   a. If your current working directory is inside a project, read its `agents.md` directly.
   b. If at the vault root (common), check the SOD's "Open Work" section (loaded in step 7) for project names, then read `agents.md` for those projects under `Work Vault/02_Projects/`.
   c. If the user states what they want to work on before orient completes, read that project's `agents.md` immediately.
   Do not enumerate all 30+ project agents.md files — only load the ones relevant to today's likely work.

6. **Lessons files** — Read `Work Vault/04_Reference/REF - Agent Lessons.md` (cross-project lessons) and any project-specific `lessons.md` for active projects (from step 5). For each lesson:
   - Check if its trigger condition matches today's likely work (based on SOD priorities and open PICs)
   - If it matches, flag it as an **active constraint** — not background reading
   List activated lessons in your response as "Active constraints: L#, L#" with one-line summaries.

7. **Period reports** — Read these from `Work Vault/01_Notes/Reports/` to understand what's been happening and what Holden's priorities are. Read in parallel:
   - **SOD** (daily context): Most recent file in `Reports/SOD/`. Check today first, fall back to most recent. This has the WTD summary, priorities, open PICs, and suggested start.
   - **Stale SOD check**: If the most recent SOD is more than 1 workday old (e.g., it's Wednesday but the latest SOD is from Monday), warn: "⚠️ SOD is stale ({date}). The EOD/closeout chain may have been skipped. Today's context may be incomplete — check daily notes for {missing dates} to fill gaps."
   - **EOW** (last week): Most recent file in `Reports/EOW/`. This is the weekly rollup — what shipped, goal progress, retro findings, and next-week setup.
   - **SOM** (monthly objectives): Current month's file in `Reports/SOM/` (e.g., `SOM - 2026-03.md`). This has Holden's monthly objectives that should frame all work.
   - **EOM** (last month): Most recent file in `Reports/EOM/`. This has the prior month's retrospective and carry-forwards.

   Skip any that don't exist. The SOD is the most important — it's the freshest context. The others provide progressively wider framing.

8. **Cross-reference reports with open work** — This step prevents wasted investigation. After reading the SOD and EOW:
   - For each open PIC in the SOD, check whether the EOW mentions the same system, pipeline, or project as recently shipped/deployed/built
   - If the EOW says "X was built/deployed" and a PIC says "X is broken" — the first hypothesis should be a deployment regression (lost env var, missed config, container rebuild), NOT that the system needs to be reverse-engineered
   - Flag any matches in your orient summary: "PIC [topic] touches [system] which was shipped [date per EOW] — check deployment state before investigating from scratch"

   This exists because agents repeatedly waste time re-discovering systems that were built days ago. The reports already contain the context — the failure is in not connecting it to the current task. (See L18 in Agent Lessons.)

9. **Vault health** _(optional)_ — If an Obsidian CLI is available, run health checks (unresolved links, orphan notes, tag distribution) and note any findings.

## Response Format

After loading, give a short summary:
- Which files you read
- Current date
- Active projects or context from local agent configs
- **Report ↔ PIC cross-references** — any open PICs that touch systems the EOW says were recently built/deployed (flag these prominently — they're likely deployment regressions, not new investigations)
- **Active constraints** — lessons whose trigger conditions match today's work (L#: one-line summary for each)
- Any stale SOD warnings
- Any vault health issues found
- Ask what the user wants to work on

Keep the summary concise — the user doesn't need a recitation of everything you read, just confirmation you loaded context and any standout items.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
