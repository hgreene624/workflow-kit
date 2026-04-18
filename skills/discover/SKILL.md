---
name: discover
description: >-
  Contextual skill discovery - observe what the user is working on and surface
  relevant WFK skills and principles they might not know about. Use this skill
  when the user says "discover", "what skills should I use", "what can you do",
  "help me work better", "workflow tips", "what am I missing", or when a new
  user wants to learn the kit. Can also run as a lightweight tip during /orient.
---

# Discover - Contextual Skill Guide

Observe the user's current work context and surface 2-3 WFK skills or principles that would help them right now. This is not a catalog dump. It's a targeted recommendation based on what the user is actually doing.

**Arguments:** $ARGUMENTS

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve directory references (e.g., `{paths.daily_notes}/DN - {today}.md`, `{paths.projects}/`). If the file doesn't exist, use defaults and warn once.

## Step 1: Read the user's context

Gather signals about what the user is doing. Read in parallel, skip missing files silently.

1. **Today's daily note** - `01_Notes/Daily/DN - {today}.md`
   - What topics are in `## Worked on`?
   - What's in `## TODO`?
   - Any meetings listed?

2. **Open PICs** - glob `**/PIC - *.md` with `status: open`
   - What work is in flight? What's stalled?
   - How many are open? (5+ suggests the user needs `/recap`)

3. **Recent daily notes** - last 3-5 days of `DN - *.md`
   - What skills has the user been invoking? (look for `[[PL -`, `[[SPC -`, `[[RE -`, `[[PJL -`, `/closeout`, `/implement` references)
   - What's repeating? What's missing?

4. **Vault structure** - quick scan of `02_Projects/`
   - How many active projects?
   - Do projects have agents.md and lessons.md?
   - Do projects have PJL files? (missing PJLs = knowledge not compounding)
   - Are there specs without plans? Plans without implementation?

5. **User profile** - read `agents.md` at vault root
   - What's the `wfk_role`?
   - Any queued context or preferences?

## Step 2: Build the skill catalog (dynamic)

**Do not use a hardcoded skill list.** Build the catalog at runtime from installed skills so it stays current as the kit evolves.

### 2a. Scan installed skills

```bash
for dir in ~/.claude/skills/*/; do
  name=$(basename "$dir")
  if [ -f "$dir/SKILL.md" ]; then
    # Extract frontmatter description (first 15 lines covers it)
    head -15 "$dir/SKILL.md"
  fi
done
```

Read each skill's frontmatter `name` and `description` fields. The description contains trigger phrases and use cases - this is your matching material.

### 2b. Categorize skills

Group skills into categories based on their descriptions. Use these categories as a guide, but let the descriptions drive categorization - new skills should slot into the right group automatically:

| Category | Description keywords to look for |
|---|---|
| **Session lifecycle** | orient, pickup, log-work, closeout, end-day, dream, recap |
| **Planning and design** | spec, review, plan, design, structure, grill |
| **Implementation** | implement, step-away, test, pr-review, git-safe |
| **Research and learning** | video, article, best-practice, learn, explain |
| **Content and quality** | meeting notes, frontend, web-theme, retro, pipeline-qa |
| **Meta and maintenance** | skill-creator, auto-research, usage-audit, update-wfk, intake, park |

### 2c. Filter out irrelevant skills

- Skip deprecated skills (check `kit.json` if available)
- Skip org-specific skills the user doesn't have installed
- Skip skills with `DEPRECATED` in their description

### 2d. Enrich with context signals

For each skill, note what vault state would make it relevant:

| If you see this... | ...recommend this |
|---|---|
| No SOD for today | `/orient` |
| Open PICs exist | `/pickup` |
| Work done but no DN entry | `/log-work` |
| User says "done" or "wrapping up" | `/closeout` |
| Multiple closeouts, no EOD | `/end-day` |
| 5+ open PICs, long conversation | `/recap` |
| Feature described with no spec | `/create-spec` |
| Spec exists, no review artifacts | `/review-spec` |
| Reviewed spec, no plan | `/create-plan` |
| Plan exists, no implementation started | `/implement` |
| Implementation done, no review | `/pr-review` |
| Complex doc or topic being discussed | `/explain` |
| Something broke and was fixed | `/learn` |
| YouTube URL or video mentioned | `/video-intel` |
| Article URL shared | `/article-intel` |
| Raw transcript or meeting content | `/create-MN` |
| User needs a web page or component | `/frontend-design` |
| Sprint or milestone completed | `/retro` |
| Files to organize | `/intake` |
| Context relevant to another project | `/park` |
| User wants to automate a workflow | `/skill-creator` |
| Token consumption concerns | `/usage-audit` |
| Kit hasn't been updated recently | `/update-wfk` |

### Workflow Principles

Not skills, but patterns the user should know. These stay as a curated list because they represent system-level knowledge, not individual tool capabilities.

| Principle | When to Teach | Signal |
|-----------|--------------|--------|
| **Spec > Plan > Implement** | User jumping straight to code | No spec or plan exists for active work |
| **PIC for everything deferred** | Work being abandoned without tracking | Tasks mentioned but no PIC created |
| **PJL for every project** | Project has work but no knowledge compounding | Active project missing a PJL file |
| **Both layers on every log** | PJL has timeline gaps | Work logged to daily note but PJL has no entry for that date |
| **One heading per project in daily notes** | Daily note is a wall of text | Multiple entries for same project as separate headings |
| **Date subfolders for project docs** | Files sitting in specs/ or plans/ directly | Spec or plan file not in a YYYY-MM-DD/ subfolder |
| **agents.md + lessons.md per project** | Project has no agent context | Active project missing these files |
| **Verify before logging** | Closeout logged unverified claims | Daily note says "deployed" but no deploy command was run |
| **Session boundaries in the PJL** | PJL only has work entries, no start/end | Pickup and create-pickup should log session boundaries |

## Step 3: Match and recommend

Compare the user's context (Step 1) against the catalog (Step 2). Find the 2-3 most relevant recommendations.

**Matching rules:**
- Prioritize skills the user has NEVER used (check daily note history) over skills they use regularly
- Prioritize skills that address an active gap (spec exists without review, plan exists without implementation, project has no PJL) over general suggestions
- Prioritize workflow principles when the user is doing things manually that a skill automates
- Never recommend more than 3 items. If nothing stands out, say so.

## Step 4: Present recommendations

Format each recommendation as:

```
### /skill-name - one-line summary

**Why now:** What you observed in their context that makes this relevant.

**What it does:** 2-3 sentences explaining the skill in plain language, focused on the outcome not the mechanics.

**Try it:** The exact command to run, with any arguments pre-filled from context.
```

For workflow principles (not skills), use:

```
### Principle name

**Why now:** What you observed.

**What to do:** Concrete action the user should take.
```

After the recommendations, add:

```
Run `/discover catalog` to see all available skills, or ask about any specific skill for details.
```

## Actions

### Default (no arguments) - contextual recommendations
Run Steps 1-4 as described above.

### `catalog` - full skill list
Run Step 2 to build the dynamic catalog, then present it as a formatted reference grouped by category. No contextual analysis needed.

### `<skill-name>` - explain a specific skill
Read the named skill's SKILL.md and explain what it does, when to use it, and show an example invocation. Tailor the explanation to the user's context if available.

## Skill Chains

Skills compose into documented chains. Key chains:
- **Daily**: orient → pickup → log-work → closeout → end-day → dream
- **Build**: create-spec → review-spec → create-plan → implement → pr-review → retro

When recommending skills, consider where the user is in a chain and suggest the natural next step.

## Constraints

- Maximum 3 recommendations. Quality over quantity.
- Never recommend a skill the user just used in this session.
- Never recommend `/orient` or `/pickup` mid-session (they're session-start skills).
- If the user is clearly experienced (daily notes show regular skill usage across categories), focus on advanced tips and workflow principles rather than basic skill introductions.
- Keep each recommendation under 100 words. The user should be able to scan all 3 in 30 seconds.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
