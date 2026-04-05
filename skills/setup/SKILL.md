---
name: setup
description: >-
  First-run setup for the Workflow Kit vault. Scans the user's machine to auto-discover
  their work environment, builds a profile, scaffolds the vault with project folders,
  custom prefixes, and daily note templates. Use this skill when the user says "setup",
  "set up", "configure the vault", "first time setup", "run setup", or when this is a
  fresh clone of the workflow-kit repo with no workflow-kit.config.json.
---

# Workflow Kit — First-Run Setup

Set up a fresh Workflow Kit vault in 6 steps. This should take about 5 minutes.

## Step 1 — Check Prerequisites

Verify silently (don't ask the user):
- `uname` returns Darwin (macOS)
- `which claude` succeeds
- `which git` succeeds
- `/Applications/Obsidian.app` exists (warn if missing but continue)

If Claude Code or git is missing, tell the user what to install and stop.

## Step 2 — Auto-Discovery

Use `AskUserQuestion` to ask: **"What's your name?"**

Then read `references/scanner.md` and follow its instructions.
Store the scan output as `SCAN_RESULT`.

If `SCAN_RESULT.blank_slate` is true:
  Read `references/profile-generator.md` → section "Blank-Slate Interview Fallback" and follow only those instructions.
Else:
  Read `references/profile-generator.md` and follow its instructions.

Store the profile output as `PROFILE`.

Read `references/report-renderer.md` and follow its instructions.
Store the approved profile as `APPROVED_PROFILE`.

If the user rejected the report and chose "start over":
  Read `references/profile-generator.md` → section "Blank-Slate Interview Fallback"
  Re-run `references/report-renderer.md` with the interview-generated profile.

Now execute vault scaffolding:

1. Read `references/scaffolder.md` and follow its instructions (uses `APPROVED_PROFILE`).
2. Read `references/bases-generator.md` and follow its instructions (uses `APPROVED_PROFILE`).
3. If `APPROVED_PROFILE.approved_migrations` is non-empty:
   Read `references/migrator.md` and follow its instructions.

## Step 3 — Generate Config

Detect the vault root (the directory containing this SKILL.md's parent `skills/` folder, or the current working directory if it contains `CLAUDE.md`).

Create `workflow-kit.config.json` in the vault root:

```json
{
  "user_name": "<from APPROVED_PROFILE.user_name>",
  "role": "<from APPROVED_PROFILE.role>",
  "role_secondary": "<from APPROVED_PROFILE.role_secondary, or null>",
  "role_confidence": <from APPROVED_PROFILE.role_confidence>,
  "vault_root": "<absolute path to vault>",
  "setup_date": "<today YYYY-MM-DD>",
  "repo_url": "https://github.com/hgreene624/workflow-kit",
  "profile_ref": "<from APPROVED_PROFILE.profile_report_path>",
  "projects": ["<from APPROVED_PROFILE.approved_projects[].name>"],
  "tools": ["<detected tools from scan>"],
  "custom_prefixes": ["<from APPROVED_PROFILE.approved_prefixes[].code>"]
}
```

## Step 4 — Install Skills

Copy every skill directory from the vault's `skills/` folder to `~/.claude/skills/`:

```bash
for skill_dir in <vault_root>/skills/*/; do
  skill_name=$(basename "$skill_dir")
  cp -r "$skill_dir" ~/.claude/skills/"$skill_name"
done
```

Skip these (user/hardware-specific): `ssh-win`, `dad-eod`, `chawdys`

Count and report: "Installed {N} skills."

## Step 5 — Create Onboarding Pickups

Create files in `<vault_root>/Notes/Pickups/`:

### PIC - Customize Your Role Profile.md

Always create this PIC.

```markdown
---
date created: <today>
tags: [pickup, onboarding]
category: Pickup
status: open
priority: 1
---

# Customize Your Role Profile

Your vault was set up with the **<APPROVED_PROFILE.role>** role (confidence: <APPROVED_PROFILE.role_confidence>). The auto-discovery system built your initial profile from what it found on your machine. Let's refine it to match how you actually work.

Your discovery report is saved at: [[<APPROVED_PROFILE.profile_report_path>]]

## What to Do

Tell Claude: "Let's customize my role profile."

Claude will ask you about:
- **Your responsibilities** — What do you own? What do you deliver?
- **Your tools** — What software, services, and systems do you use daily?
- **Your team** — Who do you work with? Who do you report to?
- **Your preferences** — How do you like information presented? Detailed or concise? Tables or prose?

Based on your answers, Claude updates the vault's agent configuration so future sessions are tailored to you.

## When You're Done

This pickup closes automatically when your profile is saved. You'll notice Claude adapts its communication style and suggestions going forward.

**Next:** Work through "PIC - Migrate Existing Work" (if created) or jump straight to "PIC - Your First Spec."
```

### PIC - Migrate Existing Work.md

**Only create this PIC if** migration was deferred by the user (they rejected the migration section during discovery report approval, but files were available to migrate). Skip if:
- `APPROVED_PROFILE.approved_migrations` was non-empty AND migration ran during Step 2
- No files were available to migrate (nothing in `PROFILE.proposed_migrations`)

```markdown
---
date created: <today>
tags: [pickup, onboarding]
category: Pickup
status: open
priority: 2
---

# Migrate Existing Work

If you have existing files — documents, notes, spreadsheets, project files — you can bring them into the vault.

## What to Do

Tell Claude: "I want to bring in some existing files" or run `/intake`.

Point Claude at a folder or specific files. It will:
1. **Copy** files into the right vault location (never moves originals)
2. **Add frontmatter** (metadata) so Obsidian can track them
3. **Rename** with the appropriate prefix (SPC, RE, REF, etc.)
4. **Log** what was migrated

## Tips

- Start small — bring in one project's files, see how it feels
- Claude will ask where things belong if it's not obvious
- Your originals are never touched — everything is copied

## Skip This If

You're starting fresh with no existing files. Just close this pickup and move to "Your First Spec."
```

### PIC - Your First Spec.md

Always create this PIC. If `APPROVED_PROFILE.approved_projects` is non-empty, reference the first project as a suggested spec target.

```markdown
---
date created: <today>
tags: [pickup, onboarding]
category: Pickup
status: open
priority: 3
---

# Your First Spec

This is where the system clicks. You're going to describe something you actually want to do, and Claude will help you plan it out.

## What to Do

1. **Think of something you need to do.** A project, a process improvement, a document to write, a feature to build — anything structured. <If projects were discovered: "Your vault already has a **<first project name>** project folder — you could start there.">

2. **Tell Claude:** "I want to create a spec for..." or run `/create-spec`

3. **Answer Claude's questions.** It will interview you about what you're trying to accomplish, who it's for, what success looks like, and what could go wrong. This usually takes 5-10 minutes.

4. **Review the spec.** Claude produces a structured document with requirements, acceptance criteria, and open questions. Read it — does it capture what you had in mind?

5. **(Optional) Run the review.** Tell Claude `/review-spec` and it dispatches a 3-agent team to check the spec for gaps and risks. This is powerful for complex work but optional for simple tasks.

6. **(Optional) Create the plan.** Tell Claude `/plan-spec` and it breaks the spec into phases with tasks and milestones.

## Why This Matters

The Spec > Plan pipeline is the core of this system. Once you've done it once, you'll use it for everything — and Claude remembers the context across sessions.
```

## Step 6 — Report Success

Tell the user:

```
Setup complete!

- Profile: <APPROVED_PROFILE.role> (<APPROVED_PROFILE.role_confidence * 100>% confidence)
- Projects created: <count of APPROVED_PROFILE.approved_projects> (<list names>)
- Custom prefixes added: <count> (<list codes>)
- Config saved to <vault_root>/workflow-kit.config.json
- Discovery report saved to <APPROVED_PROFILE.profile_report_path>
- {N} skills installed to ~/.claude/skills/
- <2 or 3> onboarding pickups created in Notes/Pickups/
<If migration ran:>
- <count> files migrated — see Notes/migration-log-<today>.md

Next steps:
1. Open this folder in Obsidian (if you haven't already) and click Trust
2. Type /pickup to start your first onboarding task
```

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
