---
name: video-intel
description: >-
  Full-pipeline YouTube video intelligence: transcribe a video or playlist, generate
  summaries, store in the vault, then evaluate content against all active projects for
  relevance and actionable value. If the initial assessment finds potential value,
  dispatches a research team for a comprehensive deep dive with current best practices,
  implementation recommendations, and project-specific application notes. Supports
  single video URLs and playlist URLs — for playlists, enumerates all videos, skips
  already-processed ones, and batch-processes the rest with a summary report.
  Use this skill whenever the user shares a YouTube URL (video or playlist) and wants to
  know if the content is useful for their work, says "check this video out", "is this
  relevant to what we're working on", "research this video", "video intel", "analyze
  this video", "what can we use from this", "process this playlist", "scan this playlist",
  or any variation of wanting YouTube content evaluated against active projects. Also
  trigger when the user pastes a YouTube link with context suggesting they want more than
  just a transcript — e.g., "found this, might be useful for FWIS" or "someone recommended
  this for the signal engine". Also handles simple transcription requests ("transcribe
  this"), YouTube search ("find videos about X"), and channel browsing ("channel @handle")
  — this is the single skill for all YouTube intelligence work.
---

# Video Intelligence Pipeline

Transform a YouTube video into actionable project intelligence. The pipeline has five phases, each gated so you don't waste time on content that turns out to be irrelevant. Supports single videos and playlists.

**Arguments:** $ARGUMENTS

## Phase 0: Input Routing

Determine whether the input is a single video or a playlist, then route accordingly.

### Detect input type

- **Playlist URL** — contains `list=PL` or `list=UU` or `list=LL` or `list=FL` or `list=OL`, or is a `youtube.com/playlist?list=` URL
- **Single video URL** — contains `watch?v=` or `youtu.be/`
- **Ambiguous** (URL has both `v=` and `list=`) — treat as playlist; the individual video will be processed as part of the batch

### Single video path

Skip to Phase 1 with the video URL. Business as usual.

### Playlist path

1. **Fetch the playlist manifest** using TranscriptAPI:
   ```bash
   curl -s "https://transcriptapi.com/api/v2/youtube/playlist/videos?playlist=<PLAYLIST_URL>" \
     -H "Authorization: Bearer <API_KEY>"
   ```
   If `has_more` is true, paginate by calling again with `?continuation=<continuation_token>` until all videos are collected.

2. **Check for already-processed videos.** For each video in the manifest, search `06_Media/Transcripts/` for a `TR -` file whose `source_url` frontmatter contains the video ID. Build two lists:
   - `already_processed` — videos with existing TR files (skip these)
   - `to_process` — videos without TR files

3. **Present the batch summary** to the user:
   ```
   **Playlist:** <playlist_info.title> by <playlist_info.ownerName>
   **Videos:** <total> total, <already_processed count> already scanned, <to_process count> to process
   ```
   Then list the videos to process (numbered, with title and length). Ask: "Process all, or pick specific videos?" using AskUserQuestion with options: "Process all (Recommended)", "Let me pick", "Skip — just wanted the inventory".

4. **Process each unprocessed video** through Phase 1→5 sequentially. Between videos, keep a running tally for the batch report (see Phase 5b).

5. **Rate limiting:** TranscriptAPI allows 300 req/min. Process videos sequentially with no artificial delay — the pipeline's natural processing time provides sufficient spacing.

## Phase 1: Transcribe & Store

Use the same TranscriptAPI machinery as the `/yt` skill. Read the API key from memory or config.

1. Extract the video ID from the URL (11 chars after `v=` or `youtu.be/`)
2. Fetch the transcript:
   ```bash
   curl -s "https://transcriptapi.com/api/v2/youtube/transcript?video_url=<ID>&format=json&include_timestamp=false&send_metadata=true" \
     -H "Authorization: Bearer <API_KEY>"
   ```
3. Parse `metadata.title`, `metadata.author`, join `transcript[].text` with spaces
4. Format into ~150-word paragraphs, breaking at sentence boundaries
5. Save as `06_Media/Transcripts/<YYYY-MM-DD>/<Video Title>/TR - <Video Title>.md` with frontmatter. Structure is date folder → title subfolder → files. Use today's date for the date folder:
   ```yaml
   ---
   date created: YYYY-MM-DD
   category: Transcript
   source_url: <full YouTube URL>
   video_title: "<Title>"
   channel: <Channel>
   date_fetched: YYYY-MM-DD
   ---
   ```

Tell the user: "Transcript saved. Generating summary and scanning projects..."

## Phase 2: Summarize

Read the transcript you just saved and generate a summary following the vault's Transcript Summary Workflow.

**Output:** `06_Media/Transcripts/<YYYY-MM-DD>/<Video Title>/TS - <Video Title>.md` (same date + title subfolder as the transcript)

**Frontmatter:**
```yaml
---
category: Transcript Summary
source: "[[TR - <Video Title>]]"
source_url: <URL>
date_created: YYYY-MM-DD
tags: [<relevant topic tags>]
---
```

**Sections:**
1. **TL;DR** — 1-2 sentence core takeaway in blockquote
2. **Key Takeaways** — 5-8 numbered actionable insights
3. **Summary** — Organized by `###` topic sections mirroring the video's structure. 2-4 sentences per section.
4. **Notable Details** — Concrete specifics: numbers, tool names, configs, costs. Table or bullet format.

Do NOT write the "Relevant To" section yet — Phase 3 handles that with real project context.

## Phase 3: Project Relevance Assessment

This is where the skill earns its keep. You need to understand what the user is actively working on, then judge whether the video content has genuine value.

### 3a. Scan active projects

Dispatch a **haiku-model Explore subagent** to quickly gather project context. It should:

1. Read `02_Projects/` directory listing to identify active project folders
2. For each project that has an `agents.md`, read the first 50 lines to get the project scope
3. Read the most recent daily note (`01_Notes/Daily/DN - <today or most recent>.md`) to see what the user is actively working on right now
4. Check for any active specs (`SPC - *.md`) or plans (`PL - *.md`) in the top 3-4 most active project folders (judged by recent daily note mentions)
5. Return a structured brief: project name, current focus, key technologies, open problems

This scan should take 30-60 seconds. The goal is a lightweight snapshot of the user's current work landscape, not an exhaustive audit.

### 3b. Evaluate relevance

With the project brief and the video summary in hand, assess each active project against the video content. For each project, answer:

- **Direct applicability**: Does the video cover a technology, pattern, or approach that directly solves a current problem or implements a planned feature?
- **Architectural insight**: Does it introduce patterns or best practices that would improve how something is built?
- **Risk/opportunity**: Does it reveal risks in the current approach, or opportunities the user hasn't considered?

**Scoring** (internal, don't show raw scores to user):
- **3 = High**: Direct, actionable value for an active project. The user would want to act on this.
- **2 = Medium**: Interesting context or background knowledge that informs decisions but doesn't require immediate action.
- **1 = Low**: Tangentially related. Nice to know, not worth a deep dive.
- **0 = None**: No meaningful connection.

### 3c. Decision gate

- If ANY project scores **3**: Proceed to Phase 4 (full deep dive)
- If highest score is **2**: Present the TLDR and relevance notes. Ask if the user wants a deep dive anyway.
- If all scores are **1 or 0**: Present the TLDR, note the weak connections, save the summary, done.

## Phase 4: Deep Dive Team Dispatch

When the assessment finds high-value content, dispatch a research team to produce a comprehensive analysis. The Vector Search / Computerphile summary in the vault is the quality bar — that level of depth, with current best practices research, implementation specifics, and project-tailored recommendations.

### Team composition

Use `TeamCreate` to spin up a team with these roles:

**1. Researcher** — Investigates the video's topics against current best practices (2025-2026). Uses Brave Search MCP to find:
- Current state of the art for the technologies/patterns discussed
- Known limitations, gotchas, and production lessons
- Competing approaches the video may not have covered
- Pricing, licensing, and infrastructure requirements

Write findings to `ARE - <Video Title> Research Notes.md` in the same directory as the TR/TS files.

**2. Architect** — Maps findings to the specific project(s) that scored high. Reads the project's agents.md, specs, plans, and existing codebase context to produce:
- How to apply the video's insights to the user's specific stack
- What changes would be needed (new dependencies, schema changes, config)
- Implementation phases with effort estimates
- Risks and trade-offs specific to the user's environment

Write findings to `ARE - <Video Title> Architecture Notes.md` in the same directory as the TR/TS files.

**3. Writer** — Reads the researcher output (`ARE - <Video Title> Research Notes.md`) and architect output (`ARE - <Video Title> Architecture Notes.md`) and produces the final deep dive document. The output replaces the Phase 2 summary with a much richer version.

### Deep dive output

The writer updates `TS - <Video Title>.md` to include everything from Phase 2 PLUS:

5. **Current Best Practices (2025-2026)** — What the researcher found. Organized by topic with tables comparing options, concrete recommendations, and citations.
6. **Project Application: <Project Name>** — One section per high-scoring project. Implementation path, recommended tools, SQL/code snippets where relevant, estimated costs.
7. **Key Takeaways** — Updated to reflect the deeper analysis, not just the video content
8. **Sources** — All research links with brief descriptions

### Resources file

When a deep dive is produced, also save a `REF - <Video Title>.md` file in the same directory as the TR and TS files. This collects all external links discovered during research — the video's referenced articles, researcher-found sources, and any supplemental URLs the user provided. Organize by topic with brief descriptions per link. Use standard REF frontmatter with `category: Reference`.

### Task coordination

The Researcher and Architect can run in parallel (researcher does web research while architect reads project context). The Writer waits for both to complete. Use `TaskCreate` with dependencies to enforce this ordering.

## Phase 5: Present Results

### 5a. Single video briefing

After all phases complete for a single video, present the user with a concise briefing:

```
**Video:** <Title> by <Channel>
**Saved:** [[TR - <Video Title>]] | [[TS - <Video Title>]] | [[REF - <Video Title>]]

**TL;DR:** <1-2 sentence takeaway>

**Relevant to:** <Project names that scored 2+, with one-line reason each>

<If deep dive was run:>
**Deep dive complete.** Key finding: <single most actionable insight>
```

Then ask (using AskUserQuestion): "Want to discuss any of the findings, or is the written report sufficient?"

### 5b. Playlist batch report

After all videos in a playlist batch are processed, produce a summary report block. This block is both displayed to the user AND written to the daily note.

**Format:**

```markdown
### Video Intel — <Playlist Title>
- **Processed:** <N> of <total> videos (<already_processed> previously scanned)
- **High relevance:** <count> → deep dive dispatched
- **Medium relevance:** <count> videos
- **Low/None:** <count> videos

| Video | Score | Key Takeaway |
|-------|-------|--------------|
| [[TS - <Video Title>]] | 🔴 High | <one-line actionable insight> |
| [[TS - <Video Title>]] | 🟡 Med | <one-line context summary> |
| [[TS - <Video Title>]] | 🟡 Med | <one-line context summary> |
| [[TS - <Video Title>]] | ⚪ Low | <one-line reason it's low> |
```

**Rules for the table:**
- Sort by score descending (High → Med → Low)
- Link to the TS (summary) file, not the TR (transcript)
- Key Takeaway is a single phrase — no full sentences, no periods
- If a deep dive was dispatched, append ` (deep dive)` to that row's Key Takeaway
- For single videos, use the same format but with one table row and no "X of Y" stats line

### 5c. Single video daily note report

For single videos, use the same table format but simplified:

```markdown
### Video Intel — <Video Title>
| Video | Score | Key Takeaway |
|-------|-------|--------------|
| [[TS - <Video Title>]] | 🔴 High | <one-line insight> (deep dive) |
```

## Vault Hygiene

- **Playlist batch reports** go in a dedicated report file: `02_Projects/<relevant-project>/reports/YYYY-MM-DD/RE - Video Intel Playlist Batch YYYY-MM-DD.md`. The daily note gets a one-liner linking to the report: `- [[RE - Video Intel Playlist Batch YYYY-MM-DD]] — <N> videos processed, <highlights>`
- **Single video reports** use the compact format (Phase 5c) directly on the daily note — these are small enough to inline
- If a deep dive was produced, the report file is the right place for the full table, P1/P2 actions, and artifact links
- If a deep dive was produced, also link the summary under the relevant project's heading in the daily note
- Tag the summary with project-relevant tags so it shows up in Obsidian graph view

## Lightweight Actions (formerly /yt)

These actions don't run the full intelligence pipeline — they're quick utility operations. video-intel subsumes the old `/yt` skill.

### `search <topic>` — Find videos

1. Use `mcp__brave-search__brave_web_search` with query `site:youtube.com <topic>`, request 10-20 results
2. Filter to actual video pages (URLs with `watch?v=` or `youtu.be/`) — discard channels, playlists, shorts
3. Present a numbered list: `N. <Title> — <URL>`
4. Ask which to transcribe (numbers, ranges like "1-3", or "all")
5. For selected videos, run the full Phase 1→5 pipeline (not just transcription)

### `transcribe <url>` — Quick transcription only

When the user explicitly says "just transcribe" or "transcribe only":
1. Run Phase 1 only (transcribe and store)
2. Offer to generate a summary (Phase 2) but don't auto-run the project assessment
3. This is the escape hatch for when the user doesn't want the full pipeline

### `channel <handle-or-url>` — Browse a channel

1. Resolve channel (free): `GET /api/v2/youtube/channel/resolve?identifier=<HANDLE>`
2. Fetch latest 15 videos (free): `GET /api/v2/youtube/channel/latest?channel_id=<ID>`
3. Present numbered list, ask which to process
4. Selected videos run through the full pipeline

### No arguments — Default playlist

When invoked with no arguments, process the default watch playlist:
`https://www.youtube.com/playlist?list=PLYLj0aEKmGayRoq6s6zjWUIqfbJyXd6bv`

Follow the standard playlist path (Phase 0 → playlist routing). This makes `/video-intel` a one-command "process my queue" action.

### `help` — Show usage

```
/video-intel                      Process default watch playlist
/video-intel <url>                Full pipeline on a single video
/video-intel <playlist-url>      Batch process a playlist
/video-intel search <topic>      Search YouTube for videos
/video-intel transcribe <url>    Quick transcription only (no project assessment)
/video-intel channel <@handle>   Browse a channel's recent uploads
```

## Edge Cases

- **Cooking/recipe video**: Skip the project relevance assessment entirely. Follow the Recipe Output path from the Transcript Summary Workflow instead. Save to `02_Food/Recipes/`.
- **Video already transcribed**: Check `06_Media/Transcripts/` first. If a `TR -` file exists for this video ID, skip to Phase 2 using the existing transcript.
- **TranscriptAPI failure**: Fall back to Brave Search for a text summary of the video content. Note in the output that full transcript wasn't available.
- **No active projects found**: Skip Phase 3/4 entirely. Just save transcript + summary and present the TL;DR.
- **Large playlist (50+ videos)**: Warn the user about credit cost (1 credit per transcript + 1 per playlist page). Suggest processing in batches or filtering by title keywords.
- **Mixed playlist (some already processed)**: Only process new videos. The batch report should still mention the total count and how many were skipped as "previously scanned."
- **Playlist pagination**: Some playlists exceed 100 videos. Always check `has_more` and paginate with `continuation` tokens until all videos are collected before presenting the batch summary.
