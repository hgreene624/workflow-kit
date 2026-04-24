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

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{vault_root}/{paths.meetings}/` for meeting note output). If the file doesn't exist, use defaults and warn once.

## Step 1 - Receive Input

Accept meeting content in any form:
- **Raw transcript** (pasted text, VTT, or SRT)
- **Limitless lifelog data** (JSON or already-processed summaries)
- **Conversational dictation** ("we talked about X, then Y, then Z")
- **Unstructured notes** (bullet points, fragments, stream of consciousness)
- **Arguments to the command** (e.g., `/create-MN topic: weekly standup, attendees: Alice, Bob`)

If the user provides no content at all, ask: "Paste or describe the meeting content and I'll structure it." Do not interview topic-by-topic - take whatever they give in one pass.

## Step 2 - Extract Structure

Parse the input to identify:

1. **Date** - from content, filename, or today's date as fallback
2. **Attendees** - only explicitly mentioned participants. Never infer attendees from context. If speaker diarization uses aliases ("You", "Speaker 1"), map them only when the real name is unambiguous from content.
3. **Topic** - a short descriptor for the filename parenthetical. Derive from the dominant theme or ask if unclear.
4. **Parts vs. single-segment** - determine whether the meeting has distinct temporal segments (see Step 2.5).
5. **Topics/Agenda items** - group related discussion into discrete topic blocks. Each topic must have at least one concrete detail.
6. **Per-topic content:**
   - **Discussion** - hierarchical bullets capturing conversation flow, reasoning, context, who said what. **Bold** key details (dates, costs, decisions, owners, names).
   - **Decisions** - only explicitly stated decisions. Omit entirely if none.
   - **Plans** - ideas or direction discussed without a clear owner or deliverable yet. Omit if none.
   - **Actions** - owned tasks with a clear deliverable and owner. Format as `- [ ] Owner: description`. Omit if none.

## Step 2.5 - Parts Detection

A meeting needs **Parts** when it has distinct temporal segments separated by:
- Location change (moved rooms, went to someone's office)
- Participant change (someone joined or left)
- Clear temporal gap (break, pause, reconvened later)
- Distinct shift in meeting mode (informal chat became structured discussion)

**Rules:**
- If there are no clear segment boundaries, do NOT use parts. Just use topics directly.
- Parts are temporal containers. Topics organize by subject matter within each part.
- Every part must have a descriptive title and time range (if available).
- A meeting with only one segment does not get a Part wrapper.

## Step 3 - Quality Rules

These rules are non-negotiable for every meeting note:

### Content fidelity
- Never invent, infer, or embellish. If something wasn't said, it doesn't go in the note.
- Capture the reasoning and context behind decisions, not just the decision itself.
- Preserve specifics: names, numbers, dates, dollar amounts. Never round or generalize.
- Bold key details throughout discussion bullets.

### Structure
- Every topic heading must have substantive discussion content.
- Omit Decisions/Plans/Actions entirely when empty for a given topic.
- No bottom-level consolidated Action Items section - decisions and actions live inline under their topic.

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

### Format A: Single-Segment Meeting (no parts)

Use when the meeting is one continuous conversation without temporal breaks.

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

### Format B: Multi-Part Meeting (temporal segments)

Use when the meeting has distinct parts (location change, participant change, temporal gap). Parts at `###`, topics at `####`, with per-topic decisions/actions inline.

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

---

### Part 1: <Descriptive Part Title>
*~HH:MM AM/PM - HH:MM AM/PM, <brief context: location, mode, who's present>*

#### <Topic title>
- <Discussion bullets, hierarchical, capturing flow and reasoning>
- **Bold** key details
- **Decision:** <only if explicitly stated for this topic>
- [ ] <Owner>: <action item, only if explicitly assigned>

#### <Next topic>
- <Discussion bullets>

---

### Part 2: <Descriptive Part Title>
*~HH:MM AM/PM - HH:MM AM/PM, <context>*

#### <Topic title>
- <Discussion bullets>
- **Decision:** <inline if applicable>

---
## Notes (optional scratchpad)
- <Only if there's extra context not captured in topics>

---
```

**Format B rules:**
- Each `####` topic heading contains its own discussion bullets plus any decisions/actions inline
- Prefix decisions with `**Decision:**` as a bold inline marker within the topic's bullets
- Actions use checkbox format `- [ ] Owner: task` within the topic
- Omit decision/action lines entirely when none exist for that topic (no "Decision: none")
- The time range and context line is italic, immediately below the Part heading
- Horizontal rules (`---`) separate parts for visual clarity

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
