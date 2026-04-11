---
name: closeout
description: End-of-day closeout — log work to the daily note and create pickup docs (PIC) for the next workday. Use this skill when the user says "closeout", "close out", "wrap up", "end of day", "EOD", "wind down", "done for the day", "call it a day", "closing out this session", or wants to finalize a work session and set up tomorrow's context. Also trigger when the user says "create a pickup", "make a PIC", or wants to carry forward work context to the next session. Even casual requests like "ok I'm done" or "wrapping up" at the end of a work session should trigger this skill.
---

# Closeout

You are closing out a work session. Your job is to capture what was done, log it to the daily note, and create pickup documents so a fresh agent tomorrow can hit the ground running without the user having to re-explain everything.

## Step 0: Check for Recap Output

Before scanning the conversation from scratch, check if a `/recap` was run in this session. Look for recap output in the conversation — it will have a "Main Thread", "Branches", and "Unanswered Questions" structure.

If a recap was run, it already contains:
- **What was worked on** (the main thread and resolved branches)
- **What's still open** (dropped items, in-progress branches)
- **What was deferred** (parked items that may need PICs)
- **Loose ends that were triaged** (decisions made about each)

Use this as your primary input instead of re-scanning the conversation. The recap already did the hard work of mapping the session — don't duplicate it. Extract the topics, group by project, and proceed to Step 2.

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

## Step 1.5: Verify What You're About to Log

Before writing anything to the daily note, verify the claims you're about to make. The daily note is read by future agents as ground truth — a false entry causes cascading mistakes.

### Deployment and state claims

If the session involved deploying, publishing, or modifying a live system, verify the outcome before logging it:

1. **Check git state.** Did the code get committed and pushed? Run `git status` and `git log @{u}..HEAD` in each repo this session touched. If commits are unpushed, log "committed (not yet pushed)" — not "shipped."

2. **Check deployment state.** If the user has deployment targets (production servers, staging environments, CI/CD pipelines), verify the change is actually running. The method depends on the user's setup:
   - CI/CD: check the workflow run status
   - Manual deploy: check if the deploy command was actually run in this session
   - Container-based: verify the running version matches what was committed
   
   If code was committed but not deployed, say so explicitly in the log: "(committed, not deployed to production)". Never log "deployed" or "shipped" unless you verified the change is live.

3. **If you can't verify**, ask the user. Don't guess.

This matters because the most dangerous closeout failure is logging "deployed the fix" when the change is sitting in git undeployed. The next session reads the daily note, assumes production is updated, and the bug stays live.

### Documentation drift

Check whether this session changed how a system works. Indicators:
- Config file or infrastructure changes (Docker, CI, routing, environment variables)
- Service creation, removal, migration, or renaming
- Architecture decisions that affect how future agents should approach the system

If any of these occurred, scan the vault's `04_Reference/` directory for REF docs that describe the affected system. Also check the relevant project's `agents.md`. If any doc now describes the old state:
- **Update it now** as part of closeout, or
- **Create a PIC** to hand off the documentation update, noting what's stale and what the correct state is

The session that makes the change owns the documentation update. Don't leave it for a future session to discover the drift.

## Step 1.6: Session Git Audit

Before writing to the daily note, audit this session's git work to catch anything that didn't make it to the remote.

**Critical scoping rule:** Only act on changes from THIS session. Other agent sessions may have their own uncommitted work that you must NOT touch.

### Find this session's repos

Walk the JSONL tool_use entries and extract every file path that was edited. Map each to its parent git repo. Then for each repo:

```bash
cd <repo>
git fetch origin --quiet
echo "branch: $(git branch --show-current)"
git status --short -- <files this session touched>
echo "unpushed:"
git log @{u}..HEAD --oneline 2>/dev/null
```

### Handle findings

- **Uncommitted changes from this session** — ask the user: "I have uncommitted changes in `<repo>`: [files]. Commit before closeout?"
- **Unpushed commits from this session** — ask: "I have unpushed commits in `<repo>`. Push to remote?"
- **Changes from other sessions** — flag but don't touch: "Note: `<repo>` has uncommitted changes not from this session."

Present a summary table before proceeding. Resolve all this-session items before logging work — otherwise the daily note may misrepresent what was actually pushed/deployed.

## Step 2: Log Work

**PJL cross-reference:** Before invoking `/log-work`, check each project touched this session for an existing PJL file (`02_Projects/<project>/PJL - <Project Name>.md`). If one exists, read its most recent entry to confirm consistency with what you're about to log and to avoid duplicate entries if another closeout already ran. Pass the PJL path to `/log-work` so it can update the PJL in detailed mode. `/log-work` handles PJL writing — closeout does not write PJL entries directly.

Use the `/log-work` skill's conventions to update today's daily note (`01_Notes/Daily/DN - YYYY-MM-DD.md`). Follow the same formatting rules — action-oriented bullets, bold key stats, wikilinks to artifacts, max 4 bullets per project heading.

If there's already an entry for a project in the daily note's `## Worked on` section, append to it rather than creating a duplicate heading.

## Step 2.5: PJL Validation Gate (MANDATORY)

Before creating any PICs, verify that `/log-work` wrote PJL entries for every project touched this session. This gate prevents the most common closeout failure: PICs created with no PJL record of what was actually built.

1. List projects touched this session (from Step 1's topic identification)
2. For each project, check for a PJL file at `02_Projects/<project>/PJL - <Project Name>.md`
3. If the PJL exists, verify it has a `## YYYY-MM-DD` heading for today
4. **If any project is missing a PJL entry for today: STOP.** Do not proceed to PIC creation. Instead:
   - Re-invoke `/log-work` for the missing project
   - Verify the PJL entry was created
   - Then continue

This gate exists because PIC creation (Step 3) is independent of PJL logging. Without this check, an agent can create a detailed PIC carrying forward context while the PJL - the only machine-readable implementation record - has no entry for the day's work. The PIC tells the next agent what to do; the PJL tells them what was done. Both are required.

## Step 3: Create Pickup Documents

For each topic that has a logical next step, invoke `/create-pickup` to generate a verified PIC document.

Pass each topic to the skill with:
- **Topic**: what work needs a pickup
- **Project**: which vault project it belongs to

The `/create-pickup` skill handles everything: verification of system state claims, file placement, frontmatter, completeness checks, and writing. It will verify factual claims against the live system before committing them to the PIC, ensuring the next agent gets accurate context.

If there are multiple topics needing pickups, invoke `/create-pickup` for each one. The skill will confirm each PIC with the user before writing.

## Asking Good Questions

When confirming summaries, pickup content, or asking about lessons — always provide enough context for the user to answer without further research. State the situation, state what you're proposing, state the impact, then ask. If the user has to say "I don't have enough context," the question was poorly framed.

## Step 4: Confirm

Tell the user what you created:
- Which daily note entries were added/updated
- Which PIC docs were created and where

Keep it brief — just a table or short list so they can verify at a glance.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
