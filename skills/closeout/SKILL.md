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

## Step 1: Scan the Conversation

*Skip this step if Step 0 found retro output.*

Read back through the conversation and identify:
- **What was worked on** — files created, modified, deployed; decisions made; research completed
- **What's in progress** — work started but not finished, or work that has a clear next step
- **Which projects were touched** — map each piece of work to its vault project

Group by project/topic. For each topic, determine:
1. Is the work complete, or is there a logical pickup?
2. If there's a pickup, what would a fresh agent need to know to continue?

Present your summary to the user and ask if it looks right before proceeding. Keep it brief — a few bullets per topic showing what you'd log and which topics need pickups.

## Step 2: Log Work

Use the `/log-work` skill's conventions to update today's daily note (`01_Notes/Daily/DN - YYYY-MM-DD.md`). Follow the same formatting rules — action-oriented bullets, bold key stats, wikilinks to artifacts, max 5 bullets per topic heading.

If there's already an entry for a topic in the daily note's `## Worked on` section, append to it rather than creating a duplicate heading.

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

PICs automatically appear in the "Pending Pickups" dataview section on every daily note (filtered to `status: open`). No need to manually add TODOs — the pickup skill finds open PICs from the dataview query.

Keep it brief — just a table or short list so they can verify at a glance.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
