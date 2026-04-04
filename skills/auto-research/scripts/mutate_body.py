"""
mutate_body.py — Body mutation engine for auto-research skill optimization.

Loads SKILL.md + grader report, calls Opus via Max Proxy with the mutator.md prompt,
parses 3 body variants, deduplicates against experiment history, validates frontmatter
preservation.

Usage:
    python3 mutate_body.py --skill-path ~/.claude/skills/create-spec --grader-report path/to/report.json
"""

import argparse
import hashlib
import json
import re
import sys
import warnings
from pathlib import Path

import requests


# ---------------------------------------------------------------------------
# Frontmatter utilities
# ---------------------------------------------------------------------------

def split_frontmatter(content: str) -> tuple[str, str]:
    """Split SKILL.md content into (frontmatter_block, body).

    frontmatter_block includes the surrounding `---` delimiters and trailing newline.
    Returns ('', content) if no frontmatter is present.
    """
    if not content.startswith("---"):
        return "", content

    end = content.find("\n---", 3)
    if end == -1:
        return "", content

    close_end = end + len("\n---")
    # Consume optional trailing newline after closing ---
    if close_end < len(content) and content[close_end] == "\n":
        close_end += 1

    return content[:close_end], content[close_end:]


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

def call_max_proxy(
    system_prompt: str,
    user_message: str,
    max_proxy_url: str,
    model: str,
    max_tokens: int = 16000,
) -> str:
    """POST to Max Proxy (OpenAI format) and return the assistant message content."""
    url = f"{max_proxy_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }
    try:
        resp = requests.post(url, json=payload, timeout=300)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"Max Proxy unreachable at {max_proxy_url}. "
            f"Is the claude-max-proxy service running? Error: {exc}"
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Max Proxy returned HTTP {resp.status_code}: {resp.text[:500]}"
        ) from exc

    data = resp.json()
    return data["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Prompt assembly
# ---------------------------------------------------------------------------

def build_user_message(
    skill_body: str,
    grader_report: dict,
    experiment_history: list,
) -> str:
    """Assemble the user-turn message that goes with the mutator system prompt."""
    recent_history = experiment_history[-5:] if experiment_history else []

    parts = [
        "## Current SKILL.md Body\n\n```markdown",
        skill_body.strip(),
        "```",
        "",
        "## Grader Report\n\n```json",
        json.dumps(grader_report, indent=2),
        "```",
    ]

    if recent_history:
        parts += [
            "",
            "## Experiment History (last 5 entries)\n\n```json",
            json.dumps(recent_history, indent=2),
            "```",
        ]

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

# Matches: ## Variant A — Conservative  (em dash, en dash, or hyphen)
_VARIANT_HEADER_RE = re.compile(
    r"^##\s+Variant\s+([ABC])\s*[—–-]\s*(\w+)",
    re.MULTILINE,
)

# After ### Body, find a fenced code block (```markdown or just ```)
_BODY_BLOCK_RE = re.compile(
    r"###\s+Body\s*\n+```(?:markdown)?\s*\n(.*?)```",
    re.DOTALL,
)

# The ### Rationale block runs until the next ### heading or end of section
_RATIONALE_BLOCK_RE = re.compile(
    r"###\s+Rationale\s*\n(.*?)(?=###|\Z)",
    re.DOTALL,
)

_STRATEGY_MAP = {"A": "conservative", "B": "structural", "C": "creative"}


def parse_variants(response_text: str) -> list[dict]:
    """Parse the mutator Opus response into a list of raw variant dicts.

    Returns list of dicts with keys: letter, strategy, variant_body, mutation_rationale.
    Empty body or missing sections are represented as empty strings.
    """
    matches = list(_VARIANT_HEADER_RE.finditer(response_text))
    if not matches:
        return []

    parsed = []
    for i, match in enumerate(matches):
        letter = match.group(1)
        section_start = match.start()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(response_text)
        section = response_text[section_start:section_end]

        body_match = _BODY_BLOCK_RE.search(section)
        body = body_match.group(1).rstrip("\n") if body_match else ""

        rationale_match = _RATIONALE_BLOCK_RE.search(section)
        rationale = rationale_match.group(1).strip() if rationale_match else ""

        parsed.append({
            "letter": letter,
            "strategy": _STRATEGY_MAP.get(letter, letter.lower()),
            "variant_body": body,
            "mutation_rationale": rationale,
        })

    return parsed


# ---------------------------------------------------------------------------
# Hash
# ---------------------------------------------------------------------------

def compute_hash(text: str) -> str:
    """Return the SHA-256 hex digest of text (encoded as UTF-8)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def mutate_body(
    skill_path: Path,
    grader_report: dict,
    experiment_history: list,
    max_proxy_url: str = "http://localhost:3456/v1",
    model: str = "claude-opus-4-20250514",
) -> list[dict]:
    """Generate 3 body variants for the given skill.

    Loads SKILL.md from skill_path, calls Opus via Max Proxy using the mutator.md
    system prompt, parses 3 variants from the response, then filters out:
      - empty bodies
      - bodies identical to the original
      - duplicates already present in experiment_history (by variant_hash)
      - variants that modified or introduced frontmatter

    Args:
        skill_path:          Path to the skill directory (must contain SKILL.md).
        grader_report:       Grader output JSON (expectations, claims, eval_feedback).
        experiment_history:  Past experiments for this skill from the DB.
        max_proxy_url:       Max Proxy OpenAI-compatible endpoint.
        model:               Opus model ID to use for mutation.

    Returns:
        List of dicts, each with:
          - variant_body: str       (complete SKILL.md body, after frontmatter)
          - variant_hash: str       (SHA-256 of variant_body)
          - mutation_rationale: str (why this change was made)
          - strategy: str           (conservative / structural / creative)
    """
    skill_path = Path(skill_path).expanduser().resolve()
    skill_md_path = skill_path / "SKILL.md"

    if not skill_md_path.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md_path}")

    # 1. Read and split current SKILL.md
    content = skill_md_path.read_text(encoding="utf-8")
    original_frontmatter, original_body = split_frontmatter(content)
    original_body_hash = compute_hash(original_body)

    # 2. Load mutator.md system prompt
    mutator_md_path = Path(__file__).parent.parent / "agents" / "mutator.md"
    if not mutator_md_path.exists():
        raise FileNotFoundError(f"mutator.md not found at {mutator_md_path}")
    mutator_prompt = mutator_md_path.read_text(encoding="utf-8")

    # 3. Build user message
    user_message = build_user_message(original_body, grader_report, experiment_history)

    # 4. Call Max Proxy
    response_text = call_max_proxy(
        system_prompt=mutator_prompt,
        user_message=user_message,
        max_proxy_url=max_proxy_url,
        model=model,
    )

    # 5. Parse variants from response
    raw_variants = parse_variants(response_text)

    if not raw_variants:
        warnings.warn(
            "mutate_body: failed to parse any variants from Opus response.\n"
            f"Response preview:\n{response_text[:1000]}",
            stacklevel=2,
        )
        return []

    if len(raw_variants) < 3:
        warnings.warn(
            f"mutate_body: only {len(raw_variants)} variant(s) parsed (expected 3).",
            stacklevel=2,
        )

    # 6. Build set of hashes already seen in experiment history
    existing_hashes = {
        e["variant_hash"]
        for e in experiment_history
        if "variant_hash" in e
    }

    # 7. Validate, deduplicate, collect results
    results = []
    for v in raw_variants:
        body = v["variant_body"]
        letter = v["letter"]

        if not body:
            warnings.warn(
                f"mutate_body: Variant {letter} has an empty body — skipping.",
                stacklevel=2,
            )
            continue

        # Handle case where LLM included frontmatter despite instructions not to
        candidate_fm, candidate_body_only = split_frontmatter(body)
        if candidate_fm:
            if original_frontmatter and candidate_fm.strip() == original_frontmatter.strip():
                # Frontmatter matches original — safe to strip
                warnings.warn(
                    f"mutate_body: Variant {letter} included (unmodified) frontmatter in "
                    "body — stripping it.",
                    stacklevel=2,
                )
                body = candidate_body_only
            else:
                # Frontmatter was added or modified — reject
                warnings.warn(
                    f"mutate_body: Variant {letter} modified or introduced frontmatter — "
                    "rejecting this variant.",
                    stacklevel=2,
                )
                continue

        if not body.strip():
            warnings.warn(
                f"mutate_body: Variant {letter} is empty after frontmatter strip — skipping.",
                stacklevel=2,
            )
            continue

        vh = compute_hash(body)

        # Skip if identical to original body
        if vh == original_body_hash:
            warnings.warn(
                f"mutate_body: Variant {letter} is identical to the original body — skipping.",
                stacklevel=2,
            )
            continue

        # Deduplicate against experiment history (FR-8)
        if vh in existing_hashes:
            warnings.warn(
                f"mutate_body: Variant {letter} hash {vh[:16]}… already exists in "
                "experiment history — skipping duplicate.",
                stacklevel=2,
            )
            continue

        results.append({
            "variant_body": body,
            "variant_hash": vh,
            "mutation_rationale": v["mutation_rationale"],
            "strategy": v["strategy"],
        })

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Generate 3 body variants for a SKILL.md via Opus mutation.\n"
            "Variants are written to <skill-path>/mutation_variants.json."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skill-path",
        required=True,
        help="Path to skill directory containing SKILL.md (e.g. ~/.claude/skills/create-spec)",
    )
    parser.add_argument(
        "--grader-report",
        required=True,
        help="Path to grader report JSON file.",
    )
    parser.add_argument(
        "--history",
        default=None,
        help="Path to experiment history JSON file (list of experiment dicts). Optional.",
    )
    parser.add_argument(
        "--max-proxy-url",
        default="http://localhost:3456/v1",
        help="Max Proxy base URL (default: http://localhost:3456/v1)",
    )
    parser.add_argument(
        "--model",
        default="claude-opus-4-20250514",
        help="Model ID to use for mutation (default: claude-opus-4-20250514)",
    )
    args = parser.parse_args()

    skill_path = Path(args.skill_path).expanduser().resolve()
    if not skill_path.exists():
        print(f"ERROR: skill path not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    grader_path = Path(args.grader_report).expanduser().resolve()
    if not grader_path.exists():
        print(f"ERROR: grader report not found: {grader_path}", file=sys.stderr)
        sys.exit(1)
    grader_report = json.loads(grader_path.read_text(encoding="utf-8"))

    experiment_history = []
    if args.history:
        history_path = Path(args.history).expanduser().resolve()
        if history_path.exists():
            experiment_history = json.loads(history_path.read_text(encoding="utf-8"))
        else:
            print(f"WARNING: history file not found at {history_path} — using empty history.",
                  file=sys.stderr)

    print(f"Calling {args.model} via {args.max_proxy_url}")
    print(f"Skill: {skill_path.name}")
    print("Generating variants…\n")

    variants = mutate_body(
        skill_path=skill_path,
        grader_report=grader_report,
        experiment_history=experiment_history,
        max_proxy_url=args.max_proxy_url,
        model=args.model,
    )

    if not variants:
        print("No variants generated.", file=sys.stderr)
        sys.exit(1)

    print(f"{len(variants)} variant(s) generated:\n")
    for i, v in enumerate(variants, 1):
        rationale_preview = v["mutation_rationale"][:120].replace("\n", " ").strip()
        print(f"  [{i}] strategy={v['strategy']}")
        print(f"       hash={v['variant_hash'][:20]}…")
        print(f"       rationale: {rationale_preview}…")
        print()

    output_path = skill_path / "mutation_variants.json"
    output_path.write_text(json.dumps(variants, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Variants saved to {output_path}")
