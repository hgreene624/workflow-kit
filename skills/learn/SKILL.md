---
name: learn
description: >-
  Extract and store reusable lessons or enforceable rules from the current conversation.
  Use this skill whenever the user says "learn this", "remember this", "don't do that again",
  or after any correction, failure, surprising fix, or non-obvious workaround worth capturing
  for future sessions. Also trigger when the user says "learn", "add a lesson", "add a rule",
  "that should be a rule", or describes a mistake they don't want repeated. Even if the user
  just says "/learn" with no arguments, this skill should activate and scan the conversation
  for the most recent teachable moment.
---

# Learn — Capture Lessons and Rules

Extract a reusable lesson or enforceable rule from this conversation and store it where future sessions will find it.

The reason this matters: without persistent lessons, every new conversation starts from zero. The same mistakes get made, the same workarounds get rediscovered, the same corrections get given. A well-placed lesson prevents that — it's a message from past-you to future-you (or future-agent) saying "we already figured this out, here's what to do."

**Arguments:** $ARGUMENTS

## Step 1: Identify What to Capture

**If arguments were provided** (e.g., `/learn Plane upgrades reset config`), use them as the lesson content directly. Don't re-scan the conversation.

**If no arguments**, scan backward through the conversation for the most recent:
- Correction from the user ("no, don't do that — instead...")
- Failure that required a non-obvious fix
- Surprising behavior that wasted time
- Workaround the user had to explain

Focus on whatever happened just before the user said "learn." If nothing stands out, ask what they want to capture.

**Gate check — is this worth persisting?** Not everything belongs in a lessons file. Good candidates:
- Would trip up a fresh agent who hasn't seen this codebase before
- Contradicts what you'd reasonably assume from docs or conventions
- Cost real time or effort to discover
- Applies beyond just this one conversation

Skip if it's purely ephemeral (a typo, a one-time config value, something the code itself now prevents).

## Step 2: Classify

**Lesson or rule?** These serve different purposes:

- **Lesson** — retrospective context. "We learned X the hard way." Advisory, not mandatory. Lives in `lessons.md` files or `REF - *Lessons.md` reference docs.
- **Rule** — prescriptive behavior. "Always do X" or "Never do Y." Mandatory for all agents working in that scope. Lives in `## Rules` sections of `agents.md` files.

The distinction matters because lessons inform judgment while rules constrain behavior. A lesson says "this went wrong once, be careful." A rule says "this must always be done this way, no exceptions."

If the user's phrasing makes the type obvious, go with it. If ambiguous, ask — one question, two options: "Lesson (advisory — informs future decisions)" vs "Rule (mandatory — agents must follow this)."

## Step 3: Scope

Pick the **narrowest** level that covers where this lesson applies. A lesson about Docker networking doesn't belong in the general agent lessons file, and a lesson about how all agents should behave doesn't belong in one project's `lessons.md`.

Consult `references/scope-map.md` for the full scope table mapping domains to file paths.

**Quick heuristic:** If you can name a specific project directory where this applies, scope it there. If it spans projects but is domain-specific (frontend, VPS, Plane), use the domain reference file. If it's about general agent behavior, use `REF - Agent Lessons.md`.

## Step 4: Dedup Check

Before writing, check if this lesson already exists:

1. Read the target file to find the current highest `L[N]` number
2. Search the target file for 2-3 key terms from your draft title (use Grep)
3. Also search one scope level up — a broader file might already cover this

**If you find a match:**
- **Same scope, same lesson** → update the existing entry with new context rather than adding a duplicate
- **Different scope, same lesson** → add a `**See also:** [[file]] L[N]` cross-reference on both
- **Same incident, multiple lessons** → each entry must teach a distinct principle. If one is "do X" and another is "the general principle behind doing X," merge them

## Step 5: Draft and Approve

Write the entry, then present it for approval. The user should see exactly what will be written.

**Lesson format (C-A-W — default):**
```markdown
## L[N]: [Short imperative title]
**Condition:** [When this applies — specific trigger or situation]
**Action:** (1) [First step]. (2) [Second step]. (3) [Third step].
**Why:** [Consequence if skipped — what goes wrong and why]
**Scope:** [Which projects/domains this applies to]
**Source:** [Date] — [Brief incident description]
```

**Lesson format (Narrative — only when no actionable steps):**
```markdown
## L[N]: [Short imperative title — verb phrase, not noun phrase]
[1-2 sentences: what to do and why. Specific enough that an agent reading this cold understands the action without needing the full incident story.]
**Source:** [YYYY-MM-DD] — [One-line incident description]
```

Default to C-A-W format. Use narrative format only when the lesson genuinely has no actionable steps (purely retrospective context).

**Rule format:**
```markdown
[N]. **[Short imperative title]**: [1-2 sentences. Specific enough to follow without additional context.]
```

**What makes a good title:** Use imperative verb phrases ("Verify schema before writing queries"), not noun phrases ("Schema verification issue"). The title alone should tell an agent what to do.

**What makes good body text:** Explain the *why* — not just "always do X" but "always do X because Y happens otherwise." An agent that understands the reason can apply the lesson to novel situations, not just the exact scenario where it was learned.

Present via AskUserQuestion with these options: "Approve", "Edit wording", "Skip", "Change scope"

**For file-scoped inline lessons:** Use `### L[N]` (h3) since `## Lessons` (h2) is the section header. Place the `## Lessons` section at the end of the file.

## Step 6: Write

- **Lessons:** Append to the target file's lessons section. If creating a new `lessons.md`, add a breadcrumb reference in the nearest `agents.md`.
- **Rules:** Append to `## Rules` in the target `agents.md`. Use the next sequential number. If no `## Rules` section exists, create one before the last section of the file.
- Match the formatting style of existing entries in the target file — consistent heading levels, spacing, and source attribution format.

## Step 7: Update Index

After creating a new lesson, update the Rules & Patterns Index at `Documentation/Rules and Patterns Index.md` — add the new lesson under the appropriate domain(s). This keeps the central index in sync with all lesson files across the vault.

## Examples

**Good lesson (C-A-W) — specific, actionable, explains why:**
```markdown
## L7: Always inspect DB schema before writing queries
**Condition:** Writing SQL against an unfamiliar or recently-changed table.
**Action:** (1) Run `\d schema.table` to see actual column names and types. (2) Compare against any spec or migration file. (3) Only then write queries.
**Why:** Guessing column names leads to cascading 500 errors — fixing one wrong column often introduces another wrong guess, each requiring a rebuild+deploy cycle.
**Scope:** All database work across projects.
**Source:** 2026-03-10 — KB edit page hit 500 three times from wrong column names, each fix required a rebuild+deploy cycle.
```

**Good lesson (Narrative) — retrospective context, no repeatable steps:**
```markdown
## L5: External attribution stops investigation too early
We spent 2 hours assuming the Plane API was down before discovering our own proxy was misconfigured. External blame is the easiest hypothesis — it stops investigation exactly when it should deepen.
**Source:** 2026-03-02 — Plane API "outage" was actually a proxy routing error.
```

**Bad lesson — vague, no action, no why:**
```markdown
## L7: Database issues
We had problems with the database. Be careful with queries.
**Source:** 2026-03-10 — Query problems.
```

**Good rule — clear mandate, specific scope:**
```markdown
3. **Read procedure docs before VPS changes**: Before modifying any VPS config or service, read the relevant procedure doc from `Maintenance/`. Never skip steps, even if you "know" the procedure.
```

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
