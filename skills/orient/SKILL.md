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

1a. **Machine detection** — Run `system_profiler SPHardwareDataType` (macOS) or equivalent to identify the current hardware. Include the machine name in your orient summary so path assumptions are correct for the session. If the hardware doesn't match any known machine, report it and ask.

1c. **Orphan agent detection (three-check sweep)** — A tmux-only check is insufficient. `claude --dangerously-skip-permissions` workers don't require tmux — they run in any tty and carry a full Bash / SSH / shell tool surface, so a worker spawned outside tmux (or from a session that has since ended) is invisible to a tmux scan. Run three checks at session start; report each category distinctly.

   ```bash
   # (a) STALE TEAM DIRS — tmux session died, team config survived on disk
   if ! tmux list-sessions >/dev/null 2>&1; then
     for d in ~/.claude/teams/*/; do
       [ -d "$d" ] || continue
       echo "STALE-TEAM-DIR: $(basename "$d") (mtime: $(stat -f %Sm -t %Y-%m-%d "$d"))"
     done
   else
     for team in ~/.claude/teams/*/; do
       [ -d "$team" ] || continue
       lead=$(jq -r '.leadSessionId // empty' "$team/config.json" 2>/dev/null)
       [ -z "$lead" ] && continue
       tmux has-session -t "$lead" 2>/dev/null || \
         echo "STALE-TEAM-DIR: $(basename "$team") (lead: $lead, mtime: $(stat -f %Sm -t %Y-%m-%d "$team"))"
     done
   fi

   # (b) LIVE LOCAL CLAUDE PROCESSES — catches non-tmux workers and concurrent sessions
   ps -ef | grep -E 'claude.*--team-name|claude.*--dangerously-skip-permissions' | grep -v grep | head -20

   # (c) LIVE REMOTE CLAUDE PROCESSES (optional) — if you have known production SSH targets,
   #     run the same check against each via a multiplexed SSH call. Configure your targets in
   #     LOCAL.md (an array of SSH aliases). High-risk: a worker running against production has
   #     full ssh / docker exec / db-client tool surface.
   #
   # Example (uncomment and customize per LOCAL.md):
   # for host in <your-ssh-aliases>; do
   #   ssh -o ConnectTimeout=5 "$host" "ps -ef | grep -E 'claude.*--team-name|claude.*--dangerously-skip' | grep -v grep" 2>/dev/null | head -20
   # done
   ```

   Report all three categories separately in the orient summary. They mean different things:

   - **(a) Stale team dirs.** Often harmless (a team dir on disk after its tmux session died). For each, report team name, mtime, worker count from `config.json`. If 5+ exist, recommend a batch cleanup. Per-orphan cleanup: archive any non-empty worker inbox, then `rm -rf ~/.claude/teams/<name>/ ~/.claude/tasks/<name>/`. Always ask before destructive cleanup. This prevents the failure mode where the agent assumes a team is reachable, sends `SendMessage`, sees `success: true`, and waits forever for responses that will never come.

   - **(b) Live local Claude processes.** Could be active concurrent sessions OR cross-session orphans from prior closeouts. The agent cannot tell from `ps` alone — surface to the operator and ask whether to leave alone or treat as orphans. Do NOT auto-kill: killing other sessions' workers can destroy in-flight work. Show `--team-name`, `--parent-session-id`, start time, and tty for each match.

   - **(c) Live remote Claude processes.** **Highest risk.** Any match means an agent with shell / SSH / db-client capability is running against your production target. Surface immediately and recommend the operator confirm whether each is owned by an active session. Do NOT auto-kill.

   **When ANY live match (b or c) appears: escalate to operator in the orient summary before continuing.** Detection's only purpose is to surface; cleanup decisions require operator authorization. (Background: a parallel-`docker exec` agent-cluster from cross-session orphans took down a production VPS in May 2026; the recovery established that orphan-sweep at session start is mandatory, not best-effort.)

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

7. **Period reports** — Read the operative chain from your reports directory to understand current priorities and recent history. These are agent-facing context documents per the Period Reporting System. Read in parallel:
   - **SOD** (daily context): Most recent file in `Reports/SOD/`. Check today first, fall back to most recent. Has WTD summary, priorities (inherited from WRM goals), open PICs, and suggested start directive.
   - **WRM** (weekly goals): Most recent file in `Reports/WRM/`. Has 3 weekly goals with done criteria, in/out scope lists, and directives from EOW retro. Constraints flow down from MRM.
   - **MRM** (monthly objectives): Current month's file in `Reports/MRM/` (e.g., `MRM - 2026-05.md`). Has 3-5 monthly objectives with done definitions, decision rules, systemic landing zones, and carry-forward. This is the highest-level strategic frame.
   - **EOW** (last week): Most recent file in `Reports/EOW/`. Weekly rollup with pattern-level retro and insight routing.
   - **EOM** (last month): Most recent file in `Reports/EOM/`. Monthly retrospective and systemic diagnosis.

   Skip any that don't exist. The SOD is the most important (freshest context). WRM and MRM provide the strategic frame. EOW and EOM provide wider historical context.

   If MRM and WRM both exist, present a brief strategic summary in the orient output: "Weekly goals: [goal 1], [goal 2], [goal 3] (from WRM W{ww}). MRM objectives: [obj 1], [obj 2], ... [N] open PICs aligned, [M] unaligned." This anchors the session in strategy, not just tasks.

   **Missing document flags:** If any operative document is missing, flag it prominently:
   - No MRM for current month: "No MRM found for {YYYY-MM}. Run /end-day on the last workday of the month to generate one."
   - No WRM for current week: "No WRM found for W{ww}. Run /end-day on Friday to generate one."
   - No SOD for today: "No SOD for today. Run /end-day yesterday or backfill."

8. **Recent Infrastructure Changes** — Scan the EOW and SOD for any infrastructure-changing events and produce a compact checklist block in your orient summary. Extract:
   - Containers added, removed, renamed, or replaced
   - Apps migrated or sunset (old location -> new location)
   - Routes changed (new paths, removed paths, domain changes)
   - Compose files modified or relocated

   Format as a reference block the agent can check when encountering infrastructure artifacts:

   ```
   ## Recent Infrastructure Changes (from EOW/SOD)
   - [container] added/removed/replaced — [context]
   - [app] migrated from [old] to [new] — old artifacts are stale
   - [route] changed: [description]
   ```

   If no infrastructure changes are found in the reports, omit this block. This prevents the "investigate unknown system from scratch" failure mode — anything listed here is already known context, not a mystery to solve.

   **8a. REF doc staleness check** — After building the infrastructure changes list, spot-check your infrastructure reference docs against the EOW for obvious drift:
   - Does the app location map list containers that the EOW says were sunset or replaced?
   - Does the infrastructure config reference paths that were removed or relocated?
   - Are there entries for services that no longer exist per the EOW?

   If mismatches are found, flag them prominently in the orient summary:
   ```
   Infrastructure ref doc drift detected:
   - [container X] listed in app location map but sunset per EOW W[n]
   - [path Y] in infrastructure docs but removed per EOW
   ```

   This catches documentation drift proactively at session start, before the agent encounters stale artifacts during work and wastes time investigating them.

9. **Vault health** _(optional)_ — If an Obsidian CLI is available, run health checks (unresolved links, orphan notes, tag distribution) and note any findings.

## Response Format

Orient reports loaded state. It does NOT propose next actions, recommend PICs, summarize "Suggested Start" content from the SOD as if it were the orient's recommendation, or ask the user what to work on. That is `/pickup`'s job. If the SOD contains a "Suggested Start" section, mention that it exists (link or reference it) but do not restate or extend it.

After loading, give a short summary:
- Which files you read
- Current date and machine
- Active projects or context from local agent configs
- **Operative chain status** — what SOD/WRM/MRM/EOW/EOM were loaded, and any missing-document flags
- **Recent Infrastructure Changes** — the checklist from Step 8 (if any infrastructure changes were found in reports)
- **REF doc drift warnings** — any staleness mismatches found in Step 8a
- **Path / vault-health flags** — anything surfaced during validation
- **Orphan sweep** — report the three categories from Step 1c distinctly:
  - **(a) Stale team dirs:** count + names + mtimes. Harmless unless >5.
  - **(b) Live local Claude processes:** count + each match's `--team-name`, `--parent-session-id`, start time, tty. Surface to operator with the explicit question "active concurrent sessions or orphans?" before continuing. Never auto-kill.
  - **(c) Live remote Claude processes:** count + each match. HIGHEST priority surface. Recommend the operator confirm ownership before proceeding.
- Stop. Do not propose work; do not ask what to work on; do not present an `AskUserQuestion` about next steps. The only `AskUserQuestion` orient may issue is the live-process triage in 1c when category (b) or (c) returns matches. If the user wants to pick up work, they will run `/pickup`.

Keep the summary concise — the user doesn't need a recitation of everything you read, just confirmation you loaded context and any standout items.
