---
name: log-work
description: >-
  Log work to the daily note and a dedicated work log file. Use this skill when
  the user wants to record what they've been working on, says "log this", "log
  work", "add to worked on", "update the daily note", or wants to capture
  implementation progress. Always creates a WL file for detail and a short
  paragraph in the daily note linking to it. Also trigger on "what did I work on"
  if the user wants to retroactively log work from the conversation.
---

# Log Work

Log work to the daily note's `## Worked on` section with a short overview paragraph, backed by a detailed work log (`WL -`) file.

**Arguments:** $ARGUMENTS — Description of work, path to a plan, or nothing (will scan conversation context).

## Step 1 — Determine What to Log

If the user provided arguments, use those. Otherwise, scan the current conversation for:
- Files created or modified (specs, reports, plans, code)
- Deployments or pipeline runs
- Research completed
- Decisions made

Ask the user to confirm what should be logged if it's ambiguous.

## Step 2 — Identify the Workstream Group

Match the work to a **top-level workstream** — the broadest natural grouping for this work. Workstreams map to major products, systems, or activity areas, NOT to individual plans, tasks, or features.

Examples of workstream groups:
- **Flora KB** — migration cleanup, translation pipeline, AI chat, TLDR, edit tool (all KB work)
- **Signal Engine** — transcription, quality gates, briefing system (all signal processing)
- **Document Generator** — v2 redesign, AI chat, research pipeline (all docgen work)
- **FWIS Platform Delivery** — research, spec, phase execution (all FWIS work)
- **Infrastructure & Platform Ops** — env switchover, VPS cleanup, auth, routing fixes
- **Workflow Kit & Tooling** — skill optimization, skill sync, orient improvements, stoplight
- **Research & Planning** — video intel, PIC triage, vault audits, weekly planning, lifelogs

**One heading per workstream in the daily note.** Multiple sub-topics within a workstream get merged under the same heading. If the user did KB translation work AND KB chat work, both go under `### Flora KB`.

Identify the project path under `02_Projects/` if one exists.

## Step 3 — Merge Check

Before creating a new `###` heading, scan ALL existing headings under `## Worked on`:

1. **Match by workstream:** If `### Flora KB` already exists and the new work is KB-related, merge into it.
2. **Match by project:** "MIP Phase 2" and "Meeting Briefing System" both belong under `### Signal Engine`.
3. **Common abbreviations:** MIP = Meeting Intelligence Pipeline → Signal Engine. DGV/DocGen = Document Generator. FAO/FWIS = FWIS Platform Delivery.

When merging, update the existing paragraph to incorporate the new work — don't append a second paragraph.

## Step 4 — Create/Update WL File

### Find or Create

- **Project-scoped:** `02_Projects/<project>/plans/YYYY-MM-DD/WL - Workstream Name.md`
- **Cross-cutting (no single project):** `01_Notes/Work Logs/YYYY-MM-DD/WL - Workstream Name.md`

If a WL file already exists for this workstream and today's date, append to it. Don't create duplicates.

### WL File Format

```yaml
---
date created: YYYY-MM-DD
tags: [work-log, <project-tag>]
category: Work Log
---
```

```markdown
# WL - Workstream Name

## Sub-Topic A
- Detailed bullet
- Detailed bullet with **bold stats**, commit hashes, artifact links
- Closed [[PIC - Whatever]]

## Sub-Topic B
- More detail here
- Everything the daily note omits goes here
```

**WL structure rules:**
- Use `## Sub-Topic` sections for each distinct effort within the workstream
- No timestamps — organize by topic, not by time
- Include everything: commit hashes, file counts, component lists, per-task breakdowns, error details, deployment steps
- Wikilink all output artifacts (specs, reports, PICs, plans)
- Bold key metrics inline

## Step 5 — Update Daily Note

1. Read today's daily note: `01_Notes/Daily/DN - YYYY-MM-DD.md`
2. Run the merge check (Step 3)
3. Find or create the `### Workstream Name` heading under `## Worked on`
   - New topics go at the **top** of the Worked on section
4. Write a **short paragraph** (2-4 sentences) summarizing the work at overview level
5. End the paragraph with a wikilink to the WL file: `[[WL - Workstream Name]]`

### Daily Note Format

Each workstream gets a `###` heading followed by a **short prose paragraph** — not bullets. The paragraph captures what happened at a glance: what was accomplished, key outcomes/stats, and current state. It ends with a wikilink to the detailed WL file.

**HARD RULE: The daily note entry for ANY workstream must be a heading + 2-4 sentence paragraph + WL link. That's it.** All detail goes in the WL file. The daily note is a scannable overview.

**DEPTH CONSISTENCY: More sub-topics means less detail per sub-topic, not a longer paragraph.** A workstream with 6 sub-topics should name each briefly in a single sentence ("translation pipeline deployed, AI chat widget shipped, TLDR backfilled...") rather than expanding each into its own sentence. The WL file has the detail — the daily note just names what happened. Never let a single workstream entry balloon into multiple paragraphs or bullet lists.

### Good Examples

```markdown
### FWIS Platform Delivery
Research → spec → plan → **31 tasks across Phases 0-2 in one session**. v7 code migration complete, actuator + entity processing live, decision linkage jumped from 5.9% → 90.3%. Schema stability contract signed through 2026-04-27. [[WL - FWIS Platform Delivery]]

### Flora KB
Five parallel efforts: migration content cleanup (0 v2 briefs remain), auto-translation pipeline built + deployed (137/177 briefs translated), AI chat widget shipped (4 scope levels, RAG), TLDR summaries backfilled (293/314 briefs), and AI edit tool spec reviewed + ready for plan. [[WL - Flora KB]]

### Signal Engine
Transcription pipeline got per-user control + round-robin. Gloria quality gate now returns structured rejections. Meeting briefing system Phases 3-5 complete (26/26 tasks) — verified working for Aldo. [[WL - Signal Engine]]
```

### Bad Example (too detailed for the daily note)

```markdown
### Flora KB
- **Migration Content Cleanup:**
  - Deleted **4 stub** `-v2` briefs (cross-references only), **6 duplicate** deed-closing briefs
  - Moved **6 rental-focused** briefs to new `rental-operations` bucket with clean slugs
  - **0 v2 briefs remain**, 13 buckets, 107 briefs total
  - Closed [[PIC - KB Migration Content Cleanup]]
- **Auto-Translation Pipeline (Full Sprint):**
  - spec → review → design → structure → plan → implementation (6 phases)
  - Built and deployed: translate endpoint, batch endpoint, glossary API...
  (20 more lines)
```

This is a task log, not an overview. All that detail belongs in `[[WL - Flora KB]]`.

## Paragraph Writing Guide

When writing the daily note paragraph:
- **Lead with the shape of work** — "Five parallel efforts:", "Research → spec → plan →", "Full pipeline:"
- **Name sub-topics briefly** — just enough to know what happened, with key stats in parens
- **Highlight headline numbers** — bold the stats that matter (task counts, percentages, key thresholds)
- **End with current state** if relevant — "ready for plan", "parked", "Phase 1 in progress"
- **Don't enumerate** — summarize. "Fixed 5 deployment bugs" not a list of all 5
- **No implementation detail** — commit hashes, file paths, config keys, endpoint URLs, and component names belong in the WL file only

## Formatting Rules

- Newer entries at top of `## Worked on` section
- `### Workstream Name` heading — no plan links on the heading line (those go in the WL file)
- Short paragraph, not bullets, in the daily note
- Paragraph ends with `[[WL - Workstream Name]]`
- NO "Lifelogs & Meeting Notes" subsection — those go in Meetings
- One heading per workstream — merge, don't duplicate

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
