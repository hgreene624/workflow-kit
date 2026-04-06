# Pipeline QA

Run quality evaluations against FWIS signal pipelines, produce a report artifact, and track pass rates over time. Does not auto-fix - diagnoses root causes and reports them for decision-making.

Use this skill when the user says "pipeline qa", "validate pipeline", "signal eval", "run pipeline eval", "check signal quality", "test the pipeline", or wants to validate that FWIS email/meeting signal generation is producing correct results.

## What It Does

1. Processes a small batch of unclassified data through the pipeline
2. Evaluates every outcome against objective criteria
3. Groups failures by root cause type
4. Produces a report artifact with pass/fail rates and actionable findings
5. Compares against prior runs to show trend

## Success Criteria

Every email processed is evaluated against these criteria:

| # | Criterion | Pass Condition |
|---|-----------|----------------|
| 1 | NOISE | Non-business emails (newsletters, marketing, spam, health, retail, political, SaaS notifications) are filtered or LLM-skipped |
| 2 | CLASSIFY | Business emails produce at least one signal |
| 3 | ROUTE | Signals link to a topically correct activity (not a mega-thread catch-all) |
| 4 | CONSOLIDATE | Emails in the same thread link to the same activity |
| 5 | QUALITY | Signal summaries are specific and LLM-generated (not template fallbacks) |
| 6 | NO_FALSE_POS | Internal @YOUR_DOMAIN emails are never noise-filtered (except calendar accepts/declines) |

A batch passes when all emails pass all criteria.

## Steps

### Step 1: Choose Target

If the user specifies a date and mailbox, use those. Otherwise:

1. Query for dates with the most unclassified emails:
```sql
SELECT e.received_at::date as d, COUNT(*) as unclassified
FROM sources.emails e
LEFT JOIN signals s ON s.source_ref = e.id AND s.source_type = 'email'
WHERE s.id IS NULL AND e.received_at > now() - interval '7 days'
GROUP BY 1 ORDER BY 2 DESC LIMIT 5
```
2. Pick the date with the most data (best eval coverage)
3. Default mailbox: `admin@YOUR_DOMAIN` (primary, most diverse email)
4. Default batch size: 20 emails (enough to surface issues, small enough to inspect)

### Step 2: Run Eval

Run the eval script on the VPS:
```bash
ssh vps 'docker exec flora-api python3 -m src.engine.pipeline_eval --mailbox {mailbox} --date {date} --limit {limit}'
```

The eval script (`services/api/src/engine/pipeline_eval.py`) handles:
- Fetching unclassified emails
- Running the noise filter
- Running classification (commits results)
- Evaluating every outcome against the 6 criteria
- Reporting pass/fail with root cause grouping

### Step 3: Diagnose Failures

For each failure type reported by the eval, trace the root cause:

**NOISE_MISS** (spam not caught):
- Check: is the sender domain in NOISE_DOMAINS_GLOBAL? If not, should it be?
- Check: does the subject match any NOISE_SUBJECT_PATTERNS? If not, should it?
- Check: did the LLM noise audit run? (look for "Noise audit LLM call failed" in logs)
- Check: is this a pattern (same domain/sender type appearing multiple times)?
- Root cause is one of: missing domain rule, missing subject pattern, audit prompt gap, or audit bug

**FALSE_POSITIVE** (business email filtered as noise):
- Check: which noise rule triggered? (grep the domain/subject against NOISE_DOMAINS_GLOBAL and NOISE_SUBJECT_PATTERNS)
- Check: is the rule too broad? (e.g., matching a business domain that shares a substring with a noise domain)
- Root cause is one of: overly broad domain rule, overly broad subject pattern, or regex matching OTP-style false positive

**CLASSIFY_MISS** (business email produced no signals):
- Check: was it in the LLM batch or did it match a thread first?
- Check: did the LLM return "skip" for it? If so, why? (check if the skip criteria are too aggressive)
- Root cause is one of: LLM skip too aggressive, email not in batch (limit exceeded), or LLM error

**MEGA_THREAD** (email in mega-conversation):
- Check: how many emails share this conversation_id?
- Check: do they span multiple unrelated topics?
- Root cause: Microsoft Graph conversation_id drift over years of forwarding/replying

**TEMPLATE_SUMMARY** (signal has generic summary):
- Check: was this from the old code path (pre-signal-extraction) or the new one?
- Check: did the LLM return a signal_summary field in its response?
- Root cause is one of: old code path (thread match doesn't do LLM extraction), or LLM didn't return signal_summary

**CONSOLIDATE failure** (same thread split across activities):
- Check: were the emails classified in different batches?
- Check: did conversation_id matching fail to link them?
- Root cause is one of: batch boundary split the thread, or conversation_id was missing

### Step 4: Produce Report

Save a report artifact to the vault:

```
Work Vault/02_Projects/{{ORG}} Intelligence/signal-engine/reports/YYYY-MM-DD/RE - Pipeline QA {date}.md
```

Report structure:
```markdown
---
date created: {today}
tags: [report, pipeline-qa, fwis]
category: Report
---

# Pipeline QA - {target_date} ({mailbox})

## Summary
- **Batch:** {limit} emails from {target_date}
- **Pass rate:** {pass}/{total} ({pct}%)
- **Failures:** {fail_count} across {n} root cause types

## Results by Email
{per-email table from eval output}

## Failures by Root Cause
{grouped failures with diagnosis}

## Recommended Fixes
{actionable items, ordered by impact}

## Trend
{comparison with prior QA runs if they exist}
```

### Step 5: Present to User

Show the summary and ask if they want to:
1. Fix the top root cause now
2. Run another batch (different date or mailbox)
3. Accept the current state and move on

Do NOT auto-fix. The user decides what to act on.

## Configuration

- **Eval script:** `~/Repos/{{MONOREPO_NAME}}/services/api/src/engine/pipeline_eval.py`
- **Noise filter config:** `services/api/src/shared/config.py` (NOISE_DOMAINS_GLOBAL, NOISE_SUBJECT_PATTERNS)
- **Classify prompt:** DB `fwis.classify.new_threads` (editable at YOUR_ADMIN_URL/prompts)
- **Noise audit prompt:** DB `fwis.classify.noise_audit`
- **Report location:** `Work Vault/02_Projects/{{ORG}} Intelligence/signal-engine/reports/`

## Eval Script Reference

The eval script lives in the monorepo and runs inside the flora-api container. It can also be run locally if DATABASE_URL is set.

```bash
# Full eval
python -m src.engine.pipeline_eval --mailbox admin@YOUR_DOMAIN --date 2026-04-01 --limit 20

# Quick smoke test (5 emails)
python -m src.engine.pipeline_eval --mailbox admin@YOUR_DOMAIN --date 2026-04-04 --limit 5
```

The script commits classification results to the DB (it's not read-only). Each run processes new emails that haven't been classified yet.
