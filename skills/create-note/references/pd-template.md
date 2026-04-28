# Product Definition Template

Use this structure for all product definitions. Omit sections that genuinely have no content (don't fill with placeholder text), but Vision, Goals, and Translation Guide are always required.

```markdown
---
date created: {YYYY-MM-DD}
tags: [product-definition, {topic-tags}]
category: Product Definition
author: {stakeholder name}
status: draft
---

# PD - {Topic Title}

**Author:** {who described this idea}
**Captured:** {date}
**Context:** {how the idea was communicated, voice memo, in-person conversation, written doc, etc.}

## Vision

{2-3 sentences in the stakeholder's own words and framing. Capture the spirit, not a sanitized corporate version. If they said "I want to stop documents from dying on shelves," write that, not "implement a document lifecycle management system."}

## Problem Statement

{What's broken, missing, or frustrating. Use the stakeholder's language. Be specific about who is affected and what the impact is.}

- {Problem 1}
- {Problem 2}
- {Problem 3}

## Goals

{Ordered by emphasis, what the stakeholder kept coming back to goes first. Each goal is an outcome, not a feature.}

1. **{Goal}**, {one sentence explaining what success looks like}
2. **{Goal}**, {one sentence}
3. **{Goal}**, {one sentence}

## Use Cases

{Concrete scenarios with real names, real situations, real workflows. These are the stakeholder's examples of where this would matter.}

### {Use Case Title}
{2-4 sentences describing the scenario: who, what situation, what they'd do, what outcome they'd get.}

### {Use Case Title}
{Same format.}

## Non-Negotiables

{Things that must be true regardless of how this gets built. These are constraints, not features.}

- {Non-negotiable 1}
- {Non-negotiable 2}

## Open Questions

{Things the stakeholder couldn't answer, areas of uncertainty, questions that need research or discussion before this can become a spec.}

- {Question 1}
- {Question 2}

## Translation Guide

{How the stakeholder's language maps to existing existing systems. This is the grounding section.}

| Stakeholder term | System equivalent | Status | Notes |
|---|---|---|---|
| {their word} | {system/feature name} | {exists / partial / new} | {what's built, what's missing} |
| {their word} | {system/feature name} | {status} | {notes} |

## Stakeholder Assumptions

{Technical or implementation opinions the stakeholder expressed. Captured without judgment. These are NOT requirements, they reflect the stakeholder's mental model, which may or may not match reality.}

- **Assumption:** {what they said}
  **Reality:** {what actually exists or how it actually works, if different}

## Priority Signal

{What the stakeholder was most emphatic about. What they mentioned repeatedly. What they flagged as urgent. This helps the developer prioritize when translating to a spec.}

**Strongest signal:** {the thing they care most about}
**Repeated themes:** {patterns in what they kept coming back to}
**Urgency markers:** {anything time-sensitive they mentioned}
```
