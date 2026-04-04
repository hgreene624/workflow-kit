---
date created: 2026-04-04
tags: [reference, workflow-kit, update, sync]
category: Reference
---

# REF - Updating the Workflow Kit

How to pull WFK updates without losing your customizations. This doc is for agents running `/update-wfk pull` and for users who want to understand what the update process does and does not touch.

## Quick Version

Run `/update-wfk` (or `/update-wfk pull`). The skill will:
- Update skills with new versions from the repo
- Show diffs for templates and let you choose
- Merge CLAUDE.md and agents.md by section markers (your content stays)
- Back up everything before modifying

Your daily notes, project files, lessons, evals, and local customizations are never touched.

## What Gets Updated

| Component | What Changes | What's Preserved |
|-----------|-------------|-----------------|
| Skills | `SKILL.md` and `references/` replaced with latest | Your `evals/`, `*-workspace/`, and any custom files you added |
| Templates | Nothing automatic. Diff shown, you choose. | Everything until you explicitly accept an upstream change |
| CLAUDE.md | `WFK:START/END` blocks replaced | `LOCAL:START/END` blocks and any unmarked content |
| agents.md | `WFK:START/END` blocks replaced | `LOCAL:START/END` blocks and any unmarked content |
| Obsidian | `community-plugins.json` only | All other Obsidian config, workspace, snippets, plugin data |

## What's Never Touched

These paths are excluded from all sync operations:

- `01_Notes/` - your daily notes, meetings, pickups, work logs
- `02_Projects/*/agents.md` - project-level agent context
- `02_Projects/*/lessons.md` - project-level lessons
- `03_Operations/` - your domain-specific content
- `06_Media/` - transcripts, podcasts
- `**/data.nosync/` - local data files
- `.obsidian/workspace*.json` - your window layout
- `.obsidian/snippets/` - your CSS snippets
- `.obsidian/plugins/*/data.json` - your plugin settings

## How Section Markers Work

CLAUDE.md and agents.md use HTML comment markers to separate WFK-managed content from your local additions.

**WFK blocks** (updated on pull):
```markdown
<!-- WFK:START - Section Name -->
Content managed by WFK. This gets replaced on update.
<!-- WFK:END -->
```

**Local blocks** (never touched):
```markdown
<!-- LOCAL:START - Your Section -->
Your custom rules, preferences, and additions.
<!-- LOCAL:END -->
```

**Unmarked content** (never touched):
Any text outside of both WFK and LOCAL markers is preserved as-is.

### Adding Your Own Rules

To add vault-specific rules that survive updates, put them inside a LOCAL block. The agents.md file already has one at the bottom:

```markdown
<!-- LOCAL:START - Add your vault-specific agent rules below this line -->
Your rules here.
<!-- LOCAL:END -->
```

You can add LOCAL blocks anywhere in the file. WFK will never modify them.

### What If I Edited a WFK Block?

If you modified text inside a `WFK:START/END` block, the next update will overwrite your changes. To keep a modified rule:

1. Move it into a LOCAL block
2. Delete it from the WFK block (or leave it, it'll be overwritten anyway)

The pull process shows a diff before applying, so you'll see what's changing.

## How Skill Updates Work

Skills live in `~/.claude/skills/`. Each skill directory can contain:

```
skills/<name>/
  SKILL.md          <- replaced on update
  references/       <- replaced on update
  evals/            <- YOUR data, never touched
  *-workspace/      <- YOUR data, never touched
  (any other files) <- YOUR data, never touched
```

The update replaces `SKILL.md` and the entire `references/` directory. Everything else is yours.

### New Skills

When the kit adds a new skill, the update offers to install it. You choose yes or no per skill.

### Deprecated Skills

When a skill is deprecated (listed in `deprecated_skills` in kit.json), the update:
1. Backs up the skill directory
2. Deletes it
3. Tells you it was removed and why

## The Sync Manifest

The file `~/.claude/skills/.sync-manifest.json` tracks content hashes for every synced file. This is how the system knows whether you changed something locally, the repo changed upstream, or both.

| Your Copy | Repo Copy | Status | Action |
|-----------|-----------|--------|--------|
| Same as last sync | Same as last sync | Synced | Nothing to do |
| Changed since last sync | Same as last sync | Local ahead | Your changes are kept. Repo hasn't changed. |
| Same as last sync | Changed since last sync | Remote ahead | Safe to update. Your copy hasn't changed. |
| Changed since last sync | Changed since last sync | Conflict | Diff shown. You choose which version to keep. |

## Pre-Update Backups

Every update creates a timestamped backup at:
```
~/.claude/skills/.backup/YYYY-MM-DDTHH-MM-SS/
```

The system keeps the 3 most recent backups and deletes older ones. If an update breaks something, you can restore from the backup.

## The Kit Manifest (kit.json)

The file `kit.json` at the repo root controls everything:

```json
{
  "core_skills": ["orient", "closeout", ...],
  "org_skills": ["limitless", "vps-deploy"],
  "deprecated_skills": ["yt", "pickup-triage"],
  "sync_rules": { ... },
  "never_sync": [ ... ]
}
```

- **core_skills** - skills that ship with the kit. Updated on pull.
- **org_skills** - org-specific skills. Listed for reference but not synced to users.
- **deprecated_skills** - old skills removed on pull.
- **sync_rules** - per-component merge behavior.
- **never_sync** - glob patterns for files that are always excluded.

## Troubleshooting

**"I accidentally accepted an update that broke my CLAUDE.md"**
Restore from backup: `cp ~/.claude/skills/.backup/<latest>/CLAUDE.md ~/Documents/Vaults/CLAUDE.md`

**"I want to skip a specific skill update"**
When the update shows the diff, choose "Keep yours" for that skill.

**"I added a file to a skill directory and it disappeared"**
Files inside `references/` are replaced on update. Move custom reference files outside `references/` (e.g., `my-notes/`) to preserve them.

**"The update says 'Conflict' on everything"**
Your sync manifest may be stale. Run `/update-wfk status` to see the full state, then `/update-wfk pull` and resolve conflicts one by one.
