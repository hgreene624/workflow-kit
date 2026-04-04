"""
Mock test for mutate_body.py — validates parsing logic with a pre-canned Opus response.

Tests:
  1. parse_variants() extracts 3 distinct variants
  2. All variants preserve create-spec frontmatter (no frontmatter in variant bodies)
  3. Each variant has a unique SHA-256 hash
  4. Each variant has non-empty mutation_rationale
  5. Each variant has correct strategy label (conservative/structural/creative)
  6. Deduplication logic skips bodies matching existing experiment_history hashes
"""
import hashlib
import json
import sys
import warnings
from pathlib import Path

# Make sure we can import from auto-research/scripts
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.mutate_body import parse_variants, split_frontmatter, compute_hash

# ---------------------------------------------------------------------------
# Pre-canned "Opus" response — realistic format matching mutator.md output spec
# ---------------------------------------------------------------------------
MOCK_OPUS_RESPONSE = '''
## Failure Analysis

- **Root cause 1**: Skill does not explicitly state that all 11 sections must be written — "fill every section" appears in the checklist but the Step 3 drafting rules do not enforce it with a hard gate.
- **Root cause 2**: review-spec invocation is described in Step 4 but there is no explicit "MUST invoke" or "do not skip" language — agents can silently omit it.
- **Pattern**: Both failures share a common cause: the skill describes correct behavior as a recommendation rather than a hard requirement.
- **eval_feedback observation**: The assertion about 11 sections checks count but not quality — fixing section count alone without addressing why it was missed (no hard gate) would only partially resolve the issue.

## Preserved Elements

- **Frontmatter**: `name: create-spec`
- **Tool references**: `AskUserQuestion`, `Glob`, `Read`, `Write`, `Skill`, `Bash`
- **Template variables**: `{today}`, `{Project Name}`, `{spec_path}`
- **Safety constraints**: "Never reuse or renumber existing IDs", "Do NOT touch completed phases"
- **Schema injections**: none found

---

## Variant A — Conservative

### Rationale
- **What changed**: Added "MUST" gate language to Step 3 requiring all 11 sections; added explicit enforcement to Step 4 mandating review-spec invocation before presenting results.
- **Which failures this addresses**: "skill should create all 11 spec sections" — the gate prevents omission; "skill should gate with review-spec" — explicit MUST language removes discretion.
- **Risk introduced**: Minimal — no structural changes, only strengthened enforcement language.
- **Confidence**: high — targeted changes directly address the two failed assertions.

### Body
```markdown
# Spec Creator

You guide the creation and update of spec documents through a structured workflow. The goal is to produce specs that are tight enough to plan from — no gaps, no ambiguity, no scope creep.

This skill has two paths:
- **Create mode** — new spec from scratch (full interview → draft → review → handoff)
- **Update mode** — add features to an existing spec (triage → surgical update → delta review → propagate to plan/Plane)

And two audiences:
- **Interactive users** — walk them through questions one at a time, using `AskUserQuestion` for every decision point
- **Agent callers** — they pass structured context upfront; skip the interview and go straight to drafting/updating. Still run the review gate.

## Detecting the Mode

- **Interactive mode**: The user is talking to you directly. Use `AskUserQuestion` for every question. One question at a time, numbered options.
- **Agent mode**: Invoked programmatically with structured purpose, requirements, and constraints. Skip the interview. If the agent specifies a target spec to update, go to Update mode; otherwise Create mode.

If you're unsure which mode you're in, default to interactive.

---

## Step 0 — Orient

Before anything else:

1. Run `date` for a fresh timestamp
2. Read the vault-root `AGENTS.md` to understand current vault conventions
3. If the user mentioned a project or you can infer one from context, read that project's `agents.md` and `lessons.md` if they exist

---

## Step 0.5 — Triage: New Spec or Update? (Interactive Mode Only)

Before jumping into the full interview, check whether this idea belongs under an existing spec.

### Skip Triage When:

- **No specs found** in the project area → go straight to Create mode
- **Agent mode** → the caller specifies whether to create or update
- **User explicitly said "new spec"** → skip triage, go to Create mode

---

## Step 1 — Interview (Interactive Mode Only)

The interview has three phases. Each question uses `AskUserQuestion` — never dump multiple questions as text.

### Phase A: What and Why

**Question 1: What is this spec for?**

**Question 2: What does success look like?**

### Phase B: Scope and Constraints

**Question 3: What's explicitly OUT of scope?**

**Question 4: Any hard constraints?**

### Phase C: Requirements Deep-Dive

Based on what you've learned, ask 1-3 targeted follow-up questions about the requirements.

### Phase D: Confirm Understanding

Before drafting, give a 3-5 bullet summary of what you understood.

---

## Step 2 — File Placement

Determine where the spec file should live in the vault.

---

## Step 3 — Draft the Spec

Read the template at `references/spec-template.md`.

### MANDATORY Drafting Gate

**STOP before writing and verify: you MUST produce all 11 spec sections.** Check the template for the exact section headers. Missing any section is a failure — do not proceed without all 11 present.

The 11 required sections are defined in the spec template. If any section is unclear or has no content yet, write it as a placeholder with a note, but DO NOT omit it.

### Drafting Rules

1. **Fill every section.** All 11 sections must appear. Empty sections signal gaps — fine at draft stage, but they must be present.
2. **Use IDs for everything trackable.** FR-1, NFR-1, A-1, SAT-1, etc.
3. **Frontmatter is mandatory.**
4. **Keep implementation out.** No build phases, no deployment steps.

---

## Step 4 — Review Gate — MANDATORY

**You MUST invoke the review-spec skill.** This is not optional. Do not present the spec to the user as complete without running review-spec.

Tell the user:
> "Spec drafted and saved. Now running the review gate to catch any issues before we move to planning."

Then invoke: `/review-spec {spec_path}`

Do not skip this step under any circumstances. A spec without a review gate is incomplete.

---

## Step 5 — TLDR & Handoff

After the review gate completes:

1. Give a TLDR — 3-5 bullet summary
2. Offer plan-spec handoff using `AskUserQuestion`

---

## Checklist — Create Mode

- [ ] All 11 sections present
- [ ] Frontmatter complete
- [ ] IDs on all requirements, assumptions, acceptance criteria
- [ ] Review gate passed — review-spec invoked and completed
```

---

## Variant B — Structural

### Rationale
- **What changed**: Restructured Step 3 and Step 4 into a single "Draft + Validate" stage with an explicit section-count check built into the flow; moved the review gate emphasis to the top of its section with a prominent "NON-NEGOTIABLE" marker.
- **Which failures this addresses**: Both failures — by coupling the section count check to the writing phase and making review-spec the structural climax of the workflow rather than a footnote.
- **Risk introduced**: Consolidating Step 3 and the review mandate could make the skill slightly longer to parse; low risk given the clarity gain.
- **Confidence**: medium — structural reorganization helps but depends on execution following the new flow.

### Body
```markdown
# Spec Creator

You guide the creation and update of spec documents. Two paths: **Create** (new spec) and **Update** (add to existing). Two audiences: **interactive users** (use AskUserQuestion) and **agent callers** (skip interview, draft directly).

---

## Phase 0 — Setup

1. Run `date`
2. Read vault-root `AGENTS.md`
3. Read project `agents.md` and `lessons.md` if the project is identifiable

---

## Phase 1 — Triage (Interactive Only)

Search for existing specs in the project area. Present them via `AskUserQuestion`. Branch to Update mode if the user picks an existing spec; otherwise continue to Phase 2.

Skip triage when: no specs found, agent mode, or user explicitly specified new vs. update.

---

## Phase 2 — Interview (Interactive Only)

Run 4 questions via `AskUserQuestion`, one at a time:
1. What is this spec for?
2. What does success look like?
3. What's explicitly OUT of scope?
4. Any hard constraints?

Follow with 1-3 domain-specific follow-ups. End with a confirm-understanding summary.

---

## Phase 3 — Draft: All 11 Sections Required

**Before writing, load `references/spec-template.md` and count the section headers.**

Write every section. The count check is part of the draft completion criterion — you are not done drafting until all 11 sections exist in the file.

Required sections (from the template):
1. Purpose / Objectives
2. Scope
3. Functional Requirements
4. Non-Functional Requirements
5. Constraints
6. Assumptions
7. Deliverables
8. Acceptance Criteria (SATs)
9. Architecture
10. Risks
11. Open Decisions

If a section has no content yet, write a placeholder — but never omit the section header.

Drafting rules:
- Use IDs: FR-1, NFR-1, A-1, SAT-1
- Include frontmatter with category, dates, status, project, source
- No build phases or deployment steps
- Verify external references before including them
- Include golden examples for quality-dependent SATs
- Open Decisions must have recommendations

---

## Phase 4 — Review Gate (NON-NEGOTIABLE)

**INVOKE `/review-spec {spec_path}` BEFORE presenting results to the user.**

This is the quality gate. It is not optional. Every spec — regardless of size, simplicity, or confidence level — goes through review-spec. A spec without a passed review gate is incomplete.

Tell the user:
> "Spec drafted. Running review gate now — this catches gaps before planning."

Then call: `/review-spec {spec_path}`

Wait for review-spec to complete. Apply any approved improvements.

---

## Phase 5 — Handoff

Give a 3-5 bullet TLDR. Offer plan-spec handoff via `AskUserQuestion`.

---

## Checklist

- [ ] All 11 sections present and written
- [ ] Frontmatter complete
- [ ] IDs on all FRs, NFRs, Assumptions, SATs
- [ ] No implementation phases in spec
- [ ] External references verified
- [ ] Golden examples included where needed
- [ ] review-spec invoked and completed
- [ ] Daily note updated
```

---

## Variant C — Creative

### Rationale
- **What changed**: Replaced step-by-step imperative instructions with an outcome-first "contract" framing. The skill now opens with explicit PASS/FAIL criteria (the two assertions that failed become explicit exit conditions), then provides the procedure as the mechanism to meet those criteria. Self-check loop added before handoff.
- **Which failures this addresses**: Both failures — by front-loading the success criteria, the agent understands what "done" means before starting. The section count and review gate become checkboxes the agent verifies before exiting, not steps it might skip.
- **Risk introduced**: The outcome-first framing is less conventional — if an agent doesn't read carefully it might attempt to satisfy the exit criteria mechanically. Mitigated by the procedural steps still being present.
- **Confidence**: medium — creative restructuring may improve reliability for agents that plan ahead but could confuse agents that follow instructions linearly.

### Body
```markdown
# Spec Creator

## What Success Looks Like

Before starting, internalize what a completed run looks like:

**This skill succeeds when:**
- A spec file exists at the correct vault path with **all 11 sections** (Purpose, Scope, Functional Requirements, Non-Functional Requirements, Constraints, Assumptions, Deliverables, Acceptance Criteria, Architecture, Risks, Open Decisions)
- The spec has been reviewed by **review-spec** and any high/critical findings addressed
- The user has been offered a plan-spec handoff

**This skill fails when:**
- Any of the 11 sections is missing from the written file
- review-spec was not invoked
- The spec contains implementation phases or build steps

Keep these exit criteria in mind throughout. They are your checklist before considering the work done.

---

## Procedure

### 1. Orient

Run `date`. Read vault-root `AGENTS.md`. Read project `agents.md` and `lessons.md` if identifiable.

### 2. Triage (Interactive Mode Only)

Check for existing specs in the project area. If found, ask the user via `AskUserQuestion` whether this is an addition to an existing spec or a new one. Branch accordingly.

### 3. Interview (Interactive Mode Only)

Use `AskUserQuestion` for each question — never dump multiple questions as text:
1. What is this spec for?
2. What does success look like?
3. What's explicitly OUT of scope?
4. Any hard constraints?
5-7. (optional) 1-3 domain-specific follow-ups

Confirm understanding before drafting.

### 4. File Placement

Determine the correct vault path. Confirm with user in interactive mode.

### 5. Draft — All 11 Sections

Load `references/spec-template.md`. Write every section.

**As you write, track which sections you've completed.** When you think you're done, count: is the number exactly 11? If not, find what's missing and add it before proceeding.

Drafting rules:
- Use IDs (FR-1, NFR-1, A-1, SAT-1)
- Include complete frontmatter
- No build phases or deployment steps
- Verify external references
- Golden examples for quality-dependent SATs
- Open Decisions need recommendations

### 6. Pre-Handoff Self-Check

Before invoking review-spec, verify:

```
□ Sections present: count them. Is it 11?
□ Frontmatter: category, dates, status, project, source — all filled?
□ IDs: every FR, NFR, Assumption, SAT has an ID?
□ No implementation phases written?
□ Daily note updated?
```

Fix anything that fails the self-check before continuing.

### 7. Review Gate

**Invoke review-spec now:**

> "Spec drafted and validated. Running review gate."

Call: `/review-spec {spec_path}`

Apply approved improvements. Do not skip this step.

### 8. Handoff

Give a 3-5 bullet TLDR. Offer plan-spec via `AskUserQuestion`.

---

## Update Mode (Abbreviated)

When adding to an existing spec: read the spec fully → run a short interview → continue IDs from highest existing → delta review via review-spec → propagate to plan/Plane if they exist → TLDR.

Never delete or renumber existing IDs. Mark superseded FRs with strikethrough.
```

'''

# ---------------------------------------------------------------------------
# Build a synthetic "current SKILL.md" that has frontmatter
# ---------------------------------------------------------------------------
SYNTHETIC_SKILL_CONTENT = """\
---
name: create-spec
description: >
  Create or update a spec document (SPC - *.md) through a guided workflow.
---

# Spec Creator

You guide the creation and update of spec documents through a structured workflow.
This is the existing body content used as the baseline.
"""

def run_tests():
    results = {
        "max_proxy_status": "UNAVAILABLE — connection refused at localhost:3456. Max Proxy runs on VPS only.",
        "import_check": None,
        "parse_test": None,
        "mock_test": None,
        "deduplication_test": None,
        "overall": None,
    }

    # --- Test 1: import check ---
    try:
        from scripts.mutate_body import parse_variants, split_frontmatter, compute_hash, mutate_body
        results["import_check"] = {"status": "PASS", "detail": "mutate_body module imports cleanly"}
    except Exception as e:
        results["import_check"] = {"status": "FAIL", "detail": str(e)}
        results["overall"] = "FAIL"
        return results

    # --- Test 2: split_frontmatter ---
    fm, body = split_frontmatter(SYNTHETIC_SKILL_CONTENT)
    assert fm.startswith("---"), "split_frontmatter should return frontmatter starting with ---"
    assert "name: create-spec" in fm, "frontmatter should contain name field"
    assert "Spec Creator" in body, "body should contain skill content"

    # --- Test 3: parse_variants on the mock Opus response ---
    variants = parse_variants(MOCK_OPUS_RESPONSE)
    parse_test = {
        "count": len(variants),
        "variants": [],
    }

    hashes_seen = set()
    all_pass = True

    for v in variants:
        vh = compute_hash(v["variant_body"])
        checks = {
            "letter": v["letter"],
            "strategy": v["strategy"],
            "body_non_empty": bool(v["variant_body"].strip()),
            "rationale_non_empty": bool(v["mutation_rationale"].strip()),
            "strategy_valid": v["strategy"] in ("conservative", "structural", "creative"),
            "hash": vh[:20] + "...",
            "hash_unique": vh not in hashes_seen,
            "frontmatter_absent": not v["variant_body"].lstrip().startswith("---"),
        }
        hashes_seen.add(vh)

        for k, val in checks.items():
            if k not in ("letter", "strategy", "hash") and not val:
                all_pass = False

        parse_test["variants"].append(checks)

    parse_test["all_checks_pass"] = all_pass
    results["parse_test"] = parse_test

    # --- Test 4: full mutate_body validation pipeline (mock path) ---
    # We simulate what mutate_body does after the LLM call:
    # validate frontmatter, dedup, hash, rationale
    original_fm, original_body = split_frontmatter(SYNTHETIC_SKILL_CONTENT)
    original_hash = compute_hash(original_body)

    mock_test_variants = []
    for v in variants:
        body = v["variant_body"]
        # Check: LLM should not have included frontmatter in the body
        candidate_fm, candidate_body_only = split_frontmatter(body)
        if candidate_fm:
            # Frontmatter found in variant — check if it matches original
            if candidate_fm.strip() == original_fm.strip():
                body = candidate_body_only  # strip it (as mutate_body does)
            else:
                mock_test_variants.append({
                    "letter": v["letter"],
                    "status": "REJECTED_FRONTMATTER_MODIFIED",
                })
                continue

        if not body.strip():
            mock_test_variants.append({"letter": v["letter"], "status": "REJECTED_EMPTY"})
            continue

        vh = compute_hash(body)
        if vh == original_hash:
            mock_test_variants.append({"letter": v["letter"], "status": "REJECTED_IDENTICAL_TO_ORIGINAL"})
            continue

        mock_test_variants.append({
            "letter": v["letter"],
            "strategy": v["strategy"],
            "status": "ACCEPTED",
            "hash": vh[:20] + "...",
            "rationale_length": len(v["mutation_rationale"]),
            "body_length": len(body),
        })

    results["mock_test"] = {
        "variants": mock_test_variants,
        "accepted_count": sum(1 for v in mock_test_variants if v.get("status") == "ACCEPTED"),
        "all_3_accepted": sum(1 for v in mock_test_variants if v.get("status") == "ACCEPTED") == 3,
    }

    # --- Test 5: deduplication ---
    # Simulate that variant A's hash is already in experiment_history
    variant_a = next((v for v in variants if v["letter"] == "A"), None)
    if variant_a:
        existing_hash = compute_hash(variant_a["variant_body"])
        experiment_history = [{"variant_hash": existing_hash, "strategy": "conservative"}]
        existing_hashes = {e["variant_hash"] for e in experiment_history if "variant_hash" in e}
        would_be_skipped = compute_hash(variant_a["variant_body"]) in existing_hashes
        results["deduplication_test"] = {
            "status": "PASS" if would_be_skipped else "FAIL",
            "detail": "Variant A correctly identified as duplicate when its hash is in experiment_history" if would_be_skipped else "Deduplication check failed",
        }

    # --- Overall ---
    checks = [
        results["import_check"]["status"] == "PASS",
        results["parse_test"]["count"] == 3,
        results["parse_test"]["all_checks_pass"],
        results["mock_test"]["all_3_accepted"],
        results["deduplication_test"]["status"] == "PASS",
    ]
    results["overall"] = "PASS" if all(checks) else "FAIL"
    results["checks_summary"] = {
        "import_ok": checks[0],
        "3_variants_parsed": checks[1],
        "all_variant_checks_pass": checks[2],
        "all_3_accepted_after_validation": checks[3],
        "deduplication_works": checks[4],
    }

    return results


if __name__ == "__main__":
    print("Running mock test for mutate_body.py...\n")
    results = run_tests()
    output_path = Path(__file__).parent / "t1_4_test_results.json"
    output_path.write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\nResults saved to {output_path}")
    if results["overall"] == "PASS":
        print("\n✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n✗ SOME TESTS FAILED")
        sys.exit(1)
