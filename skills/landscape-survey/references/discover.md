# Phase 2 — Discover: Tool Composition

The discover phase produces the candidate set + the grounding doc. It composes three existing skills + a final lock step. Sequential; each step seeds the next.

## Sequence

### 2a. Video intelligence

Run `/video-intel` on 2-5 relevant talks. The user supplies URLs, OR the skill asks for domain keywords + a YouTube search.

Output: per-video transcripts + research notes + architectural patterns surfaced. Lands at `06_Media/Transcripts/<date>/<title>/`.

What to do with the output: extract every architectural pattern named in the videos. These become candidate borrows. Carry them forward as input to the oracle.

Example from the OCG survey: Chin (Neo4j) talk surfaced POLE+O, `:TOUCHED` audit edges, consolidation primitives as API. Martin (SurrealDB) talk surfaced enrichment-as-navigation (LightRAG pattern), two-tier retrieval tools, KG-vs-vector decision gate.

### 2b. Oracle research

Run `/oracle-create` (or expand an existing oracle with `/oracle-research`). Seed with:
- The video research notes from 2a
- Any existing grounding docs in the vault on the same domain
- Web search results for "best 2026 [domain] frameworks", "[domain] state of the art", "production [domain] open source"

Run `deep_research` passes until convergence (no net-new sources after a pass). For a fresh domain expect 3-5 passes.

Produce a grounding doc at `02_Projects/<project>/reports/<date>/ARE - <Domain> Grounding Report.md`. The grounding doc carries the literature-anchored verdicts and surfaces the candidate repo list with provisional verdicts.

What "convergence" means: a deep_research pass with 0-2 net-new sources, and the new sources don't add architectural patterns the prior passes missed. If pass N+1 surfaces a brand-new pattern, run pass N+2 and N+3 to confirm it stabilizes.

### 2c. Surface-read validation

Take the top 3-5 candidate repos from the grounding doc. For each, run a WebFetch on:
- The repo's README on GitHub
- The repo's homepage / docs landing page
- The repo's pricing or license page (if applicable)

Catch stale claims in the grounding doc. The grounding doc cites 2024 sources sometimes; the surface read confirms whether those claims still apply in 2026.

Common stale-claim patterns:
- "X doesn't support Y" — and then Y shipped in v2.0 last quarter
- "X requires substrate Z" — and then Z became optional
- "X has no Anthropic adapter" — and the adapter shipped in the last release

If you find a stale claim, update the grounding doc inline with a "(Updated YYYY-MM-DD)" note. Don't silently overwrite.

### 2d. Candidate lockdown

Present the user with:
- The locked candidate list (3-8 repos)
- Per-repo provisional verdict (substrate match Y/N, license compatibility Y/N, maintenance signal active/stale/abandoned, relevance score, 1-line description)
- Recommended depth per repo (deep-read vs combined-skim)

Use AskUserQuestion. Provide options like "Lock as-is", "Drop repo X", "Add repo Y not in current list". Wait for confirmation.

After user approval, the list is LOCKED for Phases 3-6. Adding candidates mid-stream destroys the parallelism of Phase 5; the synthesis worker has to redo its work.

If the user wants to add candidates mid-stream after Phase 2 closes, log them as a follow-up survey. Do not silently expand the current run.

## When to skip Phase 2

If the user already has a candidate set in hand and a recent grounding doc on the domain (within the last 2-3 weeks), you can skip 2a-2c and go straight to 2d for the lockdown.

Example: today's OCG survey had two prior grounding docs from yesterday and a list of 7 candidates already named. We skipped the video-intel + oracle-research steps because they had run yesterday; we just confirmed the candidate set and moved to Phase 3.

If you skip, document why in the PIC's bracket section so a future reader knows the lockdown wasn't arbitrary.

## When Phase 2 is the entire skill invocation

Sometimes the user invokes `/landscape-survey` and the actual work IS the discover phase — they want the grounding doc and candidate list, not the full deep-reads.

If the user signals this intent (e.g., "just give me the landscape, I'll do the reads myself", or "build me a candidate list for X"), run Phase 1 (bracket) + Phase 2 (discover) and then hand off rather than continuing to Phase 3-6.

Tell the user explicitly: "Discovery complete. Candidate set is locked. To continue with the deep reads, invoke `/landscape-survey` again with the same bracket; I'll pick up at Phase 3."
