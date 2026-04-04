# Vault Agent Rules

<!-- WFK:START - Kit Role -->
## Kit Role

```
wfk_role: user
```

This determines how `/update-workflow` behaves when called without arguments:
- `user` (default) - pulls the latest improvements from the WFK repo
- `developer` - pushes local changes to the WFK repo

If you are the kit maintainer, change this to `developer` in your local copy.
<!-- WFK:END -->

<!-- WFK:START - Core Pipeline -->
## Core Pipeline

All structured work follows **Spec > Plan > Implement**:
1. `/create-spec` — define what you're doing
2. `/review-spec` — validate the spec
3. `/plan-spec` — create the implementation plan
4. `/implement` — execute the plan

This applies to any work — software, documents, processes, analysis — not just code.
<!-- WFK:END -->

<!-- WFK:START - Daily Operations -->
## Daily Operations

- Start each day with `/orient` then `/pickup`
- End each day with `/closeout`
- Log work throughout the day with `/log-work`
- Use `/park` to defer context for later
<!-- WFK:END -->

<!-- WFK:START - File Prefix Conventions -->
## File Prefix Conventions

See CLAUDE.md for the full prefix table. Every document gets a prefix.
<!-- WFK:END -->

<!-- WFK:START - Project Structure Enforcement -->
## Project Structure Enforcement

All projects MUST use the standard structure:
- `specs/` for SPC files (in dated subfolders)
- `plans/` for PL files (in dated subfolders)
- `reports/YYYY-MM-DD/` for RE files
- `reviews/YYYY-MM-DD/` for review artifacts
- `agents.md` and `lessons.md` at project root
<!-- WFK:END -->

<!-- LOCAL:START - Add your vault-specific agent rules below this line -->
<!-- LOCAL:END -->
