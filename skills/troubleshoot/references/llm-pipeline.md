# LLM Pipeline / Signal Engine Diagnostics

## Pipeline Architecture

```
Email fetch (Graph API) → classify.py → signal_builder.py → DB insert
                              ↓
                     sales_classifier.py → sales_actuator.py → sales_profile_builder.py
```

- **Container:** `fwis-api` (Flora compose)
- **Source:** `/docker/flora/<SIGNAL_ENGINE>/`
- **DB:** `flora_signal` (PostgreSQL 17, `flora-postgres`)
- **API:** `api.<YOUR_DOMAIN>` (FastAPI, basic auth)

## Prompt Library

**ALL prompts must live in the Prompt Library.** No hardcoded prompts.

- **Table:** `public.prompt_templates` in `flora_signal` DB
- **Admin UI:** `admin.<YOUR_DOMAIN>/prompts`
- **Key format:** `project.module.function` (e.g., `inbox-triage.classifier.system`)
- **Client:** `prompt_client.py` (Python) or `prompt-client.ts` (TypeScript)
- **Current count:** 74 prompts across 8 projects

```bash
# List all prompts
ssh <YOUR_VPS> "docker exec flora-postgres psql -U flora -d flora_signal -c \"SELECT key, version, updated_at FROM prompt_templates ORDER BY key\""

# Check a specific prompt
ssh <YOUR_VPS> "docker exec flora-postgres psql -U flora -d flora_signal -c \"SELECT content FROM prompt_templates WHERE key = '<key>'\""
```

**Cross-ref:** FWIS L6 (regenerate prompts.json after DB updates)

## Diagnostic Checklist

### 1. Is the pipeline using the latest prompt?

```bash
# Check if prompts.json is stale
ssh <YOUR_VPS> "docker exec fwis-api cat /app/prompts.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print([(k,v.get(\"version\",\"?\")) for k,v in d.items() if \"<keyword>\" in k])'"

# Regenerate from API
ssh <YOUR_VPS> "docker exec fwis-api curl -s http://localhost:8000/api/prompts > /app/prompts.json"
```

### 2. Check pipeline execution

```bash
# Run with verbose + dry-run
ssh <YOUR_VPS> "docker exec fwis-api python3 flora_signal.py --mailbox <email> --verbose --dry-run --limit 5"

# Check recent pipeline logs
ssh <YOUR_VPS> "docker logs fwis-api 2>&1 | grep -i 'pipeline\|error\|signal' | tail -20"
```

### 3. Verify prompt-to-DB alignment

When a prompt outputs structured JSON that maps to a DB table:
1. Every DB column has a corresponding prompt field?
2. Every prompt output field exists in the applicator's field map?
3. No phantom fields being silently dropped?

**Cross-ref:** FWIS L4 (prompt-applicator-DB alignment)

### 4. Check signal/data insertion

```bash
# Verify data was actually written
ssh <YOUR_VPS> "docker exec flora-postgres psql -U flora -d flora_signal -c \"SELECT id, signal_type, created_at FROM signals ORDER BY created_at DESC LIMIT 5\""

# Check for NULL columns that should have data
ssh <YOUR_VPS> "docker exec flora-postgres psql -U flora -d flora_signal -c \"SELECT COUNT(*) FILTER (WHERE signal_type IS NULL) as null_signal_type FROM signals\""
```

**Cross-ref:** FWIS L7 (INSERT SQL missing column in list)

## Common Failure Modes

| Symptom | Likely Cause | Fix | Lesson |
|---------|-------------|-----|--------|
| Pipeline uses old prompt | Stale `prompts.json` cache | Regenerate from API | FWIS L6 |
| Prompt output missing fields | Prompt doesn't ask for all DB columns | Audit prompt vs schema | FWIS L4 |
| Data written but column NULL | INSERT SQL missing column | Check signature + columns + VALUES + tuple | FWIS L7 |
| Classification wrong | Enum values not constrained | Check `sales_classifier.py` ENUM_NORMALIZERS | — |
| API returns error object, frontend crashes | No `Array.isArray()` guard | Add guard to all list endpoint consumers | FWIS L3 |
| Telegram spam during bulk ops | `TELEGRAM_TARGET` not disabled | Set to `""` in config.py | FWIS L2 |
| Pipeline processes too many items | CLI date range too wide | Use targeted script with specific IDs | Agent L12 |

## Sales Pipeline

- **Modules:** `sales_classifier.py` (v1.1.0), `sales_actuator.py`, `sales_profile_builder.py`
- **Schema:** `CREATE SCHEMA sales` — tables NOT in `db.py` SCHEMA_SQL
- **Enum normalization:** `ENUM_NORMALIZERS` in `sales_profile_builder.py` for 34-field profiles
- **Validation:** Progressive batches (50 → 200 → 500 → full), formal quality audit at each step

## Quality Gates

- **Every phase that produces data needs a quality audit** — actual output quality, not just "0 errors"
- **Failed audit = remediation sub-phase inserted.** No skipping ahead.
- **Never backfill before full validation.** Progressive batches only.
- **Split progressive validation into separate blocked tasks** — agents skip verification gates in single-task descriptions (Agent L13)

## Pipeline CLI Reference

```bash
# Standard run (today's emails only)
docker exec fwis-api python3 flora_signal.py --mailbox user@domain.com

# Date range with limit
docker exec fwis-api python3 flora_signal.py --mailbox user@domain.com --start-date 2026-03-01 --end-date 2026-03-14 --limit 20

# Skip email fetch (reprocess cached)
docker exec fwis-api python3 flora_signal.py --mailbox user@domain.com --skip-fetch

# Dry run (no DB writes)
docker exec fwis-api python3 flora_signal.py --mailbox user@domain.com --dry-run --verbose
```

## Lessons Files
- `01_Work/03_Projects/Flora Work Intelligence System/lessons.md` — L1-L7
- `04_ Tools/Reference/REF - Agent Lessons.md` — L12 (batch limits), L13 (progressive validation)
- MEMORY topic: `llm-pipeline-lessons.md`
