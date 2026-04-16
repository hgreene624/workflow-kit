# Workflow Kit

A personal productivity system that pairs Claude (AI) with Obsidian (notes) to create a shared workspace where you and AI build on the same files, the same context, and the same history.

## Why This Exists

The biggest limitation of working with AI today is memory. Chat windows bloat, context degrades, and everything you build together lives and dies inside a conversation. You start fresh every time. You repeat yourself. The AI forgets what you told it yesterday.

Workflow Kit solves this by giving you and AI a **shared filesystem**. Your vault is just a folder of text files on your computer, but those files become persistent storage that both you and AI can read, write, and build on across sessions. The more you use it, the smarter your AI gets, because it has a growing repository of your work, your decisions, your project history, and your preferences to draw from.

This isn't just a chat wrapper. It's a system that:

- **Saves everything you do** as organized files that AI can reference later
- **Builds your personal knowledge base** automatically through the work itself, not manual documentation
- **Lets you pick up any project instantly**, even weeks later, because the context is in the files, not in your head
- **Gets better over time** as your vault accumulates project logs, lessons, and work history

For a deeper look at how all the pieces connect, see [How It All Works](WORKFLOW.md).

---

## What You Can Do With It

**The short version:** You describe what you want to accomplish, and the system walks you through it:

1. **Spec it out** -- Claude asks you questions to understand what you're trying to do, then writes it up clearly
2. **Check your thinking** -- A review team (3 AI agents) looks for gaps, risks, and things you might have missed
3. **Plan the work** -- Breaks it into phases with clear milestones so you can track progress
4. **Do the work** -- Claude helps you execute each phase, checking quality along the way
5. **Pick up where you left off** -- Everything is saved. Start a new session and resume exactly where you stopped

This works for anything structured: a software feature, a business process, a hiring plan, a menu redesign, a budget model. It's not just for code.

---

## Getting Started

### What You Need

- **macOS or Windows**
- **A modern terminal** — **[Warp](https://www.warp.dev)** on macOS (free, has tabs and AI features) or **[Windows Terminal](https://aka.ms/terminal)** on Windows (free, has tabs). The default macOS Terminal and Windows Command Prompt also work.
- **[Claude Code](https://www.claude.com/product/claude-code)** — the terminal/CLI tool (not Claude Desktop, which is a separate chat app)
- **[Obsidian](https://obsidian.md)** installed (free note-taking app)
- **Git** — on macOS, open your terminal and type `git` to check (installs automatically). On Windows, download from [git-scm.com](https://git-scm.com)

> **Important:** Claude Code and Claude Desktop are different products. Claude Desktop is a chat app. Claude Code is a terminal tool that reads your files and runs commands. You need Claude Code for this system. If you only have Claude Desktop installed, [install Claude Code](https://www.claude.com/product/claude-code) separately.

### Step 1: Download the vault

**macOS** — Open Terminal and paste:
```bash
git clone https://github.com/YOUR_USERNAME/workflow-kit.git ~/Documents/Vaults/Work\ Vault
```

**Windows** — Open Terminal and paste:
```cmd
git clone https://github.com/YOUR_USERNAME/workflow-kit.git "%USERPROFILE%\Documents\Vaults\Work Vault"
```

If `git` is not recognized, install it from [git-scm.com](https://git-scm.com) first, then restart your terminal.

This creates a folder called `Work Vault` in your Documents. That folder **is** your workspace.

### Step 2: Install skills

Claude Code needs the skills installed before `/setup` will work. In your terminal:

**macOS:**
```bash
cp -r ~/Documents/Vaults/Work\ Vault/skills/* ~/.claude/skills/
```

**Windows:**
```cmd
xcopy /E /I "%USERPROFILE%\Documents\Vaults\Work Vault\skills\*" "%USERPROFILE%\.claude\skills\"
```

This copies all skill folders into Claude Code's skills directory. You only need to do this once. After this, `/update-wfk` handles future updates.

### Step 3: Open it in Obsidian

1. Open Obsidian
2. Click "Open folder as vault"
3. Navigate to `Work Vault` in your Documents
4. Click **Trust** when prompted (this enables the pre-configured plugins)

You'll see a sidebar with folders like `01_Notes`, `02_Projects`, etc. These are already set up for you.

### Step 4: Set up Claude

Open your terminal and navigate to the vault:

**macOS:**
```bash
cd ~/Documents/Vaults/Work\ Vault
claude --dangerously-skip-permissions
```

**Windows:**
```cmd
cd "%USERPROFILE%\Documents\Vaults\Work Vault"
claude --dangerously-skip-permissions
```

> The `--dangerously-skip-permissions` flag lets Claude run without asking permission for every file read and command. This is recommended during setup because the scan reads many files and the permission prompts make it very tedious. After setup, you can run `claude` without the flag if you prefer approval prompts.

Then type:

```
/setup
```

Claude will ask your name, then scan your files and installed tools to understand your work and set everything up. Takes about 5 minutes.

### Step 5: Start your first project

After setup, type:

```
/pickup
```

This shows three starter tasks that teach you the system by using it:

| Task | What You'll Learn |
|------|------------------|
| **Customize Your Profile** | How to make the system fit your specific work style |
| **Bring In Your Files** | How to organize existing work into the vault |
| **Your First Spec** | The core workflow — describing what you want to build and having Claude plan it out |

Work through these in order. By the end, you'll know how everything fits together.

---

## How It Works Day to Day

### Starting Your Day

Open Claude in your vault directory and say `/orient`. This loads your context — what you were working on, what's pending, what's next. Then say `/pickup` to resume where you left off.

### Working on Something New

Tell Claude what you want to do. It will walk you through the process:

1. **"I want to..."** — Claude interviews you about the idea, asks clarifying questions, and writes up a clear description of what you're trying to accomplish (a "spec")
2. **Review** — Before you commit to building it, Claude checks the spec for problems. Are there gaps? Things that could go wrong? Conflicts with other work?
3. **Plan** — Claude breaks the work into phases. Each phase delivers something you can actually see and test, not just invisible background work
4. **Build** — Claude helps you execute each phase. For code projects, it dispatches teams of AI agents. For other work, it guides you through the steps and tracks progress
5. **Review the output** — When done, Claude reviews what was produced for quality

You don't have to use every step. For small tasks, just tell Claude what you want and it'll figure out the right level of process.

### Ending Your Day

Say `/closeout`. Claude logs what you worked on and creates "pickup" documents — context files that let you (or a future Claude session) resume exactly where you stopped. No more "where was I?" moments.

### Key Commands

| What You Want | What to Say |
|---------------|------------|
| Start a session | `/orient` |
| Resume previous work | `/pickup` |
| Start a new project | `/create-spec` |
| Plan the work | `/create-plan` |
| Log what you did | `/log-work` |
| Understand a document or topic | `/explain` |
| Organize incoming files | `/intake` |
| Save context for later | `/park` |
| End your day | `/closeout` |
| Review completed work | `/retro` |
| See what skills can help you | `/discover` |
| Review your backlog | `/pickup` (shows triage when multiple PICs exist) |

### When Things Go Wrong

If Claude seems stuck or keeps trying the same fix repeatedly, say `/troubleshoot`. This activates a diagnostic mode that stops, investigates the root cause, and proposes a targeted fix instead of guessing.

### How Your Work Compounds

Every project gets a **Project Log** (`PJL - <Project>.md`) that accumulates across sessions. When you come back to a project, Claude reads the PJL and knows what was built, what decisions were made, what failed, and what's deployed. The more you use the system, the faster Claude ramps up on your projects.

---

## Your Vault

Everything lives in organized folders:

| Folder | What Goes Here |
|--------|---------------|
| **01_Notes** | Daily notes, meeting notes, weekly summaries, pickup documents |
| **02_Projects** | Your projects — each one gets its own folder with specs, plans, and reports |
| **03_Operations** | Domain-specific operational content |
| **04_Reference** | Long-lived knowledge — guides, decisions, runbooks |
| **05_System** | Templates and workflow configuration |

### Projects

When you start a new project, Claude creates a folder structure automatically:

```
02_Projects/my-project/
├── specs/          ← What you're trying to do
├── plans/          ← How you'll do it (broken into phases)
├── reports/        ← Analysis and research
├── reviews/        ← Quality checks
├── agents.md       ← AI instructions specific to this project
└── lessons.md      ← What you've learned along the way
```

You don't need to create this manually — Claude handles it when you run `/create-spec`.

### File Naming

Every document starts with a short prefix so you always know what it is at a glance:

| Prefix | What It Is |
|--------|-----------|
| `DN` | Daily Note |
| `MN` | Meeting Note |
| `SPC` | Spec (what you're building) |
| `PL` | Plan (how you'll build it) |
| `PIC` | Pickup (context for resuming work) |
| `RE` | Report |
| `REF` | Reference (permanent knowledge) |
| `RET` | Retrospective (what went well/wrong) |

---

## Adapting It to Your Work

### Making It Yours

During setup, the system scans your machine to detect what kind of work you do and tailors the vault accordingly — daily note sections, file prefixes, and project structure all adapt to your role. The first onboarding pickup helps you refine it further.

The system adapts over time:
- **Lessons** — When Claude learns something about how your work goes (a tool that doesn't work as expected, a process that needs an extra step), it saves that as a lesson. Future sessions read those lessons and avoid the same mistakes.
- **Agent configs** — Each project has an `agents.md` file where Claude stores project-specific context. This means Claude remembers the tech stack, the conventions, and the gotchas for each project.
- **Pickups** — Every time you stop working, the context is saved. When you come back, Claude reads the pickup and knows exactly where you were and what's next.

### Adding Your Own Skills

Skills are like saved recipes for Claude — repeatable workflows you can trigger with a slash command. You can create your own:

1. Say `/skill-creator` and describe what you want the skill to do
2. Claude writes the skill, tests it, and installs it
3. Now you can trigger it with `/your-skill-name` any time

---

## Staying Updated

To get the latest improvements:

```
/update-wfk
```

This pulls new skills and updated templates from this repository. Your personal files and project data are never touched — only the workflow tools get updated.

---

## Contributing

Found a bug or have an improvement? Run `/update-wfk contribute` and Claude will handle the fork, branch, and PR creation for you.

**Authentication note:** GitHub fine-grained PATs cannot create pull requests against repos owned by other users. The contribute action uses `gh` OAuth instead. If you haven't already, run `gh auth login` in your terminal before contributing. This is a GitHub API limitation, not a WFK issue.

You can also open issues at [github.com/hgreene624/workflow-kit/issues](https://github.com/hgreene624/workflow-kit/issues) to report bugs or suggest features.

---

## License

MIT
