---
date created: 2026-03-29
tags: [getting-started]
category: Reference
---

# Getting Started

Welcome to your Workflow Kit. Here's how to get up and running.

> **Note:** This system uses **Claude Code** (the terminal/CLI tool), not Claude Desktop (the chat app). If you haven't installed Claude Code yet, get it at [claude.com/product/claude-code](https://www.claude.com/product/claude-code).

## 1. Install Skills

Before anything else, copy the skills into Claude Code's directory. In your terminal:

**macOS:**
```bash
cp -r skills/* ~/.claude/skills/
```

**Windows:**
```cmd
xcopy /E /I "skills\*" "%USERPROFILE%\.claude\skills\"
```

This makes all the workflow commands (like `/setup`, `/orient`, `/pickup`) available to Claude.

## 2. Open in Obsidian

Open this folder as a vault in Obsidian. When it asks you to trust community plugins, click **Trust**. The plugins are already configured.

## 3. Run Setup

Open a terminal **in this folder** and start Claude with permissions skipped (setup reads many files and the prompts are tedious):

```bash
claude --dangerously-skip-permissions
```

Then type:

```
/setup
```

Claude will ask your name and what kind of work you do, then scan your files to understand your work and set everything up. Takes about 5 minutes.

> **Windows users:** If `claude` isn't recognized, you may need to add it to your PATH. Ask Claude Desktop or search "add to PATH Windows" for instructions.

## 3. Start Your First Pickup

After setup, type:

```
/pickup
```

You'll see three starter tasks. Work through them in order — they teach you the system by having you use it on real work.

## Daily Habits

| When | What to Type | What Happens |
|------|-------------|-------------|
| Start of day | `/orient` then `/pickup` | Load your context and see what's next |
| During work | `/log-work` | Record what you're doing |
| End of day | `/closeout` | Save your progress for tomorrow |

## The Core Workflow

When you want to do something structured:

1. `/create-spec` — Describe what you want to do (Claude interviews you)
2. `/review-spec` — Check the spec for problems (optional but recommended)
3. `/plan-spec` — Break it into phases with milestones
4. `/implement` — Execute the plan with AI assistance

This works for anything — software, documents, processes, budgets, operational procedures.

## Key Concepts

- **Pickups** — Context documents that save where you left off. Created by `/closeout`, loaded by `/pickup`. This is how you resume across sessions.
- **Specs** — Structured descriptions of what you're trying to accomplish. Created by `/create-spec`.
- **Plans** — Phased breakdowns of how to get there. Created by `/plan-spec`.
- **Daily Notes** — Click a date in the Calendar sidebar to create one. They track what you worked on each day.

## Need Help?

- Type `/orient` to have Claude load all vault context
- Type `/troubleshoot` if something isn't working
- Type `/recap` to see where you are in the current conversation
