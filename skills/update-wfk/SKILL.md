---
name: update-wfk
description: >-
  Sync core Workflow Kit skills and conventions to/from the public GitHub repo.
  The distribution channel for the WFK. Use this skill when the user says
  "update wfk", "update kit", "sync kit", "push skills", "pull skills",
  "update-wfk", "update-skills", "update-workflow-kit", or wants to push
  improvements to the WFK repo or pull the latest kit updates. This skill
  replaces the old /update-skills and /update-workflow-kit commands.
---

# Update WFK — Kit Distribution Sync

Sync core Workflow Kit skills, templates, and conventions with the `YOUR_USERNAME/workflow-kit` GitHub repo. This is the distribution channel - you push improvements, users pull updates.

**Arguments:** $ARGUMENTS

## Kit Manifest

The repo contains a `kit.json` manifest that governs all sync behavior. **Read it before every push or pull.**

```bash
cat /tmp/flora-skills-repo/kit.json
```

The manifest declares:
- `version` - current kit version (used for changelog display)
- `core_skills` - skills that ship with the kit (pushed to/pulled from repo)
- `org_skills` - organization-specific skills (never pushed to repo)
- `deprecated_skills` - old skills to remove from user machines on pull
- `renamed_skills` - old name -> new name mappings with migration context
- `deprecation_context` - human-readable explanation of what replaced each deprecated skill
- `sync_rules` - per-category merge behavior
- `never_sync` - patterns that are always excluded

## What Gets Synced

| Component | Repo Path | Local Source | Push Behavior | Pull Behavior |
|-----------|-----------|--------------|---------------|---------------|
| Core skills | `skills/` | `~/.claude/skills/` | Only `core_skills` from kit.json | Replace SKILL.md + references/ |
| Templates | `05_System/Templates/` | Work Vault `05_System/Templates/` | Push generalized versions | Show diff, user chooses |
| CLAUDE.md | `CLAUDE.md` | Work Vault `CLAUDE.md` | **Never overwrite repo version** | Section-marker merge |
| agents.md | `agents.md` | Work Vault `agents.md` | **Never overwrite repo version** | Section-marker merge |
| Obsidian config | `.obsidian/` | Work Vault `.obsidian/` | Only `community-plugins.json` | Same |
| Vault structure | `01_Notes/` through `04_Reference/` | - | Never (scaffold only) | First-run only |
| Getting Started | `Getting Started.md`, `SETUP.md`, `README.md` | Repo only | Repo-only edits | Not pulled to vault |

## Configuration

- **Repo:** `YOUR_USERNAME/workflow-kit`
- **Branch:** `main`
- **Clone cache:** `/tmp/flora-skills-repo`
- **Active skills:** `~/.claude/skills/`
- **Sync manifest:** `~/.claude/skills/.sync-manifest.json`

## Architecture

```
~/.claude/skills/ (active skills)
        |
   push v  ^ pull
        |
/tmp/flora-skills-repo/      <- Scratch clone for git operations
        |
   push v  ^ fetch
        |
github.com/YOUR_USERNAME/workflow-kit
```

## Default Action Detection

When called with no arguments, read `wfk_role` from the vault's `agents.md`:
- `wfk_role: developer` -> default to **push**
- `wfk_role: user` (or not set) -> default to **pull**

## Sync State Tracking

The sync manifest at `~/.claude/skills/.sync-manifest.json` tracks content hashes and version:

```json
{
  "version": "1.0.0",
  "skills": { "orient": "a1b2c3...", "closeout": "d4e5f6..." },
  "vault_files": { "CLAUDE.md": "1a2b3c..." },
  "last_sync": "2026-04-01T18:30:00Z"
}
```

The `version` field records which kit version the user last pulled. On pull, compare this against `kit.json.version` to determine if an update is available and which changelog entries to show.

**Direction logic:**
| active vs synced | remote vs synced | Status |
|---|---|---|
| Same | Same | **Synced** |
| Different | Same | **Local ahead** (user edited) |
| Same | Different | **Remote ahead** (upstream updated) |
| Different | Different | **Conflict** (both changed) |

## Actions

### `push` - Push local changes to the WFK repo

#### Step 1: Setup

Clone or pull the latest repo:
```bash
if [ -d /tmp/flora-skills-repo/.git ]; then
  cd /tmp/flora-skills-repo && git pull --quiet
else
  rm -rf /tmp/flora-skills-repo
  git clone https://github.com/YOUR_USERNAME/workflow-kit.git /tmp/flora-skills-repo
fi
```

Read the kit manifest and sync manifest:
```bash
cat /tmp/flora-skills-repo/kit.json
cat ~/.claude/skills/.sync-manifest.json 2>/dev/null
```

#### Step 2: Diff analysis

For each local skill, classify it into one of five categories:

**2a. Inventory local skills:**
```bash
# List all local skills (excluding workspaces)
ls -d ~/.claude/skills/*/ | grep -v workspace
```

**2b. Classify each skill:**

| Local skill | In core_skills? | In org_skills? | Category |
|---|---|---|---|
| exists locally, in core_skills | yes | - | **SYNC CANDIDATE** |
| exists locally, in org_skills | - | yes | **ORG (skip)** |
| exists locally, in neither | no | no | **NEW (needs categorization)** |
| in core_skills, missing locally | - | - | **REMOVED (flag)** |

**For NEW skills:** Ask the user one at a time via AskUserQuestion:
> "Local skill `<name>` is not in kit.json. How should it be categorized?"
> Options: `["Add to core_skills (ships with WFK)", "Add to org_skills (stays local)", "Skip for now"]`

If added to core_skills, update kit.json before proceeding.

**2c. For each SYNC CANDIDATE, classify the change tier:**

Compare the local SKILL.md against the repo SKILL.md. If they're identical (or differ only by scrub-map values), the skill is unchanged. If they differ, classify the diff:

**Tier 1 - Auto (scrub-only):** The diff consists entirely of values that appear in the scrub map (domain names, paths, usernames). After scrub-map replacement, local and repo would be identical. These can be copied and scrubbed without review.

**Tier 2 - Review (structural additions):** The diff adds new sections, steps, or rules that are written in generic language. After scrub-map replacement, the content reads correctly for any user. Copy, scrub, and show the diff for confirmation.

**Tier 3 - Rewrite (org-specific logic):** The diff contains org-specific implementations that the scrub map can't fix. Detect by checking whether the post-scrub diff still contains:
- Specific service or container names not in the scrub map
- SSH commands to specific hosts
- SQL queries against specific database schemas
- Hardcoded port numbers, endpoint paths, or service counts
- References to org-specific tools or infrastructure (deploy scripts, CI workflows, PM tools)

These require the agent to understand the concept the local version implements and rewrite it as a generic framework. **Do not blind-copy these.** Instead:
1. Read both versions (local and repo)
2. Identify the generalizable concept (e.g., "audit container drift" → "check deployment targets for staleness")
3. Write a generalized version to the repo that preserves the concept but removes the org-specific implementation
4. Show the result to the user for confirmation

Present the classification to the user:
```
Push analysis:
  Unchanged:     12 skills
  Tier 1 (auto): 8 skills (scrub-map only)
  Tier 2 (review): 3 skills (structural additions)
  Tier 3 (rewrite): 2 skills (org-specific logic needs generalization)
  New skills:     1 (categorized as core)
  Org (skipped):  4 skills
```

#### Step 3: Sync skills

Process in tier order:

**Tier 1 (auto):** Copy local skill directories to repo, replacing existing. No user interaction needed.

**Tier 2 (review):** Copy local skill directories to repo. Show a concise summary of what changed in each (added sections, new steps, modified rules). Ask: "These additions look generic. Confirm, or flag any for closer review?"

**Tier 3 (rewrite):** For each skill, read both versions side by side. Draft a generalized version that:
- Keeps the concept and behavioral improvement
- Replaces org-specific implementations with environment-adaptive logic
- Uses generic examples and placeholder patterns
- Lets users customize via LOCAL.md

Show the drafted version to the user. Ask: "This is the generalized version of [skill]. Look right?" Iterate if needed.

**New skills:** Copy the local skill directory, then apply Tier classification (most new skills will be Tier 2 or 3).

#### Step 4: Sync non-skill components

**Templates:**
```bash
cp <VAULT_ROOT>/05_System/Templates/*.md /tmp/flora-skills-repo/05_System/Templates/
```

**CLAUDE.md and agents.md - NEVER OVERWRITE:**
The repo has its own generalized versions with `<!-- WFK:START -->` / `<!-- WFK:END -->` section markers. Do NOT copy the vault versions over the repo versions.

If a structural change needs to go upstream:
1. Read the repo version
2. Read the vault version
3. Identify what changed that should apply generically
4. Edit the repo version (without org-specific content)
5. Preserve all section markers

**Obsidian config** (selective):
```bash
cp <VAULT_ROOT>/.obsidian/community-plugins.json /tmp/flora-skills-repo/.obsidian/community-plugins.json
```

#### Step 5: Scrub org-specific content

Read the scrub map at `~/.claude/skills/update-wfk/scrub-map.json`. Apply all replacements (longest match first) to every synced file. Also verify no `flora_only_skills` from the scrub map exist in the repo's `skills/` directory.

#### Step 6: Validate - no secrets or org content remaining

**6a. Scrub-map pattern scan:**
```bash
cd /tmp/flora-skills-repo
grep -r "$(jq -r '[.replacements[].pattern] | join("\\|")' ~/.claude/skills/update-wfk/scrub-map.json)" \
  --include="*.md" --include="*.py" --include="*.sh" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.toml" \
  | grep -v ".git/"
```

**6b. Structural org-content scan:**
After scrubbing, check for org-specific patterns that aren't string-replaceable:
- Hardcoded service lists or container maps (arrays of 5+ specific names)
- SSH commands to specific hosts
- SQL queries with specific table/schema names
- Specific CI/CD workflow references
- Specific deploy tool invocations

If any hits are found, the skill was miscategorized as Tier 1/2 when it's actually Tier 3. Go back and rewrite it.

**6c. Gitleaks** (if installed):
```bash
gitleaks detect --source /tmp/flora-skills-repo --no-git --config /tmp/flora-skills-repo/.gitleaks.toml
```

**Only proceed if all three scans are clean.**

#### Step 7: Update kit.json

Check whether kit.json needs updates:
- **Version bump:** If any Tier 2 or Tier 3 changes exist, bump the version. Patch for Tier 2 only, minor for Tier 3 or new skills, major for breaking changes (renames, removed skills, mandatory new behavior).
- **New core skills:** Add any skills categorized as core in Step 2.
- **Renamed skills:** If a deprecated skill has a replacement, add to `renamed_skills` with migration context.
- **Deprecation context:** Ensure every entry in `deprecated_skills` has a matching entry in `deprecation_context`.

#### Step 8: Generate changelog entry

Read the existing `CHANGELOG.md`. Draft a new version entry based on what actually changed:

**For each new skill:** Write a 2-3 sentence description of what it does and why.

**For each improved skill (Tier 2/3):** Write a paragraph describing what got better from the user's perspective. Focus on the problem it solves, not the implementation. No line counts.

**For renames/deprecations:** List them with migration instructions.

**For breaking changes:** List what the user needs to do differently.

**Structure:**
```markdown
## v{version} - {date}

### What this release is about
{2-3 sentences: what problems were addressed}

### New skills
{if any}

### What got better
{per-skill paragraphs, user-facing language}

### What you need to do
{breaking changes, migration steps}

### Migration
{what update-wfk pull will do automatically}
```

Show the draft to the user. This is the most important artifact - it's what users read. Iterate until the user approves.

#### Step 8b: Update README.md

Read the repo's `README.md`. Check whether it needs updates based on this push:

1. **Key Commands table** - does it list all core skills the user should know about? If new skills were added that a user would invoke directly (not internal-only skills), add them to the table.
2. **Skill descriptions** - if a skill's behavior changed significantly (Tier 3 rewrite), check whether the README's description is still accurate.
3. **Getting Started section** - if the install process or setup steps changed, update them.
4. **Any section referencing specific skill names** - if a skill was renamed, update the reference.

Don't bloat the README. It's an introduction, not documentation. Only add skills to the Key Commands table if they're user-invocable entry points (like `/create-spec`, `/pickup`, `/closeout`). Internal skills (like `/git-safe`) don't need a README mention.

Show any README changes to the user for confirmation before proceeding.

#### Step 9: Show what changed

```bash
cd /tmp/flora-skills-repo && git diff --stat
git status --short
```

Present a summary grouped by:
- New files (untracked)
- Modified skills (with tier labels)
- Kit.json changes
- Changelog

#### Step 10: Confirm and push

Ask the user to confirm. Show: changed file count, new skill count, version bump, changelog summary.

```bash
cd /tmp/flora-skills-repo
git add -A
git commit -m "WFK v{version}: {one-line summary}"
git push origin main
```

#### Step 11: Update sync manifest

Write the new manifest with current hashes for all synced skills and the new version number. Report what was pushed and skipped.

### `pull` - Pull latest from the WFK repo

#### Step 1: Clone or pull the latest repo

```bash
if [ -d /tmp/flora-skills-repo/.git ]; then
  cd /tmp/flora-skills-repo && git pull --quiet
else
  rm -rf /tmp/flora-skills-repo
  git clone https://github.com/YOUR_USERNAME/workflow-kit.git /tmp/flora-skills-repo
fi
```

#### Step 2: Read kit.json and sync manifest

```bash
cat /tmp/flora-skills-repo/kit.json
cat ~/.claude/skills/.sync-manifest.json 2>/dev/null || echo '{"version":"0.0.0","skills":{}}'
```

Compare `kit.json.version` against `manifest.version`. If they differ, an update is available.

#### Step 3: Show what's new (changelog)

Read `CHANGELOG.md` from the repo. Find all version entries newer than the user's `manifest.version`. Present a summary:

```
WFK update available: v1.0.0 -> v2.0.0

What's new:
- 3 new skills: create-plan, document-change, explain
- 8 improved skills: closeout, end-day, create-spec, log-work, implement, create-pickup, pickup, pipeline-qa
- 1 renamed skill: plan-spec -> create-plan
- 5 deprecated skills removed

See full changelog? (y/n)
```

If the user wants the full changelog, show the relevant entries. Then ask: "Proceed with update?"

If no version change (hashes differ but same version), skip the changelog and go to Step 4.

#### Step 4: Pre-update backup

```bash
BACKUP_DIR=~/.claude/skills/.backup/$(date +%Y-%m-%dT%H-%M-%S)
mkdir -p "$BACKUP_DIR"
```

Back up every file that will be modified. Keep last 3 backups, delete older ones:
```bash
ls -dt ~/.claude/skills/.backup/*/ 2>/dev/null | tail -n +4 | xargs rm -rf
```

#### Step 5: Handle deprecated skills

Read `deprecated_skills` and `deprecation_context` from kit.json. For each deprecated skill that exists locally:

1. Back it up to `$BACKUP_DIR/<skill-name>/`
2. Check if the skill has a `LOCAL.md` - if so, preserve it separately
3. Delete the skill directory
4. Tell the user with context: "Removed `plan-spec` - replaced by `create-plan` (adaptive depth, no external PM dependency)"

The `deprecation_context` field provides the human-readable explanation. Never just silently delete.

#### Step 6: Handle renamed skills

Read `renamed_skills` from kit.json. For each rename where the OLD name exists locally:

1. Check if user has a `LOCAL.md` in the old skill directory
2. If so, copy it to the new skill directory (it will be picked up after the new SKILL.md is installed)
3. Back up and delete the old skill directory
4. Report: "Renamed `plan-spec` -> `create-plan`. Your LOCAL.md was preserved."

#### Step 7: Sync skills (with user-edit preservation)

This is the core of the pull. For each skill in the repo's `skills/` directory:

**7a. Classify the skill's local state:**

```bash
# For each skill:
LOCAL_SKILL="$HOME/.claude/skills/<name>/SKILL.md"
REPO_SKILL="/tmp/flora-skills-repo/skills/<name>/SKILL.md"
MANIFEST_HASH=$(jq -r '.skills["<name>"] // empty' ~/.claude/skills/.sync-manifest.json)
```

Compute hashes:
```bash
LOCAL_HASH=$(md5 -q "$LOCAL_SKILL" 2>/dev/null || echo "missing")
REPO_HASH=$(md5 -q "$REPO_SKILL" 2>/dev/null || echo "missing")
```

Classify into one of five states:

| Local exists? | Manifest hash? | Local = Manifest? | Local = Repo? | State |
|---|---|---|---|---|
| No | - | - | - | **NEW** - skill not installed locally |
| Yes | None | - | Same | **SYNCED** - first sync established this |
| Yes | Yes | Yes | Same | **SYNCED** - no changes anywhere |
| Yes | Yes | Yes | Different | **UPSTREAM** - repo updated, user didn't edit |
| Yes | Yes | No | Same | **LOCAL EDIT** - user edited, repo unchanged |
| Yes | Yes | No | Different | **CONFLICT** - both sides changed |
| Yes | None | - | Different | **CONFLICT** - no baseline, can't determine who changed what |

**MANDATORY PRE-REPLACE GATE — agents MUST NOT skip this:**

Before replacing ANY local SKILL.md with a repo version, hash both files and compare. If they differ, check whether a manifest entry exists:
- Manifest entry exists and local matches it → safe to replace (UPSTREAM)
- Manifest entry exists and local differs from it → CONFLICT (both changed)
- **No manifest entry and local differs from repo → CONFLICT.** Do NOT treat this as UPSTREAM. The manifest is an optimization for detecting *who* changed what — its absence does not mean the user didn't edit the file. When in doubt, ask.

This gate exists because agents historically took the fast path (silent replace) when the manifest was absent, silently overwriting user edits. That is the failure mode this gate prevents.

**7b. Handle each state:**

**NEW:** Ask user via AskUserQuestion:
> "New skill available: `<name>` - <description from SKILL.md frontmatter>. Install it?"

Options: `["Install", "Skip"]`. If Install, copy the skill directory.

**SYNCED:** Nothing to do. Skip silently.

**UPSTREAM (repo updated, user did not edit):** Replace `SKILL.md` and `references/` directory. Never touch `evals/`, `*-workspace/`, `LOCAL.md`, or other user-added files in the skill directory.

Before replacing, show a 1-line diff summary (e.g., "+42 lines: environment verification, PJL gates, DN style rules"). If the local SKILL.md has ANY differences from the repo version — even if the manifest classifies this as UPSTREAM — offer via AskUserQuestion:

> "Updating `<skill>` — want me to save your current version to LOCAL.md first?"

Options: `["Update (no backup needed)", "Save to LOCAL.md first, then update"]`

If "Save to LOCAL.md first": extract the full local SKILL.md content to `LOCAL.md` with a dated header, then replace SKILL.md with the repo version. If LOCAL.md already exists, append under a dated section.

Batch this prompt for efficiency: group all UPSTREAM skills into one question listing the skills and their change summaries, with a single yes/no for "save any to LOCAL.md first?" Then ask which specific ones to save only if they say yes.

**LOCAL EDIT (user edited, repo unchanged):** Nothing to do - user's version is ahead and repo hasn't changed. Skip silently. Note: the sync manifest hash will be updated at the end to reflect the user's current version, so next pull won't re-flag this.

**CONFLICT (both sides changed) - THE CRITICAL PATH:**

This is where user-edit preservation matters. Handle one skill at a time:

1. **Show what changed on both sides.** Diff the user's SKILL.md against the manifest hash (user's changes) and diff the repo SKILL.md against the manifest hash (upstream changes). Present a concise summary:

   ```
   Skill: closeout
   Upstream changes: +131 lines (environment verification, infra documentation gate, deploy audit)
   Your local edits: +12 lines (added custom step for Slack notification after closeout)
   ```

2. **Ask the user via AskUserQuestion** (one skill at a time):

   > "`closeout` has upstream updates AND your local edits. How do you want to handle it?"

   Options: `["Clean install (my edits go to LOCAL.md)", "Clean install (discard my edits)", "Skip (keep my version)"]`

3. **If "Clean install (my edits go to LOCAL.md)":**
   - Extract the user's edits by diffing their SKILL.md against the last-synced version
   - Write them to `~/.claude/skills/<name>/LOCAL.md` with a header:

     ```markdown
     # Local Customizations for <skill-name>

     These overrides were extracted from your edited SKILL.md during WFK update
     on YYYY-MM-DD. They are loaded after the upstream SKILL.md and take precedence
     where they conflict.

     Review these and remove any that are no longer needed.

     ---

     <extracted user additions/changes>
     ```

   - If a `LOCAL.md` already exists, append the new extractions under a dated section header rather than overwriting.
   - Install the upstream SKILL.md and references/ cleanly.

4. **If "Clean install (discard my edits)":**
   - Install the upstream SKILL.md and references/ cleanly.
   - Do NOT create or modify LOCAL.md.

5. **If "Skip":**
   - Leave the skill as-is. Do not update the manifest hash for this skill.

**IMPORTANT:** Process skills one at a time through AskUserQuestion. Do NOT batch them. The user needs to make an informed decision per skill. However, you MAY group SYNCED and UPSTREAM skills into a single summary line ("12 skills updated cleanly, 0 conflicts") since those don't need user decisions.

#### Step 8: Templates

Diff each template file. For each that differs:
- Show a concise summary of what changed
- Ask: "Keep yours / Take upstream / Show full diff"
- **Never silently overwrite.**

#### Step 9: CLAUDE.md section-marker merge

- Replace `<!-- WFK:START -->` / `<!-- WFK:END -->` blocks with repo content
- Preserve `<!-- LOCAL:START -->` / `<!-- LOCAL:END -->` blocks untouched
- Preserve any content outside both marker types
- Show the merged result and ask user to confirm before writing

#### Step 10: agents.md

Same section-marker merge as CLAUDE.md. Never touch project-level agents.md files (only the vault root agents.md).

#### Step 11: Obsidian config

Copy `community-plugins.json` only:
```bash
cp /tmp/flora-skills-repo/.obsidian/community-plugins.json <VAULT_ROOT>/.obsidian/community-plugins.json
```

#### Step 12: Scripts

Copy all scripts from repo `scripts/` to `~/.claude/scripts/`, `chmod +x` each:
```bash
mkdir -p ~/.claude/scripts
cp /tmp/flora-skills-repo/scripts/* ~/.claude/scripts/ 2>/dev/null
chmod +x ~/.claude/scripts/*.sh 2>/dev/null
```

#### Step 13: Post-pull setup hooks

Detect the environment and run setup scripts. **This is mandatory, not optional.**
```bash
# iTerm2 auto-setup (macOS only)
if mdfind "kMDItemKind == 'Application'" 2>/dev/null | grep -qi "iTerm.app"; then
  ~/.claude/scripts/iterm-setup.sh
fi
```
Report any manual steps the setup script identifies. If the script fails, diagnose and fix before continuing.

#### Step 14: Post-pull validation

After all files are synced, verify consistency:

1. **Reference check** - scan all installed SKILL.md files for references to deprecated or renamed skills:
   ```bash
   # Check for references to old skill names
   for old_name in $(jq -r '.renamed_skills | keys[]' /tmp/flora-skills-repo/kit.json 2>/dev/null); do
     grep -rl "/$old_name" ~/.claude/skills/*/SKILL.md 2>/dev/null
   done
   ```
   If stale references are found, offer to update them (e.g., `/plan-spec` -> `/create-plan`).

2. **CLAUDE.md reference check** - verify that skill names referenced in CLAUDE.md exist as installed skills.

3. **LOCAL.md audit** - list all LOCAL.md files and their age. Flag any older than 90 days as potentially stale.

4. **Path config validation** - check `~/.claude/wfk-paths.json`:
   - **If missing:** warn the user: "No wfk-paths.json found. Skills will use hardcoded default paths. Run `/setup` or create `~/.claude/wfk-paths.json` manually." Show the expected format.
   - **If present:** validate each path exists as a directory under `vault_root`. Report any stale paths and offer to fix them.
   - **Check for new path keys:** scan all pulled SKILL.md files for `{paths.<key>}` references. If any key is referenced in a skill but missing from the config, warn: "Skill `<name>` references `paths.<key>` which is not in your wfk-paths.json. Add it?" Offer to add the default value.
   - Update `last_validated` to today's date after a successful check.

#### Step 15: Update sync manifest

Write the new manifest with current hashes for all synced skills:

```bash
# Build manifest with version + hashes for every installed core skill
```

```json
{
  "version": "<kit.json version>",
  "skills": { "<name>": "<md5 of installed SKILL.md>", ... },
  "vault_files": { "CLAUDE.md": "<hash>", "agents.md": "<hash>" },
  "last_sync": "<ISO timestamp>"
}
```

**IMPORTANT:** For skills the user chose to "Skip" in Step 7, do NOT update their hash. Their hash should remain as the previous manifest value so the next pull correctly detects them as conflicts again.

#### Step 16: Report

Present a final summary:

```
WFK updated to v2.0.0

Updated:      12 skills (clean install)
Preserved:     2 skills (edits saved to LOCAL.md)
Skipped:       1 skill (user chose to keep local version)
New:           3 skills installed (create-plan, document-change, explain)
Deprecated:    1 skill removed (plan-spec -> create-plan)
Templates:     2 updated
CLAUDE.md:     merged (WFK sections updated, LOCAL sections preserved)
Scripts:       3 copied

LOCAL.md files created:
  - ~/.claude/skills/closeout/LOCAL.md (your Slack notification step)
  - ~/.claude/skills/log-work/LOCAL.md (your custom group names)

Backup at: ~/.claude/skills/.backup/2026-04-11T09-30-00/
```

### `contribute` - Submit changes upstream via PR

Use this when the user has local skill edits they want to contribute back to the WFK repo.

#### Step 1: Identify changes

Compare local skills against the repo. Show which skills have local edits that aren't in the repo yet. Let the user pick which ones to contribute.

#### Step 2: Fork check

```bash
gh repo view YOUR_USERNAME/workflow-kit --json isFork 2>/dev/null
```

If the user's repo is already the upstream, they can push directly. If not, check for a fork:

```bash
gh repo list --fork --json nameWithOwner,parent --jq '.[] | select(.parent.nameWithOwner == "YOUR_USERNAME/workflow-kit")'
```

If no fork exists, create one:
```bash
gh repo fork YOUR_USERNAME/workflow-kit --clone=false
```

#### Step 3: Push to fork and create PR

```bash
# Create a branch on the fork
FORK_NAME=$(gh api user --jq '.login')
cd /tmp/flora-skills-repo
git remote add fork "https://github.com/$FORK_NAME/workflow-kit.git" 2>/dev/null || true
git checkout -b contribute/$(date +%Y%m%d)-$(echo "$DESCRIPTION" | tr ' ' '-' | head -c 30)
# Copy the changed skill files
# Commit and push to fork
git push fork HEAD
# Create PR using gh (uses OAuth, not fine-grained PAT)
gh pr create --repo YOUR_USERNAME/workflow-kit --head "$FORK_NAME:$(git branch --show-current)" --title "..." --body "..."
```

**Important:** `gh pr create` uses the `gh` OAuth token, which works for cross-owner PRs. Fine-grained PATs cannot create PRs against repos owned by other users, even with Triage/collaborator role. If the user hasn't run `gh auth login`, guide them through it first.

#### Step 4: Report

Show the PR URL and what was submitted. The user can track it from there.

### `status` - Show sync status

Clone/pull repo, compute hashes, show status table for all skills and vault files.

### `list` - Show available skills

Same as status but also shows available (not installed) skills from the repo.

## What NOT to Sync

- User content (daily notes, reports, specs, plans, PICs)
- Obsidian workspace layout
- Plugin runtime data
- Sync manifests
- Skill workspaces / eval artifacts
- data.nosync directories
- Lessons and project agents.md
- CSS snippets

## Safety

- Always show diff/summary before pushing or pulling
- Never push user content
- Never overwrite local changes without confirmation
- Never force-push
- Use full clone (not `--depth 1`) for push operations

## Relationship to /update-workflow

`/update-wfk` distributes the Workflow Kit (public repo, core skills only).
`/update-workflow` backs up your personal vault (private repo, everything).

They are completely independent.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
