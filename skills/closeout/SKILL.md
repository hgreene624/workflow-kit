---
name: closeout
description: End-of-session closeout — log work to the daily note and create pickup docs (PIC) for the next workday. Use this skill when the user says "closeout", "close out", "wrap up", "end of day", "EOD", "wind down", "done for the day", "call it a day", "closing out this session", or wants to finalize a work session and set up tomorrow's context. Also trigger when the user says "create a pickup", "make a PIC", or wants to carry forward work context to the next session. Even casual requests like "ok I'm done" or "wrapping up" at the end of a work session should trigger this skill.
---

# Closeout

You are closing out a work session. Your job is to capture what was done, log it to the daily note, and create pickup documents so a fresh agent tomorrow can hit the ground running without the user having to re-explain everything.

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{paths.daily_notes}/DN - YYYY-MM-DD.md`). If the file doesn't exist, use defaults and warn once.

## Step 0: Roadmap Context

Read the current **RM** (most recent file in `01_Notes/Roadmaps/`) and **WF** (most recent `WF - *.md` in the latest dated subfolder of `Reports/`). Use these to:

1. **Group the session summary by goal** in Step 1d. Instead of a flat list of topics, present work grouped by which strategic goal it served: "Goal A: [work done]. Goal B: [work done]. Off-focus: [work done]." This makes goal-level progress visible at closeout.

2. **Flag off-focus work** when deciding which topics need PICs (Step 3). If a topic doesn't serve any current weekly goal, note it: "This work isn't on the weekly focus. PIC it, or just log to PJL?" This is informational, not a gate. Sometimes reactive work is necessary. The flag just makes the choice conscious.

3. **Pass goal context to /create-pickup** (Step 3). The create-pickup skill has its own capacity gate and goal-tagging. Pass the RM goal name so it can tag the PIC's frontmatter without re-reading the RM.

If no RM or WF exists, skip this step. All downstream behavior works without it.

## Step 0b: PIC State Snapshot (MANDATORY)

Before logging work or deciding what needs new PICs, scan the current PIC landscape. This prevents duplicate PICs, catches PICs closed by parallel sessions, and shows what's already tracked.

**Run two Grep calls in parallel (same pattern as /pickup):**
- `Grep pattern="^status: open" glob="**/PIC - *.md" path="{vault_root}/" output_mode="files_with_matches" head_limit=0`
- `Grep pattern="^status: picked-up" glob="**/PIC - *.md" path="{vault_root}/" output_mode="files_with_matches" head_limit=0`

Filter results to files whose basename starts with `PIC -` (discard IRs, DTs, templates).

**Use this context throughout closeout:**
- **Step 1d (session summary):** When listing topics worked on, note which ones already have open PICs. Don't propose creating a PIC for something that's already tracked.
- **Step 3 (PIC creation):** Before creating a new PIC, check if an open PIC already covers the same domain. If yes, update the existing PIC instead of creating a duplicate.
- **Step 3 (PIC closure):** If any open PICs were fully resolved during this session, close them as part of closeout. Don't leave completed PICs in `open` status.
- **Step 4 (final summary):** Include PIC counts (open, created, closed) in the closing block so the user sees the net change.

This snapshot is context, not output. Don't present the full PIC list to the user unless they ask. Just use it to make better decisions about what to create, update, or close.

## Step 0a: Environment Verification (MANDATORY for deployed apps)

Before logging anything, audit the session for code changes to deployed services and verify the deployment state of every change. The closeout log will end up in the daily note where future agents read it as ground truth, so false claims here cause cascading bugs.

For every service you touched this session that has a deployed component, answer:

1. **Was it deployed to production?** Check by:
   - Did anyone run the project's deploy command? Look for the actual command in the conversation/JSONL.
   - If yes, verify via CI/CD logs or the live URL that the deployment succeeded.
   - Do NOT count `git push` as a deploy unless your CI/CD auto-deploys on push. Many projects use a Push =/= Deploy model where pushing to main does NOT trigger deployment.

2. **If it was LOCAL ONLY**, the closeout log MUST say so explicitly: "(local, verified at http://localhost:<port>/<path>) -- NOT deployed to production".

3. **If it was deployed**, log MUST include: "(deployed via [deploy command], verified at [production URL])".

4. **If you cannot determine the environment** for a code change, STOP and ask the user before logging. Don't guess.

This step exists because the most dangerous closeout failure is logging "deployed the fix" when the change is actually only on the local dev server. The next session's agent reads the daily note, assumes prod is updated, doesn't deploy, and the bug stays live for days.

## Step 0: Check for Recap Output

Before scanning the conversation from scratch, check if a `/recap` was run in this session. Look for recap output in the conversation -- it will have a "Main Thread", "Branches", and "Unanswered Questions" structure.

If a recap was run, it already contains:
- **What was worked on** (the main thread and resolved branches)
- **What's still open** (dropped items, in-progress branches)
- **What was deferred** (parked items that may need PICs)
- **Loose ends that were triaged** (decisions made about each)

Use this as your primary input instead of re-scanning the conversation. The recap already did the hard work of mapping the session -- don't duplicate it. Extract the topics, group by project, and proceed to Step 2.

If no recap was run, fall through to Step 1 as normal.

## Step 1: Load Full Session History from JSONL

*Skip this step if Step 0 found recap output.*

Context compaction loses detail. The live conversation context may be missing early work, decisions, or branches that were compacted away. **Always load the full JSONL session log** so you capture everything that happened.

### 1a. Find the current session's JSONL

Session logs live at `~/.claude/projects/<project-slug>/`. The project slug is derived from the working directory path (slashes become dashes). Find the most recent `.jsonl` file:

```bash
ls -lt ~/.claude/projects/<project-slug>/*.jsonl 2>/dev/null | head -5
```

The current session is typically the most recently modified file.

### 1b. Extract a structured summary

Don't read the whole JSONL into context (they can be 2MB+). Run a Python script to extract what closeout needs:

```python
import json, sys

topics = []       # user requests/instructions
actions = []      # significant tool calls (file writes, git ops, deploys)
artifacts = []    # files created or modified
decisions = []    # explicit decisions made

with open(sys.argv[1]) as f:
    for line in f:
        try:
            entry = json.loads(line)
        except:
            continue
        
        msg_type = entry.get("type")
        msg = entry.get("message", {})
        content = msg.get("content", "")
        
        # Extract text from content blocks
        if isinstance(content, list):
            texts = []
            tool_uses = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        texts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_uses.append(block.get("name", "") + ": " + str(block.get("input", {})).get("description", block.get("input", {}).get("file_path", ""))[:100])
            content = " ".join(texts)
            if tool_uses:
                actions.extend(tool_uses[:3])  # cap per message
        
        if not isinstance(content, str):
            continue
        
        if msg_type == "user" and len(content.strip()) > 10:
            # Skip teammate messages and skill loading
            if "<teammate-message" not in content and "Base directory" not in content:
                topics.append(content.strip()[:200])

# Print structured summary
print("=== USER REQUESTS ===")
for t in topics:
    print(f"- {t}")
print(f"\n=== TOOL ACTIONS ({len(actions)} total) ===")
for a in actions[:30]:
    print(f"- {a}")
```

### 1c. Identify work topics

From the JSONL summary, identify:
- **What was worked on** -- files created, modified, deployed; decisions made; research completed
- **What's in progress** -- work started but not finished, or work that has a clear next step
- **Which projects were touched** -- map each piece of work to its vault project

Also cross-reference with the live conversation context. Items from the JSONL that are still in context are confirmed. Items only in the JSONL may have been resolved or dropped -- check the actual file system to verify.

### 1d. Present summary for confirmation

Group by project/topic. For each topic, determine:
1. Is the work complete, or is there a logical pickup?
2. If there's a pickup, what would a fresh agent need to know to continue?

Present your summary to the user and ask if it looks right before proceeding. Keep it brief -- a few bullets per topic showing what you'd log and which topics need pickups.

## Step 1.5: Infrastructure Documentation Gate

Check whether this session modified infrastructure. Indicators:
- Docker compose file changes (new services, removed services, renamed containers)
- Container creation, removal, or rebuild
- Route or reverse-proxy label changes (new paths, removed paths, domain changes)
- Deploy path changes (app moved to a different directory)
- Service migration (old system replaced by new system)

If **any** infrastructure changes occurred, verify these reference docs are still accurate:
1. Infrastructure reference docs (server work rules, service route maps, app location maps)
2. Relevant project `CLAUDE.md` files (architecture descriptions, container references)

For each doc, spot-check the sections that would be affected by this session's changes. If a doc is stale (references old containers, removed paths, or pre-migration architecture), either:
- **Update it now** as part of closeout, or
- **Create a PIC** specifically for the doc update, flagging what's stale and what the correct state is

Do not skip this step. Migrations and sunsets are high-drift-risk events -- the session that makes the change must also update the docs or explicitly hand off that responsibility via a PIC.

## Step 1.6: Session Push & Deploy Verification (MANDATORY)

Before writing anything to the daily note, audit **this session's** code work to ensure everything that should be pushed and deployed actually is. This is the most common closeout failure: the session writes code, commits it, but never pushes -- or pushes but never deploys -- and the daily note then claims work was shipped that wasn't.

**Critical scoping rule:** Only act on changes from THIS session. Other agent sessions on the same machine may have their own uncommitted work in progress that you must NOT touch. Scope every check by:
- Files this session edited (extract from JSONL `tool_use` entries: Edit, Write, NotebookEdit, Bash with git commit/add)
- Commits authored in the last few hours by you (this session)
- Services this session explicitly built or deployed

If you cannot determine whether a change is yours vs another session's, **leave it alone** and flag it in the closeout summary instead of acting on it.

### 1.6a -- Identify this session's repos

Walk the JSONL tool_use entries and extract every file path that was edited/written. Map each file to its parent git repo by walking up to find a `.git` directory. Common candidates:
- Your vault directory (e.g., `~/Documents/Vaults/`)
- Your code repos (e.g., `~/Repos/{{MONOREPO_NAME}}/`)
- `~/.claude/skills/` (only if a `.git` directory exists -- otherwise changes may be backed up via a vault mirror instead)
- Remote repos on deployment targets (check via SSH if applicable)

For each repo, build a list of files **this session touched**.

### 1.6b -- Check commit state per repo

For each repo + this-session's-files:

```bash
cd <repo> && git status --short -- <files...>
```

For any file that shows as `M` (modified, uncommitted) or `??` (untracked):
- **Is this session responsible for the change?** Cross-check against the JSONL Edit/Write entries.
- If yes, **commit immediately** using `/git-safe`. Don't ask. Closeout implies "wrap up my work," which includes committing it. Use a descriptive message referencing the session's work.
- If no (e.g., another session's WIP, framework auto-mods, machine-state files), leave alone. List in the closeout summary as "uncommitted state present in [repo] not from this session -- flagged but not touched."

**Never `git add -A` blindly.** Always stage specific files from the session's edit list. Other agents may have their own staged work you don't see.

### 1.6c -- Check push state per repo

For each repo with this-session's commits:

```bash
cd <repo> && git fetch origin --quiet && git log origin/main..HEAD --oneline
```

For each unpushed commit, verify it's yours:
- `git log --format="%h %an %s" origin/main..HEAD` -- author should be the human user
- Cross-check the commit time against the session start time (JSONL first message timestamp)
- Cross-check the commit message against the session's work (the topics from Step 0/1)

If yes, **push immediately** via `git push origin main` (after verifying branch via `git branch --show-current`). Don't ask. Closeout implies "wrap up my work," which includes pushing it. The user approved this by running `/closeout`.

If the commit is from another session (older timestamp, unrelated message), leave it alone. Flag it in the closeout summary.

**Per git-safe**: always verify the branch first, never force push. But pushing your own session's commits to main during closeout does not require a separate approval -- the closeout invocation IS the approval.

### 1.6d -- Check deploy state for code changes

This step is MANDATORY when this session edited any file in a service that has a deployed production component.

For each service you touched this session, verify the running production instance has this session's code:

1. **Find the latest commit touching the service's paths:**
   ```bash
   cd ~/Repos/<project> && git log -1 --format="%h %ai" -- <service-path>/
   ```

2. **Compare against the running deployment:** Use whatever verification method your project supports (container image timestamps, version endpoints, distinctive string grep, CI/CD status).

3. **If the latest commit is NEWER than the deployed version:** the service is on stale code.

4. **Functional verification (preferred over timestamps):** for the file you edited, check that a distinctive line from your edit is present in the running service. This is the most reliable check -- timestamps can be misleading for cached builds, but the actual file content is ground truth.

If the running service does NOT have your fix:
- **Deploy immediately** using your project's deploy command. Don't ask. If you edited code in this session and it's not deployed, deploy it. Closeout means "wrap up my work," which includes getting your code live.
- If your project uses a Push =/= Deploy model: pushing to main does NOT auto-deploy. You must run the deploy command explicitly.

**Do NOT deploy services you didn't edit in this session**, even if you notice they're stale. That's another session's responsibility (or end-day's audit step). Closeout's scope is your own work.

**Hot-patched instances are NOT deployed.** If the session used `docker cp` or similar to patch files into a running container, those changes will be lost on restart. The closeout must push the code and rebuild the container properly. A hot-patch is a temporary fix during development, not a deploy.

### 1.6e -- Present the audit summary

Before continuing to Step 2, output a clear table:

```
Session Push & Deploy Audit
===========================

Repo: ~/Repos/my-project
- 2 commits unpushed (mine):    [hash] [msg], [hash] [msg]    -> pushed
- 1 service with stale deploy:  web-app (latest commit 30min newer than deploy)  -> deployed

Repo: ~/Documents/Vaults
- 0 uncommitted, 0 unpushed                                   -> clean

NOT TOUCHED (other sessions' work, flagged not acted on):
- ~/Repos/my-project: 6 auto-generated type files (framework noise)
```

Wait for user input on each item before proceeding. Resolve all "yours" items before logging work to the daily note -- otherwise the daily note will lie about what was deployed.

## Step 2: Log Work

**PJL cross-reference:** Before invoking `/log-work`, check each project touched this session for an existing PJL file (`02_Projects/<project>/PJL - <Project Name>.md`). If one exists, read its most recent entry to confirm consistency with what you're about to log and to avoid duplicate entries if another closeout already ran. Pass the PJL path to `/log-work` so it can update the PJL in detailed mode. `/log-work` handles PJL writing -- closeout does not write PJL entries directly.

Use the `/log-work` skill's conventions to update today's daily note (`01_Notes/Daily/DN - YYYY-MM-DD.md`). Follow the same formatting rules -- action-oriented bullets, bold key stats, wikilinks to artifacts, max 5 bullets per topic heading.

If there's already an entry for a topic in the daily note's `## Worked on` section, append to it rather than creating a duplicate heading.

## Step 2.5: Plan Update Gate (MANDATORY)

Before creating PICs, update every active implementation plan touched this session. Stale plan task statuses cause the next agent to re-do completed work or make wrong assumptions about what's left.

1. For each project worked on, check for active plans: `Glob pattern="**/PL - *.md" path="02_Projects/<project>/plans/"`
2. For each plan found, read the task table and compare against this session's work
3. Update task statuses: `todo` -> `done`, `in-progress`, or `partial` as appropriate
4. Add a row to the plan's Work Log table with today's date, task numbers, and what was done
5. Update the `completed` count in frontmatter to match actual done tasks

Do not skip this step. The plan is the tracker. If you advanced tasks 3.2, 3.7, and 3.8 from `todo` to `done` during the session but leave the plan unchanged, the next agent reads stale `todo` statuses and may re-do the work.

## Step 2.6: PJL Validation Gate (MANDATORY)

Before creating any PICs, verify that `/log-work` wrote PJL entries for every project touched this session. This gate prevents the most common closeout failure: PICs created with no PJL record of what was actually built.

1. List every project that appears under `## Worked on` in today's daily note
2. For each project, check for a PJL file at `02_Projects/<project>/PJL - <Project Name>.md`
3. If the PJL exists, verify it has a `## YYYY-MM-DD` heading for today
4. **If any project is missing a PJL entry for today: STOP.** Do not proceed to PIC creation. Instead:
   - Re-invoke `/log-work` for the missing project(s), passing the project name explicitly
   - Verify the PJL entry was created
   - Only then continue to Step 3

This gate exists because PIC creation (Step 3) is independent of PJL logging. Without this check, an agent can create a detailed PIC carrying forward context while the PJL -- the only machine-readable implementation record -- has no entry for the day's work. The PIC tells the next agent what to do; the PJL tells them what was done. Both are required.

## Step 2.7: Cross-Reference Open PICs Against Session Work (MANDATORY)

Work in one session often resolves items from PICs created in earlier sessions. Without this step, those PIC items stay listed as "open" indefinitely, causing future agents to investigate already-resolved problems.

1. Use the PIC landscape from Step 0b (the grep results of all open/picked-up PICs).
2. For each project or system touched this session, check if any open PICs have "What Needs to Happen Next" items that were addressed by this session's work. Match by:
   - Same project name
   - Same system or subsystem
   - Same IR or spec reference
3. For each match found, read the PIC's "What Needs to Happen Next" section and compare against what was done.
4. If items were resolved: append a dated session update to the PIC documenting what was resolved and what remains. Format:

```markdown
## YYYY-MM-DD Session Update

**Resolved by [topic/commit/deploy]:**
- S{N}: {description of what was done}

**Still open:**
- S{M}: {remaining item}
```

5. If ALL items are resolved: close the PIC (update frontmatter to `status: closed`, add Closing Update per the PIC lifecycle rules in `/pickup`).
6. If the PIC was picked up by this session and work was done on it directly, its updates are handled by the normal pickup flow. This step targets PICs that were NOT picked up but had items indirectly resolved.

**Why this exists:** PICs with multiple items can have items resolved across separate sessions that work on different PICs. None of those closeouts update the original PIC. It stays listed as fully open for days until a manual audit discovers half the items are resolved. Each intervening session's agent re-investigates systems that the prior session already fixed.

## Step 3: Create Pickup Documents

For each topic that has a logical next step, invoke `/create-pickup` to generate a verified PIC document.

Pass each topic to the skill with:
- **Topic**: what work needs a pickup
- **Project**: which vault project it belongs to

The `/create-pickup` skill handles everything: verification of system state claims, file placement, frontmatter, completeness checks, and writing. It will verify factual claims against the live system before committing them to the PIC, ensuring the next agent gets accurate context.

If there are multiple topics needing pickups, invoke `/create-pickup` for each one. The skill will confirm each PIC with the user before writing.

### Unfinished plan check (MANDATORY)

After creating PICs for obvious topics, check every active plan updated in Step 2.5. For each plan with remaining `todo` or `in-progress` tasks, determine whether the plan itself is sufficient context for the next session or whether a PIC is needed.

**A PIC is needed when:**
- The plan's remaining tasks depend on context not captured in the plan (session decisions, discovered blockers, environment state, oracle findings)
- The next step requires specific commands, credentials, or verification that the plan doesn't spell out
- Work was partially completed and the boundary between "done" and "todo" needs explanation

**The plan alone is sufficient when:**
- The remaining tasks are self-contained and fully described in the plan
- No session-specific context is needed to continue
- An existing open PIC already covers this plan's work

Ask the user for each unfinished plan: "The [plan name] has [N] remaining tasks. The existing PIC [name] covers this / there's no PIC for this work. Create or update a PIC, or is the plan sufficient?" Present the remaining task summary so the user can decide without reading the plan.

## Asking Good Questions

When confirming summaries, pickup content, or asking about lessons -- always provide enough context for the user to answer without further research. State the situation, state what you're proposing, state the impact, then ask. If the user has to say "I don't have enough context," the question was poorly framed.

## Step 4: Final Summary and Tab-Close Signal

End with a clear, unambiguous closeout confirmation. The user needs to know at a glance that everything is done and they can close the tab without losing anything.

**Format (mandatory):**

```
---
## Session Closed

**DN:** [updated / created] -- [count] entries logged
**PJL:** [list of project logs updated]
**Plans updated:** [list of plans updated with task counts, or "none active"]
**PICs created:** [count] -- [names, or "none needed"]
**PICs closed:** [count] -- [names, or "none"]
**Deploys:** [all verified / none this session / list any pending]
**Unpushed work:** none [or list]

Everything is saved. You can close this tab.
---
```

The last line ("Everything is saved. You can close this tab.") is the explicit signal. Do not omit it. Do not hedge it with "I think" or "should be." If there IS something unresolved (a deploy still running, a question unanswered), say so instead: "Deploy still running for [service]. Check back in ~2 min, or close and it'll finish on its own."

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
