# Phase 6 Synthesis Worker Brief Template

ONE synthesis worker per survey. Single worker by design. Multi-worker synthesis produces fragmented documents where the comparison table contradicts the per-repo sections.

## Brief structure

### 1. Why this work matters

2-3 sentences naming the target system and the role of the comparative RE. The synthesis is the spine of the downstream SD update and SPC v1 draft; quality matters more than speed.

### 2. Input AREs

List the paths of every ARE produced in the survey + the upstream grounding doc(s). Tell the worker to READ ALL OF THEM IN FULL before writing. Skimming produces incomplete synthesis.

Estimated reading time for the worker: 30-60 minutes for 5-7 AREs at ~9,000 words each + 2 grounding docs at ~5,000 words each. Tell the worker to take the time.

### 3. Output paths

- Primary: `02_Projects/<project>/reports/<date>/RE - <Topic> Comparative Analysis.md`
- Secondary: append a 5-10 line "Source Analysis Findings" section to the upstream grounding doc cross-referencing the new RE

### 4. The architectural-shape hint

The team-lead's prose synthesis (what shape the system seems to take across the AREs) is a useful seed for the worker. Carry it in the brief as a starting point, but tell the worker explicitly: "this is a hint, not a constraint. If the AREs contradict the hint, follow the AREs and document the contradiction."

Workers that treat the hint as constraint will write a confirmation document instead of a synthesis. The whole point of the synthesis pass is to produce findings that did not exist in any single ARE.

### 5. Required RE sections

Repeat the RE template verbatim (see `RE-template.md`). All 6 sections:
1. Executive summary
2. Comparison table
3. Per-repo verdict
4. Synthesis (the build plan, with the layered architecture)
5. Consolidated Q-list
6. Anti-patterns explicitly rejected

Plus the grounding-doc appendix.

### 6. The synthesis brief is most important

This is where workers most often produce inadequate output. The "Synthesis" section (4) is not a re-summary of the AREs; it is the **multiplicative finding** layer.

Tell the worker explicitly:
- Open the synthesis section by naming the N-layer composition
- Per layer: name the borrowed pattern, cite the file:line origin, name the target-side implementation path in the user's codebase, state any constitutional clauses that emerge
- End the synthesis section with a "Multiplicative interactions" sub-section: where do borrowed patterns combine to produce guarantees no single pattern produces alone?
- If the Multiplicative section is empty, the worker has not synthesized hard enough — refuse to ship the RE

Examples of multiplicative findings (from the OCG survey):
- Closed POLE+O + closed `edge_type_map` combine MULTIPLICATIVELY (open ontology with edge_type_map still permits invented edges via type-inflation; the conjunction fail-closes both axes)
- Faithfulness as two-tier composition: cheap in-loop span-existence + paid semantic judge at promotion, memoized on `(content_fp, judge_prompt_version, judge_model)`
- Content-fingerprinted `staged_edge_id` makes idempotent extraction a SCHEMA property, not a runtime property

These are the findings that justify the synthesis pass.

### 7. Contradiction handling

The worker must explicitly look for contradictions across the AREs and reconcile them in the RE. Common contradiction patterns:

- Open vs closed type systems (Graphiti open, CCG closed in the OCG case)
- Edge direction defaults (Graphiti directional, LightRAG undirected)
- Provenance granularity (uuid only vs char-level)
- Storage substrate assumptions

Tell the worker: when reconciling, name the contradiction, name the source AREs, name the reconciliation choice, and explain the reasoning. Reconciliations land in the per-repo verdicts (Section 3) or the synthesis (Section 4) depending on scope.

### 8. Q-list consolidation

Workers in Phase 5 used pre-allocated Q-ranges. Collisions may still exist if a worker overran. The synthesis worker:
- Reads every Open Question from every ARE
- Deduplicates (questions that ask the same thing in different words become one)
- Groups by domain (storage/schema, ontology, extraction, faithfulness, provenance, staging/promotion, retrieval, etc.)
- Renumbers globally Q1-QN
- Documents the renumbering map in a small "Renumbering note" sub-section at the bottom of Section 5

The output Q-list is the SPC's open-decision backlog. Quality of the Q-list determines quality of the SPC drafting that follows.

### 9. Writing constraints

- NO em dashes
- Tight spacing
- 6,000-9,000 word target
- No SPC drafting
- Concise per-repo sections (200-400 words each); deep synthesis section (substantial)
- Obsidian wikilinks throughout
- file:line refs for concrete claims
- Frontmatter complete (link every input ARE in `upstream:`; link every output target in `downstream:`)

### 10. Return-message format

When the RE lands, the synthesis worker sends team-lead a 6-10 sentence summary covering:
- Headline architectural shape (the N-layer composition)
- Q-list size and renumbering notes
- Contradictions found and reconciled (with how)
- Genuinely new synthesis findings (the multiplicative ones)

NOT: a re-summary of the RE. The RE is written; the summary names what's NEW for the team-lead.

## Length

Brief should be 1,500-2,500 words. Longer than a parallel-worker brief because the synthesis worker carries more responsibility per output and benefits from explicit framing.

## Dispatch mechanics

- `TeamCreate` (can be a separate team from the Phase 5 team, or reuse if Phase 5 team is still active)
- `TaskCreate` one task for the synthesis
- `Agent` with `team_name` and `name: "synthesis-writer"`, `subagent_type: "general-purpose"`
- Worker runs, writes the RE, writes the appendix, marks task completed, SendMessages team-lead
- Team-lead shuts down the worker and the team after the RE is verified
