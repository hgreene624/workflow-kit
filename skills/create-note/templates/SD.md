# SD Template - System Definition

## Frontmatter additions

```yaml
status: Living Document
version: 1
date modified: YYYY-MM-DD
```

Tags: `[<system-tag>, system-definition, architecture, canonical]`

## Reference files

Read `references/sd-guide.md` for the SD writing guide (constitutional voice, section craft, anti-patterns, oracle reference).

## Classify scope

Before interviewing, assess what kind of system definition this is:

| Scope | Signals | Shape |
|-------|---------|-------|
| **Entity** | Defines a single concept within a larger system (e.g., Process Entity, Person Enrichment) | Tight. 80-100 lines. Position section anchors it relative to the parent system. |
| **System** | Defines a full subsystem or service (e.g., FWIS, KB Creation System, Meeting Intelligence) | Standard. 100-120 lines. Mechanics section is the heaviest. Multiple mechanism subsections. |
| **Framework** | Defines a methodology, pattern, or governance model (e.g., Oracle System, Teams Governance) | Flexible. Mechanics may use different subsection names (e.g., "The proposition pattern" instead of "Signal Routing"). |

Present assessment: "This is an **{scope}** SD for {subject}. I'll ask {N} questions to understand the domain, then draft."

## Oracle check

Check for a cross-cutting oracle at `04_Reference/oracle-ledger.md` and the project's own oracle ledger (PJL frontmatter `oracles:`). Query with:

- "What established frameworks, models, or industry patterns apply to {subject}?"
- "What are known failure modes or anti-patterns in {domain}?"

Surface findings as propositions (oracle insight + source count + question to user). Never silently apply oracle recommendations to principles or grounding sections.

If no oracle exists, offer to create one. SDs benefit more from oracle grounding than any other document type because their principles should be evidence-based, not intuition-based.

## Discovery interview

Constraint-based, not fixed-question. One question at a time via AskUserQuestion. The goal is to understand what the system IS, not what to build.

**All scopes:**
- What is this system's job? (one sentence, active voice)
- What is explicitly NOT this system's job? (the boundaries list matters as much as the definition)
- What decisions are already locked? (existing SDs, ADRs, or constraints this must respect)

**System and Framework add:**
- What adjacent systems does this touch? (name each, state the interface)
- What principles must never be violated? (the non-negotiable rules that should survive any implementation change)
- What prior approaches were tried or considered, and why were they rejected? (prevents relitigating)

**Entity adds:**
- What parent system does this entity belong to? (Position section depends on this)
- How does this entity relate to other entities in the same system? (containment, composition, reference)

Skip questions when the answer is already documented in conversation context, existing SDs, or specs. Don't ask what you can read.

## Section structure

Follow this order. All sections mandatory unless marked optional. Detailed section guidance in `references/sd-guide.md`.

1. **Definition** - One paragraph. What it is and its purpose. No preamble.
2. **Position** - Where it sits relative to neighbors. Table or short list.
3. **Mechanics** - How it works. Subsections by mechanism. Definition > rules > boundary conditions per subsection.
4. **Principles** - Numbered, non-negotiable constraints. Bold name + 1-3 sentences.
5. **Adjacent systems** - One short paragraph per neighbor. State the interface.
6. **Boundaries** - What it is NOT. Bold label + 1-2 sentences. Only plausible confusions.
7. **Theoretical grounding** - (Optional) Framework name, one sentence on contribution.
8. **Future direction** - (Optional) Compact list of capabilities v1 excludes.
9. **Change Log** - `| Date | Change | Author |` table.

## Writing rules

These rules encode the SD writing profile (`WP - SD.md`) and oracle-informed patterns. The guide (`references/sd-guide.md`) explains rationale.

### Constitutional voice
- Active present tense. "The system routes signals" not "will route" or "should route."
- Declarative, not explanatory. State the rule. Brief rationale acceptable; narrative not.
- No implementation detail. No table names, endpoints, container names, file paths, config keys.

### Prior decisions
- **Document architectural alternatives considered.** If the design chose pattern A over B, state it in the relevant Mechanics subsection or as a Principle rationale. Agents writing specs from this SD need to know what was rejected and why.
- **Reference existing constraints.** If another SD, ADR, or spec already governs a boundary, cite it rather than restating. "See Principle 6 of [[SD - FWIS System Definition]]" not a restatement of the FWIS rule.

### YAGNI enforcement
- **SDs define principles, not implementations.** If a statement could change without violating the theory, it belongs in a spec.
- **Future Direction is a controlled list.** Add capabilities the architecture enables but v1 excludes. No narrative about what might be nice to have someday.

### Context precision
- **Reference specific systems by name.** "The Flora Context Graph's bi-temporal model" not "the temporal tracking system." Precision enables agents to look up the referenced system.
- **Inline examples are parenthetical.** Use sparingly: `(e.g., "Vendor Payment Processing")` not a full paragraph exploring the example.

### Density
- Size target: 80-120 lines of content (excluding frontmatter and changelog).
- No "Today vs. With" narratives. Motivation belongs in the Definition paragraph.
- No redundant boundary definitions. If a Principle already defines a boundary, the Boundaries section should not restate it.
- No tutorial repetition. State each concept once with precision.

## SD vs SPC decision

If the deliverable defines how a system behaves (principles, constraints, boundaries), write an SD. If it defines what to build (requirements, acceptance criteria, implementation scope), write a spec. Skill frameworks, workflow patterns, and agent behavior systems are SDs. Apps, services, and infrastructure changes are SPCs.

## Self-review checklist

Before presenting to the user, verify:

- [ ] Definition paragraph answers "what is it?" in one paragraph, active present tense
- [ ] Position section uses a table or compact list (no narrative tour)
- [ ] Every Principle is bold-named with 1-3 sentences (no preamble like "these are non-negotiable")
- [ ] No implementation detail leaked into any section (table names, endpoints, file paths)
- [ ] Boundaries section only lists plausible confusions not already covered by Principles
- [ ] Size is 80-120 lines of content
- [ ] Prior decisions documented (what alternatives were considered, what existing constraints apply)
- [ ] Theoretical grounding references functional frameworks (decision tools, not decoration)
- [ ] Change Log has the initial entry

Fix issues before presenting. This is not a gate that requires user approval, it's a quality check.

## Workflow

1. Oracle check (from shared setup + above)
2. Discovery interview (above)
3. Read existing context (project CLAUDE.md, related SDs, specs, ADRs, any existing SD fragments)
4. Draft v1 following section structure
5. Run self-review checklist
6. Present to user for review
7. Iterate, bump version and date modified

## Handoff

After user approves the SD:
1. Summary: what the SD defines, key principles, scope classification
2. Offer next step: "This SD can ground a spec. Run `/create-note SPC` to spec an implementation, or make changes first."
