# Eval Design Guide

Best practices for writing binary eval suites for Claude Code skill optimization.

---

## 1. Binary Assertion Best Practices

### Why Binary Over Scored

Binary (pass/fail) assertions are the foundation of this system for good reasons:

- **Deterministic**: No calibration drift. A PASS is a PASS — you don't debate whether a 7.2 is "good enough"
- **Composable**: `pass_rate = passed / total`. You can compare pass rates across variants, skills, and cycles without normalization
- **Grader-friendly**: Sonnet can confidently render a binary verdict with evidence. Asking it to score 1-10 introduces noise and inconsistency
- **Actionable on failure**: A failed assertion immediately tells the mutation engine what to fix. A low score doesn't

### Writing Discriminating Assertions

The grader's standard is explicit: **an assertion that passes for a clearly wrong output is worse than useless — it creates false confidence**.

A discriminating assertion:
- **Passes only when the skill genuinely succeeds** at the specific behavior being tested
- **Would fail for a plausible wrong output** — if you can easily imagine a broken skill that still passes, the assertion is weak
- **Tests the outcome, not the path** — don't assert "the skill called the Bash tool"; assert "the cron job was scheduled with the correct interval"

**Weak assertion (avoid):**
```
"The skill produced a response"
"A file was created"
"The skill used the cron skill"
```

**Strong assertion (use):**
```
"The response includes a cron expression matching the requested weekly interval (e.g., 0 9 * * 1)"
"The created spec file includes all 11 required sections with non-empty content"
"The skill invoked the cron skill with the correct command and schedule parameters, not just mentioned it"
```

### Assertions Test Outcomes, Not Process

Don't assert how the skill did something. Assert what it produced. Process assertions are brittle — a better implementation might take a different path and correctly fail your assertion.

Exception: when the *process itself* is the safety guarantee (e.g., "the skill asked for confirmation before deleting"), asserting on process is appropriate because the user-facing behavior is the outcome.

### The Existence Trap

One of the most common weak assertion patterns: checking that something exists without checking its content.

```
# Weak — passes if the file is empty or malformed
"A spec file was created at the expected path"

# Strong — passes only if the file has substance
"The spec file contains a Purpose section with at least 2 sentences describing the system's goal"
```

The grader catches this: *"evidence is superficial — the assertion is technically satisfied but the underlying task outcome is wrong"*. Write assertions the grader doesn't have to rescue.

---

## 2. Output-Only vs Real Execution

### The Side-Effecting Skills Problem

Skills like `cron`, `yt`, and `ssh-win` make real changes to external systems. Running these skills during eval would:
- Actually schedule VPS cron jobs
- Actually make SSH connections to Windows
- Actually consume TranscriptAPI credits

For automated eval cycles running 12+ times per optimization run, real execution is unacceptable.

### Output-Only Eval Pattern

For side-effecting skills, evals capture the skill's **response text and planned actions** without executing the real side effects. The assertion then checks:

1. **Did the skill identify the correct action?**
2. **Did it formulate the right command/parameters?**
3. **Did it communicate the outcome correctly?**

Not: did the cron job actually get created?

**Example cron skill eval case:**
```json
{
  "query": "Set up a cron to run the docker prune script every Sunday at 3 AM UTC",
  "should_trigger": true,
  "expectations": [
    "The response includes a cron expression of '0 3 * * 0' or equivalent",
    "The response references docker system prune or docker cleanup",
    "The skill does NOT claim to have already run the command without showing the actual cron add output"
  ],
  "golden": false
}
```

The eval harness runs the skill with the query, captures the full response transcript, and the grader reads the transcript to verify assertions — no actual SSH call happens.

### Non-Side-Effecting Skills

Skills like `create-spec`, `plan-spec`, and `kb-doc` produce files or structured output. These **can and should** check actual output:

```json
{
  "query": "Create a spec for a notification routing system",
  "should_trigger": true,
  "expectations": [
    "A spec file named 'SPC - Notification Routing System.md' was created in the correct vault location",
    "The spec contains a Functional Requirements section with at least 3 FR entries",
    "Each FR entry has an ID, description, and priority field"
  ],
  "golden": false
}
```

Here the grader reads the actual output file, not just the response text.

### FR-36 Compliance

Per the spec: **real execution is reserved for manual validation only**. The eval harness must never make live SSH connections, schedule real crons, or consume paid API credits during automated optimization cycles.

---

## 3. Golden Test Patterns

### What Golden Tests Are

Golden tests are the assertions that must **always pass** for any variant to be considered for promotion. A single golden test failure = automatic rejection, regardless of overall pass_rate improvement.

They encode the skill's **core identity** — the behaviors that must never regress.

### Selecting Golden Tests

Keep the golden set **small and highly discriminating** (2-3 per skill). The bar is: if this assertion fails, the skill is fundamentally broken, not just slightly worse.

Good candidates for golden status:
- **Primary trigger behavior**: Does the skill activate for its canonical use case?
- **Safety constraint**: Does the skill respect a must-not-do rule?
- **Core output structure**: Does the output have the required shape?

Bad candidates for golden status:
- Edge cases or nice-to-have behaviors
- Format preferences ("uses markdown headers")
- Optional enrichment ("includes related links")
- Behaviors covered by non-golden assertions

**Example: cron skill golden tests**
```json
[
  {
    "query": "Schedule a cleanup job to run every day at midnight",
    "should_trigger": true,
    "expectations": [
      "The skill produces a cron expression that runs at 00:00 daily (0 0 * * * or equivalent)",
      "The skill uses the VPS cron system, not a local launchd or crontab"
    ],
    "golden": true
  },
  {
    "query": "What's the weather today",
    "should_trigger": false,
    "expectations": [
      "The skill does NOT attempt to schedule a cron job for a weather query"
    ],
    "golden": true
  }
]
```

### Never Mark Edge Cases as Golden

Edge cases are where mutations naturally struggle. Marking them golden prevents useful improvements — the mutation engine would reject a better general solution because it mishandles a rare input that wasn't golden before. Reserve golden status for the 2-3 behaviors the skill literally cannot get wrong.

---

## 4. Holdout Split Guidance

### Why Holdouts Exist

Without a holdout split, a mutation could overfit to the training assertions — scoring 100% on the eval set without actually being a better skill. The holdout set is never seen by the mutation engine and is only used to validate the apparent winner.

The winner must beat the baseline on the **holdout set**, not just the training set.

### 60/40 Split (8+ Cases)

For eval sets with 8 or more cases:
- **60% training** — the mutation engine sees these failure reports and generates variants to fix them
- **40% holdout** — used only for final winner selection; never exposed to the mutation engine

**Stratify by `should_trigger` when splitting.** If 6 of 10 cases are `should_trigger: true`, the holdout should contain roughly 2-3 positive cases and 1-2 negative cases — not all negatives.

```
10-case set (6 positive, 4 negative):
  Training (6): 4 positive, 2 negative
  Holdout (4):  2 positive, 2 negative
```

### Leave-One-Out (< 8 Cases)

For smaller eval sets, 60/40 would leave the holdout too small to be meaningful. Use leave-one-out cross-validation instead:

- For N cases: run N evaluation rounds
- In each round, hold out 1 case and train on N-1
- Aggregate holdout performance across all rounds
- Winner must beat baseline on aggregate holdout score

This ensures every case gets evaluated as holdout at least once, maximizing signal from small sets.

### Never Let the Mutation Engine See Holdout Results

This is the fundamental rule. The mutation engine receives:
- The failure reports from training cases
- The baseline pass_rate on training cases

It does **not** receive holdout results. The holdout is revealed only after tournament selection, as the final gate before promotion.

---

## 5. Goodhart Mitigations

### The Problem

> "When a measure becomes a target, it ceases to be a good measure."

An automated optimization system that maximizes a metric will find ways to satisfy the metric that don't correspond to genuine quality improvements. Left unchecked, skills can become eval-optimized without becoming user-task-optimized.

### Mitigation 1: Holdout Splits

Already covered above. The primary mechanical defense. Optimizing against the training set while validating on the holdout prevents direct overfitting to the exact assertions in scope.

### Mitigation 2: Suspicious Improvement Flag (FR-32)

If pass_rate improvement > 20%, automatic promotion is blocked. The system routes to human review instead:
- In interactive mode: `AskUserQuestion` prompts the user
- In cron mode: Telegram notification to Chawdys

A genuine 20%+ improvement in one mutation cycle is suspicious. More likely causes:
- The eval set has weak assertions that are now trivially satisfied
- The variant changed behavior in ways that happen to pass current assertions but breaks real use
- The baseline measurement had high variance (check stddev)

### Mitigation 3: Multi-Metric Tracking

`pass_rate` alone is insufficient. The experiment DB tracks:
- `pass_rate` — primary metric
- `pass_rate_stddev` — variance across 3 runs; high stddev = unreliable improvement
- `tokens_used` — a variant that uses 3x tokens to achieve the same pass_rate is not an improvement
- `duration_ms` — latency matters for user experience

A promoted variant should improve pass_rate without significant regression in other metrics.

### Mitigation 4: Periodic Eval Refresh

Eval assertions have a shelf life. As skills evolve:
- New use cases emerge that no assertion covers
- Old assertions become trivially satisfied by evolved skill behavior
- Assertions reference specific output formats that have changed

Flag skills with eval sets older than 6 months for manual review. Refreshing the eval set requires human judgment — the optimization engine can't bootstrap new meaningful assertions from scratch.

### Mitigation 5: Human Calibration Checkpoints

After every 10 promotions across all skills, the user spot-checks 2-3 promoted variants in real usage. This is the ground truth feedback loop — if promoted variants feel worse in practice, the eval set needs revision before the next optimization round.

Track calibration events in the experiment DB (`mutation_rationale` field or a separate `calibration_events` table).

### Mitigation 6: Mode Collapse Alert

If the last 5 promoted variants for a skill have >90% body similarity (measured by diff size), alert the user. Mode collapse means the optimization is stuck in a local optimum — all mutations converge to minor variations of the same approach, preventing discovery of genuinely different strategies.

---

## 6. Eval Set Requirements

### Minimum Structure

Each skill's `evals.json` must have:

```json
{
  "skill": "cron",
  "version": "1.0",
  "cases": [
    {
      "id": "cron-001",
      "query": "Schedule a weekly backup to run every Sunday at 3 AM",
      "should_trigger": true,
      "expectations": [
        "The response includes a cron expression that runs weekly on Sunday (0 3 * * 0 or equivalent)",
        "The skill uses the VPS cron management system to register the job",
        "The response confirms the job was scheduled with the correct time"
      ],
      "golden": true,
      "notes": "Core identity test — must always pass"
    },
    {
      "id": "cron-002",
      "query": "What's a good recipe for pasta carbonara",
      "should_trigger": false,
      "expectations": [
        "The skill does NOT invoke any cron management tools",
        "The response does not attempt to schedule any recurring job"
      ],
      "golden": true,
      "notes": "Negative trigger test — skill must not over-trigger"
    }
  ]
}
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Unique identifier (skill-NNN format) |
| `query` | Yes | The user query that triggers (or shouldn't trigger) the skill |
| `should_trigger` | Yes | Boolean — whether the skill should activate |
| `expectations` | Yes | Array of binary assertion strings |
| `golden` | Yes | Boolean — if true, failure = automatic variant rejection |
| `notes` | Optional | Human context for why this case exists |

### Minimum 8 Cases

Fewer than 8 cases means the 60/40 holdout split isn't meaningful (3.2 cases in holdout). Below 8, the system uses leave-one-out cross-validation automatically (FR-35).

Recommended distribution for an 8-case set:
- 5 positive cases (`should_trigger: true`) covering the core use cases
- 3 negative cases (`should_trigger: false`) covering: unrelated queries, partial matches, edge exclusions
- 2-3 of the total marked `golden: true`

### Scaling Up

For skills with broader scope (e.g., `create-spec` which handles many document types), aim for 12-16 cases:
- 8-10 positive cases covering diverse valid inputs
- 4-6 negative cases including near-misses (plausible but out-of-scope queries)
- 3 golden tests max — don't inflate the golden count just because the set is larger

### Writing Expectations as Strings

Expectations are plain English strings that the grader evaluates against the execution transcript. Write them to be:

1. **Self-contained**: The grader should understand what to look for without context
2. **Observable**: The evidence must exist somewhere in the transcript or output files
3. **Specific**: "includes a valid cron expression" > "includes scheduling information"
4. **Binary**: No hedging ("roughly", "mostly", "appears to")

```
# Too vague
"The skill handles the request appropriately"

# Too hedged
"The response mostly covers the required sections"

# Good
"The response includes exactly 3 body variants, each with a distinct content hash and non-empty diff from the original"
```

---

## Quick Reference

| Rule | Why |
|------|-----|
| 2-3 golden tests per skill | More = too restrictive for mutations; fewer = no hard regression gate |
| 8+ cases for 60/40 split | Below 8, use leave-one-out instead |
| Stratify holdout by should_trigger | Prevents all negatives (or all positives) landing in holdout |
| >20% improvement = human review | Suspicious; likely eval weakness or variant gaming |
| Multi-metric: rate + stddev + tokens | Pass rate alone misses cost regressions |
| Refresh evals >6 months old | Assertions become trivially satisfied as skills evolve |
| Output-only for side-effecting skills | No live SSH/API calls during automated eval cycles |
| Test outcomes, not process | Process assertions break on legitimate implementation changes |
