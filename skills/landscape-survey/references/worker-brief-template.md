# Phase 5 Parallel Worker Brief Template

Every worker spawned in Phase 5 (parallel deep-reads) gets a brief in this shape. The team-lead writes the brief at dispatch time and includes it inline in the `Agent` tool's `prompt` parameter.

## Brief structure

Address eight things, in this order:

### 1. Why this work matters

2-3 sentences naming the user's target system, the failure mode the survey is preventing, and the role this specific repo plays. Workers who understand the strategic context produce better verdicts than workers running off pure procedure.

Example (drawn from the canonical worked survey in `references/example-survey.md`): "We're rebuilding our knowledge graph from scratch. The current graph was built by a single-pass LLM extractor with no schema constraints and a visualization just exposed a canonical failure mode. Graphiti is the closest architectural peer that we found; your read decides whether we adopt patterns or the library."

### 2. Prior AREs (for tone, structure, depth)

List the paths to AREs that already shipped in this survey. Tell the worker to read them first to mimic the template, frontmatter, section structure, and writing voice.

This is non-negotiable. Workers that don't read prior AREs produce drift. Subsequent synthesis cannot reconcile drift.

### 3. Scratch path + repo metadata

The exact filesystem path of the cloned repo (`~/Repos/.scratch/<topic>/<repo>`). Plus pre-captured metadata (license, version, last commit, star count, LOC, scratch_path) that goes into the ARE frontmatter. Workers should not have to re-derive metadata; they should focus on source reads.

Include the commit SHA. The ARE frontmatter must carry it for deterministic re-checkout.

### 4. Required ARE sections

Repeat the standard ARE section list verbatim (see `ARE-template.md`). Don't link; embed the list. Workers should not have to navigate to find the section structure.

Include any domain-specific sections the survey's bracket called out (e.g., "POLE+O Label Layer", "Bi-Temporal Schema", "Pydantic Ontology Pattern"). Workers shouldn't have to guess what domain sections the survey expects.

### 5. Writing constraints

- NO em dashes
- Tight markdown spacing
- `file:line_number` references for concrete code claims
- Required frontmatter keys
- Output path (the exact vault path where the ARE lands)
- Concise (target word count for this repo: heavyweight ~9k, library ~5k, skim ~3k)
- No draft SPC content
- Obsidian wikilinks

### 6. Pre-allocated Q-number range

Q-number collisions across workers are the #1 synthesis-pass headache. Pre-allocate per worker:
- Worker A (closest peer #1): Q1-Q10
- Worker B (closest peer #2): Q11-Q20
- Worker C (third candidate): Q21-Q30
- ... etc

If a worker runs out of range, they extend into the next 10. The synthesis pass will renumber globally; the pre-allocation just prevents same-number collisions during writing.

### 7. Return-message format

Tell the worker explicitly what to send back to team-lead when the task completes. The standard return format is 4-6 sentences covering:
- Headline verdict (1 sentence)
- Top 2-3 borrows with origin file:line refs
- The single adoption candidate (if any) with version pin
- 2-3 most important open questions with their Q-numbers
- Anything contradictory to a prior ARE that needs reconciling at synthesis

Tell the worker to NOT re-summarize the full ARE — that's already written to the file. The return message should carry NEW strategic information the team-lead needs to coordinate.

### 8. Domain-specific deep-read focus

Per the PIC's Step instructions (the PIC for the survey carries Step-by-Step deep-read focus per repo). Carry these in for the worker. Examples from the OCG survey:

- Graphiti Step 2: read `graphiti_core/nodes.py` → `edges.py` → `llm_client/` → `prompts/` → `search/` → DB adapters → `tests/` → `examples/`
- CocoIndex Step 4: Python flow API, delta detection, PostgreSQL adapter, lineage tracking
- Instructor Step 5: core Instructor class, retry/validation loop, Anthropic adapter, AI Gateway compatibility

If the PIC doesn't specify, the worker picks the focus based on the user's target system and the repo's architectural surface.

## Anti-patterns to flag in the brief

Tell the worker explicitly to refuse:
- Reading source for "where" questions (use `Grep` or `Glob`)
- Inventing Q-numbers outside their allocated range
- Drafting SPC content
- Reading the repo's marketing / pricing pages instead of source code
- Adding new candidate repos mid-stream

## Length

The brief should be 800-1,500 words. Long enough to ground the worker; short enough that the agent uses most of its context on reading source, not parsing the brief.

## Dispatch mechanics

- `TeamCreate` once for the survey (team name like `<topic>-deep-reads`)
- `TaskCreate` once per candidate repo (descriptive subjects)
- `Agent` invocations: one per worker, `team_name` set, `name` set (e.g., `cocoindex-reader`), `subagent_type: "general-purpose"`
- All `Agent` invocations in a single message (parallel dispatch)
- Workers run their work, write the ARE, mark task completed, SendMessage their summary
- Team-lead doesn't poll; idle notifications come automatically
