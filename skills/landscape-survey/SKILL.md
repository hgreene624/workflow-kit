---
name: landscape-survey
description: >-
  Run a structured open-source landscape survey before designing or rebuilding a
  complex system. Six phases: bracket, discover (video + oracle + grounding doc),
  workspace (scratch clone), anchor read (manual, 1-2 closest peers), parallel
  deep-reads (team-dispatched), synthesis (single-worker comparative RE).
  Produces per-repo AREs + one comparative-analysis RE + grounding-doc cross-ref
  appendix; hands off to SD update and SPC drafting. Use whenever the user says
  "landscape survey", "deep-read these repos", "what should we borrow from X",
  "research before we spec", "evaluate candidates before the rebuild",
  "comparative source analysis", "what's the state of the art for [domain]",
  or invokes /landscape-survey. Also fires when the user points the assistant
  at a candidate set (a list of repos / libraries / approaches) and asks for
  a build plan before the SPC. The skill is the structural answer to "we built
  the system on marketing-page understanding and only discovered the failure
  mode after shipping."
---

# Landscape Survey — Open-Source Research Workflow

You are about to research the open-source landscape for a complex system the user wants to design or rebuild. This skill walks six phases that produce a build plan grounded in source-code reads, not marketing pages. It is the structural answer to the failure mode where a system gets designed on surface-level understanding and ships with foreseeable problems.

The survey is bounded research. It does not draft the SPC. It does not write implementation code. It produces verdicts (Borrow / Adopt / Reject), open strategic questions (numbered), and a single comparative-analysis RE that becomes the spine of the downstream SD and SPC.

## When to survey

REQUIRED before designing or rebuilding any system where 3+ open-source candidates exist, choosing between architectural approaches with non-trivial cost-of-being-wrong, or verifying a marketing-page-level verdict against source code. NOT appropriate for single-library evaluation, pure literature review, reading code we own, or implementation work. If unsure, run Phase 1 (bracket) and let the user decide.

## Persistence rules (READ FIRST)

| Class | Location | Persistence |
|---|---|---|
| AREs / RE / grounding-doc appendix | `02_Projects/<project>/reports/<date>/` (vault) | Persistent, iCloud-synced |
| Cloned source repos | `~/Repos/.scratch/<topic>/` (outside vault) | Ephemeral, deletable after SPC ships |

Every ARE frontmatter MUST include `commit_sha` per repo so scratch is deterministically reconstructable from the ARE alone. Never write AREs into scratch. Never commit scratch repos to git.

## Phase 1 — Bracket

Verify there is a PIC scoping this research. If not, invoke `/bracket` first and require:

- **Surface:** what system is being researched, what downstream artifacts the survey feeds (SD update + SPC draft)
- **Success criteria:** "Comparative-analysis RE landed, Q-list consolidated, candidate set verdicts pinned"
- **Anti-scope (mandatory):** no SPC drafting during research; no design recommendations beyond Borrow/Adopt/Reject framing; no code sketches; no adding candidates mid-stream after Phase 2 locks the set
- **Validation plan:** the RE is reviewed against the AREs for contradiction; downstream SD update inherits the verdicts
- **Handoff trigger:** when the RE lands and the Q-list is consolidated, hand off to `/create-note SD` (constitutional clauses) and `/create-note SPC` (implementation)

Do not proceed without the bracket. Drift past the anti-scope rules in a survey is the failure mode this skill exists to prevent.

## Phase 2 — Discover

Compose existing skills to produce the candidate set + grounding doc. The phase is sequential; each step seeds the next.

**Video intelligence.** Run `/video-intel` on 2-5 relevant talks. The user provides URLs, or the skill prompts for domain keywords + a YouTube search. Outputs land at `06_Media/Transcripts/<date>/<title>/` (handled by `/video-intel`). Capture every architectural pattern surfaced; these become candidate borrows.

**Oracle research.** Run `/oracle-create` (or expand an existing oracle via `/oracle-research`) seeded by the video research notes + any prior vault grounding docs + web search for "best 2026 [domain] frameworks." Run `deep_research` passes until convergence (no net-new sources after a pass). Produce a grounding doc at `02_Projects/<project>/reports/<date>/ARE - <Domain> Grounding Report.md` with the literature-anchored verdicts.

**Surface-read validation.** WebFetch each top-candidate repo's homepage / README / pricing / license pages. Catch stale claims in the grounding doc (a 2024 GitHub issue cited as a 2026 limitation; a project that pivoted; a license change). This is cheap insurance against wasting a deep-read session on premise-broken work.

**Lock the candidate set.** Present the user with the candidate list + per-repo provisional verdicts (substrate match, license, maintenance signal, relevance score, 1-line description). Use AskUserQuestion. After approval, the set is LOCKED for Phases 3-6. Adding candidates mid-stream destroys the parallelism of Phase 5; if a new candidate surfaces during deep-read, log it as a follow-up survey.

See `references/discover.md` for the full prompt patterns and tool composition details.

## Phase 3 — Workspace

`mkdir -p ~/Repos/.scratch/<topic>/`. `git clone --depth=1 <url>` each candidate. Capture per-repo metadata in a single pass:

- License (from `LICENSE` or `pyproject.toml`)
- Last commit (`git log -1 --format="%cs %h %s"`)
- Star + fork count (`gh repo view <owner>/<repo> --json stargazerCount,forkCount`)
- LOC by primary language (`find . -name "*.py" -not -path "*/.git/*" | xargs cat | wc -l`)
- Top-level directory layout (`ls -d */`)

Validate all clones succeeded before continuing. A failed clone at this stage means the candidate list is wrong; correct it before any read.

If the user has `cloc` or `tokei` installed, prefer those over `find + wc`. Do not install new system tools without asking.

## Phase 4 — Anchor read (MANUAL, you do this yourself, NOT a worker)

Read the 1-2 closest architectural peers manually. Closest = the candidate that most resembles what the user is designing (same substrate, same problem shape). For the OCG rebuild, that was Graphiti; the second was create-context-graph + neo4j-agent-memory.

Produce one ARE per anchor at `02_Projects/<project>/reports/<date>/ARE - <Repo> Source Analysis.md`. The ARE template lives at `references/ARE-template.md` — read it before writing. Required sections:

- Summary (verdict in 2-3 sentences)
- Architectural Fit (compatibility with the user's target stack; PG+AGE compatibility verdict if relevant)
- Domain-specific sections (named in the bracket)
- Test Patterns (if the repo has notable test coverage to learn from)
- Borrow As Concept / Adopt As Direct Dependency / Reject (with `file:line` evidence for every verdict)
- Open Questions for the downstream SPC (numbered Q1, Q2, …)

The manual anchor read is non-negotiable. It establishes the template, depth, tone, section structure, and Q-numbering convention that subsequent agents will mimic. Skipping it produces fragmented AREs that the synthesis pass cannot reconcile. Tempting to delegate all candidates to a team cold; do not.

## Phase 5 — Parallel deep-reads (TEAM)

`TeamCreate` a team named `<topic>-deep-reads`. One `TaskCreate` per remaining candidate. One worker per task via `Agent` with `team_name` and `name`. Workers run in parallel.

Each worker brief includes:
- Scratch path to the repo
- Prior AREs (path) to read for tone, structure, depth
- Required ARE sections (same template as the anchor reads)
- Writing constraints (frontmatter keys, no em dashes, `file:line` refs, vault path conventions)
- Pre-allocated Q-number range (e.g., Q14-Q20 for worker A, Q21-Q27 for worker B) to prevent collisions
- Output path
- Summary format for the return message (4-6 sentences, headline verdict + key borrows + integration cost)

See `references/worker-brief-template.md` for the full brief shape.

Combined or lower-depth (skim) reads are allowed for candidates that surfaced in Discovery as lower-relevance. One worker can cover 2-3 skim candidates in one combined ARE.

Wait for all workers to mark their tasks completed before Phase 6. Do not start synthesis with workers still in flight; the synthesis worker needs the full ARE set.

## Phase 6 — Synthesis (TEAM, SINGLE worker by design)

`TeamCreate` a new team (or reuse), `TaskCreate` one synthesis task, spawn ONE worker. Multi-worker synthesis is an anti-pattern — fragmented output where the comparison table from one worker contradicts the per-repo sections from another. Single-worker by design.

The synthesis worker reads all AREs + the grounding doc, then produces ONE comparative-analysis RE at `02_Projects/<project>/reports/<date>/RE - <Topic> Comparative Analysis.md`. Required sections:

- Executive summary (5-7 sentences naming the build-vs-buy verdict, key borrows, adopted deps, rejected paths)
- Comparison table (all candidates as rows; columns Architectural Fit / License / Maintenance / Borrow / Adopt / Reject / Integration Vector)
- Per-repo verdict (link to ARE, key code-pattern snippet inline)
- Synthesis section (concrete file paths in the target codebase, citing concept origins — "the staged_edges schema borrows the CocoIndex lineage pattern; the Pydantic ontology pattern adopts Graphiti's `graphiti_core/nodes.py:42-78` verbatim")
- Consolidated Q-list (renumbered Q1-QN, deduplicated, grouped by domain)

After the RE lands, the synthesis worker also appends a short (5-10 line) "Source Analysis Findings" section to the upstream grounding doc cross-referencing the RE. The grounding doc stays the literature-grounded synthesis; the RE is the source-code-grounded synthesis; they cite each other.

See `references/RE-template.md` and `references/synthesis-worker-brief.md` for full templates.

## Phase 7 — Handoff

Team shutdown (`SendMessage` shutdown_request, then `TeamDelete`). Update PIC claim log + project PJL with deliverables. Then offer the natural next steps:

1. Strategic-question reopens (if synthesis surfaced foundation-level decisions the original PIC ruled out)
2. `/create-note SD` for the constitutional clauses the survey identified as stable
3. `/create-note SPC` for the implementation, using the Q-list as the open-decision backlog

Offer the next step explicitly. Don't silently end.

## Anti-patterns to refuse

See `references/anti-patterns.md` for the full list of 10 failure modes with refusal guidance. The most critical four:

1. Skipping the manual anchor read (Phase 4 must be manual on 1-2 closest peers)
2. Multi-worker synthesis (Phase 6 must be single-worker)
3. Adding candidates mid-stream (Phase 2 lock is contractual)
4. Drafting SPC content during the survey (Open Questions section is the right place)

Read `references/anti-patterns.md` before starting Phase 4 and again before Phase 6 — those are the two phases most prone to violation.

## References

- `references/discover.md` — Phase 2 detail: video-intel + oracle composition, candidate-lock pattern
- `references/ARE-template.md` — per-repo ARE structure with all required sections and frontmatter
- `references/RE-template.md` — comparative-analysis RE structure
- `references/worker-brief-template.md` — Phase 5 parallel-worker brief shape
- `references/synthesis-worker-brief.md` — Phase 6 single-worker synthesis brief shape
- `references/example-survey.md` — the OCG rebuild survey (May 19-20, 2026) as the canonical worked example

## Acknowledgment

After running the survey, write a short acknowledgment to the user: deliverables produced, where they live, what the natural next step is. Update the PIC and PJL. Offer the next handoff explicitly.
