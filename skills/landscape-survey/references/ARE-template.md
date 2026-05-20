# Per-Repo ARE Template

The Agent Report Extended (ARE) is the per-repo deliverable from Phase 4 (anchor) and Phase 5 (parallel team). One ARE per repo, except for low-relevance skim candidates which can be combined.

## Path

`02_Projects/<project>/reports/<date>/ARE - <Repo Name> Source Analysis.md`

Example: `02_Projects/<umbrella>/<sub-project>/reports/YYYY-MM-DD/ARE - <Repo Name> Source Analysis.md`. See `references/example-survey.md` for a concrete worked example.

Never write into the scratch dir. Never commit AREs to source-code git repos; they live in the vault only.

## Frontmatter

Required keys:

```yaml
---
date created: YYYY-MM-DD
tags: [agent-report, <domain>, <repo-short-name>, source-analysis, <topic>]
category: Report
type: ARE
project: "<Project name from PIC>"
pickup: "[[PIC - <bracket name>]]"
upstream:
  - "[[ARE - <Domain> Grounding Report]]"
  - "[[SD - <relevant constitutional SD>]]"
repo:
  name: "<owner>/<repo>"
  version: "<from pyproject.toml or package.json>"
  license: "<SPDX id from LICENSE first line>"
  last_commit: "<YYYY-MM-DD short-hash subject>"
  commit_sha: "<full sha>"        # so a future agent can git checkout deterministically
  stars: <integer>
  loc: "<N Python + M TS + ...>"
  scratch_path: "~/Repos/.scratch/<topic>/<repo>"
---
```

For combined skim AREs covering 2+ repos, use a `repos:` list instead of `repo:`:

```yaml
repos:
  - name: "microsoft/graphrag"
    license: "MIT"
    last_commit: "..."
    commit_sha: "..."
    stars: 33125
    loc: "50,414 Python"
    scratch_path: "~/Repos/.scratch/<topic>/graphrag"
  - name: "HKUDS/LightRAG"
    ...
```

## Required sections

In this order:

### Summary

2-3 sentences. State the headline verdict (build vs buy / borrow vs adopt / reject) and the single most important finding. Read it in 15 seconds and know the conclusion.

### 1. Architectural Fit

Compatibility with the user's target stack (whatever it is). Name the storage / runtime / language assumptions the repo makes. Identify any abstraction layers that would let a custom adapter slot in. Estimate adapter effort in LOC if relevant.

If the repo expects a stack the user doesn't run, that's a Reject candidate by default; surface it here and let the reader decide.

### 2-N. Domain-specific sections

Named in the bracket. Examples from the OCG survey:
- Pydantic Ontology Pattern (Graphiti, CCG)
- POLE+O Label Layer (CCG)
- Episode Model (Graphiti)
- Bi-Temporal Schema (Graphiti)
- Extraction Loop (Graphiti, Instructor)
- Fact Invalidation (Graphiti)
- Delta Detection (CocoIndex)
- Lineage Tracking (CocoIndex)
- Agent Tool Interface Pattern (CCG)
- Decision Trace UI (CCG)
- Memory Integration Portability (NAMS)

These are NOT prescribed by this template; the bracket defines them. Adapt to the domain.

### Test Patterns

If the repo has notable test coverage worth learning from. Include LOC:test ratio, test areas, patterns NOT covered that should be in the user's downstream SPC (e.g., "Graphiti has no bi-temporal regression tests; that's a gap the OCG SPC should fill from day one").

Optional. Omit if the repo's tests are unremarkable.

### Borrow As Concept / Adopt As Direct Dependency / Reject

The verdict surface. Three sub-sections, in this order. Every architectural observation flows into one of them.

**Borrow As Concept** — patterns we copy without depending. Each entry names the pattern, cites the source with `file:line` evidence, names the target-side implementation location in the user's codebase. ~5-10 entries typical.

**Adopt As Direct Dependency** — libraries we depend on at runtime. Each entry names the library, the version to pin, the integration point in the target codebase, the incremental adoption path. Usually 0-1 entries.

**Reject** — paths we considered and ruled out. Each entry names what was rejected, why (with evidence), and what we lose. 3-7 entries typical.

### Open Questions for the SPC

Numbered Q1, Q2, … Each question carries:

- The question (one sentence)
- Originating context (where in the source read this surfaced)
- Candidate options (with file:line refs where applicable)
- Recommended default (per the user's "recommend-default" pattern; mark "(Recommended)" on the option you'd pre-select)

Numbering is local to this ARE; the synthesis worker in Phase 6 will renumber globally.

If your worker brief pre-allocated a Q-range, use that range. If not, start at Q1.

## Writing constraints

- NO em dashes (—). The vault has a soft warn hook; respect it.
- Tight markdown spacing. No double blank lines.
- Use `file_path:line_number` references for every concrete code claim.
- Concise. Aim for 4,000-9,000 words depending on repo complexity. Heavyweight runtime libs (Graphiti, CCG) land at ~9,000; pure-library adoptions (Instructor) at ~5,000; skim reports (GraphRAG + LightRAG combined) at ~3,000.
- Don't draft SPC content. Findings that would shape SPC FRs go in the Open Questions section.
- Use Obsidian wikilinks: `[[ARE - Other Source Analysis]]`, `[[SD - Constitutional Doc]]`.
- Don't summarize what the README says. The README is a known input; the ARE adds source-code-deep findings the README doesn't surface.

## Tone

The ARE is read by the user's future self while drafting the SD and SPC. It's a strategic artifact, not a tutorial. Assume the reader knows the domain. Don't explain what Pydantic is, what a knowledge graph is, what Cypher syntax looks like. Do explain the SPECIFIC architectural choices the repo made and why they matter for the target system.

The ARE is also read by the synthesis worker in Phase 6. Make the verdicts unambiguous so synthesis isn't guessing what you meant.
