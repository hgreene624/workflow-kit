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
   - What skills has the user been invoking? (look for `[[PL -`, `[[SPC -`, `[[RE -`, `/closeout`, `/implement` references)
   - What's repeating? What's missing?

4. **Vault structure** - quick scan of `02_Projects/`
   - How many active projects?
   - Do projects have agents.md and lessons.md?
   - Are there specs without plans? Plans without implementation?

5. **User profile** - read `agents.md` at vault root
   - What's the `wfk_role`?
   - Any queued context or preferences?

## Step 2: Build the skill catalog

These are the WFK skills grouped by when they're useful. Use this to match against the user's context.

### Daily Operations
| Skill | When It Helps | Signal to Look For |
|-------|--------------|-------------------|
| `/orient` | Start of every session | No SOD exists, agent seems unaware of context |
| `/pickup` | Resuming deferred work | Open PICs exist, user says "where was I" |
| `/log-work` | Recording what was done | User manually editing the daily note |
| `/closeout` | End of a work session | User says "done for now", work was done but not logged |
| `/end-day` | End of the workday | Multiple closeouts happened, no EOD exists |
| `/dream` | Memory cleanup | Auto-memory growing stale, duplicates accumulating |
| `/recap` | Lost track of threads | 5+ open PICs, long conversation, multiple side-threads |

### Planning and Design
| Skill | When It Helps | Signal to Look For |
|-------|--------------|-------------------|
| `/create-spec` | Defining new work | User describing a feature/project without a spec |
| `/review-spec` | Validating a spec | Spec exists but no review artifacts alongside it |
| `/design` | Aligning on approach | Spec reviewed, but implementation approach unclear |
| `/structure` | Module/phase planning | Design decided, need to define boundaries before coding |
| `/plan-spec` | Creating implementation plan | Reviewed spec exists, no plan yet |
| `/grill` | Stress-testing a design | User has a design but hasn't challenged assumptions |

### Implementation
| Skill | When It Helps | Signal to Look For |
|-------|--------------|-------------------|
| `/implement` | Executing a plan | Plan exists with tasks, no implementation started |
| `/step-away` | Autonomous work while away | User leaving for a while, wants work to continue |
| `/test-check` | Verifying code changes | Code was written but tests not mentioned |
| `/pr-review` | Post-implementation review | Implementation done, no review artifact |
| `/git-safe` | Any git operation | About to push, merge, or rebase |

### Research and Learning
| Skill | When It Helps | Signal to Look For |
|-------|--------------|-------------------|
| `/video-intel` | Processing video content | User mentions a YouTube video or has a watch queue |
| `/article-intel` | Processing articles | User shares a URL or article to analyze |
| `/best-practice` | Comparing approaches | User weighing options, needs research |
| `/learn` | Capturing a lesson | Something broke, was fixed, or a non-obvious workaround was found |

### Content and Quality
| Skill | When It Helps | Signal to Look For |
|-------|--------------|-------------------|
| `/create-MN` | Structuring meeting notes | User has raw transcript or meeting content |
| `/frontend-design` | Building UI | User needs a web page, component, or visual artifact |
| `/web-theme` | Capturing site aesthetics | User wants to match another site's style |
| `/retro` | After a sprint or milestone | Significant body of work completed, no retrospective |

### Meta and Maintenance
| Skill | When It Helps | Signal to Look For |
|-------|--------------|-------------------|
| `/skill-creator` | Building new skills | User wants to automate a repeated workflow |
| `/auto-research` | Improving existing skills | A skill underperforms, needs optimization |
| `/usage-audit` | Token consumption issues | User hitting rate limits or concerned about costs |
| `/update-wfk` | Getting latest kit updates | Kit hasn't been updated recently |
| `/intake` | Organizing incoming files | User has files to sort into the vault |
| `/park` | Deferring context | Found something relevant to another project during current work |

### Workflow Principles
Not skills, but patterns the user should know:

| Principle | When to Teach | Signal |
|-----------|--------------|--------|
| **Spec > Plan > Implement** | User jumping straight to code | No spec or plan exists for active work |
| **PIC for everything deferred** | Work being abandoned without tracking | Tasks mentioned but no PIC created |
| **One heading per project in daily notes** | Daily note is a wall of text | Multiple entries for same project as separate headings |
| **Date subfolders for project docs** | Files sitting in specs/ or plans/ directly | Spec or plan file not in a YYYY-MM-DD/ subfolder |
| **agents.md + lessons.md per project** | Project has no agent context | Active project missing these files |

## Step 3: Match and recommend

Compare the user's context (Step 1) against the catalog (Step 2). Find the 2-3 most relevant recommendations.

**Matching rules:**
- Prioritize skills the user has NEVER used (check daily note history) over skills they use regularly
- Prioritize skills that address an active gap (spec exists without review, plan exists without implementation) over general suggestions
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

After the recommendations, add:

```
Run `/discover catalog` to see all available skills, or ask about any specific skill for details.
```

## Actions

### Default (no arguments) - contextual recommendations
Run Steps 1-4 as described above.

### `catalog` - full skill list
Show the complete catalog from Step 2 as a formatted reference. No contextual analysis needed. Group by category.

### `<skill-name>` - explain a specific skill
Read the named skill's SKILL.md and explain what it does, when to use it, and show an example invocation. Tailor the explanation to the user's context if available.

## Constraints

- Maximum 3 recommendations. Quality over quantity.
- Never recommend a skill the user just used in this session.
- Never recommend `/orient` or `/pickup` mid-session (they're session-start skills).
- If the user is clearly experienced (daily notes show regular skill usage across categories), focus on advanced tips and workflow principles rather than basic skill introductions.
- Keep each recommendation under 100 words. The user should be able to scan all 3 in 30 seconds.
