# Workflow Kit — First-Run Setup

Run this setup by telling Claude: "Run the setup in SETUP.md"

## Prerequisites

Before running, verify:
- macOS or Windows (check `uname` on Mac, or `$env:OS` on Windows)
- Claude Code CLI installed (`which claude` on Mac, `where claude` on Windows)
- Obsidian installed
- Git installed (`which git` on Mac, `where git` on Windows)

**If a prerequisite is missing, do not just fail.** Guide the user:
- **Git missing:** "Git is not installed. On macOS, run `xcode-select --install`. On Windows, download from https://git-scm.com. Then restart your terminal and run /setup again."
- **Claude Code not in PATH (Windows):** "Claude Code is installed but not in your system PATH. Try closing and reopening your terminal, or search for 'add to PATH' in Windows settings."
- **Obsidian missing:** Warn but continue. "Obsidian is not installed yet. You can install it from https://obsidian.md. Setup will continue, but you'll want Obsidian to browse your vault."

## Step 1 — User Info

Ask the user: **"What's your name?"**

Then scan the machine for role signals (repos, installed tools, existing files) to auto-detect the user's role. The setup skill handles this via its scanner and profile generator — roles are inferred, not picked from a menu. If the scan can't determine a role confidently, ask the user to describe their work in a sentence or two.

## Step 2 — Generate Config

Create `workflow-kit.config.json` in the vault root with:

```json
{
  "user_name": "<name>",
  "role": "<detected or stated role>",
  "vault_root": "<absolute path to this directory>",
  "daily_note_path": "<vault_root>/01_Notes/Daily",
  "meetings_path": "<vault_root>/01_Notes/Meetings",
  "pickups_path": "<vault_root>/01_Notes/Pickups",
  "projects_path": "<vault_root>/02_Projects",
  "operations_path": "<vault_root>/03_Operations",
  "reference_path": "<vault_root>/04_Reference",
  "templates_path": "<vault_root>/05_System/Templates",
  "setup_date": "<today YYYY-MM-DD>",
  "repo_url": "https://github.com/YOUR_USERNAME/workflow-kit"
}
```

## Step 3 — Install Skills

Copy every directory from `skills/` in this repo to `~/.claude/skills/`.

For each skill directory:

**macOS:**
```bash
cp -r skills/<skill-name> ~/.claude/skills/<skill-name>
```

**Windows:**
```cmd
xcopy /E /I "skills\<skill-name>" "%USERPROFILE%\.claude\skills\<skill-name>"
```

If skills are already installed (user ran the manual copy from the README), skip any that already exist and are identical. Report how many skills were installed or updated.

## Step 4 — Generate Onboarding PICs

Create three pickup documents in `01_Notes/Pickups/`:

### PIC - Customize Your Role Profile.md

```yaml
---
date created: <today>
tags: [pickup, onboarding]
category: Pickup
status: open
---
```

Content: Walk the user through refining their role profile. Claude should ask about their responsibilities, deliverables, tools, and team. Then update `agents.md` and `CLAUDE.md` to better match their actual work.

### PIC - Migrate Existing Work.md

```yaml
---
date created: <today>
tags: [pickup, onboarding]
category: Pickup
status: open
---
```

Content: Guide the user through pointing at their existing files and migrating them into the vault. Copy files (never move), add frontmatter, rename with prefixes, create a migration log.

### PIC - Your First Spec.md

```yaml
---
date created: <today>
tags: [pickup, onboarding]
category: Pickup
status: open
---
```

Content: Teach the Spec > Plan > Implement pipeline by having the user create a real spec with `/create-spec`, review it with `/review-spec`, and optionally plan it with `/plan-spec`.

## Step 5 — Summary

Tell the user:
- How many skills were installed
- Where the config file is
- That they should open this directory in Obsidian and click Trust
- That they should run `/pickup` to start working through their onboarding PICs
