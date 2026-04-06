---
name: recap
description: Recap the current conversation — surface the main topic, identify side-threads, unanswered questions, unresolved decisions, and loose ends, then triage them interactively. Use this skill when the user says "recap", "where are we", "what were we doing", "what's outstanding", "any loose ends", "what did we miss", "back to the main thing", or when the conversation has branched into multiple topics and needs re-grounding. Also trigger after context compaction when the user seems disoriented, or when the user says "ok what now" mid-session and the conversation has been long or meandering. This skill is the "gather yourself" moment before continuing — it prevents lost context, dropped questions, and forgotten side-tasks.
---

# Recap

Long conversations branch. Your job is to scan the **full conversation history**, present a compact dashboard of where things stand, then immediately start an interactive triage session to close out loose ends — quick fixes first, PICs only as a last resort.

The recap has two phases: a read-only **dashboard** (you present), then an interactive **triage loop** (you ask, user decides, you act).

## Step 0 — Load Full Session History

Context compaction loses detail. Before scanning, load the **full JSONL session log** so you can see everything that happened, including compacted messages.

1. **Find the current session's JSONL.** Session logs live at:
   ```
   ~/.claude/projects/<project-slug>/<session-id>.jsonl
   ```
   The project slug is derived from the working directory path (slashes become dashes). To find the right file, list `*.jsonl` in the project directory sorted by modification time — the current session is typically the most recently modified file whose first user message matches this conversation.

2. **Extract user and assistant messages.** Run a script to pull all `type: "user"` and `type: "assistant"` entries. For each, extract the text content:
   ```bash
   python3 -c "
   import json, os, glob
   project_dir = os.path.expanduser('~/.claude/projects/')
   # Find project dirs, pick the one matching cwd
   # Then find most recent .jsonl
   # Extract messages...
   "
   ```
   The message structure: each line is JSON with `{"type": "user"|"assistant", "message": {"role": "...", "content": ...}}`. Content can be a string or an array of content blocks (text, tool_use, tool_result, etc.).

3. **Build a conversation summary.** From the full JSONL, extract:
   - Every user request/instruction (what they asked for)
   - Every significant action taken (tool calls, file writes, decisions made)
   - Every question asked by either party and whether it was answered
   - Every topic/thread that was started

4. **Cross-reference with live context.** The JSONL gives you what happened; the live context gives you what's still active. Items from the JSONL that are no longer in context may be resolved or may be dropped — check.

**Performance note:** JSONL files can be large (1MB+). Don't read the whole file into context. Use a Python script to extract a structured summary (topics, decisions, open questions, actions) and read that summary. Target < 2000 lines of extracted content.

## Asking Good Questions

Every question must include enough context to answer without further research. The pattern: **state the situation, state the options, state the impact, then ask.**

## Phase 1 — Dashboard

Scan the conversation and present a compact summary. The dashboard should be scannable in 10 seconds — use tables and tight formatting, not prose.

### Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 RECAP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Main thread:** [one sentence]
**Status:** [where it stands]

**Resolved ({N})**
- Short one-liners only. No details.
- These are done — just confirming they happened.
- Collapse if > 8.

**Open Items ({N})**

| # | Type | Item | Est |
|---|------|------|-----|
| 1 | fix | [desc] | ~2 min |
| 2 | fix | [desc] | ~1 min |
| 3 | decide | [desc] | ~1 min |
| 4 | question | [desc] | ~1 min |
| 5 | parked | [desc] | needs PIC |

Types: fix (can do now), decide (needs user input),
question (unanswered), parked (explicitly deferred),
blocked (waiting on external)

Ready to triage? Starting with #1.
```

**Formatting rules:**
- Use markdown bold headers (`**Resolved (N)**`) instead of box-drawing characters
- Use bullet lists for resolved items — one line each, no boxes
- Use markdown tables for open items — clean columns, no manual padding
- Use `━` dividers only for the top/bottom RECAP banner
- Never use `┌ │ └ ┐ ┘ ─` box-drawing characters — they break in variable-width terminals and look messy when content overflows

### Dashboard Rules

1. **The main thread is NEVER an open item.** The main thread is what you return to after triage — it's the destination, not something to triage. If the main thread hasn't been started yet, that's fine — report its status and move on. Only side-branches, dropped items, and loose ends go in the open items table. Putting the main thread in the open items list is like putting "go to work" on your grocery list — it's a category error.

2. **Resolved items are one line each.** No explanations. `Dockerfile audit — fixed 9 Dockerfiles, pushed.` That's it. If there are more than 8, show the count and the 3 most significant, then `...and N more`.

3. **Open items get a numbered table** sorted by effort (quickest first). Each row has: number, type, short description, estimated effort. This is the triage queue.

4. **Types drive the triage behavior:**
   - `fix` — you can do this right now without user input. Propose the fix, user says go/skip.
   - `decide` — user needs to make a call. Present options with context.
   - `question` — an unanswered question from earlier. Re-ask with full context.
   - `parked` — was explicitly deferred. Confirm it should stay deferred or needs a PIC.
   - `blocked` — waiting on something external. Note what, move on.

5. **Effort estimates are honest.** `~2 min` means you can actually do it in 2 minutes. Don't lowball. If something is genuinely a session of work, say `needs PIC` not `~30 min`.

6. **Don't show "Suggested Next Steps" as a separate section.** The open items table IS the plan. The triage loop IS the execution.

## Phase 2 — Triage Loop

After presenting the dashboard, immediately start working through the open items, starting with #1. Don't wait for the user to pick — start with the quickest fix and ask.

### For each item, based on type:

**fix:** Present what you'd do and ask for permission.
```
#1 fix — work_items default is 'open' but CHECK only allows 'pending'.
One ALTER command on VPS. Fix it now? [yes/skip]
```

**decide:** Present the options with full context.
```
#2 decide — VPS has 6 uncommitted files from before our session.
They're in .gitignore, docker-compose.yml, ai-gateway, flora-ai-client-py,
api config. Options:
  a) Investigate what they are (I'll read the diff, ~2 min)
  b) Commit them as-is
  c) Discard — they're pre-existing and not ours
  d) Skip for now
```

**question:** Re-ask the original question with context.
```
#3 question — Earlier I asked whether to add 'risk' to the activities
type CHECK. Context: spec defines 6 types, DB only has 2, no code uses
'risk' yet. Adding it is a no-op. Add it, or skip?
```

**parked:** Confirm the deferral.
```
#4 parked — CI/GHCR migration was assessed as ~1 session effort.
It's mitigated by NODE_OPTIONS + safe-build pre-flight.
Leave deferred, or create a PIC to track it?
```

**blocked:** Acknowledge and move on.
```
#5 blocked — Planner-sync deploy needs next API container rebuild.
Nothing to do now. Moving to #6.
```

### Triage Principles

1. **Bias toward closure, not tracking.** If something can be fixed in 2 minutes, fix it. Don't create a PIC for a one-line command. PICs are for work that genuinely needs a future session.

2. **One item at a time.** Present one, wait for the user's response, act on it, then move to the next. Don't batch.

3. **Quick fixes go first.** The open items table is already sorted by effort. Work through it in order — momentum from quick closures makes the harder decisions easier.

4. **"Skip" is always an option.** The user can skip any item. Skipped items stay unresolved — that's their call. Don't nag.

5. **Keep a running count.** After each item: `Resolved #1. 4 remaining.` or `Skipped #3. 3 remaining.`

6. **When the queue is empty:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Triage complete: {N} resolved, {M} skipped, {K} need PICs.
 Main thread: [topic]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then either return to main thread work, or offer closeout if the session is ending.

## Closeout Handoff

If the session is ending (user is wrapping up, or all main work is done), offer to flow into closeout after triage:

> "Want me to run `/closeout` to log today's work and create pickups?"

Closeout will detect the recap was just run and use its findings. Don't re-scan.

## Tips

- If the conversation was linear with no branches: "No loose ends. Main thread: [topic]. Continuing."
- Be honest about your own dropped balls. "I asked about X but moved on without waiting for your answer."
- If the conversation is short (< 10 messages), a recap is overkill. Say so and skip it.
- After context compaction, the JSONL still has the full history. Always load it in Step 0 so you don't miss compacted branches.
