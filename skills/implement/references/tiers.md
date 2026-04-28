# Ceremony Tiers

## Light (Default)

For: UI features, CRUD endpoints, config changes, documentation, tooling. Under 15 tasks, no production DB or deploy.

- Workers dispatch directly from orchestrator
- No PM tracker, no QA auditor agent
- No audit gates between phases
- No Plane sync during sprint (batch at closeout)
- Smoke checks after each phase (build + curl, inline)
- Workers self-verify and report to orchestrator

## Standard

For: Auth rewrites, schema migrations, production deploys, API gateway changes. Any work that is irreversible or touches real user data.

Everything in Light, plus:

- **Deploy gates** — smoke check must pass before reporting "deployed". Orchestrator verifies.
- **Security eval** — LLM review of auth/middleware diffs (see `security-eval.md`)
- **Migration gates** — review SQL before running against production. Orchestrator presents to user.
- **Bulk operation gates** — explicit user approval for operations affecting real users (emails, data changes)
- Plane sync still at closeout, not mid-sprint

## Heavy

For: Multi-day, multi-team infrastructure migrations with rollback plans. Rare.

Loads the original `/implement` skill (v1) which has full ceremony: PM tracker, QA auditor agent, per-phase audit gates, mid-sprint Plane sync, user testing gates, routing manifests.

Use heavy when: 3+ workers need real-time coordination, work spans multiple repos or deploy targets, rollback plans are required, or a prior attempt at standard tier failed due to coordination issues.

## Inferring Tier from Plan

When `ceremony_tier` is missing from frontmatter:

| Signal | Tier |
|--------|------|
| <15 tasks, no DB/deploy work | light |
| Auth, schema migration, or production deploy in task list | standard |
| Multiple repos, multiple deploy targets, 30+ tasks | heavy |
| `ceremony` block with v1 flags exists | Map: all off = light, some on = standard, all on = heavy |
