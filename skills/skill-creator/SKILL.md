---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator — Router

This skill has three modes. Classify the user's request, load the appropriate reference file, and follow it.

## Mode Classification

Determine which mode the user needs:

1. **Create** — The user wants to build a new skill or substantially rewrite an existing one. Signals: "make a skill", "turn this into a skill", "create a skill for X", "I want a skill that does Y", editing/rewriting skill instructions.
2. **Eval** — The user wants to test a skill, run benchmarks, review outputs, or iterate on improvements based on test results. Signals: "run evals", "test this skill", "how does it perform", "let's iterate", "run the test cases", providing feedback on eval outputs.
3. **Optimize** — The user wants to improve triggering accuracy, package a skill, or back it up. Signals: "optimize the description", "it's not triggering", "package this", "push to GitHub", "back up this skill".

If the mode is ambiguous, ask the user one clarifying question with numbered options.

## Dispatch

After classification, read the corresponding reference file and follow its instructions:

- **Create** → Read `references/skill-create.md` and follow it
- **Eval** → Read `references/skill-eval.md` and follow it
- **Optimize** → Read `references/skill-optimize.md` and follow it

## Routing Manifest

On entry, write a routing manifest to `/tmp/routing-manifest-skill-creator-{timestamp}.json`:
```json
{
  "router": "skill-creator",
  "mode": "<create|eval|optimize>",
  "expected": ["<selected-mode>"],
  "completed": [],
  "timestamp": "..."
}
```

When the selected mode's flow completes, mark it completed in the manifest and verify no expected steps were skipped. Delete the manifest on success.

## Cross-Mode Handoffs

The modes often chain naturally:
- After **create**, the user often wants to **eval**
- After **eval** iterations stabilize, the user often wants to **optimize**
- After **optimize**, back up via `/update-skills push <skill-name>`

When one mode completes, check if the user wants to continue to the next natural mode. Don't assume — ask.

## Communicating with the User

Pay attention to context cues about the user's technical familiarity. Terms like "evaluation" and "benchmark" are fine for most users. For "JSON", "assertion", or technical jargon, look for cues that the user knows what those are before using them without explanation. Briefly explain terms if in doubt.

## Reference Files

- `references/skill-create.md` — Full create flow: intent capture, interview, writing, post-generation checks
- `references/skill-eval.md` — Full eval flow: test runs, grading, benchmarking, iteration loop
- `references/skill-optimize.md` — Description optimization, packaging, GitHub backup
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.

## Agent Files

- `agents/grader.md` — Assertion evaluation against outputs
- `agents/comparator.md` — Blind A/B comparison
- `agents/analyzer.md` — Benchmark analysis and pattern detection
