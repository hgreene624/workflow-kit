# Pipeline QA — Subsystem Audit Framework

Evaluate pipeline subsystems against their specs, verify output correctness, diagnose failures, and log results. The spec is the ground truth — criteria come from your specs, not arbitrary quality scores.

Use this skill when the user says "pipeline qa", "validate pipeline", "subsystem qa", "run pipeline eval", "check pipeline quality", "test the pipeline", or wants to verify that a subsystem is producing spec-compliant output.

## Core Principle

Quality has two layers, and both must pass:

1. **Structural compliance:** Does the output match the spec's schemas, enums, gating rules, and behavioral requirements?
2. **Content truth:** Does the generated content accurately describe the source data it claims to represent?

A record that passes every structural check can still be worthless if the summary describes the wrong input, the classification mischaracterizes what happened, or the attribution points to the wrong entity. **Checking that fields are populated is not QA. Checking that fields contain the correct information is QA.**

When a subsystem fails either layer, you can modify anything needed to fix it: prompts (DB or code), processing logic, config lists, schema migrations, compose files. The fix is whatever makes the output both structurally valid and substantively true.

---

## Prerequisites — Subsystem Registry

Before this skill can run, define your subsystems in your project's `agents.md` or a dedicated config file. Each subsystem entry needs:

```yaml
subsystems:
  - name: "Email Processing Pipeline"
    spec: "SPC - Email Processing System.md"
    infrastructure:
      services: ["api-server", "worker"]
      db_tables: ["emails", "signals", "activities"]
      endpoints: ["/api/health", "/api/pipeline/status"]
      env_vars: ["DATABASE_URL", "API_KEY", "LLM_GATEWAY_URL"]
    sub_components: ["Noise Filter", "Classification", "Entity Resolution", "Output Validation"]
    eval_command: "python -m pipeline_eval --subsystem email --limit 20"
    qa_log: "reports/qa/QAL - Email Processing Pipeline.md"
```

If no registry exists, ask the user to define the subsystem before proceeding.

---

## Step 1: Select Subsystem

Read the subsystem registry. Present the user with a numbered list of available systems. After system selection, present the sub-components for that system (also from the registry).

Always include a "Full Pipeline" option that evaluates all sub-components in sequence.

```
Which system?
1. Email Processing Pipeline
2. Data Enrichment Service
3. Notification System

Which sub-component?
1. Noise Filter
2. Classification
3. Entity Resolution
4. Output Validation
5. Full Pipeline (all of the above)
```

---

## Step 2: Load Context

Before running any evaluation:

1. **Read the spec** — Load the SPC file referenced in the subsystem registry. Focus on sections relevant to the selected sub-component.
2. **Read project context** — Load `agents.md` and `lessons.md` for the project.
3. **Read the code** for the selected sub-component.
4. **Read the QA Log** if one exists for this subsystem (path from registry).
5. **Check golden tests** — if a `golden/` directory exists alongside the QA logs, load the relevant golden test file.

Build a concrete understanding of:
- What the spec says this sub-component should produce
- What the code currently does
- What previous QA runs found

---

## Step 3: Infrastructure Audit

Before evaluating output quality, verify the subsystem's foundation is intact. Many pipeline failures are not output quality issues, they are infrastructure gaps, missing migrations, stale config, or inherited technical debt. This step catches those.

Run every check relevant to the selected subsystem. Each check is binary: PASS or FAIL with specifics.

### Universal Checks (all subsystems)

Run these for every subsystem, using the values from the registry:

| ID | Check | How to Verify | What Failure Means |
|----|-------|---------------|-------------------|
| INF-1 | **Services running** | Check each service listed in `infrastructure.services` is up and responsive | Pipeline can't execute at all |
| INF-2 | **Code matches deploy** | Compare a key function signature in the running service vs committed code | Deployed code is stale; fixes committed but never deployed |
| INF-3 | **DB connectivity** | Verify connection to database and that tables in `infrastructure.db_tables` exist with expected columns | Pipeline will fail on all DB operations |
| INF-4 | **Environment variables** | Check each var in `infrastructure.env_vars` is set and non-empty in the running service | API calls fail, DB writes fail, features silently disabled |
| INF-5 | **Endpoints reachable** | Hit each URL in `infrastructure.endpoints` | Dependent services unreachable |

### Subsystem-Specific Checks

Beyond universal checks, each subsystem needs domain-specific infrastructure verification. Define these in `agents.md` or derive them from the spec. Common categories to consider:

- **Data freshness:** Is the source data pipeline feeding new records? (e.g., check recent row counts in source tables)
- **Prompt/config registration:** Are LLM prompts, feature flags, or config entries that the code references actually present in the database or config store?
- **Upstream API access:** Can the pipeline reach the external APIs it reads from? (e.g., email provider, calendar API, data feeds)
- **Backlog size:** How many unprocessed records exist? A large backlog may indicate a stalled pipeline or misconfigured parameters.
- **Dependent service health:** Are downstream services the pipeline writes to (gateways, queues, caches) reachable and accepting data?

### Reporting

Record every check in the QA Log under a `### Infrastructure Audit` section (before the output evaluation):

```markdown
### Infrastructure Audit

| ID | Check | Result | Detail |
|----|-------|--------|--------|
| INF-1 | Services running | PASS | api-server up 3 days, worker up 3 days |
| INF-3 | DB connectivity | PASS | All 4 tables present |
| INF-5 | Endpoints reachable | FAIL | /api/enrich/health returns 503 |
```

**Any infrastructure FAIL is a hard blocker.** Fix infrastructure issues before running the output evaluation. There is no point evaluating classification quality if the service is down or reading stale data.

Infrastructure fixes follow the same diagnose-fix-verify loop as output fixes (Step 7). Log them in the same QA Log entry under Fixes Applied.

---

## Step 4: Define Spec Compliance Criteria

Read the spec for the selected sub-component and translate its requirements into binary pass/fail criteria. These are NOT arbitrary quality checks — they are direct translations of what the spec requires.

For each spec requirement that produces observable output: identify the requirement, define a binary pass condition, and note the spec section for traceability.

### Example Criteria Table

| # | Criterion | Spec Source | Pass Condition |
|---|-----------|-------------|----------------|
| C1 | VALID_CATEGORY | Section 3.2 | category is one of the defined enum values |
| C2 | SOURCE_LINKED | Section 3.4 | Every output record has a non-null source FK |
| C3 | NO_DUPLICATES | Section 3.5 | No two output records share the same source_ref |
| C4 | SCHEMA_VALID | Section 4.1 | Payload matches the per-type JSON schema |
| C5 | WEIGHT_CORRECT | Section 4.3 | weight = base_weight * multiplier per spec tables |

**Show the criteria to the user before running.** If the spec is ambiguous or silent on a quality dimension, flag it rather than inventing criteria.

---

## Step 5: Content Truth Verification

Spec compliance (Step 4) checks structure. Content truth verification checks **whether the generated content actually matches the source data it claims to describe.**

This is the most critical QA step. A record can pass every structural check and still be wrong if the summary describes the wrong input, the classification mischaracterizes what happened, or the attribution points to the wrong entity.

### The Method

For every pipeline output you evaluate, perform a **source-to-output comparison**:

1. **Pull the output joined to its source.** Never evaluate output in isolation. Join the generated artifact back to the raw input that produced it. Find the FK or source reference that connects output to input, build the join, and compare.

   Generic pattern:
   ```
   SELECT output.id, output.type, output.generated_summary,
          source.id, source.original_content
   FROM outputs
   JOIN sources ON sources.id = outputs.source_ref
   WHERE outputs.created_at > recent_window
   ORDER BY outputs.created_at DESC;
   ```

2. **For each output, answer three questions:**
   - **Is this true?** Does the output accurately reflect what the source material says? Not just "is it plausible" but "does the source actually say this?" Look for hallucinated details, cross-contaminated content from other sources in the same batch, and content extracted from nested/quoted data rather than the primary record.
   - **Is this attributed correctly?** Does the entity, person, or parent record this output points to match what the source data indicates? Check that the attributed author matches the actual source author, and that linked parent records are topically related.
   - **Is the judgment correct?** For outputs involving a classification decision (type, priority, category, weight), would a human reading the source data make the same call?

3. **Compare across the batch.** Cross-contamination is a batch-level bug — you won't catch it by looking at records individually. For every batch processed together, verify that no two outputs swapped their content. The telltale sign: output A's summary describes what source B actually says, and vice versa.

### Batch-Level Audit Pattern

When auditing a batch that was processed together:

1. Pull all outputs from the batch (same timestamp or run ID)
2. For each output, check: does the attribution match the source author? Does the summary match the source content?
3. If you find a mismatch, check the *other* outputs in the batch. The mismatched content probably belongs to one of them.
4. Count: how many outputs in the batch are correct vs contaminated? If more than one is wrong, the bug is in the batch processing logic (ID mapping, positional mapping, prompt confusion).

### What to Look For

| Issue Type | How to Detect | Severity |
|-----------|---------------|----------|
| **Hallucination** | Output contains details not present anywhere in the source | P0 — the system is inventing information |
| **Cross-contamination** | Output accurately describes a *different* source in the same batch | P0 — correct info on wrong record |
| **Nested extraction** | Output describes content from a quoted/forwarded/nested section, not the primary record | P1 — real info but wrong attribution |
| **Template placeholder** | Output is a pattern like "{type}: {title}" with no analysis | P1 — zero analytical value |
| **Wrong judgment** | Classification doesn't match what the source material warrants | P2 — structurally valid, substantively wrong |
| **Entity mismatch** | Attribution doesn't match the actual source sender/author | P2 — downstream scoring and routing affected |
| **Cascade misroute** | One bad classification propagates to all subsequent items in the same group | P1 — one error poisons N downstream records |

### When Content Issues Are Found

Content truth failures are more serious than structural failures because they produce *plausible-looking wrong data* that downstream consumers will trust. Fix priority:

1. **Stop the bleeding** — if the bug affects all future processing (not just historical data), fix the code path first
2. **Identify the root cause** — trace the code that produced the wrong content. Common causes: LLM response matched to wrong input (ID mapping bug), LLM reading nested/quoted content instead of the primary record, group/thread matching linking to a stale parent, fallback logic assigning default values that look real but aren't
3. **Fix and retest on the same data** — delete the bad outputs, reset the inputs, reprocess, compare before/after
4. **Quantify the blast radius** — how many existing records are affected? Is this a one-off or systematic?

---

## Step 6: Run Evaluation

Run the evaluation using the method appropriate to the subsystem:

- **If an eval command exists** in the registry, run it and parse the output
- **If no eval command**, query the database directly to pull recent outputs joined to their sources

For sub-components without a dedicated eval script, build targeted queries that pull outputs alongside the source data they were derived from, then manually verify each result against the criteria.

### Evaluate Every Result

For each output item, check against every criterion from Step 4 and the content truth questions from Step 5. Record:
- **PASS** or **FAIL** per criterion
- For failures: the specific value that violated the criterion and what the spec says it should be
- Group failures by root cause type

### "Full Pipeline" Option

When the user selects "Full Pipeline":
1. Run infrastructure audit with ALL checks for that system
2. Evaluate each sub-component in pipeline order (upstream before downstream)
3. Fix infrastructure issues first, then work through sub-component failures in order
4. A single combined QA Log entry covers all sub-components, with separate criteria/data sections per sub-component

---

## Step 7: Diagnose and Fix

For each failure group:

### 7a: Check Prior Run History

Before diagnosing, read the QA Log (if it exists). Check:
- Has this failure type appeared before?
- Was a fix attempted? Did it work, partially work, or regress?
- Are there "Remaining Issues" from prior runs that match this failure?

This prevents re-attempting fixes that already failed and surfaces recurring issues (e.g., "this is the third time this failure type has appeared, the previous fix wasn't sufficient").

### 7b: Classify Root Cause

| Root Cause Type | What to Investigate | Fix Target |
|----------------|--------------------|-----------| 
| **Prompt gap** | LLM prompt doesn't instruct the model to produce spec-compliant output | Prompt template (DB or code) |
| **Code logic** | Code doesn't implement the spec correctly | Source files |
| **Config gap** | Missing entries in filter lists, wrong enum values, missing mappings | Config files |
| **Schema gap** | Missing column, wrong type, missing constraint | DB migration |
| **Data quality** | Stale or orphan data causing misroutes | Data cleanup query |

### 7c: Implement and Verify

1. **Implement** the fix (prompt, code, config, schema, or data)
2. **Verify** by re-running only the failing cases. Check:
   - Do previously failing cases now pass?
   - Do the golden tests still pass (if they exist)?
   - Did the fix introduce any new failures in the passing cases?
3. **Deploy** if the fix involved code/config changes. DB-only changes (prompt updates, data cleanup) may not need a deploy.

If the fix causes regressions, revert and try a different approach.

### 7d: Iterate

Repeat for each failure group. Stop when:
- All criteria pass, OR
- Remaining failures require user decisions, OR
- Remaining failures are blocked on external dependencies

Present remaining issues to the user with enough context for them to decide.

---

## Step 8: Write QA Log

After evaluation (and any fixes), write or append to the QA Log file at the path specified in the subsystem registry. One log file per system. Each run appends an entry. The file accumulates over time.

### QA Log Format

```yaml
---
date created: YYYY-MM-DD
tags: [qa-log, pipeline-qa, {system-tag}]
category: Report
type: QAL
system: "{system name}"
---
```

```markdown
# QAL - {System Name}

## Run: YYYY-MM-DD HH:MM — {Sub-component}

**Batch:** {description of what was evaluated}

### Infrastructure Audit

| ID | Check | Result | Detail |
|----|-------|--------|--------|
| INF-1 | Services running | PASS | Up 3 days |
| INF-5 | Endpoints reachable | FAIL | /health returns 503 |

**Infrastructure blockers:** {count} FAIL
**Infrastructure fixes applied this run:** {list, or "none needed"}

### Spec Compliance Criteria

Criteria derived from {spec filename}:

| ID | Criterion | Spec Source | Pass Condition |
|----|-----------|-------------|----------------|
| C1 | {NAME} | {section ref} | {condition} |

### Evaluation Data

| # | Item | C1 | C2 | C3 | Verdict | Notes |
|---|------|----|----|----|---------|-------|
| 1 | {item identifier} | PASS | PASS | FAIL | FAIL | {what was wrong} |

**Summary:** {pass}/{total} items passed all criteria ({pct}%). {N} distinct failure types across {M} failing items.

### Failures Found
- **{Root cause type}: {description}**
  - Affected: {N} items (#{list of item numbers from table above})
  - Example: {specific failing case with actual values}
  - Spec requirement: {what the spec says, with section reference}
  - Actual output: {what the system produced}
  - Code location: {file:line}

### Fixes Applied
- **{Fix description}**
  - Type: {prompt|code|config|schema|data}
  - Files changed: {list}
  - Commit: {hash} (if applicable)
  - Verified: {yes|no} — {pass rate after fix}

### Remaining Issues
- {Failures not fixed and why}

### Trend (vs prior runs)
- **Last run:** {date} — {pass_rate}% -> this run: {pass_rate}%
- **Recurring failures:** {list any failure types that appeared in previous runs, or "none — first run"}
- **Infrastructure delta:** {checks that changed since last run}
- **Previously attempted fixes that didn't hold:** {list, or "none"}

### Golden Test Results
- {PASS|FAIL}: {N}/{M} golden tests passed

---
```

Each new run appends a `## Run:` section at the top (newest first).

---

## Step 9: Present Summary

After completing evaluation and any fixes, present:

1. **Before/after pass rate** for the sub-component
2. **What was fixed** (one line per fix)
3. **What remains** (failures not fixed and why)
4. **Suggested next sub-component** to evaluate

Ask if the user wants to:
1. Run the next sub-component
2. Re-run this sub-component to verify
3. Move on to other work

Do NOT auto-fix without user confirmation on the approach. The user decides what to act on.

---

## Golden Tests

Golden tests are a small set of cases (5-10) with known-correct outcomes that must never regress. If golden tests don't exist yet, the first QA run should establish them:

1. From the current batch, select 5-10 cases that clearly pass all criteria
2. Save them as the golden test set for that sub-component
3. On subsequent runs, always verify golden tests pass before promoting any fix

Store in a `golden/` subdirectory alongside QA logs (one JSON line per case: input, expected, rationale).

---

## Tips

- Start with the sub-component most likely to have failures (check PICs or recent QA logs)
- When fixing prompts, include the specific failure case in context ("these 3 records were misclassified because the prompt doesn't handle X")
- For code fixes, verify the fix is deployed to the environment you're testing against
- Don't optimize beyond spec compliance — if the spec is silent, don't invent criteria
- If the spec itself seems wrong or incomplete for a sub-component, flag it to the user rather than inventing criteria

---

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local customizations override upstream where they conflict. Use `LOCAL.md` to define your specific subsystem registry, infrastructure checks, DB queries, and file paths.
