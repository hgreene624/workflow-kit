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

This matters because agent config files form a chain — root AGENTS.md may reference project-level CLAUDE.md files, which reference lessons files. Missing any link means you'll violate rules you didn't know existed or repeat mistakes that were already captured.

## Path Resolution

Before using any vault paths below, read `~/.claude/wfk-paths.json`. If it exists, use `vault_root` and the `paths` object to resolve all directory references. For example, `{vault_root}/{paths.reports}/SOD/` instead of hardcoded paths. If the file doesn't exist, fall back to the defaults written in these instructions and warn the user: "No wfk-paths.json found. Run `/setup` to create one, or create `~/.claude/wfk-paths.json` manually. Using default paths."

## Steps

Do all of these before responding to the user:

1. **Date/time** — Run `date` to anchor your context temporally

1b. **Validate vault paths** — Read `~/.claude/wfk-paths.json`. For each entry in `paths`, check that `{vault_root}/{path}` exists as a directory (use `ls`). If any path is missing:
   - Report which paths are stale: "Path config drift: `{key}` points to `{path}` but directory doesn't exist."
   - Offer to fix: "Want me to update wfk-paths.json with the correct paths?"
   - If the user confirms, scan the vault root for the closest matching directory and update the config.
   - Update `last_validated` to today's date after a successful check.
   
   If `wfk-paths.json` doesn't exist, skip validation and warn once (see Path Resolution above). Don't ask again during this session.

2. **Root agent config** — Read `AGENTS.md` in the workspace root. This is the master configuration that defines how all agents should behave in this vault. Follow any "read this first" directives it contains.

3. **Style guardrails** — Read whatever interaction preference files AGENTS.md points to. These contain mandatory interaction rules (question format, response style, tool usage patterns), not optional suggestions.

4. **Vault/project structure** — Read any structure reference doc to understand the file tree and folder purposes. This prevents you from creating files in wrong locations or missing existing work.

5. **Local agent config** — If your current working directory is different from the vault root, check for a local `CLAUDE.md`. Project-level configs add constraints and context on top of the root config.

6. **Lessons files** — Read the general lessons file (cross-project lessons) and any local `lessons.md` in the current project. These are hard-won knowledge from past sessions — ignoring them means repeating the same mistakes.

7. **Period reports** — Read these from `Work Vault/01_Notes/Reports/` to understand what's been happening and what Holden's priorities are. Read in parallel:
   - **SOD** (daily context): Most recent file in `Reports/SOD/`. Check today first, fall back to most recent. This has the WTD summary, priorities, open PICs, and suggested start.
   - **EOW** (last week): Most recent file in `Reports/EOW/`. This is the weekly rollup — what shipped, goal progress, retro findings, and next-week setup.
   - **SOM** (monthly objectives): Current month's file in `Reports/SOM/` (e.g., `SOM - 2026-03.md`). This has Holden's monthly objectives that should frame all work.
   - **EOM** (last month): Most recent file in `Reports/EOM/`. This has the prior month's retrospective and carry-forwards.

   Skip any that don't exist. The SOD is the most important, it's the freshest context. The others provide progressively wider framing.

7b. **Strategic context** — Read the current Roadmap and Weekly Focus to understand what goals are driving all work:
   - **RM** (roadmap): Most recent file in `01_Notes/Roadmaps/`. This maps all active work to strategic goals, defines what's parked, and provides decision rules for incoming requests. It is the "why" behind every PIC and SOD priority.
   - **WF** (weekly focus): Most recent file matching `WF - *.md` in the latest dated subfolder of `Reports/`. This names the 3 goals for the current week and lists what's explicitly not this week.

   If both exist, present a brief strategic summary in the orient output: "Active goals: [goal 1], [goal 2], [goal 3]. [N] open PICs aligned. [M] parked." This anchors the session in strategy, not just tasks.

8. **Cross-reference reports with open work** — This step prevents wasted investigation. After reading the SOD and EOW:
   - For each open PIC in the SOD, check whether the EOW mentions the same system, pipeline, or project as recently shipped/deployed/built
   - If the EOW says "X was built/deployed" and a PIC says "X is broken" — the first hypothesis should be a deployment regression (lost env var, missed config, container rebuild), NOT that the system needs to be reverse-engineered
   - Flag any matches in your orient summary: "PIC [topic] touches [system] which was shipped [date per EOW] — check deployment state before investigating from scratch"

   This exists because agents repeatedly waste time re-discovering systems that were built days ago. The reports already contain the context — the failure is in not connecting it to the current task. (See L18 in Agent Lessons.)

   **8a. Recent Infrastructure Changes** — Scan the EOW and SOD for any infrastructure-changing events and produce a compact checklist block in your orient summary. Extract:
   - Containers added, removed, renamed, or replaced
   - Apps migrated or sunset (old location -> new location)
   - Routes changed (new paths, removed paths, domain changes)
   - Compose files modified or relocated

   Format as a reference block the agent can check when encountering VPS artifacts:

   ```
   ## Recent Infrastructure Changes (from EOW/SOD)
   - [container] added/removed/replaced — [context]
   - [app] migrated from [old] to [new] — old artifacts are stale
   - [route] changed: [description]
   ```

   If no infrastructure changes are found in the reports, omit this block. This prevents the "investigate unknown system from scratch" failure mode — anything listed here is already known context, not a mystery to solve.

   **8b. REF doc staleness check** — After building the infrastructure changes list, spot-check `REF - VPS Work Rules.md` against the EOW for obvious drift:
   - Does the App Location Map list containers that the EOW says were sunset or replaced?
   - Does the Docker Compose Projects table reference paths that were removed or relocated?
   - Are there entries for services that no longer exist per the EOW?

   If mismatches are found, flag them prominently in the orient summary:
   ```
   ⚠ VPS Work Rules drift detected:
   - [container X] listed in App Location Map but sunset per EOW W[n]
   - [path Y] in Docker Compose Projects table but removed per EOW
   ```

   This catches documentation drift proactively at session start, before the agent encounters stale artifacts during work and wastes time investigating them.

9. **Vault health** _(optional)_ — If an Obsidian CLI is available, run health checks (unresolved links, orphan notes, tag distribution) and note any findings.

## Response Format

After loading, give a short summary:
- Which files you read
- Current date
- Active projects or context from local agent configs
- **Report ↔ PIC cross-references** — any open PICs that touch systems the EOW says were recently built/deployed (flag these prominently — they're likely deployment regressions, not new investigations)
- **Recent Infrastructure Changes** — the checklist from Step 8a (if any infrastructure changes were found in reports)
- **REF doc drift warnings** — any staleness mismatches found in Step 8b
- Key lessons that seem relevant to whatever work is coming
- Any vault health issues found
- Ask what the user wants to work on

Keep the summary concise — the user doesn't need a recitation of everything you read, just confirmation you loaded context and any standout items.
