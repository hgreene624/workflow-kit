---
name: create-MN
description: >-
  Create structured meeting notes from any input source - raw transcript, lifelog data,
  pasted text, or conversational dictation. Use this skill whenever the user wants to
  create meeting notes, says "create meeting notes", "MN for", "meeting note",
  "write up the meeting", "process this meeting", or provides meeting content and
  wants it structured.
---

# Create Meeting Note

Generate a structured meeting note from whatever input the user provides. No interview - work entirely from the supplied content.

## Step 1 - Receive Input

Accept meeting content in any form:
- **Raw transcript** (pasted text, VTT, or SRT)
- **Limitless lifelog data** (JSON or already-processed summaries)
- **Conversational dictation** ("we talked about X, then Y, then Z")
- **Unstructured notes** (bullet points, fragments, stream of consciousness)
- **Arguments to the command** (e.g., `/create-MN topic: weekly standup, attendees: Holden, Dad`)

If the user provides no content at all, ask: "Paste or describe the meeting content and I'll structure it." Do not interview topic-by-topic - take whatever they give in one pass.

## Step 2 - Extract Structure

Parse the input to identify:

1. **Date** - from content, filename, or today's date as fallback
2. **Attendees** - only explicitly mentioned participants. Never infer attendees from context. If speaker diarization uses aliases ("You", "Speaker 1"), map them only when the real name is unambiguous from content.
3. **Topic** - a short descriptor for the filename parenthetical. Derive from the dominant theme or ask if unclear.
4. **Topics/Agenda items** - group related discussion into discrete topic blocks. Each topic must have at least one concrete detail.
5. **Per-topic content:**
   - **Discussion** - hierarchical bullets capturing conversation flow, reasoning, context, who said what. **Bold** key details (dates, costs, decisions, owners, names).
   - **Decisions** - only explicitly stated decisions. Omit section entirely if none.
   - **Plans** - ideas or direction discussed without a clear owner or deliverable yet (e.g., "exploring adding a mezcal section" with no decision). If a topic had discussion but no decision and no action, use Plans to capture the direction. Omit if none.
   - **Actions** - owned tasks with a clear deliverable and owner. Format as `- [ ] Owner: description`. Omit if none.

## Step 3 - Quality Rules

These rules are non-negotiable for every meeting note:

### Content fidelity
- Never invent, infer, or embellish. If something wasn't said, it doesn't go in the note.
- Capture the reasoning and context behind decisions, not just the decision itself.
- Preserve specifics: names, numbers, dates, dollar amounts. Never round or generalize.
- Bold key details throughout discussion bullets.

### Structure
- Every topic heading (`###`) must have a Discussion section with substantive content.
- Omit Decisions/Plans/Actions subsections entirely when empty rather than leaving them blank.
- No bottom-level consolidated Action Items section - actions live inline under their topic.
- Use `#### Discussion`, `#### Decisions`, `#### Plans`, `#### Actions` as subsection headings.

### Signal vs. noise
- Skip greetings, wrap-ups, small talk, ambient noise, and filler.
- Collapse repetitive back-and-forth into the conclusion or key exchange.
- Every bullet should carry information the reader would want when reviewing this note later.

### Style (from vault guardrails)
- No em dashes. Use commas, periods, parentheses, or ` - ` if a dash is needed.
- Tight spacing. No double blank lines.
- Concise for executives - these notes get shared with stakeholders who skim.

## Step 4 - Generate the File

**Filename:** `MN - YYYY-MM-DD (<Topic>).md`
**Location:** `Work Vault/01_Notes/Meetings/`

Use this exact structure:

```markdown
---
date created: YYYY-MM-DD
tags:
  - meeting
  - <relevant-project-or-domain-tags>
category: Meeting
---

## Attendees
- <Name>
- <Name>

---
## Agenda / Topics

### <Topic title>
#### Discussion
- <Hierarchical bullets capturing conversation flow, reasoning, who said what>
- **Bold** key details

#### Decisions
- <Only if explicitly stated>

#### Plans (ideas/direction; no owner/deliverable yet)
- <Only if discussed>

#### Actions (owned tasks with clear deliverable)
- [ ] <Owner>: <Task description>

### <Next topic>
...

---
## Notes (optional scratchpad)
- <Only if there's extra context not captured in topics>

---
```

## Step 5 - Link in Daily Note

If a daily note exists for the meeting date (`DN - YYYY-MM-DD.md`), add a link under the `## Meetings/Calls` section:

```markdown
- <Time if known> <Primary attendee> - [[MN - YYYY-MM-DD (<Topic>)]]
  - **Key takeaway 1**
  - **Key takeaway 2**
```

If no daily note exists or the section can't be found, skip this step silently.

## Step 6 - Present

Show the user the generated filename and a brief summary:
- Number of topics extracted
- Number of action items found
- Any content that was ambiguous or dropped (explain why)

Do not ask for confirmation before writing - just write it. The user can review and request changes.
