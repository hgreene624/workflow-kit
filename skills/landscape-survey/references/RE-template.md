# Comparative-Analysis RE Template

The Research Extended (RE) is the synthesis deliverable from Phase 6. ONE RE per survey. Spine of the downstream SD update and SPC v1 draft.

## Path

`02_Projects/<project>/reports/<date>/RE - <Topic> Comparative Analysis.md`

Example: `02_Projects/<umbrella>/<sub-project>/reports/YYYY-MM-DD/RE - <Topic> Comparative Analysis.md`. See `references/example-survey.md` for a worked example.

## Frontmatter

```yaml
---
date created: YYYY-MM-DD
tags: [research, comparative-analysis, <domain>, <topic>]
category: Report
type: RE
project: "<Project>"
pickup: "[[PIC - <bracket name>]]"
upstream:
  - "[[ARE - <Domain> Grounding Report]]"
  - "[[ARE - <Repo 1> Source Analysis]]"
  - "[[ARE - <Repo 2> Source Analysis]]"
  - ... (link every input ARE)
downstream:
  - "[[SD - <Constitutional doc>]] (target for v2 update)"
  - "[[SPC - <Future implementation spec>]] (drafted from this RE)"
repos:                      # list of all candidate repos surveyed
  - name: "<owner>/<repo>"
    license: "<spdx>"
    commit_sha: "<full sha>"
    scratch_path: "~/Repos/.scratch/<topic>/<repo>"
    verdict: "<borrow|adopt|reject>"
  - ...
---
```

## Required sections

### 1. Executive summary

5-7 sentences. State:
- The build-vs-buy verdict
- Patterns we borrow as concept (named, with counts)
- Dependencies we adopt (named, with version pins)
- Rejected paths (named, with one-line reasons)
- The one most important open strategic question

This section is read in 30 seconds. Make every word count.

### 2. Comparison table

All candidate repos as rows. Columns:

| Repo | Architectural Fit | License | Maintenance | Borrow As Concept | Adopt As Dep | Reject | Integration Vector |
|------|-------------------|---------|-------------|-------------------|--------------|--------|---------------------|

The "Maintenance" column carries: last commit date, star/fork count, signal of active development. The "Integration Vector" column carries: where in the user's codebase this repo's patterns land (e.g., `services/api/src/kg/extract/`).

Verdicts here MUST match the per-ARE verdicts in Section 3. If the table says "Borrow" and the ARE says "Reject", reconcile both before publishing the RE.

### 3. Per-repo verdict

One sub-section per repo. Each:
- Links to the source ARE (wikilink)
- Carries the verdict in 2-3 sentences
- Includes the single most important code-pattern snippet inline (the one the reader cares about most)
- Lists the borrows (concept) + adoptions (dep) + rejections, briefly
- Lists 1-3 specific file:line refs the SPC author should re-read when implementing

Aim for 200-400 words per repo. Skim AREs get less; deep AREs get more.

### 4. Synthesis (the build plan)

This is the load-bearing section. Output: a concrete build plan in the user's codebase.

Open with one paragraph: "Given these reads, the [system] should be built as a [N-layer] composition. The layers, top-to-bottom, are …"

Then one sub-section per layer of the proposed system. Each sub-section:
- Names the layer
- States the borrowed pattern with `file:line` origin (e.g., "Layer 1 ontology borrows the POLE+O 5-category taxonomy from CCG's `_base.yaml`")
- Names the target-side implementation path in the user's codebase (e.g., `services/api/src/<module>/<file>.py`)
- States any constitutional clauses that emerge (these will land in the SD update)

End with a "Multiplicative interactions" sub-section: where do borrowed patterns combine to produce structural guarantees no single pattern produces alone? This is where the genuinely new synthesis findings live; if you have nothing here, you have not synthesized hard enough.

Example multiplicative finding from the OCG survey: "Closed POLE+O + closed `edge_type_map` combine multiplicatively, not additively. Open ontology with edge_type_map alone still permits invented edges via type-inflation. The CONJUNCTION fail-closes both the node and edge axes." That insight existed in no single ARE; it only emerged in synthesis.

### 5. Consolidated Q-list

Renumber every Open Question from every input ARE into a single flat Q1-QN list. Group by domain (storage/schema, ontology, extraction, faithfulness, provenance, staging/promotion, retrieval, etc.). Within each group, order by urgency.

Each Q entry:
- The question (one sentence)
- Originating ARE(s) (the source AREs are stable references; carry the wikilink)
- Candidate options (with file:line refs where applicable)
- Recommended default per the user's "recommend-default" pattern

Collisions (multiple AREs using the same Q-number) are resolved at synthesis time, not pushed to the reader. Document the collision resolution at the bottom of Section 5 in a small "Renumbering note" sub-section.

### 6. Anti-patterns explicitly rejected

A short numbered list of patterns the survey identified as anti-patterns. These carry over into the SPC as constraints ("the SPC must NOT do X because the survey found that X produces failure mode Y").

Concise. 5-10 entries typical.

## Writing constraints

- NO em dashes. Use commas, periods, parentheses.
- Tight spacing. No double blank lines.
- Concise overall. Target 6,000-9,000 words. Below 5,000 = under-synthesized; above 10,000 = the AREs are doing the synthesis worker's job.
- Don't duplicate ARE content. Link to AREs; carry forward verdicts + key snippets only.
- Don't draft SPC FRs. Findings that shape SPC FRs go in Section 5 (Open Questions) or Section 6 (Anti-patterns).
- Use Obsidian wikilinks throughout.

## After the RE lands

The synthesis worker appends a short "Source Analysis Findings" section (5-10 lines) to the upstream grounding doc cross-referencing the new RE. The grounding doc is the literature-grounded synthesis; the RE is the source-code-grounded synthesis. They cite each other for symmetric findability.

Then the synthesis worker marks its task completed and SendMessages the team-lead a 6-10 sentence summary covering: headline architectural shape, Q-list size + renumbering notes, contradictions reconciled, genuinely new synthesis findings.
