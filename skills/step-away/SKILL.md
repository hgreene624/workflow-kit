---
name: step-away
description: Autonomous sprint mode — user is stepping away and wants work to continue without them. Replaces all user test gates with QA auditor verification, removes soak periods, and sets up Telegram escalation for blockers. Use this skill whenever the user says "step away", "stepping away", "I'm leaving", "run without me", "autonomous mode", "don't wait for me", "keep going without me", "I'll check later", "don't stop working", or any indication they want to leave while an active /implement sprint continues. Also trigger when the user says /step-away. This skill ONLY works during an active implementation sprint with a team (pm-tracker, qa-auditor, workers) — if no team is running, tell the user to start /implement first. Detection: look for any active team containing pm-tracker and qa-auditor roles, regardless of how the team was created (direct /implement or via the implement router's sub-skills like implement-setup).
---

# Step Away — Autonomous Sprint Mode

When the user steps away during an active implementation sprint, this skill transitions the team to fully autonomous operation. No work stops. Quality gates shift from user verification to QA auditor verification. The user does one final review when they return.

## Why This Exists

Implementation sprints (run via `/implement`) have user test gates after every deploy — the user manually checks URLs, confirms pages render, verifies data. When the user needs to step away (meeting, sleep, errands), these gates become blockers that halt all progress. This skill removes those blockers by promoting the QA auditor to handle verification, while preserving a safety net (Telegram escalation) for genuine blockers that need human judgment.

## Prerequisites

- An active implementation team must be running with pm-tracker, qa-auditor, and workers. The team may have been created by `/implement` directly or by one of its sub-skills (e.g., implement-setup). Detection: check for any active team containing `pm-tracker` and `qa-auditor` teammates — the team name pattern is `{plan-name}-{sprint}`.
- The `/chawdys` skill must be available for Telegram escalation
- If no team exists, tell the user: "No active implementation team found. Run `/implement` first to start a sprint, then `/step-away` when you're ready to leave."

## Step 1 — Notify PM Tracker

Send this message to `pm-tracker`:

```
**PROTOCOL CHANGE — Step-Away Mode Active**

1. All user test gates are removed. Do NOT escalate to team-lead for user verification.
2. QA auditor replaces user gates. When a worker hits what would be a user test gate, message `qa-auditor` with the verification checklist instead.
3. If QA auditor finds issues → relay to the worker to fix. Iterate.
4. If stuck after 3 failed fix attempts on the same issue → escalate to team-lead for Telegram notification.
5. No soak periods. Chain phases immediately after QA auditor passes the gate.
6. User will do a single final review after sprint completes.
```

## Step 2 — Expand QA Auditor Role

Send this message to `qa-auditor`:

```
**EXPANDED ROLE — You now own ALL quality gates.**

User is away. Every gate that would normally require user verification now goes through you instead.

When PM triggers a quality gate check:

1. **HTTP verification** — `curl -sf <url>` for each URL in the gate checklist. Check for 200 status. Flag non-200 or connection failures.

2. **Content verification** — `curl -s <url> | head -200` and check that:
   - Response is HTML (not a JSON error or stack trace)
   - Page title or key headings are present (not a blank/error page)
   - Key data elements exist (e.g., table rows, list items, bucket names)
   - No "500", "Internal Server Error", "NEXT_REDIRECT", or framework error pages

3. **Routing regression checks** — After any Traefik change, verify at least 3 other services still respond:
   - `curl -sf https://<YOUR_DOMAIN>/ -o /dev/null && echo OK || echo FAIL`
   - `curl -sf https://hub.<YOUR_DOMAIN>/ -o /dev/null && echo OK || echo FAIL`
   - `curl -sf https://admin.<YOUR_DOMAIN>/ -o /dev/null && echo OK || echo FAIL`

4. **Container health** — `ssh <YOUR_VPS> "docker ps --format '{{.Names}}\t{{.Status}}'" | grep -E 'unhealthy|Restarting|Exited'`

5. **Report format** — Send PM a structured pass/fail:
   ```
   QA GATE: [phase/task name]
   - URL checks: PASS/FAIL (details)
   - Content checks: PASS/FAIL (details)
   - Regression checks: PASS/FAIL (details)
   - Container health: PASS/FAIL (details)
   VERDICT: PASS / FAIL (specific failures listed)
   ```

If FAIL: PM tells worker to fix, then re-triggers you. Iterate until PASS.
If 3 consecutive FAILs on the same issue: PM escalates to team-lead.

### Known Limitation: Auth-Protected Pages

All Flora apps use ForwardAuth via Traefik. Unauthenticated `curl` requests return 302 redirects, not page content. This means you CANNOT verify:
- Page content renders correctly (DOM-level check)
- Data is present in the UI
- JavaScript interactions work
- No client-side errors

**Mitigation:** If the app exposes `/api/health/content` (recommended pattern from R3), use it to verify data connectivity:
```bash
ssh <YOUR_VPS> "curl -sf http://localhost:<port>/api/health/content | python3 -c 'import json,sys; d=json.load(sys.stdin); print(f\"db: {d.get(\"db_connected\")}, records: {d.get(\"sample_data\",{}).get(\"count\",0)}\")'"
```
This checks that the app can read from its database and has data — partial but meaningful verification without browser access. If the endpoint does not exist, note "content verification not possible — no /api/health/content endpoint" in your report. Do NOT report PASS for content checks you cannot perform.
```

## Step 3 — Notify Active Workers

Send to all active workers (or broadcast `*`):

```
Protocol change: user test gates are now QA auditor gates. When you complete a deploy task, report to pm-tracker as normal. PM will route verification to the QA auditor instead of the user. Do not wait for user confirmation — continue working as soon as PM clears you.
```

## Step 4 — Set Escalation Protocol

The orchestrator (team-lead) must remember this escalation path.

**Pre-flight check (MANDATORY before confirming step-away mode):** Verify the Telegram path works by sending a test message NOW, before the user leaves:

```
/chawdys send Step-away mode activated. Test notification — if you see this, Telegram escalation is working.
```

If the message fails to send (Chawdys down, webhook broken, etc.), tell the user: "Telegram escalation is not working. If you step away, blocker notifications will only be visible in the conversation when you return." Let the user decide whether to proceed.

**When PM reports "3 failed attempts, escalating":**

1. Gather context: what's broken, what was tried (3 attempts), what specific input is needed from the user
2. Send Telegram via the `/chawdys` skill:
   ```
   /chawdys send Sprint 5 blocker — [service name] deploy failed after 3 fix attempts.

   What's broken: [specific symptom]
   What was tried: [attempt 1], [attempt 2], [attempt 3]
   What we need: [specific user input or decision required]

   Sprint is paused on this item. Other work continues if possible.
   ```
3. If the blocker is isolated to one phase, continue other independent work
4. If the blocker affects all downstream work, pause the sprint and note it for the handoff report

## Step 5 — Queue Final Review

When the sprint completes (all phases Done, all QG gates passed by auditor):

1. Compile a **User Review Checklist** with every URL/service that was deployed or modified:

```markdown
## Sprint [N] — User Review Checklist

### Services Deployed
| Service | URL | QA Auditor Result | Notes |
|---------|-----|-------------------|-------|
| [name] | [url] | PASS (date) | [any caveats] |

### Verification Steps
- [ ] [URL] — [what to check]
- [ ] [URL] — [what to check]
- [ ] Admin panel migration page — all statuses correct

### Issues Found and Fixed During Sprint
| Issue | Fix | Confidence |
|-------|-----|------------|
| [what broke] | [what was done] | High/Medium/Low |

### Items Requiring User Decision
- [any deferred decisions or edge cases]
```

2. Present this checklist when the user returns (either in conversation or saved to the daily note)
3. Do NOT mark the sprint as fully complete until user confirms — mark it as "QA-complete, pending user review"

## Reverting Step-Away Mode

If the user returns mid-sprint ("I'm back", "what's the status"), revert to normal protocol:
- Re-enable user test gates for remaining work
- Present current status + the partial review checklist
- QA auditor returns to standard audit posture

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
