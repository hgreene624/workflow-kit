---
name: dream
description: "Memory and lesson system consolidation — scan automemory files, merge duplicates, resolve contradictions, prune stale data, cross-reference feedback memories against project lessons for supersession, sync any lesson trigger index, flag stale project lessons, and tighten the MEMORY.md index. Use this skill whenever the user says 'dream', 'consolidate memory', 'clean up memory', 'prune memory', 'memory consolidation', '/dream', or mentions that their memory feels bloated, stale, or contradictory. Also trigger when the user is doing end-of-day closeout and wants a memory hygiene pass, or says 'tighten memory', 'memory cleanup', 'dedupe memory'. Even a casual 'my memory is getting messy' should trigger this."
---

# Dream — Memory Consolidation

A reflective pass over your memory files. Synthesize what you've learned recently into durable, well-organized memories so that future sessions can orient quickly.

## Arguments

| Argument | Scope | Memory directory | Index file |
|----------|-------|-----------------|------------|
| *(none)* or `project` | Current project | `~/.claude/projects/<encoded-cwd>/memory/` | `MEMORY.md` in that directory |
| `user` | User-level (all projects) | `~/.claude/memory/` | `MEMORY.md` in that directory |
| `all` | Both scopes | Both directories | Both index files |

Where `<encoded-cwd>` is the current working directory with `/` replaced by `-` and leading `-` (e.g., `-Users-username-Documents-Vaults-Work-Vault`).

Session transcripts are JSONL files in the **project directory** (sibling to `memory/`, not inside it): `~/.claude/projects/<encoded-cwd>/*.jsonl`

If you're running at `user` scope, there are no user-level transcripts — just consolidate what's in the memory directory.

## Phase 1 — Orient

Get the lay of the land before changing anything.

1. `ls` the memory directory to see every file
2. Read `MEMORY.md` to understand the current index — note its line count and size
3. Read each memory file (they're small — usually under 50 lines). Build a mental map: what topics are covered, what types (user/feedback/project/reference), any obvious overlaps or tensions between files
4. If the memory directory is empty or MEMORY.md doesn't exist, say so and stop — nothing to consolidate

The goal here is to understand the full picture before touching anything. Rushing to edit without reading everything is how you create new contradictions.

## Phase 2 — Gather recent signal

Look for information that should update what's in memory. Sources in priority order:

1. **Existing memories that drifted** — facts in memory files that contradict current reality. For example, a project memory saying "using SQLite" when the codebase now uses Postgres, or a feedback memory about a workflow that no longer exists.

2. **Transcript search** — if you suspect a memory might be stale or there's been a recent shift, grep the JSONL transcripts for narrow terms. Never read whole transcript files — they're huge.
   ```bash
   grep -rn "<specific term>" ~/.claude/projects/<encoded-cwd>/*.jsonl | tail -30
   ```
   Look at the last 5-10 sessions worth of transcripts (sort by modification time, take the most recent). You're looking for corrections, preference changes, or new patterns that should update existing memories.

3. **Relative dates** — scan all memory files for relative time references: "yesterday", "last week", "next Friday", "recently", "soon", "a few days ago". These decay in meaning and need to be converted to absolute dates or removed if they're no longer relevant.

## Phase 3 — Consolidate

Now make changes. For each issue you identified, act on it:

### Merge near-duplicates
If two files cover the same topic (e.g., `feedback_testing.md` and `feedback_test_approach.md`), merge them into one file. Keep the better filename. Preserve all non-redundant information from both files. Delete the duplicate.

### Resolve contradictions
If two memories disagree (e.g., one says "use React" and another says "never use React"), determine which is current by checking transcript evidence. Update the correct one, delete the wrong one.

### Fix stale data
If a memory references something that no longer exists (a removed file, a completed project, an outdated preference), either update it to reflect current state or delete it if it's no longer useful.

### Convert relative dates
Replace every relative date with an absolute one. If you can determine the date from context (the memory file's creation date, nearby transcript timestamps), use that. If you can't determine the exact date, note it as approximate: "~2026-03-20". If the date was the entire point of the memory and it's now past, consider whether the memory is still useful.

### Respect memory type conventions
When editing memory files, maintain the frontmatter format from the system prompt's automemory section:
```yaml
---
name: {{memory name}}
description: {{one-line description}}
type: {{user, feedback, project, reference}}
---
```
For feedback and project types, keep the structure: rule/fact, then **Why:** and **How to apply:** lines.

### What NOT to do
- Don't create new memories during consolidation — this is a cleanup pass, not a creation pass
- Don't change the meaning of a memory, only its accuracy and currency
- Don't remove memories just because they seem minor — if they were worth saving, they're probably worth keeping unless actually wrong or stale

## Phase 3b — Cross-tier dedup

Check whether any feedback memory has been superseded by a formalized rule in a higher tier. This is the structural fix for the "same rule loaded from two places" problem.

**Tiers (lowest to highest):** feedback memory → project `lessons.md` → vault-level lessons reference (if present) → `CLAUDE.md` rule

**Procedure:**

1. If your vault keeps a consolidated agent-lessons reference (e.g., `REF - Agent Lessons.md`), read it (or grep for key terms if too large to read fully). Skip this sub-step if no such file exists.
2. Read the `## Rules` sections of any `CLAUDE.md` files that load into the current scope (root and vault-level).
3. For each feedback memory, check if the same behavioral rule exists in a higher tier:
   - Compare the feedback memory's core directive (the "what to do" part) against the higher-tier rule's condition/action.
   - A match means: same trigger condition AND same prescribed action, even if worded differently.
   - A partial match (same topic, different angle) is NOT a duplicate. Only supersede exact behavioral overlaps.
4. For each confirmed duplicate, replace the feedback file content with a supersession pointer:
   ```markdown
   ---
   name: {{original name}}
   description: Superseded by {{target reference}}
   type: feedback
   superseded_by: "{{lesson ID or CLAUDE.md rule name}}"
   ---
   Superseded. See {{target reference}}.
   ```
5. Remove superseded entries from MEMORY.md.
6. Report all supersessions in the output summary under `### Cross-tier supersessions`.

**What NOT to supersede:**
- Feedback about interaction style (question format, response tone, emoji preferences) that has no higher-tier equivalent
- Feedback that adds context the higher-tier rule doesn't capture (the "why" behind a user preference)
- Feedback about specific people, projects, or domain knowledge

## Phase 4 — Prune and index

Update MEMORY.md to be tight and accurate.

**Hard limits:** Under 200 lines, under ~25KB. MEMORY.md is an index, not a dump — each entry should be one line under ~150 characters.

Format: `- [Title](file.md) — one-line hook`

Checklist:
- Remove pointers to files you deleted in Phase 3
- Add pointers to any files that exist but aren't indexed (orphans)
- If an index line is over ~200 chars, it's carrying content that belongs in the topic file — shorten the line, move the detail
- Group entries by type (## Feedback, ## Projects, ## Reference, ## User)
- Resolve any contradictions visible at the index level — if two entries describe conflicting states, the files should already be fixed from Phase 3

## Phase 5 — Lesson system health

After automemory is clean, run a health check on the broader lesson system. This catches drift that accumulates between sessions. Skip any sub-step whose target file/directory does not exist in your vault.

### 5a. Trigger index sync

If your vault keeps a trigger index (an action-to-lesson lookup table) alongside its agent-lessons reference, sync them.

Check:
- **Missing entries:** Are there lessons added since the last dream that aren't in the trigger index? Grep the lessons file for entry headings (e.g., `## L[N]`), compare against trigger index mentions. Any lesson created in the last 7 days that isn't in the trigger index should be added under the appropriate action category.
- **Stale entries:** Does the trigger index reference any lesson ID that no longer exists? (Unlikely but catches renumbering errors.)
- **Category coverage:** If a new lesson doesn't fit any existing category, note it in the output but don't create a new category unless 3+ lessons would belong to it.

### 5b. Project lessons staleness

Glob for `**/lessons.md` under your projects directory. For each file with real content (not empty or superseded):
- Check if any lesson references a system, function, or pattern that was removed or renamed in the last 30 days (grep the lesson's key terms against recent incident-report titles and project-log entries).
- If a lesson is obviously stale (references a deleted container, a sunset app, a removed code path), flag it in the output.
- Don't auto-delete project lessons. Flag them for the user: "Project lesson [X] in [project] may be stale: references [term] which [evidence of removal]."

### 5c. Empty stub detection

Glob for any new `lessons.md` files that are stubs (under 10 lines, no entry headings). These get created by project scaffolding but add no value. Report: "N empty lessons.md stubs found. Consider deleting: [paths]."

### 5d. Promotion candidates

Scan project `lessons.md` files for lessons that appear cross-cutting (the lesson's scope or action applies beyond its home project). Signals:
- The lesson references a tool, pattern, or convention used across multiple projects (Docker, reverse-proxy routing, framework conventions, shared UI components)
- The lesson has been cited or duplicated in a second project's CLAUDE.md
- The lesson's condition is not project-specific ("when deploying any service" vs "when deploying the X app")

For each candidate, report: "Project lesson [X] in [project] may be ready for promotion to the vault-level lessons reference. Reason: [signal]."

Don't auto-promote. The user or `/learn` skill handles promotion with the supersession protocol.

## Output

Return a brief summary structured like this:

```
## Dream Summary

**Scope:** project | user | all
**Files scanned:** N memory files, M recent transcripts

### Memory changes
- **Merged:** file_a.md + file_b.md → file_a.md (reason)
- **Updated:** file_c.md — fixed stale project status
- **Pruned:** file_d.md — referenced completed work from January
- **Date-fixed:** file_e.md — "next Friday" → 2026-03-28
- **Superseded:** file_x.md → {{target reference}} (cross-tier dedup)
- **Index:** removed 2 stale entries, added 1 new entry, trimmed 3 verbose lines

### Lesson system health
- **Trigger index:** N new lessons synced, M stale references removed (or "in sync", or "not applicable")
- **Project lessons:** N flagged as potentially stale (list), M promotion candidates (list)
- **Empty stubs:** N found (list paths, or "none")

### No changes needed
- file_f.md, file_g.md — still accurate

**MEMORY.md:** X lines (was Y)
```

If nothing changed, say: "Memory is already clean — no changes needed."
