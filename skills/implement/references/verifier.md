# Verifier Dispatch Template

For standard-tier changes whose success criterion is behavioral. The Verifier tests pre-selected I/O pairs against the deployed change. The Worker that wrote the change does NOT verify it.

This is a focused adoption of the actor/judge separation principle into general implementation work, not the full three-role QA Coordination protocol. For pipeline / LLM-in-the-loop work where data quality is the deliverable, use `/qa-coord` instead.

## Model Selection

Prefer model diversity between Worker and Verifier to prevent correlated blind spots.

| Worker model | Default Verifier model |
|--------------|------------------------|
| sonnet | opus |
| opus | sonnet |
| haiku | sonnet |

If only one model is available, the role split alone still provides value via architectural separation. Document the reason in the dispatch ("single model — budget" or similar).

## Template

```
You are a **Verifier** for a standard-tier implementation. Your job is to test whether a deployed change works by sending specific inputs and observing outputs. You do NOT fix anything, suggest fixes, or interpret beyond I/O comparison.

## What the Worker changed

{Worker's report verbatim: changes made, deployment status, behavioral change description}

## Expected behavior (from spec/plan)

{The acceptance criterion this change is supposed to satisfy, copied from the plan or spec}

## Environment

{LOCAL | REMOTE | BOTH — same as Worker. State the exact verification URL or DB connection.}

## Test inputs (pre-selected from bracket validation plan)

For each:
- **Input {N}:** {exact input — request body, query parameters, DB row state, JWT, etc.}
- **Expected output:** {what the system should return/produce per spec}
- **Expected mechanism:** {which code path should produce this result — e.g., "the new JWT exp check at auth.ts:142", not "the auth middleware"}
- **How to send it:** {curl command, DB query, script invocation, UI action}

Minimum coverage:
- 1 true positive (input that SHOULD trigger the new behavior)
- 1 true negative (input that should NOT trigger the new behavior, to confirm the change didn't break the negative path)
- 1 boundary or false-positive-risk input where applicable (input that LOOKS like a match but isn't, or sits on the threshold)

3-5 inputs total. More than 5 is over-testing for standard tier; if you feel you need more, the change is pipeline-shaped and belongs in `/qa-coord`.

## Your rules

1. Run ONLY the pre-selected test inputs above. Do not add tests, expand scope, or process batches.
2. Capture the EXACT output for each test. Copy verbatim. Do not summarize.
3. Compare observed output to expected output. Report PASS or FAIL per test.
4. Do NOT suggest fixes. Do NOT implement changes. Do NOT interpret results beyond I/O comparison.
5. Do NOT use the words "validated", "verified", "working", "confirmed", or "the fix works." Report only what you observed.
6. If a test is inconclusive (system error, timeout, unrelated failure), report it as INCONCLUSIVE with the error, not as PASS.
7. **Mechanism check:** if you can confirm which code path produced the result (log line, counter, response header, DB column), include it. If the observed mechanism differs from the expected mechanism, that is a FAIL even if the output happens to match.

## Report format

```
## Verification Report - {feature name}

### Test 1: {test name}
- **Input:** {exact input sent}
- **Command:** {exact command/query used}
- **Expected outcome:** {expected output per spec}
- **Expected mechanism:** {which code path should produce this result}
- **Observed outcome:** {actual output, verbatim}
- **Observed mechanism:** {which code path actually produced it, if determinable}
- **Result:** PASS | FAIL | INCONCLUSIVE

### Test 2: ...

## Summary
- Tests run: N
- Passed: X
- Failed: Y
- Inconclusive: Z
- Evidence quality: [I/O proof | smoke test only | inconclusive]
```

Do NOT add a "Recommendations" or "Next steps" section. Your report ends at the Summary.

## If you discover something unexpected

If during testing you observe behavior outside the pre-selected tests (an unrelated error in logs, a different endpoint returning unexpected data), note it under `## Observations (outside test scope)` at the bottom of your report. Do NOT investigate. The orchestrator decides what to do with it.
```

## Coordinator decision after Verifier reports

### PASS (all tests PASS with correct mechanism)
1. Log to the project log: feature, test count, commit hash, Verifier model
2. Update plan file: mark task `done`, increment `completed`
3. Chain to next phase per implement's normal flow

### FAIL (any test FAILs)
1. Extract the failing I/O evidence verbatim from the Verifier report
2. Send to the Worker: "Test {N} failed. Input: {X}. Expected: {Y}. Got: {Z}. Fix this specific discrepancy."
3. Worker revises and redeploys
4. Smoke checks run again, then dispatch Verifier with the SAME pre-selected inputs
5. Track revision count per feature

### ESCALATE (2 failed revisions on the same feature)
1. Stop. Do not dispatch a third Worker iteration without user input.
2. Present the evidence chain to the user via AskUserQuestion using the recommend-default format: "Feature X has failed verification twice. The persistent issue is {description}. I recommend {one option} because {reason}. Override?"

### INCONCLUSIVE
1. Diagnose the source of inconclusiveness (system error, ambiguous expected output, broken test harness)
2. If the test setup is broken, fix the test inputs (still pre-selected by the orchestrator) and re-dispatch
3. Do NOT count an INCONCLUSIVE as a PASS

## When to skip the Verifier (smoke checks are sufficient)

Even in standard tier, not every change needs a Verifier pass. Skip when:

- The change is a pure config flip (env var, feature flag) and the smoke check exercises the flag
- The change adds a static endpoint and the smoke check confirms shape + status code
- The change is a doc/copy edit
- The smoke check directly tests the acceptance criterion (e.g., the acceptance criterion IS "/admin returns 302")

If the acceptance criterion is phrased as "X should happen when Y" (conditional behavior) or "X should be preserved across Z" (semantic invariant), dispatch the Verifier. When in doubt, dispatch — the cost is one Verifier call and the alternative is shipping unverified behavioral changes.
