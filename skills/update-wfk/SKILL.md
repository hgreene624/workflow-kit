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

Sync core Workflow Kit skills, templates, and conventions with the `hgreene624/workflow-kit` GitHub repo. This is the distribution channel - you push improvements, users pull updates.

**Arguments:** $ARGUMENTS

## Kit Manifest

The repo contains a `kit.json` manifest that governs all sync behavior. **Read it before every push or pull.**

```bash
cat /tmp/flora-skills-repo/kit.json
```

The manifest declares:
- `core_skills` - skills that ship with the kit (pushed to/pulled from repo)
- `org_skills` - organization-specific skills (never pushed to repo)
- `deprecated_skills` - old skills to remove from user machines on pull
- `sync_rules` - per-category merge behavior
- `never_sync` - patterns that are always excluded

## What Gets Synced

| Component | Repo Path | Local Source | Push Behavior | Pull Behavior |
|-----------|-----------|--------------|---------------|---------------|
| Core skills | `skills/` | `~/.claude/skills/` | Only `core_skills` from kit.json | Replace SKILL.md + references/ |
| Scripts | `scripts/` | `~/.claude/scripts/` | Push all scripts | Install + chmod +x |
| Templates | `05_System/Templates/` | Work Vault `05_System/Templates/` | Push generalized versions | Show diff, user chooses |
| CLAUDE.md | `CLAUDE.md` | Work Vault `CLAUDE.md` | **Never overwrite repo version** | Section-marker merge |
| agents.md | `agents.md` | Work Vault `agents.md` | **Never overwrite repo version** | Section-marker merge |
| Obsidian config | `.obsidian/` | Work Vault `.obsidian/` | Only `community-plugins.json` | Same |
| Vault structure | `01_Notes/` through `04_Reference/` | - | Never (scaffold only) | First-run only |
| Getting Started | `Getting Started.md`, `SETUP.md`, `README.md` | Repo only | Repo-only edits | Not pulled to vault |

## Configuration

- **Repo:** `hgreene624/workflow-kit`
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
github.com/hgreene624/workflow-kit
```

## Default Action Detection

When called with no arguments, read `wfk_role` from the vault's `agents.md`:
- `wfk_role: developer` -> default to **push**
- `wfk_role: user` (or not set) -> default to **pull**

## Sync State Tracking

The sync manifest at `~/.claude/skills/.sync-manifest.json` tracks content hashes:

```json
{
  "skills": { "orient": "a1b2c3...", "closeout": "d4e5f6..." },
  "vault_files": { "CLAUDE.md": "1a2b3c..." },
  "last_sync": "2026-04-01T18:30:00Z"
}
```

**Direction logic:**
| active vs synced | remote vs synced | Status |
|---|---|---|
| Same | Same | **Synced** |
| Different | Same | **Local ahead** |
| Same | Different | **Remote ahead** |
| Different | Different | **Conflict** |

## Actions

### `push` - Push local changes to the WFK repo

1. **Clone or pull the latest repo:**
   ```bash
   if [ -d /tmp/flora-skills-repo/.git ]; then
     cd /tmp/flora-skills-repo && git pull --quiet
   else
     rm -rf /tmp/flora-skills-repo
     git clone https://github.com/hgreene624/workflow-kit.git /tmp/flora-skills-repo
   fi
   ```

2. **Read the kit manifest:**
   ```bash
   cat /tmp/flora-skills-repo/kit.json
   ```
   Parse `core_skills` and `org_skills`. Only `core_skills` are eligible for push.

3. **Sync each component:**

   **Skills** (core only):
   ```bash
   # For each skill in core_skills from kit.json:
   # Skip if skill dir doesn't exist locally
   # Skip *-workspace directories
   rm -rf /tmp/flora-skills-repo/skills/<name>
   cp -r ~/.claude/skills/<name> /tmp/flora-skills-repo/skills/<name>
   ```
   **IMPORTANT:** If a local skill is NOT in `core_skills` and NOT in `org_skills`, ask the user to categorize it before pushing.

   **Templates:**
   ```bash
   cp ~/Documents/Vaults/Work\ Vault/05_System/Templates/*.md /tmp/flora-skills-repo/05_System/Templates/
   ```

   **CLAUDE.md and agents.md - NEVER OVERWRITE:**
   The repo has its own generalized versions with `<!-- WFK:START -->` / `<!-- WFK:END -->` section markers. Do NOT copy the vault versions over the repo versions.

   If a structural change needs to go upstream:
   1. Read the repo version
   2. Read the vault version
   3. Identify what changed that should apply generically
   4. Edit the repo version (without org-specific content)
   5. Preserve all section markers

   **Scripts:**
   ```bash
   mkdir -p /tmp/flora-skills-repo/scripts
   cp ~/.claude/scripts/*.sh /tmp/flora-skills-repo/scripts/
   ```

   **Obsidian config** (selective):
   ```bash
   cp ~/Documents/Vaults/Work\ Vault/.obsidian/community-plugins.json /tmp/flora-skills-repo/.obsidian/community-plugins.json
   ```

4. **Show what changed:**
   ```bash
   cd /tmp/flora-skills-repo && git status --short
   ```

5. **Ask the user to confirm.** Show changed files grouped by component. Flag skipped org_skills.

6. **Commit and push:**
   ```bash
   cd /tmp/flora-skills-repo
   git add -A
   git commit -m "Update WFK: <summary>"
   git push origin main
   ```

7. Update sync manifest. Report what was pushed and skipped.

### `pull` - Pull latest from the WFK repo

1. **Clone or pull the latest repo**

2. **Read kit.json**

3. **Pre-update backup:**
   ```bash
   BACKUP_DIR=~/.claude/skills/.backup/$(date +%Y-%m-%dT%H-%M-%S)
   mkdir -p "$BACKUP_DIR"
   ```
   Back up every file that will be modified. Keep last 3 backups, delete older ones.

4. **Clean up deprecated skills** - read `deprecated_skills` from kit.json. For each one that exists locally:
   - Back it up, then delete it
   - Tell the user: "Removed deprecated skill `<name>`."

5. **Skills** - for each skill in repo `skills/`:
   - Local edits (per manifest): show diff, ask user
   - Synced: replace `SKILL.md` and `references/` only. **Never touch** `evals/`, `*-workspace/`, or user-added files
   - New: offer to install

6. **Templates** - diff and ask: "Keep yours / Take upstream / Show full diff". **Never silently overwrite.**

7. **CLAUDE.md - Section-marker merge:**
   - Replace `WFK:START/END` blocks with repo content
   - Preserve `LOCAL:START/END` blocks
   - Preserve unmarked content
   - Show merged result, ask to confirm

8. **agents.md** - same section-marker merge. Never touch project-level agents.md.

9. **Obsidian config** - copy `community-plugins.json` only

10. **Update sync manifest**

11. **Scripts** - copy all scripts from `scripts/` to `~/.claude/scripts/`, `chmod +x` each.

12. **Post-pull setup hooks** - detect the environment and run setup scripts:
    ```bash
    # iTerm2 auto-setup (macOS only)
    if mdfind "kMDItemKind == 'Application'" 2>/dev/null | grep -qi "iTerm.app"; then
      ~/.claude/scripts/iterm-setup.sh
    fi
    ```
    Report any manual steps the setup script identifies.

13. **Update sync manifest**

14. Report what was updated. "Backup at `~/.claude/skills/.backup/<timestamp>/`"

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
