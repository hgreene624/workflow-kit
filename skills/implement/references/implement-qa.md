# Implement — QA Protocols

QA verification protocols for the implement skill. Referenced by `implement-execute.md` during user testing gates.

## Playwright QA Verification (Pre-Gate — MANDATORY)

Before presenting a user testing gate, the QA auditor MUST run the **crawl-based audit** against the deployed service. This auto-discovers ALL pages by following nav links, catches client-side exceptions, and takes screenshots — no manual route list needed.

The monorepo includes two QA tools at `tests/qa/`:

### 1. Crawl-based audit (primary — catches all pages)

```bash
pnpm exec playwright test tests/qa/crawl-audit.spec.ts --project=chromium -g "<service>"
```
- Auto-discovers pages by following nav/sidebar links
- Screenshots every page + checks for JS console errors and "Application error" crashes
- Results saved to `tests/qa/results/crawl/<service>/results.json`
- **This is what catches sub-page crashes** that health endpoints miss

### 2. Static screenshot suite (secondary — quick spot-checks)

```bash
pnpm exec playwright test tests/qa/screenshots.spec.ts --project=chromium -g "<service>"
```

### Auth State

Both tools default to **authenticated mode** (saved Entra auth state). Fallback: `QA_MODE=internal` uses SSH tunnels.

Auth state at `tests/qa/.auth-state.json`. If expired, ask user to refresh via `./scripts/qa-auth-setup.sh`.

## QA Workflow Sequence

This sequence enforces generator-evaluator separation — workers generate, QA auditor evaluates independently:

1. **Worker deploys** the service change
2. **Worker runs crawl audit** — first-pass check from the implementer's perspective
3. **PM requests QA auditor phase audit** — QA auditor is independent from the worker
4. **QA auditor runs independent crawl audit** — fresh eyes, no knowledge of what the worker claims to have fixed
5. **QA reports to orchestrator** — pass/fail with evidence
6. **Orchestrator presents user test gate** — only after QA passes

## Per-Task Acceptance Criteria Verification

When the plan includes an **Acceptance Criteria** column in task tables (mandatory for plans created after 2026-03-26), the QA auditor verifies each completed task against its criteria — not just at phase boundaries.

### Protocol

1. When PM reports a task as complete, QA auditor reads the task's acceptance criteria from the plan
2. For criteria with UI/API checks: QA auditor independently runs the verification (curl, Playwright, query) — does NOT trust the worker's self-report
3. For criteria that are code-structural (e.g., "function exists", "test passes"): QA auditor greps/runs the check
4. QA reports per-task pass/fail to orchestrator. Failed criteria → worker gets concrete feedback on what to fix

This is the generator-evaluator separation: workers generate, QA auditor evaluates against the contract (acceptance criteria) defined before work began.
