---
name: create-concept-brief
description: >-
  Capture a stakeholder's vision for a feature, system, or initiative and produce
  a structured concept brief that grounds their ideas against existing systems.
  Use this skill when someone says "concept brief", "create concept brief",
  "I have an idea for", "I want to build", "let me describe what I'm thinking",
  or starts describing what they want.
---

# Create Concept Brief

Capture a stakeholder's vision for a feature, system, or initiative and produce a structured concept brief that grounds their ideas against your organization's existing systems. The brief is a pre-spec document -- it clarifies intent, not implementation.

Use this skill when you have an idea for a feature or system and want to turn it into a clear concept document. Say "concept brief", "create concept brief", "I have an idea for", "I want to build", "let me describe what I'm thinking", or just start talking about what you want.

**Arguments:** $ARGUMENTS

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{vault_root}/{paths.projects}/`). If the file doesn't exist, use defaults and warn once.

## What this produces

A **Concept Brief (CB)** -- a structured document that captures:
- What you want and why
- Real use cases and examples
- What matters most (non-negotiables)
- How your ideas connect to what already exists in your organization's systems
- Open questions that need answers before building

The CB is designed so that when a developer reads it, they immediately understand what you want without having to guess your intent from technical assumptions.

## How it works

### Step 1: Capture

Accept whatever the user gives you -- voice memo transcript, pasted text, a rambling description, a list of bullet points, a formal document, or just a conversation. Don't require a specific format.

If the input is sparse or unclear, interview the user conversationally. Focus on:
- **Outcomes:** "What should this let people do that they can't do today?"
- **Frustrations:** "What's broken or missing right now?"
- **Examples:** "Can you describe a specific situation where you'd use this?"
- **Priorities:** "If you could only have one piece of this, what would it be?"
- **Non-negotiables:** "What absolutely must be true about how this works?"

Do NOT ask about technology, architecture, databases, APIs, or implementation. Those are developer decisions. If the user volunteers technical opinions, capture them as "stakeholder assumptions" but don't treat them as requirements.

Ask one question at a time. Keep it conversational.

### Step 2: Ground

Read the organization context file at `references/org-context.md`. This file should contain summaries of existing systems, active projects, and current capabilities relevant to your organization. If the file doesn't exist, skip grounding and note in the brief that no organizational context was available.

For each idea the user described, check:
- Does something like this already exist? (partially or fully)
- Which existing system is closest to what they're describing?
- Are they using different words for something that already has a name in your systems?
- What would actually need to be new vs extended?

### Step 3: Structure

Produce the Concept Brief using the template in `references/cb-template.md`. Key sections:

1. **Vision** -- 2-3 sentences capturing the core idea in the user's own words
2. **Problem Statement** -- what's broken, missing, or frustrating today
3. **Goals** -- numbered list of outcomes, ordered by emphasis (what the user kept coming back to)
4. **Use Cases** -- concrete scenarios with named people and real situations
5. **Non-Negotiables** -- constraints that must be true regardless of implementation
6. **Open Questions** -- things the user couldn't answer or that need research
7. **Translation Guide** -- table mapping the user's language to existing system names, with notes on what exists, what's partially built, and what's new
8. **Stakeholder Assumptions** -- technical or implementation opinions the user expressed, captured without judgment, flagged as "stakeholder perspective, not requirement"
9. **Priority Signal** -- what the user was most emphatic about, what they mentioned repeatedly, what they said was urgent

### Step 4: Review and file

Show the user the draft brief. Ask if anything is missing or wrong. Revise based on feedback.

File the final brief to: `{vault_root}/{paths.projects}/<project>/specs/{date}/CB - {Topic}.md`

Where `<project>` is the relevant project folder and `{date}` is today's date in YYYY-MM-DD format. If the topic clearly maps to an existing project, file it there. If no project exists yet, ask the user where to file it.

## What this does NOT produce

- Technical specs (use `/create-spec` for that)
- Implementation plans (use `/create-plan` for that)
- Architecture diagrams or system designs
- Database schemas or API definitions

The concept brief is input TO those processes, not a replacement for them.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
