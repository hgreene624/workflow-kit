# PD Template - Product Definition

## Frontmatter additions

Tags: `[spec, product-definition, <project-tag>]`

## What a PD is

A pre-spec document that captures stakeholder vision. Clarifies intent, scope, and success criteria, not implementation. PD and SD are siblings, not a pipeline. Either can lead to a spec.

## Interview (if input is sparse)

Focus on outcomes, not technology:
- "What should this let people do that they can't do today?"
- "What's broken or missing right now?"
- "Can you describe a specific situation where you'd use this?"
- "If you could only have one piece, what would it be?"
- "What absolutely must be true about how this works?"

Do NOT ask about technology, architecture, databases, or APIs. If the user volunteers technical opinions, capture as "stakeholder assumptions."

One question at a time via AskUserQuestion.

## Ground against project context

Read `references/flora-context.md`. For each idea, check: does something exist already? Which system is closest? Different words for the same thing? What's new vs extended?

## Section structure

1. **Vision** - 2-3 sentences in the user's own words
2. **Problem Statement** - what's broken, missing, or frustrating
3. **Goals** - numbered outcomes, ordered by emphasis
4. **Use Cases** - concrete scenarios with named people and real situations
5. **Non-Negotiables** - constraints regardless of implementation
6. **Open Questions** - things the user couldn't answer
7. **Translation Guide** - table mapping user language to system names (exists/partial/new)
8. **Stakeholder Assumptions** - technical opinions flagged as "stakeholder perspective, not requirement"
9. **Priority Signal** - what was emphatic, repeated, urgent

## Handoff

Offer: run `/create-note SPC` to spec it, or `/prototype` for visual prototyping.
