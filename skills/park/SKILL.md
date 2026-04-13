---
name: park
description: Park research, context, or deferred work into a target project's agents.md so it surfaces when future agents work on that project. Use this skill whenever the user wants to defer context for later use, says "park this", "park context", "defer this to", "queue this for", "save this for later", "save this for when we work on X", "hold this for the portal work", or any variation of wanting to attach context to a project for future pickup. Also trigger on "/park" with arguments. Even casual requests like "we'll need this when we start on X" or "remember this for the portal redesign" should trigger this skill when there's a specific project the context should attach to. This skill is the bridge between "research done now" and "implementation later" — it prevents context from being lost between sessions by embedding it directly in the project's agent config.
---

# Park

You are parking context — research findings, deferred work, or other information — into a project's `agents.md` file so that any future agent working on that project will see it automatically.

This is a lightweight operation. The goal is to capture *just enough* context that a future agent knows what exists and when to use it, without duplicating the source material. Think of it as leaving a sticky note on a project folder.

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{paths.projects}/` for project tree). If the file doesn't exist, use defaults and warn once.

## Inputs

You need two things from the user:

1. **Source** — what to park. This can be:
   - A path to a PIC, research report (RE), spec, or other vault document
   - A wikilink like `[[RE - Read.ai Platform Reverse Engineering]]`
   - Free-text description from the conversation ("the patterns we found in the Read.ai analysis")

2. **Target project** — where to park it. This can be:
   - A project name ("<APP_2>", "signal-engine")
   - A path to an agents.md file
   - A description ("the portal project", "kitchen ops")

If the user doesn't provide both, ask. If the target project is ambiguous, search for matching agents.md files under `02_Projects/` and confirm with the user.

## Step 1: Find the Target agents.md

Projects live under `<VAULT_ROOT>/02_Projects/`. Each project has an `agents.md` at its root. Search for the target:

```bash
find "<VAULT_ROOT>/02_Projects" -name "agents.md" -type f
```

If the user gave a project name, match it against directory names. If ambiguous, show the options and ask.

Read the target `agents.md` to confirm it's the right project and understand existing content.

## Step 2: Read the Source

If the source is a file path or wikilink, read it. Extract:

- **What it is** — a 1-2 sentence summary of the content
- **What's actionable** — the specific patterns, findings, or deferred work that a future agent should apply
- **When it's relevant** — what kind of work would trigger needing this context (e.g., "when designing the meeting lifecycle UI", "when implementing the actuator")

If the source is free-text from the conversation, distill the same three things from what the user described and your conversation history.

Keep it concise. The entry in agents.md should be scannable, not a wall of text.

## Step 3: Add the Entry to agents.md

Add the entry under a `## Queued Context` section. This section goes after `## Project-Specific Context` (or at the end of the file if that section doesn't exist).

**If `## Queued Context` already exists**, append the new entry to it.
**If it doesn't exist**, create it.

### Entry Format

```markdown
## Queued Context

- [[Source Document Name]] — Summary of what to apply. *Relevance: when this context matters.*
```

For example:

```markdown
## Queued Context

- [[RE - Read.ai Platform Reverse Engineering]] — Reverse-engineered Read.ai API surface: lazy-load heavy endpoints (transcripts/metrics), unified clip model for shareable segments, async processing with status polling, pre-generated copilot questions. *Relevance: apply these patterns when designing the meeting lifecycle UI for Flora Portal.*
- [[PIC - MIP Phase 3 Context Enrichment]] — Context assembler needs to handle per-segment S-label mismatches using person_id from speaker_map, not raw labels. 8k token budget with priority truncation. *Relevance: when building the context assembler in limitless-sync/intelligence/.*
```

Each entry should be:
- **One bullet point** — no sub-bullets or multi-paragraph entries
- **Linked to the source** via Obsidian wikilink `[[Document Name]]` — if the source is a PIC that references other documents (like a research report), link both: `[[RE - Source Report]] · [[PIC - Source Pickup]]`. The PIC often contains context the referenced document doesn't (e.g., session notes, dad's vision, feature mappings).
- **Summarized in 1-2 sentences** focusing on what to *do* with the information, not a full recap
- **Tagged with relevance** in italics so a future agent can quickly judge whether it applies to their current task

## Step 4: Park the Source PIC (if applicable)

If the source is a PIC (Pickup document), update its frontmatter to mark it as parked:

```yaml
status: parked
parked_date: "YYYY-MM-DD"
parked_to: "[project name]"
```

The `parked` status means the PIC's context has been embedded in the target project's agents.md and will surface automatically when future agents work on that project. Parked PICs are excluded from `/pickup` listings and `/pickup-triage` active counts — they're neither open work nor closed work, they're deferred context.

Ask the user before parking — they may want the PIC to remain open if there's other work in it beyond what was parked. If only part of the PIC's context is being parked, leave it as `open` and note in the agents.md entry which items were parked.

## Step 5: Confirm

Tell the user what you did:
- Which agents.md was updated
- The entry that was added
- Whether the source PIC was closed (if applicable)

That's it. Keep it simple.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
