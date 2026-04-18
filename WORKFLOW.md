# How It All Works

This is the full picture of how Workflow Kit turns a folder of text files into a personal productivity system. Read this if you want to understand why the system is built the way it is and how the pieces connect.

## The Problem

When you work with AI through a chat window, everything lives inside that conversation. The chat gets longer, the AI's memory fills up, and eventually it starts losing track of what you said earlier. If you close the window and start a new one, you're back to zero. There's no continuity.

This means:
- You repeat yourself constantly
- Complex projects fall apart across sessions
- There's no record of what was decided, what was tried, or what failed
- The AI can't learn your preferences or build on previous work

Tools like Microsoft Co-pilot promise to know your organization, but in practice they don't have the depth of context needed for real work. Setting them up is laborious, and they hallucinate about your systems because they lack grounding in your actual files and decisions.

## The Solution: A Shared Workspace

The core idea is simple: instead of working inside a chat, you work inside a **folder on your computer**. Both you and the AI can read and write files in that folder. Those files persist between sessions, between computers, and between different AI instances.

That folder is your **vault**. It's managed by [Obsidian](https://obsidian.md), which is just a note-taking app that makes text files look nice. But under the hood, everything is plain markdown (`.md` files), which is text that AI models are optimized to read and write.

This creates a shared interface:
- You can look at the files and see your work in a clean, organized format
- AI can look at the same files and understand exactly what's going on
- Either side can create, edit, and organize files
- Nothing is locked inside a chat window

When you have an agent that can see and work on the same files as you, you're collaborating. You're not asking questions to a chat anymore. You have a shared workspace where both sides contribute.

If you put your vault on iCloud, OneDrive, or another cloud drive, it syncs between your machines. Open Claude Code on any computer, point it at the vault, and you're right where you left off.

## Skills: Reusable Workflows

A **skill** is a set of instructions that tells Claude how to handle a specific type of task. Instead of explaining what you want step by step every time, you trigger a skill with a slash command and it runs the whole workflow for you.

For example, `/create-spec` is a skill that:
1. Asks you clarifying questions about what you're trying to build
2. Researches best practices
3. Creates a structured document with purpose, scope, requirements, and constraints
4. Iterates with you until the description is right

Skills encode months of iteration into a single command. When you find a better way to do something, you update the skill and every future use benefits from that improvement. When Claude produces something you don't like, you refine it and save the correction in the skill so it never makes that mistake again. You can also build your own skills for workflows specific to your work.

## The Core Pipeline: Spec, Plan, Implement

The main workflow for getting structured work done has three stages, each producing a persistent file that serves as the source of truth.

### 1. Spec (`/create-spec`)

A spec defines **what** you want to accomplish. It's a document with purpose, objectives, scope, requirements, and constraints. Think of it as the bible for what you're building.

The key insight: this file lives on your computer, not inside a chat. You can come back to it next week, next month, or next year. You can hand it to a different AI instance and it immediately understands the project. You never have the "actually the last version was better" problem because the spec is always the current truth.

This isn't just for software. If you want to build a tip calculator, map your network infrastructure, create a reporting workflow for your ticketing system, or redesign a business process, a spec gives you the structured starting point.

### 2. Plan (`/create-plan`)

A plan takes the spec and breaks it into **how** you'll execute it. It's a sequential series of phases, each with specific tasks, technical decisions, and milestones.

The plan is a **living document**. As you work through it, the status gets updated. If you need to pick the project up after a break, the plan tells you exactly where things stand: what's done, what's in progress, and what's next. Without this, picking up a complex project after a few days away is nearly impossible.

Why not just do everything in one shot? Because if you try to do something complex in a single chat, the context window fills up and the AI starts hallucinating halfway through. You lose everything. By keeping the plan outside the chat as a persistent file, you can restart sessions, pick up at any phase, and never lose progress.

### 3. Implement (`/implement`)

Implement takes the plan and executes it. It gauges the complexity of your project and decides how much oversight is needed. Simple projects can be one-shot. Complex ones get human-in-the-loop checkpoints at each phase.

For software projects, Claude can dispatch teams of AI agents to work in parallel. For non-code work, it guides you through the steps and tracks progress in the plan file. As each step completes, it marks it done in the plan so you always know where you stand.

## How Your Work Stays Organized

Everything you create goes into a structured folder system. You don't manage this manually; the system handles it.

### Project Folders

Each project gets its own directory with standard subfolders:

```
02_Projects/my-project/
  specs/2026-04-16/      -- What you're building
  plans/2026-04-16/      -- How you'll build it
  reports/2026-04-16/    -- Research and analysis
  reviews/2026-04-16/    -- Quality checks
  agents.md              -- AI context for this project
  PJL - My Project.md   -- Project log (work history)
```

Date subfolders keep things organized without "plan_v5_FINAL_FINAL" naming chaos. You can always find the most recent version of anything by looking at the latest date folder.

### File Prefixes

Every file starts with a short prefix so you know what it is at a glance:

| Prefix | Type |
|--------|------|
| `SPC` | Spec (what you're building) |
| `PL` | Plan (how you'll build it) |
| `PIC` | Pickup (context for resuming) |
| `DN` | Daily Note |
| `MN` | Meeting Note |
| `RE` | Report |
| `PJL` | Project Log |
| `WL` | Work Log (detailed session log) |
| `REF` | Reference (permanent knowledge) |

The AI knows these prefixes too, so it always creates files with the right naming and puts them in the right place.

## Two Layers of Logging

The system captures your work at two levels of detail, serving two different audiences.

### Daily Notes (Human Layer)

Your daily note is a running record of each day: what you worked on, what meetings you had, what decisions were made. It's written for you to scan quickly, like a standup summary. Bullet points, bold key accomplishments, links to detailed files.

You don't write this manually. As you use the system, Claude logs your work to the daily note automatically. At end of day, `/closeout` ensures everything is captured.

### Project Logs and Work Logs (AI Layer)

A **Project Log** (`PJL`) accumulates across sessions for each project. It captures what a future AI session needs to know: exact file paths, function names, deployment commands, decisions and their rationale, what was tried and failed. This is the machine-readable memory that lets a new Claude session pick up your project instantly.

A **Work Log** (`WL`) is a detailed session log for heavy work days (10+ tasks, multi-phase sprints). It captures per-task breakdowns, component lists, error messages, and SQL queries. Think of it as the detailed session transcript. Work logs link from the project log so there's a clear chain from daily note to PJL to WL.

The principle: daily notes tell you what moved the project forward. Project logs tell the AI how to continue the work. Work logs provide forensic detail when something goes wrong.

### The Rollup Hierarchy

Information distills upward over time:

- **Daily notes** capture what happened each day (human-friendly summaries)
- **Project logs** capture detailed implementation history (AI-friendly, per-project)
- **Weekly rollups** analyze the week: what went well, what went wrong, what trends are emerging
- **Monthly rollups** distill from weekly reports for higher-level patterns

This creates a searchable history of your work at any level of detail. Need to know what you worked on Tuesday? Check the daily note. Need to understand a project's full history? Read the PJL. Need to spot trends over the last month? Check the monthly rollup.

## Pickups and Closeouts: Your Memory Extension

When you're juggling multiple projects, your brain can't hold all the details. You have 10 things going, you switch contexts, and by the time you come back to something, you've forgotten what you decided and where you were.

**Pickups** solve this. A pickup (`PIC`) is a context document that captures everything a fresh session needs to continue work: what was done, what's next, known issues, key files, blockers. Think of it as an extension of your RAM.

**Closeout** (`/closeout`) is how pickups get created. At end of day, Claude reviews everything you worked on, logs it to your daily note, and creates a pickup for each piece of unfinished work. In the morning, you run `/pickup` and the system loads exactly the context you need.

This cycle means you can confidently close every session knowing nothing is lost, and start every session knowing exactly where to pick up.

## CLAUDE.md: Priming Every Session

When you start Claude Code in a directory, it automatically reads a file called `CLAUDE.md` if one exists. This file primes every new session with information that should always be loaded: your name, your role, how files should be formatted, where things go, and what conventions to follow.

Think of it as default instructions that you never have to type out. Instead of starting every session with "my name is X, I work at Y, format things like Z," the CLAUDE.md handles it and the AI is ready to go from the first message.

You can include things like:
- Your identity and role
- File formatting rules
- Recent weekly or monthly summaries (so the AI knows what you've been working on)
- Project-specific conventions
- Links to reference documents

The more useful context you put here, the higher the quality of interaction from the very first message.

## Building Domain Context

The quality of AI output is directly proportional to the quality of context you give it. This is the single most important principle in the system.

### The Cautionary Tale

One user asked Claude to configure a MikroTik router. Claude confidently proposed a solution. The solution broke their VPN tunnels because Claude didn't know the existing network topology. The user hadn't provided that context, and Claude didn't know what it didn't know.

The lesson: **always build your context before asking for action.** For any domain you work in (network management, restaurant operations, financial compliance, whatever), invest the time to create reference files that ground the AI in your actual environment.

### How to Build Context

1. **Reference manuals** -- Download vendor documentation, convert PDFs to markdown, and store them in your vault. Claude can help with the conversion. Always prefer markdown over PDF: it's faster to process, more accurate for AI, and doesn't suffer from garbled diagrams and spatial relationships.

2. **Inventories** -- List your devices, systems, accounts, vendors, or whatever entities matter in your domain. These become the "ground truth" files that prevent hallucination.

3. **Decision records** -- When you make a choice (this vendor over that one, this architecture over that one), document why. Future sessions won't re-argue resolved questions.

4. **Work artifacts** -- 80% of the work you do should be producing files. When you do a site visit, narrate what you find and transcribe it. When you investigate an incident, record it. Every artifact grows your context base.

5. **Recordings** -- If you have a recording device (Omi pendant, phone recorder, meeting transcription), feed transcripts through the system. Each conversation becomes searchable context.

## How It Compounds

Each piece of the system feeds into the others:

1. You do work, and the system **saves it** as organized files
2. Those files become **context** for future sessions
3. Future sessions produce **higher quality work** because they have better context
4. That work gets saved too, and the cycle continues

After a few weeks, your vault becomes a genuine personal knowledge base. After a few months, it's a detailed history of every project you've touched, every decision you made, and every lesson you learned. That history is always available to AI, which means the AI working with you today is informed by everything you've done before.

This is the real value: not any single feature, but the compound effect of persistent, organized, AI-accessible information that grows with your work.
