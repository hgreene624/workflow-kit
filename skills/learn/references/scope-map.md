# Scope Map — Where Lessons and Rules Live

Use this table to pick the narrowest scope that covers where the lesson applies. When in doubt, go narrower — you can always promote a lesson to a broader scope later, but a lesson filed too broadly becomes noise.

## Scope Table

| Domain | Lessons file | Rules file |
|--------|-------------|------------|
| VPS / Docker / Traefik | `01_Work/03_Projects/VPS/lessons.md` | that dir's `CLAUDE.md` |
| Plane tracker | `04_ Tools/Reference/REF - Plane Lessons.md` | — |
| Frontend / UI / CSS | `04_ Tools/Reference/REF - Frontend Lessons.md` | — |
| Project planning | `04_ Tools/Reference/REF - Project Planning Lessons.md` | — |
| Chawdys / OpenClaw | `01_Work/03_Projects/Chawdys/lessons.md` | that dir's `CLAUDE.md` |
| {{SIGNAL_ENGINE}} / Signal Engine | `{{PROJECT_PATH}}/{{INTELLIGENCE_PROJECT}}/lessons.md` | that dir's `CLAUDE.md` |
| Specific project | that project's `lessons.md` | that project's `CLAUDE.md` |
| Specific file's gotcha | `## Lessons` section in that file | — (rules don't go in content files) |
| General agent behavior | `04_ Tools/Reference/REF - Agent Lessons.md` | root `CLAUDE.md` |

## How to Pick a Scope

1. **Can you name a specific project directory?** → Use that project's `lessons.md`
2. **Is it about a tool or domain that spans projects?** → Use the domain-level `REF - *Lessons.md`
3. **Is it about how agents should behave in general?** → `REF - Agent Lessons.md`
4. **Is it a gotcha specific to one file?** → Inline `## Lessons` section at the bottom of that file

## Adding New Scopes

If a project doesn't have a `lessons.md` yet:
1. Create `lessons.md` in the project directory with the same frontmatter pattern as existing ones
2. Add a breadcrumb in the project's `CLAUDE.md`: `- **Lessons**: See [[lessons]]`
