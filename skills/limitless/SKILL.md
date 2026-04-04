---
name: limitless
description: Fetch Limitless lifelog data, store it in the vault, and generate meeting notes. Use this skill whenever the user mentions lifelogs, Limitless recordings, "process today's meetings", "what meetings did I have", "update lifelogs", "create meeting notes from recordings", "process yesterday's calls", or any reference to turning Limitless pendant recordings into structured notes. Also trigger on "fetch lifelogs", "sync limitless", "meeting summary from limitless", or when the user asks about meetings from a specific date and lifelogs are the source. Even casual requests like "what did I talk about today" or "summarize my meetings" should trigger this if the user has a Limitless pendant.
---

# Limitless Lifelog Processor

Fetches raw lifelog data from the Limitless API, archives it as JSON in the vault, and generates structured meeting notes from the recordings.

## Step 1 — Fetch & Store Lifelogs

Run the update script to pull latest data from the Limitless API. The script reads the API key from macOS Keychain (`limitless-api-key`) or the `LIMITLESS_API_KEY` env var.

```bash
LIMITLESS_TIMEZONE={{TIMEZONE}} python3 "04_ Tools/Limitless/update_lifelogs.py"
```

**Common flags:**
- Default: fills missing dates and refreshes last 2 days
- `--date=YYYY-MM-DD` — fetch a single date
- `--start=YYYY-MM-DD --end=YYYY-MM-DD` — backfill a range
- `--refresh-days=N` — refresh the N most recent days
- `--force` — rewrite all dates from earliest archive through today

**Output location:** `01_Work/01_Notes/Limitless Lifelogs/lifelogs_YYYY-MM-DD.json`

If no lifelogs exist for the requested date, stop and tell the user — do not generate empty notes.

## Step 2 — Read & Triage the Lifelogs

Open the JSON for the target date. Each file has this structure:
- `lifelogs[]` — array of recording sessions
- Each lifelog has `contents[]` with typed entries:
  - `heading1` — meeting/session title
  - `heading2` — section headers
  - `paragraph` / `blockquote` — transcript with optional `speakerName`, `startTime`, `endTime`

**Triage rules — which meetings to process:**
- Prioritize meetings with clear, direct discussion of a specific topic
- Secondary signals: longer duration, ties to active work initiatives, structured agendas
- Skip: ambient radio/music, small talk without actionable content, personal conversations unless they contain work decisions
- When in doubt, favor clarity and work relevance over length

## Step 3 — Apply Event Hierarchy

Before writing any notes, organize the raw data:

1. **Build a timeline** — titles + start/end times for the target date
2. **Group into events:**
   - Merge interruptions when the subject is continuous within 60 minutes
   - Consolidate adjacent lifelog entries that are the same conversation (shared participants/topic + continuous time) — use the earliest start time
   - If a thread is unrelated and too small for its own note, skip it or fold it as a side topic
3. **Extract important points** (explicit facts only):
   - Dates, availability windows, decisions, approvals, costs, deadlines, owners, next actions
   - **Bold** key details (dates, costs, decisions, owners)
   - Skip low-signal content: greetings, wrap-ups, banter, ambient noise
   - Identify participants only when explicit (`speakerName` or clear transcript mention) — never infer
   - Every topic heading must have at least one concrete detail bullet; drop empty headings

## Step 4 — Generate Meeting Notes

For each significant meeting, create a meeting note file.

**Filename:** `MN - YYYY-MM-DD (<Topic>).md`
**Location:** `01_Work/05_Meetings/Meeting_Notes/`

**Template structure:**
```markdown
---
date created: YYYY-MM-DD
tags:
  - meeting
category: Meeting
---

## Attendees
- <Only explicitly identified participants>

---
## Agenda / Topics

### <Topic title>
#### Discussion
- <Hierarchical bullets: conversation flow, reasoning, context>
- **Bold** key details (dates, costs, decisions, owners)

#### Decisions
- <Only explicitly stated decisions>

#### Actions (owned tasks with clear deliverable)
- <Only explicitly assigned actions with owners>

---
## Action Items
(dataviewjs block for Obsidian task aggregation)

---
```

**Rules:**
- Omit Decisions/Actions sections entirely if nothing was explicitly stated
- Include the `dataviewjs` block for Action Items exactly as shown in the template at `04_ Tools/Templates/Meeting Notes Template.md`
- Convert `startTime` values to local time in 12-hour format
- Keep meeting notes self-contained — do not reference or modify the source JSON

## Step 5 — Generate Daily Summary (if multiple meetings)

When processing multiple meetings for one day, also create a daily overview.

**Filename:** `AIS - limitless_meetings_YYYY-MM-DD.md`
**Location:** `01_Work/01_Notes/Limitless Lifelogs/AI Meeting Summaries/Daily/`

**Structure:**
```markdown
---
date created: YYYY-MM-DD
tags: [limitless, daily]
---

# Meetings Overview — YYYY-MM-DD

## <Meeting title> — start <time>
### Main points
- <1-3 key points>

### Outcomes
- <If any>

### Follow-up
- <Only items explicitly stated by the user or assigned to them>
```

Order meetings from latest to earliest. Omit Outcomes/Follow-up sections if empty.

## Step 6 — Link in Daily Note

Add meeting note links to the daily note at `01_Work/01_Notes/Daily/DN - YYYY-MM-DD.md` under the Meetings/Calls section:

```markdown
- (time) Person — [[MN - YYYY-MM-DD (Topic)]]
  - **Key detail 1**
  - **Key detail 2**
```

Format: `- (time) <Person> — <topic>` when participant is explicit; otherwise `- (time) <topic>`.

## Reference Paths

| Type | Path |
|------|------|
| Update script | `04_ Tools/Limitless/update_lifelogs.py` |
| Raw lifelogs | `01_Work/01_Notes/Limitless Lifelogs/lifelogs_YYYY-MM-DD.json` |
| Backup archive | `01_Work/01_Notes/Limitless Lifelogs/Archive/` |
| Meeting notes output | `01_Work/05_Meetings/Meeting_Notes/` |
| Daily summaries | `01_Work/01_Notes/Limitless Lifelogs/AI Meeting Summaries/Daily/` |
| Weekly summaries | `01_Work/01_Notes/Limitless Lifelogs/AI Meeting Summaries/Weekly/` |
| Meeting template | `04_ Tools/Templates/Meeting Notes Template.md` |
| Daily summary template | `04_ Tools/Templates/AIS - limitless_meetings_template.md` |
| Full workflow reference | `04_ Tools/Reference/REF - Limitless Lifelogs Workflow.md` |

## Quality Checks

Before finishing, verify:
- Every topic heading has at least one concrete detail bullet
- Key details are **bolded** (dates, costs, decisions, owners)
- Empty sections (Decisions, Actions, Outcomes, Follow-up) are omitted entirely
- Participants are only listed when explicitly identified — never inferred
- Meeting notes are linked in the daily note
- No meeting note was created for empty/ambient-only recordings

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
