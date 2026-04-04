# Database Diagnostics

## Databases in the Stack

| Database | Container | Type | Access |
|----------|-----------|------|--------|
| `{{PROJECT_DB}}` | `{{DB_CONTAINER}}` | PostgreSQL 17 | `ssh <YOUR_VPS> "docker exec {{DB_CONTAINER}} psql -U flora -d {{PROJECT_DB}}"` |
| Plane DB | `plane-plane-db-1` | PostgreSQL | `ssh <YOUR_VPS> "docker exec -e PGPASSWORD=YOUR_DB_PASSWORD plane-plane-db-1 psql -U plane -d plane"` |
| IK Buckets search | `ik-buckets` | SQLite | `/app/db/search.db` (bind-mounted from host) |
| IK Buckets data | `ik-buckets` | SQLite | `/app/db/ik_buckets.db` (bind-mounted) |
| IK Buckets users | `ik-buckets` | SQLite | `/app/db/users.db` (bind-mounted) |

## Diagnostic Checklist

### 1. ALWAYS inspect schema before writing queries

```sql
-- PostgreSQL: list columns
\d schema.table

-- SQLite: list columns
.schema table_name
```

**This is the #1 rule.** Never guess column names. One wrong column = one wasted deploy cycle.

**Cross-ref:** Agent L7, Agent L11, Agent L18

### 2. Verify the right database

```bash
# {{PROJECT_DB}} (main app DB)
ssh <YOUR_VPS> "docker exec {{DB_CONTAINER}} psql -U flora -d {{PROJECT_DB}} -c '\dt public.*'"

# Sales schema (inside {{PROJECT_DB}})
ssh <YOUR_VPS> "docker exec {{DB_CONTAINER}} psql -U flora -d {{PROJECT_DB}} -c '\dt sales.*'"

# Plane DB
ssh <YOUR_VPS> 'docker exec -e PGPASSWORD=YOUR_DB_PASSWORD plane-plane-db-1 psql -U plane -d plane -c "\dt"'
```

### 3. Check for schema mismatches in agent-generated code

When you find ONE column-doesn't-exist error in agent-generated code, audit ALL SQL queries in the codebase — the agent made the same wrong assumptions everywhere.

```bash
# Find all SQL queries in a codebase
grep -rn "SELECT\|INSERT\|UPDATE\|DELETE\|FROM\|JOIN" /path/to/app/ --include="*.py" --include="*.ts" --include="*.js"
```

**Cross-ref:** Agent L11, Agent L18

### 4. Verify data was actually written

```sql
-- After an INSERT, verify it landed
SELECT * FROM table WHERE created_at > NOW() - INTERVAL '5 minutes';

-- Check for NULL columns that should have data
SELECT column_name, COUNT(*) FILTER (WHERE column_name IS NULL) as null_count
FROM table GROUP BY 1;
```

**Cross-ref:** FWIS L7 (insert_signal silently dropped signal_type)

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| "column X does not exist" | Wrong column name guessed | Run `\d table` first | Agent L7 |
| Data written but column is NULL | INSERT SQL missing the column | Check column list + VALUES + param tuple | FWIS L7 |
| 500 on page load | Agent-generated queries assumed wrong schema | Audit ALL queries against real schema | Agent L11, L18 |
| "relation X does not exist" | Wrong table name or schema prefix | Check `\dt schema.*` | Agent L20 |
| Heredoc INSERT over SSH returns 0 rows | Heredoc feeds local stdin to ssh | Use `-c` with escaped quotes | VPS L16 |
| SyntaxError in python3 -c over SSH | Bash history expansion mangles `!=` | Use single-quoted python or temp script | VPS L17 |

## {{PROJECT_DB}} Key Schemas

- `public.*` — signals, work_items, initiatives, meetings, email data
- `sales.*` — sales pipeline (profiles, contacts, classifications)
- `auth.*` — user management, audit log, sessions
- `reservations.*` — restaurant reservations
- Materialized views: `mv_daily_signal_volume` (refreshed nightly at 7 PM)

## PostgreSQL Connection Details

- **Host:** `{{DB_CONTAINER}}` (internal network) or `127.0.0.1:5432` (VPS host)
- **User:** `flora`
- **DB:** `{{PROJECT_DB}}`
- **Password:** In env vars of connected containers
- **Backups:** `/docker/flora/backups/{{PROJECT_DB}}_YYYY-MM-DD.sql.gz` (7-day retention, nightly at 2:30 AM)

## Key Gotchas

- **Passwords with special chars break DATABASE_URL.** Use individual params instead of connection string URI. (VPS L8)
- **Never hardcode entity ID lists.** Query the DB for current IDs. (Agent L9)
- **Sales tables are NOT in db.py SCHEMA_SQL** — managed via direct DDL
- **`{{PROJECT_DB}}.db` is a legacy artifact at 0 bytes** — the active DB is PostgreSQL

## Lessons Files
- `04_ Tools/Reference/REF - Agent Lessons.md` — L7 (schema inspection), L9 (query for IDs), L11 (validate agent SQL), L18 (audit all queries)
- `01_Work/03_Projects/Flora Work Intelligence System/lessons.md` — L7 (insert_signal SQL)
- `01_Work/03_Projects/VPS/lessons.md` — L8 (password URI), L16-18 (shell/heredoc issues)
