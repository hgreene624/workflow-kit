---
name: pickup
description: Start-of-day pickup — load context from a PIC document and get oriented for work. Use this skill when the user says "pickup", "pick up", "start of day", "what's on my plate", "what do I need to do", "get started", "load the pickup", "continue where I left off", "resume work", or points at a specific PIC document. Also trigger when the user opens a new session and says something like "ok what am I doing today" or "what was I working on". Even "what's in my TODOs" at the start of a session should trigger this if there are PIC-linked TODOs in today's daily note.
---

# Pickup

You are starting a work session by loading context from a pickup document. The goal is to get oriented quickly so the user can start working without having to re-explain everything from yesterday.

## Pre-flight: Orient Check

Before doing anything else, check whether `/orient` has already been run in this session. Look for evidence in the conversation history — if you've already read the SOD, EOW, vault agents.md, and lessons.md earlier in this conversation, orient has been done.

If orient has NOT been run yet, run `/orient` first (invoke the Skill tool with skill: "orient"). This ensures vault config, style guardrails, lessons, and period reports are loaded before you start loading PIC context. Do not skip this — pickup without orient means you'll miss project rules and lessons.

After orient completes, continue with the pickup steps below.

## PIC Lifecycle

PICs have four statuses:
- **`open`** — created by closeout, waiting to be picked up
- **`picked-up`** — actively being worked on in a session
- **`parked`** — context deferred to a project's agents.md via `/park`. Not active work, but not done — the context will surface when future agents work on that project.
- **`closed`** — work is complete, no longer shown in the daily note Pickups section

You are responsible for managing these transitions. When you pick up a PIC, mark it `picked-up` immediately. When the work described in the PIC is done, ask the user if you can close it. Don't let PICs linger in `picked-up` forever — if the topic has been fully addressed during the session, proactively ask: "The work from [PIC topic] looks complete. Can I close that pickup?"

## Step 1: Find the Pickup

**If the user pointed at a specific PIC file:** Read it directly.

**If no specific PIC was given:** Find all open PICs across the vault.

1. Search for all PIC files using Glob: `**/PIC - *.md` across `Work Vault/02_Projects` and `Work Vault/01_Notes`
2. Read each PIC file's frontmatter and filter to `status: open` only — skip `picked-up`, `closed`, and `parked`
3. If there are multiple open pickups, present them to the user and ask which one to work on (one question at a time — use AskUserQuestion). Show the topic name, the project, and the first item from "What Needs to Happen Next" so the user can choose quickly.
4. If there's exactly one open pickup, confirm with the user: "I found one open pickup: [topic]. Want me to load it?"
5. If there are no open pickups, tell the user: "No open pickups found. Starting fresh — what would you like to work on?"

## Step 2: Load Context

Once you have the PIC to work from:

1. Read the full PIC document
2. Read every file listed in the `## Key Files` section — these are the files the previous session identified as essential context
3. Read the project's `agents.md` and `lessons.md` if they exist
4. If the PIC references a spec or plan, read those too
5. Explore beyond the PIC if context feels incomplete — PICs are written at end-of-session when things may have been rushed. If a next step references code or systems you don't fully understand from the PIC alone, read the relevant files until you do.

Build your understanding of:
- What project this is and its scope
- What was already done
- What the concrete next steps are
- Any blockers or dependencies
- Any user preferences or decisions from the previous session

## Step 3: Mark as Picked Up

Update the PIC document's frontmatter immediately:
- Change `status: open` to `status: picked-up`
- Add `picked_up_date: YYYY-MM-DD`

This moves the PIC from "open" to "picked-up" in the daily note's Pickups dataview, showing the user it's actively being worked on. Do this before presenting the plan — don't wait.

After marking the PIC, set the WezTerm tab title so the user can identify which PIC this session is working on. Run:

```bash
wezterm cli set-tab-title "PK - SHORT_NAME"
```

Where `SHORT_NAME` is a short all-caps label derived from the PIC title (e.g., "PIC - FWIS Pipeline Quality Remediation" becomes `PK - FWIS PIPELINE REMEDIATION`, "PIC - KB Approval Workflow for Briefs" becomes `PK - KB APPROVAL WORKFLOW`). Drop filler words like "Implementation", "System", and prepositions when they make the name too long. Keep it under ~30 characters so it fits in a tab. The WezTerm config will automatically color the tab teal when it detects the `PK - ` prefix.

## Step 4: Prep Brief

Before jumping into work, present a **prep brief** that orients the user on the *why* and *what* of this PIC. This is especially valuable when the user is choosing from multiple PICs — they need context to confirm they want to commit to this one.

The prep brief should cover:

1. **The problem** — why does this PIC exist? What's the underlying issue or motivation? Don't just restate the PIC title — explain what's wrong or missing and why it matters.
2. **What was already done** — the key outcome from the previous session (1-2 sentences)
3. **What's left** — the numbered next steps from the PIC, presented as a proposed sequence
4. **Observations** — anything you noticed while loading context that the PIC didn't capture: discrepancies between the PIC's assumptions and current state, risks, scope questions, or decisions the user needs to make before work begins. This is where you add value beyond just reading the PIC back.
5. **Blockers** — anything that might get in the way (or "none" if clear)

Then ask: "Ready to start, or do you want to adjust the plan?"

Once the user confirms, begin working on the first step. You now have full context — treat this like a continuation of the previous session.

## Step 5: Close When Done

As you work through the PIC's next steps, track progress against them. When all the steps have been completed (or the user indicates they're done with this topic), ask:

"The work from [PIC topic] looks complete — [brief summary of what was accomplished]. Can I close this pickup?"

If the user confirms, update the PIC frontmatter:
- Change `status: picked-up` to `status: closed`
- Add `closed_date: YYYY-MM-DD`

This removes the PIC from the daily note's Pickups section entirely.

### Closing Update

Before flipping status to `closed`, append a closing update section to the PIC document:

```markdown
## Closing Update
**Closed:** YYYY-MM-DD
**Outcome:** [1-2 sentences: what was accomplished relative to the PIC's original next steps]
**Artifacts:** [wikilinks to anything produced — commits, specs, plans, deployed services, work logs]
**Carry-forward:** [Anything not completed that needs a new PIC or was deferred, or "None — fully resolved"]
```

This creates an audit trail — when reviewing closed PICs, you can see what actually happened, not just that the status changed.

Also update the daily note: add a brief entry under `## Worked on` noting the PIC closure and outcome (e.g., `- Closed [[PIC - Topic Name]] — [one-line outcome]`). This ensures the daily note reflects completed pickups, not just new work.

### Lingering PIC Detection

If during a session you notice PICs in `picked-up` status that haven't been actively worked on (e.g., loaded at session start but the user pivoted to other work), proactively ask before the session ends: "[[PIC - Topic]] is still marked as picked-up. Should I close it, carry it forward, or leave it for next session?"

Don't let PICs accumulate in `picked-up` status across multiple sessions — that defeats the purpose of the lifecycle.

If the work isn't fully done and needs to carry forward again, don't close it — leave it as `picked-up` and let the next `/closeout` either update it or create a new PIC that supersedes it.
