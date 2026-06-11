# Worked Example: OCG Rebuild Survey (2026-05-19 to 2026-05-20)

The canonical example this skill is built from. Every reference file in this skill traces back to artifacts produced during this survey.

## Bracket

PIC: `02_Projects/{{ORG}} Intelligence/context-graph/pickups/2026-05-19/PIC - OCG Phased Rebuild Source Analysis.md`

- **Target system:** OCG (Organization Context Graph) rebuild
- **Failure mode driving the survey:** 22,516-edge graph built by single-pass LLM extraction with no schema constraints; canonical visible failure is edge id 71591 "Sergio approves Patrick" from source text "Sergio and Patrick jointly decided to keep the HOA meeting high-level"
- **Anti-scope:** no SPC drafting during research, no design recommendations beyond Borrow/Adopt/Reject framing, no code sketches
- **Downstream artifacts:** SD - Organization Context Graph v2 (constitutional lock-in), SPC - OCG Phased Quality Rebuild v1 (implementation)

## Phase 2 — Discover artifacts (ran 2026-05-19)

**Video intelligence:** Two talks via `/video-intel`:
- Stephen Chin (Neo4j) "Connecting the Dots with Context Graphs" → surfaced POLE+O label layer, `:TOUCHED` audit edges, consolidation primitives as API
- Martin (SurrealDB) "Knowledge Graphs for AI Agents" → surfaced enrichment-as-navigation (LightRAG pattern), two-tier retrieval tools, KG-vs-vector decision gate

**Oracle research:** Two oracles via `/oracle build`:
- `5812eb9f-...` "Context Graph Design" (143 sources) → [[ARE - Context Graph Design Research]]
- `44b21c8d-...` "KG System Landscape" (106 sources) → [[ARE - KG System Landscape Grounding Report]]
- `eb8a2056-...` "Context Graph - Extraction Quality" (47 sources + Appendix A recency pass) → [[ARE - OCG Extraction Quality Grounding Report]]

**Surface-read validation:** WebFetch on Graphiti, create-context-graph, CocoIndex → provisional "build with borrowed patterns, not adopt as library" verdict (later confirmed by deep reads)

**Candidate lockdown:** 7 repos:
1. getzep/graphiti (runtime KG library, Apache-2.0)
2. neo4j-labs/create-context-graph (scaffolding tool, Apache-2.0)
3. neo4j-labs/agent-memory (NAMS runtime, Apache-2.0)
4. cocoindex-io/cocoindex (incremental engine, Apache-2.0)
5. 567-labs/instructor (schema-constrained LLM extraction, MIT)
6. microsoft/graphrag (community-detection RAG, MIT)
7. HKUDS/LightRAG (dual-level retrieval RAG, MIT)

## Phase 3 — Workspace

`~/Repos/.scratch/ocg-source-analysis/` (310 MB after clones)

Per-repo metadata captured: license, last commit, star count, fork count, LOC by language, top-level layout. Stored in PJL.

## Phase 4 — Anchor reads (manual, by team-lead)

Two AREs:
1. [[ARE - Graphiti Source Analysis]] (~9,500 words) — closest architectural peer; established the template, frontmatter shape, section structure, Q-numbering convention (Q1-Q7)
2. [[ARE - Create-Context-Graph Source Analysis]] (~9,200 words) — covers CCG + neo4j-agent-memory; introduced POLE+O finding (Q8-Q13)

## Phase 5 — Parallel deep-reads (team `ocg-deep-reads`)

Three workers in parallel:
1. cocoindex-reader → [[ARE - CocoIndex Source Analysis]] (Q14-Q20)
2. instructor-reader → [[ARE - Instructor Source Analysis]] (Q14-Q20, collided with cocoindex's range — resolved at synthesis)
3. graphrag-lightrag-skimmer → [[ARE - GraphRAG and LightRAG Skim]] (Q20-Q26, partial collision — resolved at synthesis)

Q-range pre-allocation should have prevented the cocoindex/instructor Q14-Q20 collision; this skill's worker-brief template now requires pre-allocation explicitly.

All 3 workers completed within the same session.

## Phase 6 — Synthesis (team `ocg-comparative-synth`)

Single synthesis-writer produced [[RE - OCG Source Repo Comparative Analysis]] (6,869 words).

Headline architectural shape (5 layers):
1. Ontology = POLE+O closed taxonomy + Literal[...] relation enum + edge_type_map
2. Schema = bi-temporal edges + pgvector + AGE 1.7.0
3. Extraction = Instructor 1.15.2 + Anthropic via gateway + 6-call pipeline + validation_context faithfulness gate
4. Storage = ocg.staged_edges with content fingerprints + faithfulness judge at promotion + ~250 LOC CocoIndex borrow
5. Retrieval = two-tier tool surface + decision-trace + :TOUCHED audit edges + community-report layer (Phase 6+)

Q-list consolidated to Q1-Q30 across 7 domain groups. Three contradictions reconciled. Four genuinely new synthesis findings surfaced:
1. Content-fingerprinted staged_edge_id makes idempotency a SCHEMA property
2. POLE+O + edge_type_map combine multiplicatively (not additively)
3. Faithfulness is two-tier composition (in-loop span-existence + paid semantic judge memoized)
4. LightRAG's `_summarize_descriptions` conflict-detection prompt fills the gap in Graphiti's `resolve_extracted_nodes` step

Plus Appendix B added to the upstream grounding doc cross-referencing the RE.

## Phase 7 — Handoff

PIC stays picked-up. Step 9 (storage-migration strategic-question reopen, Kuzu sidecar reassessment) remains. Then SD v2 update, then SPC v1 draft.

## What this skill captured from the example

- Manual anchor read is non-negotiable — workers without a template drift
- Q-number pre-allocation prevents collisions
- Single-worker synthesis is required for coherent output
- AREs land in vault, scratch is ephemeral
- commit_sha in ARE frontmatter is mandatory for scratch reconstructability
- The "Multiplicative interactions" sub-section in the RE is where synthesis-pass value lives
- Composition with existing skills (`/video-intel`, `/oracle build`, `/oracle research`) is the right pattern for discovery

The artifacts from this survey are persistent and viewable. Future skill invocations can point at these as the canonical shape.
