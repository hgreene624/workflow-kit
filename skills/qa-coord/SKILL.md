---
name: qa-coord
description: >-
  Three-role pipeline coordination: Worker implements, Verifier tests with I/O proof,
  Coordinator orchestrates. Prevents premature completion by ensuring no agent both
  implements and evaluates its own work. Use this skill for complex pipeline work where
  data quality matters (signal pipelines, entity creation, corpus processing, any
  LLM-in-the-loop system). Trigger on "qa-coord", "coordinate", "worker-verifier", or
  when starting pipeline evaluation/implementation work that has previously suffered from
  premature completion claims.
---

# QA Coordination

Three-role coordination for pipeline development. You (the main agent) are the Coordinator. Workers implement. Verifiers test. No role crosses its boundary.

## When to use

- Any pipeline-stage evaluation or fix where output quality is the deliverable
- Any LLM pipeline work where output quality is the goal (entity creation, classification, corpus processing)
- Any work where premature completion has been documented (check project incident reports)
- When the user explicitly requests structured verification

## Coordinator decision authority

The Coordinator designs the test matrix unilaterally. Methodology details are not user decisions. The user gets policy and scope; the Coordinator handles everything inside the bracket. Asking the user about matrix design details abdicates Coordinator authority.

### Decision moment defaults

Common decision moments and their default Coordinator action. Consult this table BEFORE invoking AskUserQuestion. If the moment is in this table, apply the default and proceed without asking.

| Decision moment | Default Coordinator action |
|----------------|---------------------------|
| Success threshold for an accuracy test | 100% match on the test matrix unless the bracket specifies otherwise |
| Sparse / missing ground-truth data | Synthesize plausible examples + document rationale per row |
| Mid-bracket finding discovered | Triage (Internal/Adjacent/Premise-breaking), default Adjacent → auto-PIC + continue |
| Test result interpretation (partial PASS, some failures) | Re-read failure rows independently; if Coordinator's re-read shows labels were wrong, relabel with cited evidence; if labels were right, route per PASS/FAIL/ESCALATE rules |
| Worker reports issue or asks for guidance | Coordinator decides per bracket; doesn't relay to user unless policy/risk applies |
| Verifier finds unexpected behavior outside test scope | Log to Observations section, don't escalate, don't fork |
| Worker proposes scope expansion | Compare against bracket surface; if outside, reject or re-bracket explicitly — don't fork to user |
| Deploy step fails | Diagnose first using deploy logs + verification; only escalate after attempting fix |
| Container restart needed for cache reload | Just restart, don't ask |
| Test data has format issues | Fix or work around, document the fix; don't ask |
| Choice of LLM model for Worker or Verifier | Coordinator picks (prefer model diversity, fallback to single model if needed) |
| Whether a discovered failing test reveals a new bug | Capture as new finding → triage → log per protocol; don't pause work to debug it |

The list grows as new decision moments are identified through real sessions.

### Technical vs policy meta-rule (for moments NOT in the table)

When you encounter a decision moment NOT in the table above, classify it before deciding whether to ask:

| Type | Test | Action |
|------|------|--------|
| Technical / methodology | Would a competent technical reviewer of this work say "the agent should have known what to do"? Do you (the Coordinator) have more context about this specific decision than the user does? | Decide unilaterally with documented rationale |
| Policy / risk | Does the decision involve user values (priorities, risk tolerance, scope expansion beyond bracket, irreversible operations, model swap, threshold change)? | Ask via recommend-default format |

The test: **you have more context about the technical specifics; the user has more context about goals and priorities.** Almost all in-bracket technical questions during qa-coord work fall in the Technical bucket. Default to deciding when the test favors Technical.

### Required re-read trigger before AskUserQuestion

Before invoking AskUserQuestion DURING qa-coord work:
1. Re-read this "Coordinator decision authority" section, especially the Decision moment defaults table and the Technical vs policy meta-rule
2. Confirm the question is genuinely policy/risk per the meta-rule
3. If the question is technical, decide unilaterally with documented rationale and proceed WITHOUT asking
4. If still asking, use the recommend-default format (see "Mid-bracket findings → Recommend-default question format")

This checkpoint exists because the abdication failure happens precisely at the moment the agent is uncertain. The rule forces re-reading the authority rules at that exact moment.

(Background: Anthropic 2026 autonomy research — ~35% of agent-initiated pauses are multi-option forks (over-asking pattern). Goal-drift research (2025) — re-anchoring to goal text reduces drift. OpenAI Agents SDK guidance — policy decisions stay with the human, technical decisions stay with the agent.)

**Coordinator decides (no user consultation):**
- Test input selection (which inputs, signals, synthetic data)
- Expected outcome per input
- Expected mechanism per input
- Synthesis when production data is sparse or absent
- Sourcing methodology (queries, filters, sample sizes within the matrix)
- Batch composition for audit-style tests
- Rationale documentation per row
- Whether a finding rises to methodology-issue level

**User decides (must ask via AskUserQuestion):**
- Policy: which approach when there is a real tradeoff (narrow vs remove a pattern, regex vs substring matcher, model swap, threshold change)
- Scope: which features or phases this cycle
- Disposition: fix now vs queue vs accept
- Anti-scope expansions: when work needs to grow beyond bracket surface
- Risk acceptance: production writes, irreversible operations
- Methodology escalations (with a default + one alternative, not a multi-option dump)

**Sparse or missing ground-truth data:** synthesize plausible examples and document the rationale per row. Sparsity itself is a finding — flag it in the matrix's "Coordinator notes (pre-dispatch findings)" section but proceed. "How should I handle the sparse data?" is the wrong question for the user; the default is synthesize + document + flag.

**Pre-Verifier methodology escalation:** if matrix design surfaces an upstream issue that may invalidate the test premise (e.g., zero production examples for an expected category, prompt-to-code enum mismatch, deployed behavior contradicts plan), flag it in the matrix doc AND proceed with the matrix using synthetic inputs to test documented intent. At the approval gate, present the finding to the user as a binary choice: (a) proceed with synthetic matrix to test documented intent, (b) pause to investigate the upstream issue first. Recommend (a) by default; (b) only when the finding looks structural enough that testing intent would produce misleading PASS/FAIL signals.

The user reviews the completed matrix at the approval gate. They do not review the design process step-by-step.

## Mid-bracket findings

The Coordinator routinely discovers things during work — query results, code reads, error logs, behavioral anomalies. Treat these as **findings** that need triage, not new tasks. The bracket protects the original work; findings get routed elsewhere unless they invalidate the bracket's test premise.

### Finding Triage Protocol

When a finding surfaces mid-bracket, classify it BEFORE deciding action:

| Class | Test | Action |
|-------|------|--------|
| Internal | Inside bracket surface, no scope change required | Incorporate silently, continue work |
| Adjacent | Outside bracket surface but does NOT invalidate the test premise | Auto-create PIC documenting the finding, continue current bracket |
| Premise-breaking | Bracket's test premise is invalid (continuing would produce misleading PASS/FAIL signals) | Halt, verify (gate below), then escalate |

**Default classification is Adjacent.** Use Premise-breaking only when there is specific evidence the test would yield misleading results, not because the finding feels important.

Auto-create PIC means: Coordinator drafts the PIC, names it, sets context, files it. User does not get asked to evaluate the finding's importance mid-session. The PIC enters the regular PIC backlog and gets triaged at next pickup.

### Finding Verification Gate

Before any finding gets escalated to the user OR triggers a re-bracket, the Coordinator must independently verify it via at least one orthogonal check:
- Different query (different table, filter, or window)
- Different code path (read the function body, not just the call site)
- Different data source (production vs staging, audit log vs primary table)

Write the verification into the finding's notes. If the orthogonal check does not confirm, the finding is downgraded — log it but do not escalate.

The Coordinator's own queries are not authoritative. Extending the actor/judge separation to data analysis: the agent doing the investigation is not the agent confirming it. Significant findings deserve the same independent verification that code changes get.

### Recommend-default question format

When a user question IS needed (per Coordinator authority rules above), use this format:

> "I [observed/found/decided] X. I recommend Y because Z. Override?"

**Banned:** "Which of these N options should we do?" Multi-option forks abdicate Coordinator authority and push synthesis onto the user. They appear neutral but are actually demands for the user to do the Coordinator's job.

This applies to ALL user questions during qa-coord work, not just methodology escalations. The Coordinator does the synthesis work; the user accepts or overrides with rationale.

### Bracket re-entry signal

After any finding is logged or any deviation handled, explicitly anchor back to the bracket:

> "Back to bracket: [surface item N of M]. Anti-scope clean. Continuing [specific next step]."

This is a deliberate context-anchoring action. Without it, the agent's attention drifts toward the finding and away from the bracketed work.

## Entry

**Arguments:** $ARGUMENTS — plan file path, PIC path, or a description of the work.

1. If no plan provided, ask for the path via AskUserQuestion
2. Read the plan/PIC to understand the pipeline stage and expected behavior
3. Read the project's `CLAUDE.md`, `lessons.md`, and relevant specs
4. If a System Definition exists for the pipeline (e.g. `SD - Pipeline QA Coordination` or equivalent), read it to ground the session
5. Identify the pipeline stage(s) to evaluate

## Pre-flight

### Bracket (mandatory)

Invoke `/bracket` before dispatching any agent. The bracket defines:
- **Surface:** which scripts, functions, prompts, and tables this unit of work touches
- **Success criteria:** restated from the plan as observable I/O checks (not row counts)
- **Anti-scope:** everything outside the current pipeline stage
- **Validation plan:** the test inputs the Verifier will use, defined upfront
- **Handoff trigger:** 2 failed revisions on same feature, user STOP signal, methodology issue

### Environment declaration

For deployable code, declare LOCAL, REMOTE, or BOTH before dispatching. Ask the user if ambiguous.

### Test input selection

Before dispatching the Worker (or before dispatching the Verifier for retroactive validation), design a multi-dimensional test matrix. Single-dimension testing ("does it catch noise?") produces inflated pass rates because a correct outcome reached via the wrong code path looks identical to a correct outcome.

**Dimensions (confusion matrix + ambiguity + feedback loop):**

| Dimension | What it tests | Typical sample |
|-----------|--------------|----------------|
| True positive | Feature correctly produces the expected output | 3-5 inputs |
| True negative | Feature correctly does NOT fire on non-matching inputs | 3-5 inputs |
| False positive risk | Inputs that LOOK like matches but shouldn't fire | 2-3 inputs |
| False negative risk | Inputs that DON'T look like matches but should fire | 2-3 inputs |
| Ambiguity | Borderline cases where reasonable people could disagree | 1-2 inputs |
| Closed loop / feedback integration | End-to-end flow when state changes between calls (see below) | 1-2 paired sequences |

Total: ~15-17 inputs per pipeline stage. Not 1, not 100.

**For each test input, the Coordinator specifies:**
- The exact input (record ID, signal ID, or synthetic data)
- The expected outcome (classification, action type, weight, entity, etc.)
- The expected mechanism (which code path should produce the result)

The mechanism matters. If a blocklist domain email gets caught by HTML detection instead, the blocklist feature is untested even though the output looks correct.

**Closed loop / feedback integration (when applicable):**

Single-input tests miss bugs in systems where the output of one invocation changes state that affects a later invocation. The Coordinator must enumerate which mechanisms have feedback loops at design time and add at least one closed-loop test per loop. Apply this dimension whenever the system under test:
- Writes back state derived from its outputs (learning systems, auto-apply, audit-driven config)
- Caches state that must reload to honor new writes (runtime config, in-memory dicts)
- Has a judge/reviewer that feeds decisions forward (LLM-as-judge auto-adopt, agent runtimes)
- Accumulates memory across calls (agent memory, conversation context)

Test shape (each closed-loop test is a sequence, not a single input):
1. Send input A through the system in a known initial state
2. Observe what state changed (new DB row, cache update, memory entry)
3. Force the system to reload (container restart, cache invalidate, fresh context) if the runtime caches the changed state
4. Send input B (similar to A, matching the new state) through the system
5. Verify input B is handled per the new state, NOT the old state — and via a different mechanism than the one that caught A

A closed-loop test PASSes only when the second-call mechanism differs as expected from the first-call mechanism, proving the state actually flowed from output to input.

Example: a learning noise filter — input A is caught by an LLM-audit code path, the audit auto-applies a rule, the container reloads, input B matching the same rule is now caught by the regex filter NOT by the LLM audit. Mechanism distinction confirms the loop closed.

If the closed-loop test PASSes, it composes proof for all the individual features in the chain (catch → suggest → write → reload → fire) without needing separate sign-offs on each.

**Domain-specific examples:**
- For classification: one input per class + 3 that should remain the default class + 2 borderline
- For entity creation: 3 input sets that should produce entities, 3 that shouldn't, 2 that are borderline threshold + 1 closed-loop test where the proposer's adopted entity affects the next input's routing
- For dedup: 2 near-duplicates, 2 distinct items, 2 items that share keywords but differ in meaning
- For learning / audit-driven config: 1-2 closed-loop sequences (catch → auto-apply → reload → re-fire via the new rule)

Write the full test matrix into the bracket's validation plan. The Verifier receives these inputs with expected outcomes, not carte blanche to choose its own.

### Retroactive validation mode

When validating already-signed-off phases (no Worker needed):
1. Skip the Worker dispatch entirely
2. Coordinator designs the test matrix against the feature inventory in the plan
3. Verifier runs the matrix against the deployed system
4. Coordinator compares results to the plan's claimed status
5. Features that fail under multi-dimensional testing get downgraded regardless of prior sign-off

**Side-effect awareness.** Retroactive validation is NOT automatically read-only. Production code may have write side effects that fire during testing:
- LLM audit / scoring functions may write suggestions back to DB and auto-apply high-confidence ones
- Caching layers may update on read paths
- Metric counters may increment per invocation
- Async workers may trigger downstream pipelines from observed inputs

Before dispatching, the Coordinator must audit any function the Verifier will call for write side effects. Either:
1. Add explicit anti-scope to the bracket: "no auto-apply, no rule writes, no counter increments" — and instruct the Verifier to skip side-effect-bearing calls
2. Wrap the call in a dry-run / no-write mode if the code supports it (e.g., `dry_run=True` kwargs)
3. Accept the side effects with eyes open and document them in the bracket's "expected production writes" section, plus a cleanup plan to revert them after testing

A retroactive test that creates production state is no longer a retroactive test — it is an unintentional Worker dispatch.

## Team setup

Create a team with two members:

```
TeamCreate: "QA Coordination - {pipeline stage}"
  Worker: implements changes, deploys, reports actions
  Verifier: tests with pre-selected inputs, reports I/O evidence
```

### Model selection

**Prefer** model diversity between Worker and Verifier to prevent correlated blind spots:
- **Worker:** `sonnet` for straightforward code changes, `opus` for complex logic
- **Verifier:** preferably a different model than the Worker (if Worker is sonnet, Verifier is opus; if Worker is opus, Verifier is sonnet)

If model diversity is not available (only one model accessible, or budget constraints), the actor-judge separation still provides value via the architectural role split alone — multi-agent collaboration research has shown the effect can be achieved with a single model trained to disagree. The role split is the structural fix; model diversity is a refinement, not a hard requirement.

If you skip model diversity, document the reason in the team config (e.g., "single model — budget").

### Worker isolation

The Worker modifies code. If it targets a git repository, dispatch it with `isolation: "worktree"` so it gets an isolated copy. The Worker commits to its worktree branch. The Coordinator merges or cherry-picks after the Verifier passes.

For sequential loops (one Worker at a time), a single worktree suffices. For parallel Workers (multiple features simultaneously), each Worker needs its own worktree.

### Stop-signal protocol

If the user sends a stop signal at any point (see your CLAUDE.md "Stop Signals" list), immediately:
1. Halt the Worker (SendMessage with "STOP. Do not continue.")
2. Halt the Verifier if running
3. Summarize current state: what the Worker changed, what the Verifier found (if anything), where the loop is
4. Ask the user what to do via AskUserQuestion

Do NOT send "one more fix" to the Worker. Do NOT let a running Verifier finish "since it's almost done." Stop means stop.

### Messaging discipline

Every Coordinator → Worker or Coordinator → Verifier message that authorizes more work must include an **explicit imperative**, not just permission. Agents go idle after their turn ends; permission-style messages get acknowledged and then ignored.

Bad: "Proceed with tests #4-15." "You may continue." "Authorization granted."
Good: "Begin running tests #4-15 now." "Start the next batch immediately." "Execute step 3 now."

Each message should specify:
1. The verb (begin, execute, run, start, dispatch)
2. The exact scope (tests #4-15, step 3, the next feature)
3. The expected return condition (when done, send final summary)
4. Any constraints carried forward (no batch >8, no fixes, no new tests)

If the agent goes idle without continuing within one turn, re-send with a sharper imperative. Do not assume the previous "proceed" was sufficient.

## Dispatch: Worker

**Pre-dispatch plan re-read (mandatory).** Before composing the Worker prompt, re-read the plan's Decision Log and the bracket's anti-scope. Extract the current anti-scope entries verbatim from the plan file, not from conversation memory or a previous dispatch prompt. A mid-session plan correction does not propagate to Worker prompts unless you explicitly re-read.

Send the Worker the task with the template from `references/worker-prompt.md`.

**Critical constraints in every Worker prompt:**
1. The bracket's surface and anti-scope sections (Worker cannot edit outside surface)
2. Explicit prohibition: "Do NOT use the words 'validated', 'verified', 'working', 'complete', or 'confirmed' in your report. Report only what you changed and where."
3. The specific task from the plan
4. Relevant code context (file paths, function names, current behavior)
5. Environment declaration

**The Worker commits code but does NOT deploy.** Deployment is the Coordinator's responsibility (via the project's deploy procedure). This separates the "code change" surface from the "deploy" surface, so the Verifier tests against a known deployment state, not a Worker's self-reported deploy.

**Worker report format:**
```
## Changes made
- [file:line] changed [what] from [old] to [new]
- Commit: [hash] on branch [branch]

## What I changed (for Verifier)
- [plain description of the behavioral change the Verifier should test]
```

The Worker sends this report back via SendMessage. It does NOT include any assessment of whether the change works.

**Coordinator deploys after Worker reports.** Merge/cherry-pick the Worker's commit, deploy using the project's deploy procedure, confirm the runtime is running the new code. Then dispatch the Verifier.

## Dispatch: Verifier

After the Worker reports, send the Verifier the task with the template from `references/verifier-prompt.md`.

**Critical constraints in every Verifier prompt:**
1. The Worker's change description (what behavioral change to test)
2. The pre-selected test inputs from the bracket's validation plan
3. The expected behavior per spec/plan
4. Explicit prohibition: "Do NOT suggest fixes, implement changes, or interpret results beyond I/O comparison. Report only what you observed."
5. Maximum test scope: 1-3 inputs per feature. No batch processing, no full corpus, no pipeline-wide testing.

**Note on I/O-only strictness:** The "no interpretation beyond I/O comparison" rule is stricter than the empirically optimal point per the literature (VeriLA, ACC-Collab) — those approaches allow directional Verifier feedback. We keep the stricter rule because the specific failure mode is premature completion via Verifier-drifts-toward-implementer; the strictness blocks that drift. Revisit this rule if Verifier signal feels thin in practice — directional feedback may be allowable on a per-bracket basis.

**Verifier report format:**
```
## Verification Report - {feature}

### Test 1: {test name}
- **Input:** {exact input sent}
- **Expected:** {expected output per spec}
- **Observed:** {actual output, verbatim}
- **Result:** PASS | FAIL

### Test 2: ...

## Summary
- Tests run: N
- Passed: X
- Failed: Y
- Evidence quality: [I/O proof | smoke test only | inconclusive]
```

The Verifier does NOT say "the fix works" or "the feature is validated." It reports I/O pairs and pass/fail per test.

## Coordinator decision

After receiving the Verifier report, you (Coordinator) decide:

### PASS (all tests pass with I/O proof)
1. Log the result to the project log immediately (do not defer to handoff). Include: feature name, test count, pass/fail, commit hash.
2. Update the plan file and bracket progress
3. Move to the next pipeline stage or feature
4. Report to user: "Phase X verified. {N} tests passed with I/O proof. Moving to Phase Y."

### FAIL (any test fails)
1. Extract the specific failure evidence from the Verifier report
2. Send the failure evidence to the Worker: "Test {N} failed. Input: {X}. Expected: {Y}. Got: {Z}. Fix this specific discrepancy."
3. Worker revises and re-deploys
4. Verifier re-tests the same inputs
5. Track revision count per feature

### ESCALATE (2 failed revisions on same feature)
1. Stop the team
2. Present the full evidence chain to the user:
   - What was tried (Worker reports x2)
   - What failed (Verifier reports x2)
   - The specific I/O discrepancy that persists
3. Ask the user via AskUserQuestion in recommend-default format: "This feature has failed verification twice. The persistent issue is {description}. I recommend {one option} because {reason}. Override?"

### METHODOLOGY ISSUE (Verifier finds upstream problem)
1. Stop the team
2. Present the finding: "The Verifier found that the test failure is not a code bug but a {spec gap | upstream data quality issue | design flaw}: {description}"
3. Do NOT work around it. Do NOT tune prompts, add guards, or adjust thresholds as a substitute for fixing the methodology.
4. Ask the user what to do.

## Scope control

You (Coordinator) are the only agent that can expand scope. The rules:

1. **Worker requests scope expansion:** "I need to also modify {file} to fix this." → Check against bracket surface. If outside, ask user before approving.
2. **Verifier discovers adjacent issue:** "Test passed but I noticed {other problem}." → Log it. Do NOT route it to the Worker. Present to user as a separate finding after the current loop completes.
3. **Full-corpus evaluation:** Neither Worker nor Verifier can escalate to full-corpus testing. If the Verifier's 1-3 tests pass, the feature is verified. Full pipeline testing is a separate activity the user requests explicitly.

## Session management

### Progressive logging
After each PASS decision, log immediately to the project log (do not batch to end of session). Format:
```
- **QA-coord PASS: {feature}** — {N} tests passed. Commit {hash}. Verifier: {model}. Tests: {input1 → PASS, input2 → PASS}.
```
If context compacts mid-session, the project log preserves what was verified. Do not rely on conversation history for this.

### Progress tracking
Update the plan file after each Verifier pass. Track:
- Pipeline stages completed
- Features verified (with I/O evidence links)
- Revision counts per feature
- Methodology issues surfaced

### Multiple stages in one session
After completing a stage, present status: "Stage {N} verified ({X} features, {Y} tests). Next stage: {N+1} ({description}). Continue?"

Chain directly unless the next stage has a different bracket surface (requires re-bracketing).

### Team cleanup
Delete the team when:
- All stages for this session are complete (normal completion)
- The user sends a stop signal (after summarizing state)
- Escalation halts the loop (after presenting evidence to user)

Do not leave orphaned teams running.

### Handoff
When the session ends (user stops, context filling, natural completion):
1. Update the plan with current state
2. Invoke `/log-work` with verified stages and outstanding work
3. Create PIC if work remains via `/create-note PIC`

## What this skill does NOT do

- **Replace `/implement` for non-pipeline work.** UI features, config changes, CRUD, and documentation use `/implement` directly. QA-coord is for pipeline stages where data quality is the deliverable.
- **Run automated test suites.** The Verifier runs manual I/O checks. Automated regression is separate tooling.
- **Manage the plan itself.** The plan defines what to build. This skill governs how the agents building it coordinate and verify.
