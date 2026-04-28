# Database Checklist

Inject into worker prompt when task involves SQL queries, schema migrations, or database operations.

## Schema Inspection (MANDATORY before any SQL)

Run `\d schema.table_name` for EVERY table you will query. Copy column names exactly. Do not guess from plan descriptions — if plan says `close_at` but schema has `voting_close_date`, trust the schema.

Two tables in a single sprint had column name mismatches between plan and actual schema. Both required fix commits. `\d` takes 2 seconds; a fix cycle takes 10 minutes.

## Migration Safety

1. Write both `up()` and `down()` methods. Every migration must be reversible.
2. Test migration against a snapshot first if available (check `/root/db-snapshots/` on VPS).
3. For column renames: check ALL consumers (API routes, UI components, other services) before running. A rename that breaks a consumer at runtime is worse than no rename.
4. After migration: verify with `\d schema.table_name` that the schema matches expectations.

## Prompt Library (if registering prompts)

The ai-gateway reads from `public.prompt_templates`, NOT `ai.prompts`. Insert into the correct table:
```sql
SELECT key, model, status FROM public.prompt_templates WHERE key = '<your_key>';
```
Use single-brace interpolation (`{variable_name}`). Double braces are NOT substituted.

## Existing Data Pipelines

Before building data access for a new feature, check if the data already exists locally:
- `triage_emails` stores email content from Graph API sync
- `signals` stores extracted intelligence from meetings/emails
- Query the relevant tables before building new API integrations

The plan description is a summary. The database defines what data is actually available. When they disagree, trust the database.

## Python Import Paths (Docker services)

For Docker services with `PYTHONPATH=/app`:
```python
from src.module import X  # correct
from module import X      # fails in Docker
```
Verify before committing: `python -c "from src.<module> import <export>"`

## Dependency Pinning (Python)

After scaffolding `requirements.txt` with `>=` bounds: create venv, install, then `pip freeze > requirements.txt`. Loose bounds cause deploy breaks when Docker installs a newer version.
