# Worker Dispatch Template

Customize per task. Keep worker prompts focused — inject only the checklists relevant to the task type.

## Template

```
You are **{worker_name}** executing {task_id}: {task_title}.

Report ALL status updates to the team lead (orchestrator). When you start, hit a blocker, or finish — message the team lead directly.

## Context (read before coding)
- Plan: {plan_path} (section: {phase})
- Spec: {spec_path}
- Lessons: {lessons_path}
{additional_context}

## Environment
{environment_block — only for {{ORG}} app tasks, injected by orchestrator}

## Git Safety
Read `~/.claude/skills/git-safe/SKILL.md` before any git operation.

## Tasks
{task_details}

## When Done -- Fix Verification Contract

Before reporting completion, answer each applicable item with specific evidence:

1. **Deployed and running:** Commit hash + container created after push + health check 200.
2. **New code path exercised:** Which counter/log/DB write proves the new code ran?
   "Reproducer passed" is insufficient if new code is a retry or error-handling branch.
3. **Synthetic injection (if transient fix):** If natural reproducer fired 0 times on your
   new counter/branch, inject a synthetic failure. Cite counter output.
4. **Sibling sweep (if pattern fix):** Grep showing no other module carries the same pattern.

Report: "{task_id} complete. [Summary]. Commit: {hash}. Verification: [evidence]."
For {{ORG}} tasks, add: "Environment: {env}. Verified at: {url}."
If your task produced a written artifact, prefix it `ARE -` and save to `<project>/reports/YYYY-MM-DD/`

Source: MQ-9, MQ-20, MQ-21, RC-6 (marathon postmortem). Pattern 5: deploy != verify.
```

## Model Selection

| Task Type | Model |
|-----------|-------|
| Complex engineering, new services, rewrites | opus |
| VPS/infra ops, deploys, migrations | opus |
| File migration, scripting, mechanical | sonnet |
| Documentation, reports | sonnet |
| Quick lookups | haiku |

## Conditional Protocols

Inject into the worker prompt based on task type. Only load what's relevant.

### Halt Response (inject when task has deploy/DB/schema steps)

```
## If You Receive a Halt Directive

1. **Checkpoint:** Last completed action (specific file:line or SQL statement).
2. **Stateful changes:** Enumerate DB writes, branch pushes, builds, deploys, migrations.
3. **Per-change:** KEEP (rationale) / REVERT (command) / FLAG (follow-up).
   Do NOT auto-revert production state without team lead approval.
```

Source: MQ-18 (Round 5 halt incident, init 74/82 contamination).

### Degraded-Mode (inject when task >10 min or uses external tool)

```
## If Your Primary Data Source Fails

1. Ship whatever results you have, flagged [primary] vs [partial].
2. Preserve resumption handles in frontmatter (task_ids, offsets, session_ids).
3. Report: "DEGRADED: [what failed], [shipped], [remains unknown], [handles preserved]."
```

Source: MQ-19 (NLM MCP disconnect, 15 min silent polling).

## Conditional Checklists

Inject these into the worker prompt based on task type. Only load what's relevant.

| Task touches... | Inject |
|-----------------|--------|
| VPS deploy | `references/checklists/deploy.md` |
| Frontend UI (Next.js, basePath, AG Grid) | `references/checklists/frontend.md` |
| Database (queries, migrations, schema) | `references/checklists/db.md` |
| Auth, sessions, middleware | `references/security-eval.md` (for orchestrator review, not worker) |

## Environment Block ({{ORG}} Apps Only)

Before dispatching a {{ORG}} worker, determine and inject:

```
## Environment (set by orchestrator)
target: [LOCAL | REMOTE | BOTH]
verification_url: <exact URL>
deploy_method: flora-deploy <service> | safe-build <service> --pull | none

Push != Deploy. As of 2026-04-07, git push does NOT auto-deploy. You MUST run the deploy
method above after pushing. Reporting "deployed" without deploying is wrong.
```

If the target is ambiguous from the task description, STOP and ask the user before dispatching.
