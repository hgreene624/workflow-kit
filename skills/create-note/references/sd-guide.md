# System Definition Writing Guide

The definitive guide for writing agent-friendly system definitions. Informed by the Spec-Driven Development oracle (55 sources, 2026-04-30), 12 production SDs in the Flora vault, and the WP - SD writing profile.

A system definition is a constitution. It defines what a system IS and what principles govern it. Specs implement parts of it. The SD stays stable while implementations evolve. The quality of downstream specs, plans, and implementations is bounded by the quality of the SD they reference.

## What makes an SD agent-friendly

Agents consume SDs at two points: when writing specs (to understand constraints) and when implementing (to check whether a design decision violates a principle). An agent-friendly SD:

1. **States principles as testable rules.** "Process entities never modify the strategic hierarchy" is testable. "Process entities respect the strategic hierarchy" is vague.
2. **Names adjacent systems explicitly.** "The Flora Context Graph" not "the knowledge system." Agents look up references by name.
3. **Draws clear boundaries.** "Not a commitment tracker. No work items, no Say-Do Ratio" tells an implementing agent exactly what NOT to build.
4. **Documents rejected alternatives.** "The design chose role-based ownership over person-based ownership because..." prevents agents from proposing the rejected approach.
5. **Keeps implementation out.** An agent reading an SD should never encounter a table name, endpoint, or container. Those change; principles don't.

## Section craft

### Definition

One paragraph. Answer "what is this system and why does it exist?" No meta-commentary ("this document defines..."). No history ("we needed this because..."). The definition should work as a standalone summary if someone reads nothing else.

**Good:** "The Process Entity makes recurring operational work visible to the intelligence system without contaminating the strategic commitment hierarchy."

**Bad:** "This document defines the Process Entity Model, which was created to address the gap in operational visibility that emerged during the FWIS v8 design review."

### Position

Where the system sits relative to its neighbors. Use a table or compact list. The reader should understand in 10 seconds what sits above, below, and beside this system.

For entity SDs, show the parent system's question-hierarchy (see Process Entity Model's Position table). For system SDs, show input/output relationships. For framework SDs, show consumer/provider relationships.

No narrative tour. "The system sits between X and Y, receiving signals from Z" becomes a 3-row table.

### Mechanics

The heaviest section. Organize by mechanism, not by chronology or priority. Each subsection follows the pattern: definition of the mechanism, rules governing it, boundary conditions.

Name subsections after the mechanism: "Signal Routing," "Flow-Based Health," "Process Discovery." Not generic labels like "How It Works" or "Core Functionality."

Each mechanism subsection should be independently readable. An agent implementing just signal routing should be able to read that subsection without needing the others.

### Principles

Numbered, non-negotiable constraints. Each principle: bold name, then the rule in 1-3 sentences.

No preamble ("the following principles are non-negotiable"). The section heading implies it.

Principles should be falsifiable. An implementing agent should be able to check "does my design violate Principle N?" and get a clear yes or no. "The system should be efficient" is not falsifiable. "Signal velocity baselines use rolling averages, not fixed thresholds" is.

Order by importance: the most load-bearing principle comes first. If a principle depends on or references another, it comes after.

Include brief rationale when the reason is non-obvious, but keep rationale subordinate to the rule itself. The rule is the sentence; the rationale is the parenthetical.

### Adjacent systems

One short paragraph per neighbor. State the interface (what crosses the boundary), not the implementation (how it crosses). Name the neighbor by its SD or canonical name.

"**FWIS Signal Engine.** Process context is injected into the classification prompt alongside initiative/project context. The pipeline gains a new routing target without structural change."

This tells an implementing agent what to connect and where the boundary is. It does not tell them how to wire the connection (that's spec content).

### Boundaries

What the system is NOT. Each entry: bold label, 1-2 sentences. Only include boundaries that a reader could plausibly confuse.

Test: "Would a reasonable agent, reading only the Definition and Mechanics, mistakenly build this?" If yes, add the boundary. If no, skip it.

Do not restate boundaries already captured by a Principle. If Principle 1 says "processes do not generate work items," the Boundaries section should not say "Not a work item generator."

### Theoretical grounding (optional)

Compact list: framework name (author, year), one sentence on how it contributes to this design.

These are functional decision tools, not decorative citations. When a future design decision arises, the agent should be able to check: "What does Beer's Viable System Model say about this?" and use the grounding to resolve the question.

Only include frameworks that actively informed a design choice. "We read about X but didn't use it" does not belong here.

### Future direction (optional)

Compact list of capabilities the architecture enables but v1 excludes. One line each. No narrative about aspirations.

The purpose is to signal that the architecture was designed with these capabilities in mind, so implementing agents don't accidentally close doors that should stay open. "Process-to-project escalation" tells a spec writer "don't build this, but don't build something that would make this impossible."

### Change Log

`| Date | Change | Author |` table. One row per version. The change column should be dense: what was added/removed/changed and why, in one sentence.

## Anti-patterns

1. **The implementation leak.** Table names, endpoints, container names, config keys, file paths in the SD. Test: "Could this detail change without violating any principle?" If yes, remove it.

2. **The motivation essay.** Multi-paragraph "Today vs. With" narratives explaining why the system was needed. Motivation belongs in the Definition paragraph (2-3 sentences max) or in the source spec's problem statement.

3. **The tutorial.** Saying the same concept three different ways to ensure comprehension. State it once with precision. The reader is an agent or a system owner, not a student.

4. **The spec in disguise.** Requirements, acceptance criteria, deliverables, implementation phases. If the SD has a "Requirements" section, it's a spec. If it has a "Phase 1" section, it's a plan.

5. **The boundary novel.** Listing 10+ "what this is not" entries. If the system needs that many boundaries, the Definition is not precise enough. Tighten the definition, reduce the boundaries.

6. **The orphan principle.** A principle that no one will ever check or enforce. If it cannot influence a spec, plan, or implementation decision, it's aspirational, not constitutional.

7. **The stale grounding.** Citing a framework without connecting it to a specific design choice. "Winograd-Flores (1986)" is decoration. "Winograd-Flores conversation-for-action test defines the process/commitment boundary" is functional.

8. **The vague adjacency.** "Interacts with several other systems" instead of naming each neighbor and its interface. Agents cannot look up "several other systems."

## Relationship to other document types

| If you're writing... | It belongs in... |
|---------------------|-----------------|
| What the system IS, its principles and boundaries | SD |
| What to BUILD (requirements, acceptance criteria) | SPC |
| HOW to build it (task decomposition, sequencing) | PL |
| What the PRODUCT does for users | PD |
| Design options and tradeoffs for a specific decision | DD |
| The structure/layout of a content system | SO |

An SD can spawn multiple SPCs. Each SPC implements a slice of the SD's mechanics. The SD doesn't change when a spec ships; it only changes when a principle, boundary, or mechanism is revised.

## Oracle reference

This guide is informed by the Spec-Driven Development oracle (`40fc91f1`, 55 sources). Key SD-specific findings:

- **Constitutional voice:** Active present tense, no hedging about implementation status (Augment Code specification patterns, Claude Code CLAUDE.md conventions)
- **Falsifiable principles:** Rules an agent can mechanically check (Martin Fowler's architectural fitness functions, Superpowers verification-before-completion)
- **Named interfaces:** Adjacent system interfaces state what crosses the boundary, not how (GitHub Spec Kit boundary specification)
- **Prior decisions as constraints:** Document rejected alternatives to prevent relitigating (HITL comparative analysis, Anthropic agent teams)
- **Theoretical grounding as decision tools:** Frameworks inform choices, not decorate citations (intent-driven.dev domain-driven patterns)

Full grounding report: [[ARE - Spec-Driven Development Grounding Report]]

## Exemplars

The strongest production SD is [[SD - Process Entity Model]] (v3). It demonstrates tight constitutional voice, falsifiable principles, a position table, mechanism-per-subsection organization, and functional grounding. Read it before writing your first SD.
