---
name: troubleshoot
description: "Systematic diagnostic protocol for when you're stuck on ANY issue — VPS, Docker, Traefik routing, database schemas, frontend/UI rendering, backend APIs, authentication, deployment, LLM pipelines, or third-party integrations. MUST be invoked after 2 consecutive failed fix attempts on the same issue — do NOT wait for the user to ask. Also invoke when the user says 'troubleshoot', 'you're stuck', 'you're going in circles', 'why isn't this working', 'try again properly', or expresses frustration with repeated failures. This skill dispatches a diagnostic agent that verifies assumptions, consults lessons learned, and gathers evidence before any more fixes are attempted. Use this BEFORE trying another fix."
---

# Troubleshoot

A circuit-breaker skill that stops fix-attempt spirals and forces systematic diagnosis across all systems.

## HARD GATE — Auto-Trigger Protocol

This is NOT advisory. This is a circuit breaker that MUST fire automatically.

**Definition of "failed attempt":** Any of these:
- User says the feature doesn't work, isn't visible, or didn't change
- User sends a screenshot showing the old state
- User says "still not working", "doesn't work", "nothing changed", "I don't see it"
- You curl/test the endpoint and it doesn't show your changes
- An API returns empty results or 404 and you accepted it without verifying the query was correct
- User challenges your conclusion ("I think those meetings do have transcripts", "the data is there")

**The rule:** After 2 consecutive failed attempts on the SAME issue, you MUST:
1. STOP attempting fixes immediately
2. Tell the user: "Two attempts have failed. Invoking diagnostic protocol before trying again."
3. Execute the full diagnostic protocol below
4. Do NOT skip this to "try one more quick thing"

**Why this exists:** On 2026-03-18 alone, there were 8 instances of circular debugging — Claude kept deploying fixes and telling the user "try now" 3-4 times before the user had to manually invoke /troubleshoot. This wastes the user's time and erodes trust.

**Failure to auto-trigger is itself a failure.** If the user has to manually invoke /troubleshoot, the auto-trigger system failed.

## When This Fires

**Auto-trigger (MANDATORY):** After 2 consecutive failed attempts to fix the same issue, STOP and invoke this skill before trying a third fix. A "failed attempt" is any fix that the user reports didn't work, or that you can verify didn't work.

**Manual trigger:** User says `/troubleshoot` or expresses frustration with repeated failures.

## Step 1: Freeze

Stop all fix attempts immediately. Do not try "one more quick thing." The pattern of trying variations of the same approach is exactly what this skill exists to break.

## Step 2: Classify the Problem Domain

Identify which domain(s) the issue touches. Read the corresponding reference file(s) from `references/` for domain-specific diagnostic steps, common failures, and commands:

| If the issue involves... | Read reference file |
|---|---|
| URL routing, containers, Docker, Traefik, deploys | `references/vps-docker.md` |
| Database queries, schemas, PostgreSQL, SQLite | `references/database.md` |
| UI rendering, CSS, SvelteKit, Next.js, browser behavior | `references/frontend.md` |
| API endpoints, FastAPI, Flask, Express, pipeline | `references/backend-api.md` |
| Login, OAuth, ForwardAuth, Entra ID, permissions | `references/auth.md` |
| Git, deployment workflow, container rebuilds | `references/deployment.md` |
| LLM prompts, signal engine, classifiers, quality | `references/llm-pipeline.md` |
| MS Graph, Telegram, reservations, external services | `references/integrations.md` |
| Obsidian config, vault setup, plugins, workspace layout | `references/obsidian.md` |
| URL → container mapping | Run `ssh <YOUR_VPS> whichcontainer <path>` (primary), or see `references/routing-map.md` (fallback) |
| Which lessons files to load | `references/lessons-map.md` |

Most issues touch multiple domains — read all relevant files.

## Step 3: Dispatch Diagnostic Agent

Spawn a diagnostic agent using the team workflow (TeamCreate → TaskCreate → Agent with team_name) so it appears in a tmux pane. The agent gets the full conversation context.

**Agent prompt:**

Read `references/diagnostic-protocol.md` and use it as the agent prompt.

## Step 4: Act on the Diagnosis

1. Review the diagnostic agent's findings
2. If the diagnosis reveals a wrong target: say so explicitly to the user
3. Implement the proposed fix

## Step 4.5: Independent Fix Verification

**The agent that implemented the fix must NOT be the one that verifies it.** This is the generator-evaluator separation principle — the generator rationalizes its own output.

Spawn a **fix-verifier agent** (separate context, fresh eyes) with:
- The diagnostic agent's root cause analysis
- The specific fix that was applied
- The verification plan from the diagnosis

The fix-verifier agent:
1. Executes the verification plan independently — does NOT read the fix agent's "it works" claim
2. **Shows proof BEFORE reporting success:**
   - For UI changes: take a Playwright screenshot showing the feature works
   - **After taking the screenshot: `scp` it locally and run `open <path>` to display it in Preview on the user's desktop.** Do not just describe what you see — show them directly.
   - For API changes: show curl output with expected response
   - For data changes: show query results confirming the fix
3. Reports pass/fail to you (the orchestrator)
4. If FAIL: the fix-verifier explains what's still broken with evidence. Do NOT re-dispatch the same fix agent — go back to Step 3 (fresh diagnostic) with the new evidence.

**"Try now" without independent verification is not acceptable** — it's what caused the circular debugging pattern.

### Authenticated vs Container-Direct Verification (CRITICAL)

**Testing from inside the container (docker exec, container IP) bypasses Traefik and ForwardAuth entirely.** It proves the app renders but NOT that the user can access it. For any ForwardAuth-protected app, you MUST also verify through the authenticated path:

1. Get a valid session cookie from `auth.sessions`
2. Use Playwright with that cookie to load the real `YOUR_DOMAIN/<path>` URL
3. Check for 403s (missing permissions), 302s on static assets (auth blocking CSS/JS), and client-side fetch failures (missing basePath prefix)
4. See `references/frontend.md` section 2b for the full authenticated browser simulation procedure

**Container-direct screenshot = "the app works." Authenticated screenshot = "the user can see it."** Both are required. Today's revenue dashboard shipped with a working app behind a 403 wall because we only verified container-direct.

## Step 5: Capture Lessons

After the fix is verified, evaluate whether a new lesson should be captured using `/learn`. The diagnostic process often reveals gaps in the lessons files.

## Key Principles

- **Evidence over assumptions.** "It should work" is not evidence.
- **Verify the target first.** One `grep` is cheaper than 5 failed deploys.
- **Screenshots are mandatory for UI issues.** Never declare a UI fix complete without visual proof.
- **Lessons exist for a reason.** If a lessons file covers your scenario, follow it.
- **Stop the spiral.** If you feel the urge to "just try one more thing," run the diagnostic protocol instead.

## Local Customizations

If `LOCAL.md` exists in this skill directory, load and follow it after these instructions. Local instructions override upstream where they conflict.
