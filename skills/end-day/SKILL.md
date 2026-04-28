---
name: end-day
description: "Aggregate the day's work into an EOD report and generate tomorrow's SOD (agent context document). Rolls up all closeout entries from the daily note, compares against SOD priorities, runs a mini-retro, discovers goals for user confirmation, then writes the SOD that orient will load tomorrow. On Fridays, also produces an EOW. On the last workday of the month, also produces an EOM. Use this skill when the user says 'end day', 'end of day report', 'EOD report', 'daily report', 'wrap up the day', 'day summary', 'how did today go', 'end-day', or wants a synthesized view of what happened across all sessions. This is different from /closeout (which wraps a single terminal session and creates PICs) -- end-day aggregates ALL closeouts into the day's official record and prepares tomorrow's agent context. Should typically run after the last /closeout of the day."
---

# End of Day -- Daily Aggregation Report

The EOD is the **official record of what happened today**. It aggregates all closeout entries from the daily note into a single synthesized report, compares reality against the SOD's stated priorities, and discovers goals for user confirmation.

**Writing rules:** Load and follow any writing profiles configured for reports in your vault. EOD/EOW/EOM are reports: findings first, objective data, tables for comparisons.

After producing the EOD, this skill also generates **tomorrow's SOD** -- the agent context document that orient loads at session start. This keeps everything in one place: end-day is the only skill that writes reports.

On Fridays, this skill also produces an **EOW (End of Week)** report rolling up the week's EODs. On the last workday of the month, it also produces an **EOM (End of Month)** report rolling up the month's EOWs.

## Roadmap Awareness

Before aggregating, read the current **RM** (most recent file in `01_Notes/Roadmaps/`) and **WF** (most recent `WF - *.md` in the latest dated subfolder of `Reports/`). If both exist, add a **Goal Progress** section to the EOD that reports at the goal level, e.g.:

```
## Goal Progress
- **Goal A:** Significant progress (pipeline unblocked, 3 items shipped). Remaining: final integration.
- **Goal B:** Iterated on content depth, 4 items expanded. Ownership tracking not started.
- **Goal C:** No progress today.
```

This makes it visible when a goal stalls across days. The SOD should carry forward any goal that had no progress, flagging it: "Goal [X] had no progress yesterday. Prioritize or explicitly defer?"

On **Fridays** (EOW), also compare the week's goal progress against the WF's "What 'done' looks like" criteria. Did the weekly goals ship? What carries forward to next week's WF?

## Path Resolution

Read `~/.claude/wfk-paths.json` at startup. Use `vault_root` and `paths` to resolve all directory references in these instructions. Key mappings: `{paths.daily_notes}` for daily notes, `{paths.reports}` for all report subdirectories (SOD, EOD, EOW, SOM, SOW, EOM, Triage), `{paths.projects}` for project tree, `{paths.pickups}` for cross-cutting pickups. If the file doesn't exist, use the defaults in these instructions and warn once.

## Step 0: Day Rating

Before anything else, ask the user how today went. Use AskUserQuestion with a 1-5 scale:

| Rating | Label |
|--------|-------|
| 1 | Rough day |
| 2 | Below average |
| 3 | Decent |
| 4 | Good day |
| 5 | Great day |

Add the rating to today's daily note frontmatter as `day_rating: N`. If the user adds a comment, store it as `day_note: "..."` in frontmatter too.

This runs first because it captures the user's subjective feeling before the analytical steps reframe their perception. Don't skip it.

## Step 0a: Repository & Deploy Health Audit (MANDATORY)

End-day is the **machine-wide** truth check. While `closeout` audits a single session's own work, end-day audits **everything** -- every git repo on this machine, every deployed service, every auto-memory and config backup -- and surfaces every uncommitted change, unpushed commit, and undeployed service. This is a READ-ONLY audit that REPORTS state. It does NOT auto-fix unless the user explicitly asks.

**Why this matters:** Multiple agent sessions run in parallel. By end of day there may be commits authored by sessions that finished hours ago but never pushed, files committed on a server but not synced to a remote, services running stale code from before today's deploys, or skill edits that never made it into a backup. End-day catches all of it before tomorrow's first session.

### 0a. Local repo audit

For each known git repo on this machine, check uncommitted state, unpushed commits, and remote sync state. Run in parallel where possible.

Discover repos automatically:
```bash
find ~/Repos -maxdepth 2 -name .git -type d 2>/dev/null
```

Also check the vault directory if it's a git repo, and `~/.claude/` if it has a `.git` directory.

For each:

```bash
cd <repo>
git fetch origin --quiet
echo "branch: $(git branch --show-current)"
git status --short
echo "unpushed:"
git log @{u}..HEAD --oneline 2>/dev/null
echo "behind remote:"
git log HEAD..@{u} --oneline 2>/dev/null
```

Categorize each finding:
- **Uncommitted changes** -- `git status` output. List files. Note authorship clues (recent file mtime vs other indicators).
- **Unpushed commits** -- `git log @{u}..HEAD`. Show commit hashes, authors, messages, ages.
- **Behind remote** -- `git log HEAD..@{u}`. Means local is out of date with origin -- someone else pushed since this machine last pulled.
- **Detached HEAD or wrong branch** -- flag prominently. Should never be in this state at end of day.

### 0b. Remote repo audit (if applicable)

If the user's environment includes repos on remote servers (deploy targets, VPS hosts), check those too via SSH. Look in the project's CLAUDE.md or reference docs for remote repo locations.

```bash
ssh <deploy-target> "
for repo in <remote-repo-paths>; do
  if [ -d \$repo/.git ]; then
    echo === \$repo ===
    cd \$repo
    git fetch origin --quiet 2>/dev/null
    git branch --show-current
    git status --short
    echo unpushed:
    git log @{u}..HEAD --oneline 2>/dev/null
  fi
done
"
```

Remote repos are easy to forget. Direct edits on servers (outside normal git flow) are a common source of drift.

### 0c. Container/service drift audit (if applicable)

For every deployed service, compare the deploy artifact against the latest code commit that touches the service's paths. If the commit is newer than the deployed version, the service is on stale code.

**Adapt this to your infrastructure.** The concept is universal but the commands vary:
- Docker containers: compare image creation time against commit timestamps
- Cloud deployments: check the last deploy timestamp from your CI/CD dashboard
- Static sites: check the build artifact date

**Filtering: not all drifts are real.** Before reporting, classify each drifted commit:

- **Real code change** (touches source code, config baked into builds, Dockerfiles, compose files): NEEDS DEPLOY. Flag prominently.
- **Doc-only change** (touches only README, CLAUDE.md, markdown not in code paths): NO DEPLOY. Docs aren't baked into images. Mark as "doc only -- no deploy needed."
- **Framework auto-mods** (auto-generated type files, dev path changes, auto-flipped config values): NO DEPLOY in most cases. Production builds regenerate these. Mark as "framework noise -- no functional impact."
- **Config/env changes outside the image**: NO DEPLOY (env files are mounted, not copied).

For each "real code change" drift, do a functional verification if possible:

```bash
# Check if a distinctive string from the latest commit is present in the running service
ssh <deploy-target> "docker exec <container> grep -F '<distinctive string from latest commit>' /app/<path-to-file>"
```

If the distinctive string is present, the deployment actually has the code (the timestamp lied due to a cached build). If absent, confirmed stale.

### 0d. Backup mirror audit (if applicable)

If the user maintains backup mirrors of agent configuration files (skills, agents, settings), check that they're current:

```bash
diff -rq ~/.claude/skills/ <backup-path>/skills/ 2>/dev/null | head -20
diff -rq ~/.claude/agents/ <backup-path>/agents/ 2>/dev/null | head
diff -q ~/.claude/settings.json <backup-path>/settings.json 2>/dev/null
```

Any drift means the mirror is stale. Report which files differ but do not auto-sync.

### 0e. Auto-memory audit

Skim `~/.claude/projects/*/memory/MEMORY.md` for any new entries today (look for files with mtime today). Flag if:
- New memory files exist that aren't yet referenced in MEMORY.md (orphan entries)
- MEMORY.md references files that don't exist (broken links)

This catches the failure mode where a session saved a memory file but forgot to add the index entry.

### 0f. Present the audit report

Before continuing to Step 1, output a single comprehensive table:

```
End-Day Repository & Deploy Health Audit
========================================

Local repos:
  ~/Documents/Vaults                    branch=main  clean  ok
  ~/Repos/my-project                    branch=main  WARNING 1 unpushed commit (yours), 6 modified files (framework noise)
  ~/Repos/other-project                 branch=main  clean  ok

Remote repos (if applicable):
  deploy-target:/path/to/repo           branch=main  clean  ok  (at cb28d52, in sync with origin)

Service drift (if applicable):
  WARNING web-app     commit 30min newer  (real code: src/middleware.ts)        -> NEEDS DEPLOY
  WARNING dashboard   commit 4h newer  (framework noise: tsconfig jsx flip)     -> no real impact
  ok all other services in sync

Backup mirror (if applicable):
  skills/      drift: 2 files newer in source than mirror                      -> run backup
  agents/      ok in sync
  settings.json ok in sync

Auto-memory:
  1 new file today, indexed in MEMORY.md                                       ok
```

For each WARNING flag, ask the user how to handle it BEFORE proceeding to Step 1:

```
3 issues need attention before EOD report:

  1. my-project has 1 unpushed commit (your authored, from 14:23)
     -> push? [y/n/show diff]
  2. web-app is stale (real code change unshipped)
     -> deploy now? [y/n/skip]
  3. backup mirror is stale (2 skill files modified today)
     -> run backup? [y/n]
```

Do NOT auto-fix. The user decides each one. Reasons:
- Unpushed commits may be intentional (in-progress, not ready)
- Stale deployments may belong to another session that's about to deploy
- Mirror drift may be intentional if the user is mid-skill-edit and doesn't want it captured yet

**If no issues:** print one line -- `Repository & deploy health: clean.` -- and proceed.

**If issues are deferred** (user says "skip" or "leave it"): record them in the EOD report's "What Didn't" section so they're visible tomorrow morning.

## Step 1: Gather today's context

Read in parallel. Skip missing files silently.

**Base path:** `{vault_root}`

1. **Today's daily note** -- `01_Notes/Daily/DN - {today}.md`
   - Extract the full `## Worked on` section (this is what closeouts wrote)
   - Extract `## TODO` to check completion
   - Extract `## Meetings` for context
2. **Today's SOD** -- `01_Notes/Reports/SOD/SOD - {today}.md`
   - Read the user's Priorities and Suggested Start sections
   - This is the intent baseline to compare against
3. **PICs created today** -- glob `02_Projects/**/PIC - *.md` where `date created` = today
   - These represent carry-forward work from today's closeouts
4. **PICs closed today** -- glob for PICs where `closed_date` = today
   - These represent completed work
5. **Current SOW** -- most recent in `01_Notes/Reports/SOW/` (if exists)
   - For week-level goal context

## Step 2: Synthesize the EOD

Build the report. Keep it **under 350 words** -- this gets loaded into tomorrow's SOD context.

### EOD document structure

Read and follow the template in `templates/eod-template.md` (in this skill's folder). Keep the EOD **under 350 words**.

## Step 3: Present to user

Show the full EOD (it's short enough) and specifically call out the Goal Discovery section -- ask the user to confirm or reject each proposed goal with a checkbox interaction:

"Here are the goals I think you're working toward. Confirm the ones that are right, and I'll carry them into tomorrow's SOD:"

Then list the goals. User responds with which to keep. Update the EOD to check the confirmed ones.

## Step 4: Generate tomorrow's SOD

The SOD is an **agent-facing document** -- every agent reads it via orient to understand the state of the world and the user's priorities. It's a rolling week-to-date (WTD) context window that resets when an EOW drops.

Read and follow the template in `templates/sod-template.md` (in this skill's folder). It contains the WTD window calculation, context gathering steps, document structure, and save location.

## Step 5: EOW (Fridays only)


If today is Friday (or the last workday before a weekend), also produce an EOW.

Read and follow the template in `templates/eow-template.md` (in this skill's folder).

## Step 5: EOM (last workday of month only)

If today is the last workday of the month, also produce an EOM.

Read and follow the template in `templates/eom-template.md` (in this skill's folder).

## Step 6: Vault Hygiene Scan

Before dream, scan the vault for misplaced files created today. This catches routing violations early and identifies which workflows are generating files in the wrong location.

### What to scan

1. **Prefix-location mismatches** - find files created today (frontmatter `date created` = today) whose prefix doesn't match the routing rules:

   | Prefix | Expected Location Pattern |
   |--------|-------------------------|
   | `DN -` | `01_Notes/Daily/` |
   | `MN -` | `01_Notes/Meetings/` |
   | `WS -` | `01_Notes/Weekly/` |
   | `PIC -` | `01_Notes/Pickups/` or `02_Projects/**/pickups/` |
   | `WL -` | `01_Notes/Work Logs/` |
   | `SPC -` | `02_Projects/**/specs/YYYY-MM-DD/` |
   | `PL -` | `02_Projects/**/plans/YYYY-MM-DD/` |
   | `RE -` | `02_Projects/**/reports/YYYY-MM-DD/` |
   | `ARE -` | `02_Projects/**/reports/YYYY-MM-DD/` or `02_Projects/**/reviews/YYYY-MM-DD/` |
   | `REF -` | `04_Reference/` |
   | `DD -` | `02_Projects/**/designs/YYYY-MM-DD/` |
   | `SO -` | `02_Projects/**/structures/YYYY-MM-DD/` |
   | `RET -` | `02_Projects/**/reports/YYYY-MM-DD/` |
   | `HAN -` | `02_Projects/**/reports/YYYY-MM-DD/` |

2. **Project structure violations** - files in `02_Projects/` that aren't in a dated subfolder when they should be (specs, plans, reports, reviews sitting directly in the type folder without a `YYYY-MM-DD/` subdirectory).

3. **Orphan files** - markdown files at vault root or in unexpected locations (not in `01_Notes/`, `02_Projects/`, `03_Operations/`, `04_Reference/`, `05_System/`).

4. **Missing frontmatter** - files created today without required `date created`, `tags`, or `category` fields.

### How to scan

```bash
# Find all .md files created today (by frontmatter date, not filesystem)
grep -rl "date created: {today}" "{vault_root}/" --include="*.md"
```

Then for each file, check its prefix against the expected location table above.

### Actions

- **Auto-fix obvious cases**: A `DN - 2026-04-04.md` found at vault root can be moved to `01_Notes/Daily/` without asking.
- **Flag ambiguous cases**: A `RE -` file outside any project needs user input on which project it belongs to. Present as a numbered list.
- **Track the source**: For each violation, note what likely created it (check today's daily note for the matching topic). Add a one-line note in the EOD's "What Didn't" section: "Vault hygiene: [file] was created in [wrong location], likely by [skill/action]. Should go in [correct location]."
- **If zero violations**: Skip silently. Don't report "vault is clean" unless the user asks.

### Improving the workflow

When a violation is traced to a specific skill, park a note to that skill's project CLAUDE.md:
```
- **Routing bug**: [skill name] created [file] in [wrong location] on [date]. Expected location: [correct path]. Fix the skill's file creation logic.
```

This creates a feedback loop: vault scan finds violations, parks bugs, future agents fix the skills.

## Step 7: Dream (memory consolidation)

After all reports are written, run `/dream` to consolidate automemory. This is the natural end-of-day moment for memory hygiene -- the day's work is captured in reports, and any new memories from the session should be merged, deduplicated, and pruned before the next day starts.

Invoke the dream skill directly. No user confirmation needed -- it runs automatically as the final step of end-day.

## Constraints
- Always produce EOD. EOW and EOM are conditional on the day.
- Always run `/dream` as the final step -- no exceptions.
- Goal discovery is the key differentiator -- don't skip it even on light days.
- Don't duplicate closeout's work -- closeout writes to the daily note and creates PICs. End-day reads what closeout wrote and synthesizes.
- If no closeouts happened today (daily note Worked on is empty), produce a minimal EOD noting it was a light/off day.
- Confirmed goals persist across EODs until completed or explicitly dropped.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
