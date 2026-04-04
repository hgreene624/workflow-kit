# Learn — Examples

Reference examples for lesson and rule formatting. Read this when drafting entries.

## Good lesson (C-A-W) — specific, actionable, explains why:

```markdown
## L7: Always inspect DB schema before writing queries
**Condition:** Writing SQL against an unfamiliar or recently-changed table.
**Action:** (1) Run `\d schema.table` to see actual column names and types. (2) Compare against any spec or migration file. (3) Only then write queries.
**Why:** Guessing column names leads to cascading 500 errors — fixing one wrong column often introduces another wrong guess, each requiring a rebuild+deploy cycle.
**Scope:** All database work across projects.
**Source:** 2026-03-10 — KB edit page hit 500 three times from wrong column names, each fix required a rebuild+deploy cycle.
```

## Good lesson (Narrative) — retrospective context, no repeatable steps:

```markdown
## L5: External attribution stops investigation too early
We spent 2 hours assuming the Plane API was down before discovering our own proxy was misconfigured. External blame is the easiest hypothesis — it stops investigation exactly when it should deepen.
**Source:** 2026-03-02 — Plane API "outage" was actually a proxy routing error.
```

## Bad lesson — vague, no action, no why:

```markdown
## L7: Database issues
We had problems with the database. Be careful with queries.
**Source:** 2026-03-10 — Query problems.
```

## Good rule — clear mandate, specific scope:

```markdown
3. **Read procedure docs before VPS changes**: Before modifying any VPS config or service, read the relevant procedure doc from `Maintenance/`. Never skip steps, even if you "know" the procedure.
```
