#!/usr/bin/env python3
"""
bootstrap_evals.py — Generate eval sets for Claude Code skills by analyzing SKILL.md.

Usage:
    python3 bootstrap_evals.py --skill-path ~/.claude/skills/cron [--side-effecting] [--num-cases 10] [--num-golden 3] [--offline] [--output PATH]
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
# Core generation logic
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert at writing binary eval test cases for AI assistant skills.
Respond with ONLY a JSON array, no markdown fencing, no explanation."""

def _build_user_prompt(
    skill_name: str,
    skill_md: str,
    num_cases: int,
    num_golden: int,
    side_effecting: bool,
) -> str:
    se_note = ""
    if side_effecting:
        se_note = """
IMPORTANT — THIS IS A SIDE-EFFECTING SKILL:
All expectations must be output-only. Check what the skill SAYS it will do, NOT whether it actually executed.
- DO NOT assert "the cron job was created" → assert "the response includes a cron expression matching..."
- DO NOT assert "the SSH command ran" → assert "the response describes the correct SSH command with..."
- DO NOT assert "the API was called" → assert "the response mentions the correct API endpoint and parameters"
"""

    return f"""Analyze this Claude Code skill and generate {num_cases} binary eval test cases for it.

SKILL NAME: {skill_name}

SKILL.md CONTENT:
{skill_md}

{se_note}

Generate exactly {num_cases} eval cases as a JSON array. Each case must follow this exact structure:
{{
    "query": "realistic user request string",
    "should_trigger": true or false,
    "expectations": ["assertion 1", "assertion 2"],
    "golden": false,
    "notes": "brief rationale for this case"
}}

DISTRIBUTION REQUIREMENTS:
- Approximately 60-65% positive cases (should_trigger: true)
- Approximately 35-40% negative cases (should_trigger: false)
- Exactly {num_golden} cases marked golden: true (must be positive cases covering core identity)

POSITIVE CASES (should_trigger: true) — cover:
- The canonical / most typical use case
- Argument variations (different schedules, topics, inputs)
- Edge inputs that still clearly belong to this skill
- 2-3 expectations per case that are discriminating (would fail for a wrong output)

NEGATIVE CASES (should_trigger: false) — cover:
- Completely unrelated queries (e.g., recipe questions for a cron skill)
- Similar-but-wrong queries that look like they might trigger the skill but shouldn't
- Queries that belong to a different skill
- 1-2 expectations per case asserting what should NOT happen

GOLDEN CASES (golden: true) — exactly {num_golden} cases:
- Must be positive cases (should_trigger: true)
- Must test the CORE IDENTITY of the skill — the one thing it absolutely cannot get wrong
- Typical golden candidates: primary trigger behavior, safety constraint, core output structure
- DO NOT mark edge cases or nice-to-have behaviors as golden

ASSERTION QUALITY RULES:
- Binary: no hedging ("roughly", "mostly", "appears to") — each assertion is clearly pass or fail
- Discriminating: a plausible wrong output would fail this assertion
- Observable: the evidence exists in the transcript or output files
- Specific: "includes a cron expression '0 3 * * 0'" > "includes scheduling information"
- Avoid the existence trap: don't just check "a file was created" — check what's IN the file
- Test outcomes, not process (unless the process IS the safety guarantee)

Output ONLY the JSON array, starting with [ and ending with ]. No other text."""


def bootstrap_evals(
    skill_path: Path,
    max_proxy_url: str = "http://localhost:3456/v1",
    model: str = "claude-sonnet-4-20250514",
    num_cases: int = 10,
    num_golden: int = 3,
    side_effecting: bool = False,
) -> list[dict]:
    """Generate an eval set for a skill by analyzing its SKILL.md.

    Returns list of eval cases, each:
    {
        "query": "user request text",
        "should_trigger": true/false,
        "expectations": ["assertion 1", "assertion 2"],
        "golden": false,
        "notes": "rationale"
    }
    """
    skill_md_path = skill_path / "SKILL.md"
    if not skill_md_path.exists():
        raise FileNotFoundError(f"No SKILL.md found at {skill_md_path}")

    skill_md = skill_md_path.read_text(encoding="utf-8")
    skill_name = skill_path.name

    user_prompt = _build_user_prompt(skill_name, skill_md, num_cases, num_golden, side_effecting)

    print(f"  → Calling {model} via {max_proxy_url} ...", file=sys.stderr)

    try:
        import urllib.request
        import urllib.error

        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{max_proxy_url}/messages",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer YOUR_PROXY_AUTH",
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        raw_text = body["content"][0]["text"].strip()

    except Exception as e:
        print(f"  ⚠ Max Proxy unavailable ({e}). Falling back to template mode.", file=sys.stderr)
        return _generate_template_evals(skill_name, skill_md, num_cases, num_golden)

    return _parse_and_validate(raw_text, skill_name, num_golden)


def _parse_and_validate(raw_text: str, skill_name: str, num_golden: int) -> list[dict]:
    """Parse LLM JSON response and validate structure."""
    # Strip any accidental fencing
    text = re.sub(r"^```[a-z]*\n?", "", raw_text.strip())
    text = re.sub(r"\n?```$", "", text.strip())

    try:
        cases = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM response was not valid JSON: {e}\n\nRaw response:\n{raw_text[:500]}")

    if not isinstance(cases, list):
        raise ValueError(f"Expected JSON array, got {type(cases).__name__}")

    required_fields = {"query", "should_trigger", "expectations", "golden"}
    for i, case in enumerate(cases):
        missing = required_fields - set(case.keys())
        if missing:
            raise ValueError(f"Case {i} missing fields: {missing}")
        if not isinstance(case["expectations"], list) or len(case["expectations"]) == 0:
            raise ValueError(f"Case {i} has empty or non-list expectations")
        if not isinstance(case["should_trigger"], bool):
            raise ValueError(f"Case {i} 'should_trigger' must be boolean")
        if not isinstance(case["golden"], bool):
            raise ValueError(f"Case {i} 'golden' must be boolean")
        # Ensure notes field exists
        if "notes" not in case:
            case["notes"] = ""

    golden_count = sum(1 for c in cases if c["golden"])
    if golden_count == 0:
        print(
            f"  ⚠ Warning: no golden cases generated. Marking first {num_golden} positive cases as golden.",
            file=sys.stderr,
        )
        marked = 0
        for case in cases:
            if case["should_trigger"] and marked < num_golden:
                case["golden"] = True
                marked += 1

    return cases


# ─────────────────────────────────────────────
# Offline / template mode
# ─────────────────────────────────────────────

def _extract_trigger_phrases(skill_md: str) -> list[str]:
    """Extract trigger phrases from SKILL.md description frontmatter."""
    phrases = []
    # Parse YAML frontmatter description
    fm_match = re.search(r"^---\n(.*?)\n---", skill_md, re.DOTALL)
    if fm_match:
        fm_block = fm_match.group(1)
        desc_match = re.search(r"description:\s*[>|]?\s*\n?(.*?)(?=\n\w|\Z)", fm_block, re.DOTALL)
        if desc_match:
            desc = desc_match.group(1).replace("\n", " ").strip()
            # Pull quoted phrases or "trigger on X" patterns
            quoted = re.findall(r'"([^"]+)"', desc)
            phrases.extend(q for q in quoted if len(q) > 5)

    # Extract section headers as capability hints
    headers = re.findall(r"^#{2,3}\s+`?([^`\n]+)`?", skill_md, re.MULTILINE)
    phrases.extend(h.strip("`").lower() for h in headers[:6])

    return phrases[:8]


def _extract_skill_name_from_md(skill_md: str, fallback: str) -> str:
    """Extract the name: field from SKILL.md frontmatter."""
    match = re.search(r"^name:\s*(.+)$", skill_md, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def _generate_template_evals(
    skill_name: str,
    skill_md: str,
    num_cases: int,
    num_golden: int,
) -> list[dict]:
    """Generate template eval cases without LLM (offline mode).

    Analyzes SKILL.md locally to produce placeholder cases the user can fill in.
    """
    display_name = _extract_skill_name_from_md(skill_md, skill_name)
    triggers = _extract_trigger_phrases(skill_md)

    cases = []

    # Golden case 1 — canonical trigger
    trigger_hint = triggers[0] if triggers else f"use the {skill_name} skill"
    cases.append({
        "query": f"[FILL IN: canonical use case for {display_name} — e.g., '{trigger_hint}']",
        "should_trigger": True,
        "expectations": [
            f"[FILL IN: primary output assertion for {display_name}]",
            f"[FILL IN: secondary output assertion — content or structure check]",
        ],
        "golden": True,
        "notes": f"Golden — core identity test for {display_name}",
    })

    # Golden case 2 — another core positive
    cases.append({
        "query": f"[FILL IN: second important use case for {display_name}]",
        "should_trigger": True,
        "expectations": [
            "[FILL IN: discriminating assertion that fails for wrong output]",
            "[FILL IN: safety or structure assertion]",
        ],
        "golden": True,
        "notes": "Golden — second core behavior",
    })

    if num_golden >= 3:
        cases.append({
            "query": f"[FILL IN: negative trigger test — e.g., 'What is the weather today?']",
            "should_trigger": False,
            "expectations": [
                f"The skill does NOT attempt to use {display_name} for an unrelated query",
                "The response does not invoke any of this skill's tools",
            ],
            "golden": True,
            "notes": "Golden — skill must not over-trigger on unrelated queries",
        })

    # Fill remaining positive cases from trigger hints
    for i, phrase in enumerate(triggers[1:], start=1):
        if len(cases) >= num_cases - 2:
            break
        cases.append({
            "query": f"[FILL IN: query involving '{phrase}']",
            "should_trigger": True,
            "expectations": [
                f"[FILL IN: assertion specific to '{phrase}' use case]",
            ],
            "golden": False,
            "notes": f"Positive case for '{phrase}'",
        })

    # Pad with generic positive cases
    while len(cases) < num_cases - 2:
        idx = len(cases) + 1
        cases.append({
            "query": f"[FILL IN: positive trigger query #{idx} for {display_name}]",
            "should_trigger": True,
            "expectations": [
                "[FILL IN: discriminating assertion]",
            ],
            "golden": False,
            "notes": "",
        })

    # Add 2 negative cases
    unrelated = [
        "What's a good recipe for chicken teriyaki?",
        "How do I center a div in CSS?",
        "Summarize the latest news about AI",
    ]
    for i in range(2):
        if len(cases) < num_cases:
            cases.append({
                "query": unrelated[i] if i < len(unrelated) else f"[FILL IN: unrelated query #{i+1}]",
                "should_trigger": False,
                "expectations": [
                    f"The skill does NOT invoke {display_name} tools for this unrelated request",
                ],
                "golden": False,
                "notes": "Negative case — unrelated query",
            })

    return cases[:num_cases]


# ─────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────

def save_evals(eval_set: list[dict], output_path: Path, skill_name: str) -> None:
    """Write evals.json in the skill-creator format."""
    # Add sequential IDs if missing
    for i, case in enumerate(eval_set, start=1):
        if "id" not in case:
            case["id"] = f"{skill_name}-{i:03d}"

    payload = {
        "skill": skill_name,
        "version": "1.0",
        "cases": eval_set,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  ✓ Saved {len(eval_set)} cases → {output_path}", file=sys.stderr)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate an eval set for a Claude Code skill by analyzing its SKILL.md."
    )
    parser.add_argument(
        "--skill-path",
        required=True,
        help="Path to the skill directory containing SKILL.md (e.g., ~/.claude/skills/cron)",
    )
    parser.add_argument(
        "--side-effecting",
        action="store_true",
        default=False,
        help="Mark skill as side-effecting — all assertions will be output-only (FR-36)",
    )
    parser.add_argument(
        "--num-cases",
        type=int,
        default=10,
        help="Number of eval cases to generate (default: 10)",
    )
    parser.add_argument(
        "--num-golden",
        type=int,
        default=3,
        help="Number of cases to mark as golden (default: 3)",
    )
    parser.add_argument(
        "--max-proxy-url",
        default="http://localhost:3456/v1",
        help="Max Proxy base URL (default: http://localhost:3456/v1)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Model ID to use via Max Proxy",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=False,
        help="Generate template evals without calling an LLM (offline mode)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for evals.json (default: <skill-path>/evals.json)",
    )

    args = parser.parse_args()

    skill_path = Path(args.skill_path).expanduser().resolve()
    if not skill_path.is_dir():
        print(f"Error: skill path '{skill_path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    skill_md_path = skill_path / "SKILL.md"
    if not skill_md_path.exists():
        print(f"Error: no SKILL.md found at {skill_md_path}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output).expanduser().resolve() if args.output else skill_path / "evals.json"
    skill_name = skill_path.name

    print(f"Bootstrap evals: skill={skill_name}, cases={args.num_cases}, golden={args.num_golden}, side_effecting={args.side_effecting}, offline={args.offline}", file=sys.stderr)

    if args.offline:
        print("  → Offline mode: generating template evals from SKILL.md analysis", file=sys.stderr)
        skill_md = skill_md_path.read_text(encoding="utf-8")
        eval_set = _generate_template_evals(skill_name, skill_md, args.num_cases, args.num_golden)
    else:
        eval_set = bootstrap_evals(
            skill_path=skill_path,
            max_proxy_url=args.max_proxy_url,
            model=args.model,
            num_cases=args.num_cases,
            num_golden=args.num_golden,
            side_effecting=args.side_effecting,
        )

    save_evals(eval_set, output_path, skill_name)

    # Print summary
    total = len(eval_set)
    positive = sum(1 for c in eval_set if c["should_trigger"])
    negative = total - positive
    golden = sum(1 for c in eval_set if c.get("golden"))
    template_count = sum(1 for c in eval_set if "[FILL IN" in c.get("query", ""))

    print(f"\nEval set summary:", file=sys.stderr)
    print(f"  Total cases : {total}", file=sys.stderr)
    print(f"  Positive    : {positive} (should_trigger=true)", file=sys.stderr)
    print(f"  Negative    : {negative} (should_trigger=false)", file=sys.stderr)
    print(f"  Golden      : {golden}", file=sys.stderr)
    if template_count:
        print(f"  ⚠ Template placeholders: {template_count} cases need manual completion", file=sys.stderr)

    # Emit to stdout for pipeline use
    print(json.dumps({"output_path": str(output_path), "cases": total, "golden": golden}))


if __name__ == "__main__":
    main()
