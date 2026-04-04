# Skills Specification

Skills in this repository follow the [Agent Skills Spec](https://agentskills.io/specification).

## Structure

Each skill lives in `skills/<skill-name>/SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name          # Must match directory name, kebab-case
description: >-           # What it does + when to trigger it
  One-line description used for agent discovery.
license: MIT
metadata:
  author: YOUR_USERNAME
  version: "1.0"
  category: ops | vault | integration
---
```

## Categories

| Category      | Skills                          |
|---------------|---------------------------------|
| vault         | orient, learn, end-day          |
| ops           | troubleshoot, vps-deploy        |
| integration   | limitless, video-intel          |

## Adding a New Skill

1. Create `skills/<name>/SKILL.md` with frontmatter + instructions
2. Add entry to `.claude-plugin/marketplace.json`
3. Optional: add `scripts/`, `references/`, or `assets/` subdirectories
4. Push to GitHub
