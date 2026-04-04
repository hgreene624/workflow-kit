"""
run_cycle.py — Single-skill optimization cycle for auto-research.

Orchestrates: load → baseline → mutate → evaluate → tournament → promote/reject → log.

Implements:
- Holdout split (FR-30/FR-35): 60/40 stratified for 8+ cases, LOO for fewer
- Golden test gate (FR-29): any golden failure = automatic rejection
- Suspicious improvement flag (FR-32): >20% improvement → flag for review
- Cost budget cap (FR-31): configurable token cap, graceful termination
- Cache miss circuit breaker (FR-31): <80% hit rate → terminate early

Usage:
    python3 run_cycle.py \\
        --skill-name cron \\
        --skill-path ~/.claude/skills/cron \\
        --eval-set ~/.claude/skills/cron/evals/evals.json \\
        [--dry-run] \\
        [--token-budget 500000]
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Sibling module imports (experiment_db, mutate_body live in same scripts/ dir)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR))

from experiment_db import (  # noqa: E402
    check_duplicate,
    get_db,
    get_history,
    insert_experiment,
)
from mutate_body import compute_hash, mutate_body, split_frontmatter  # noqa: E402


# ---------------------------------------------------------------------------
# LLM-as-judge: body evaluator
# ---------------------------------------------------------------------------

_GRADER_SYSTEM = """\
You are a skill body evaluator for Claude Code skills.

You receive:
1. A skill body — the instructions Claude follows when this skill is executed
2. A user query this skill is meant to handle
3. A list of binary expectations about what a correct response should contain

Your task: For each expectation, determine whether the skill body, when followed by Claude
in response to the given query, would satisfy that expectation. Think through what Claude
would produce step-by-step, then render a binary verdict per expectation.

Respond ONLY with valid JSON in this exact schema (no markdown fences, no extra text):
{
  "reasoning": "<brief analysis of what following these instructions would produce>",
  "expectations": [
    {"expectation": "<exact expectation text>", "pass": true, "evidence": "<one sentence>"}
  ],
  "overall_pass": true
}

overall_pass is true ONLY if every single expectation passes."""


def _call_proxy(
    system: str,
    user: str,
    url: str,
    model: str,
    max_tokens: int = 1500,
) -> tuple[str, dict]:
    """POST to Max Proxy (OpenAI-compat). Returns (content, usage_dict)."""
    endpoint = f"{url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    try:
        resp = requests.post(endpoint, json=payload, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"Max Proxy unreachable at {url}. Is claude-max-proxy running? {exc}"
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Max Proxy HTTP {resp.status_code}: {resp.text[:400]}"
        ) from exc

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return content, usage


# ---------------------------------------------------------------------------
# Token budget tracker
# ---------------------------------------------------------------------------


class _Budget:
    """Accumulate token usage across all Max Proxy calls in one cycle."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.used = 0
        self.cache_reads = 0
        self.total_inputs = 0

    def record(self, usage: dict) -> None:
        input_tok = usage.get("prompt_tokens") or usage.get("input_tokens") or 0
        output_tok = usage.get("completion_tokens") or usage.get("output_tokens") or 0
        # Cache reads — OpenAI nested format or Anthropic flat format
        cache_read = usage.get("cache_read_input_tokens") or (
            (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0
        )
        self.used += input_tok + output_tok
        self.cache_reads += cache_read
        self.total_inputs += input_tok

    @property
    def exhausted(self) -> bool:
        return self.used >= self.total

    @property
    def cache_hit_rate(self) -> float:
        if self.total_inputs == 0:
            return 1.0  # No calls yet — not a failure
        return self.cache_reads / self.total_inputs


# ---------------------------------------------------------------------------
# Body evaluation (LLM-as-judge)
# ---------------------------------------------------------------------------


def evaluate_body(
    skill_body: str,
    eval_case: dict,
    model: str,
    max_proxy_url: str,
) -> tuple[dict, dict]:
    """Grade a skill body against one eval case.

    Returns (result_dict, usage_dict).

    result_dict keys:
        case_id, query, should_trigger, golden, pass (bool),
        reasoning, expectations (list of {expectation, pass, evidence})
    """
    query = eval_case["query"]
    expectations = eval_case.get("expectations", [])
    should_trigger = eval_case.get("should_trigger", True)
    case_id = eval_case.get("id", query[:50])

    trigger_note = ""
    if not should_trigger:
        trigger_note = (
            "\n\n**Scope note**: This query is OUT OF SCOPE for this skill. "
            "The expectations below describe behaviors the skill must NOT exhibit "
            "when mistakenly invoked for this query. Evaluate accordingly."
        )

    numbered = "\n".join(f"{i + 1}. {e}" for i, e in enumerate(expectations))
    user_msg = (
        f"## Skill Body\n\n```\n{skill_body.strip()}\n```\n\n"
        f"## User Query\n\n{query}{trigger_note}\n\n"
        f"## Expectations to Evaluate\n\n{numbered}\n\n"
        "Evaluate each expectation as pass (true) or fail (false)."
    )

    content, usage = _call_proxy(
        system=_GRADER_SYSTEM,
        user=user_msg,
        url=max_proxy_url,
        model=model,
    )

    # Parse JSON — strip markdown fences if present
    try:
        clean = content.strip()
        if clean.startswith("```"):
            lines = clean.splitlines()
            inner = "\n".join(
                lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            )
            clean = inner
        graded = json.loads(clean)
    except (json.JSONDecodeError, IndexError):
        graded = {
            "reasoning": f"[parse error] raw={content[:200]}",
            "expectations": [
                {"expectation": e, "pass": False, "evidence": "parse error"}
                for e in expectations
            ],
            "overall_pass": False,
        }

    exp_results = graded.get("expectations", [])
    all_pass = bool(exp_results) and all(e.get("pass", False) for e in exp_results)

    return {
        "case_id": case_id,
        "query": query,
        "should_trigger": should_trigger,
        "golden": eval_case.get("golden", False),
        "pass": all_pass,
        "reasoning": graded.get("reasoning", ""),
        "expectations": exp_results,
    }, usage


# ---------------------------------------------------------------------------
# Multi-run pass rate measurement
# ---------------------------------------------------------------------------


def _run_cases(
    body: str,
    cases: list[dict],
    grading_model: str,
    proxy_url: str,
    budget: _Budget,
) -> tuple[list[dict], bool]:
    """Evaluate body against all cases. Returns (results, terminated_early)."""
    results: list[dict] = []
    for case in cases:
        if budget.exhausted:
            return results, True
        result, usage = evaluate_body(body, case, grading_model, proxy_url)
        budget.record(usage)
        results.append(result)
    return results, False


def _pass_rate(results: list[dict]) -> float:
    if not results:
        return 0.0
    return sum(1 for r in results if r["pass"]) / len(results)


def _golden_pass(results: list[dict]) -> bool:
    golden = [r for r in results if r.get("golden", False)]
    return not golden or all(r["pass"] for r in golden)


def _measure(
    body: str,
    cases: list[dict],
    grading_model: str,
    proxy_url: str,
    budget: _Budget,
    n_runs: int = 3,
) -> tuple[float, float, list[list[dict]], bool]:
    """Run eval set n_runs times. Returns (mean, stddev, all_run_results, terminated_early)."""
    rates: list[float] = []
    all_runs: list[list[dict]] = []

    for _ in range(n_runs):
        if budget.exhausted:
            break
        run_results, early = _run_cases(body, cases, grading_model, proxy_url, budget)
        if run_results:
            all_runs.append(run_results)
            rates.append(_pass_rate(run_results))
        if early:
            mean = sum(rates) / len(rates) if rates else 0.0
            return mean, 0.0, all_runs, True

    if not rates:
        return 0.0, 0.0, all_runs, True

    mean = sum(rates) / len(rates)
    if len(rates) > 1:
        variance = sum((r - mean) ** 2 for r in rates) / (len(rates) - 1)
        stddev = math.sqrt(variance)
    else:
        stddev = 0.0

    return mean, stddev, all_runs, False


# ---------------------------------------------------------------------------
# Holdout split helpers
# ---------------------------------------------------------------------------


def _stratified_split(
    cases: list[dict],
    train_ratio: float = 0.6,
    seed: int = 42,
) -> tuple[list[dict], list[dict]]:
    """60/40 split stratified by should_trigger. Golden tests always in train."""
    rng = random.Random(seed)

    golden = [c for c in cases if c.get("golden", False)]
    non_golden = [c for c in cases if not c.get("golden", False)]

    positives = [c for c in non_golden if c.get("should_trigger", True)]
    negatives = [c for c in non_golden if not c.get("should_trigger", True)]
    rng.shuffle(positives)
    rng.shuffle(negatives)

    def _split(lst: list, ratio: float) -> tuple[list, list]:
        n = max(1, round(len(lst) * ratio))
        return lst[:n], lst[n:]

    pos_train, pos_hold = _split(positives, train_ratio)
    neg_train, neg_hold = _split(negatives, train_ratio)

    return golden + pos_train + neg_train, pos_hold + neg_hold


def _loo_folds(cases: list[dict]) -> list[tuple[list[dict], dict]]:
    """Leave-one-out folds: yields (train_cases, holdout_case)."""
    return [(cases[:i] + cases[i + 1:], case) for i, case in enumerate(cases)]


# ---------------------------------------------------------------------------
# Grader report for mutation engine
# ---------------------------------------------------------------------------


def _build_grader_report(run_results: list[list[dict]], baseline: float) -> dict:
    """Synthesize failure patterns from baseline runs into a grader report."""
    case_info: dict[str, dict] = {}

    for run in run_results:
        for r in run:
            cid = r["case_id"]
            if cid not in case_info:
                case_info[cid] = {
                    "query": r["query"],
                    "golden": r.get("golden", False),
                    "fail_count": 0,
                    "run_count": 0,
                    "failed_expectations": [],
                }
            case_info[cid]["run_count"] += 1
            if not r["pass"]:
                case_info[cid]["fail_count"] += 1
                for exp in r.get("expectations", []):
                    if not exp.get("pass", True):
                        exp_text = exp.get("expectation", "")
                        if not any(
                            e["expectation"] == exp_text
                            for e in case_info[cid]["failed_expectations"]
                        ):
                            case_info[cid]["failed_expectations"].append({
                                "expectation": exp_text,
                                "evidence": exp.get("evidence", ""),
                            })

    failing = [
        {
            "query": info["query"],
            "golden": info["golden"],
            "failure_rate": info["fail_count"] / max(info["run_count"], 1),
            "failed_expectations": info["failed_expectations"],
        }
        for info in case_info.values()
        if info["fail_count"] > 0
    ]

    return {
        "baseline_pass_rate": baseline,
        "failing_cases": failing,
        "claims": [
            f"Baseline pass rate: {baseline:.1%}",
            f"{len(failing)} case(s) failing consistently",
        ],
        "eval_feedback": failing,
    }


# ---------------------------------------------------------------------------
# SKILL.md promotion
# ---------------------------------------------------------------------------


def _promote(skill_path: Path, new_body: str) -> None:
    """Overwrite SKILL.md with new_body, preserving frontmatter."""
    skill_md = skill_path / "SKILL.md"
    original = skill_md.read_text(encoding="utf-8")
    frontmatter, _ = split_frontmatter(original)
    skill_md.write_text(frontmatter + new_body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main cycle
# ---------------------------------------------------------------------------


def run_cycle(
    skill_name: str,
    skill_path: Path,
    eval_set: list[dict],
    db_path: Path | None = None,
    max_proxy_url: str = "http://localhost:3456/v1",
    mutation_model: str = "claude-opus-4-20250514",
    grading_model: str = "claude-sonnet-4-20250514",
    token_budget: int = 500_000,
    runs_per_eval: int = 3,
    min_improvement: float = 0.05,
    suspicious_threshold: float = 0.20,
    cache_hit_floor: float = 0.80,
    dry_run: bool = False,
) -> dict:
    """Run a complete optimization cycle on one skill.

    Args:
        skill_name:           Registry name for DB logging.
        skill_path:           Directory containing SKILL.md.
        eval_set:             List of eval case dicts (already unwrapped from evals.json).
        db_path:              SQLite DB path (None → default).
        max_proxy_url:        Max Proxy OpenAI-compat base URL.
        mutation_model:       Model ID for Opus mutation calls.
        grading_model:        Model ID for Sonnet grading calls.
        token_budget:         Hard token cap for the entire cycle.
        runs_per_eval:        Eval repetitions for variance estimation (default 3).
        min_improvement:      Minimum holdout pass_rate gain required to promote.
        suspicious_threshold: Holdout improvement above this triggers human review.
        cache_hit_floor:      Cache hit rate below this triggers circuit breaker.
        dry_run:              Evaluate but do not write SKILL.md or mark promoted.

    Returns:
        Summary dict with: skill_name, baseline_pass_rate, baseline_stddev,
        variants, winner, promoted, flagged_for_review, tokens_used,
        duration_ms, terminated_early, termination_reason.
    """
    t0 = int(time.time() * 1000)
    skill_path = Path(skill_path).expanduser().resolve()
    budget = _Budget(token_budget)

    out: dict = {
        "skill_name": skill_name,
        "baseline_pass_rate": 0.0,
        "baseline_stddev": 0.0,
        "variants": [],
        "winner": None,
        "promoted": False,
        "flagged_for_review": False,
        "tokens_used": 0,
        "duration_ms": 0,
        "terminated_early": False,
        "termination_reason": None,
    }

    def _finish(early: bool = False, reason: str | None = None) -> dict:
        out["terminated_early"] = early
        out["termination_reason"] = reason
        out["tokens_used"] = budget.used
        out["duration_ms"] = int(time.time() * 1000) - t0
        return out

    # ----------------------------------------------------------------
    # Load skill body
    # ----------------------------------------------------------------
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found: {skill_md}")
    _, original_body = split_frontmatter(skill_md.read_text(encoding="utf-8"))

    # ----------------------------------------------------------------
    # Split eval set
    # ----------------------------------------------------------------
    use_loo = len(eval_set) < 8
    if use_loo:
        # LOO: all cases are training; holdout validation uses leave-one-out folds
        train_cases = eval_set
    else:
        # 60/40 stratified — golden cases always in train
        golden_cases = [c for c in eval_set if c.get("golden", False)]
        non_golden = [c for c in eval_set if not c.get("golden", False)]
        ng_train, holdout_cases = _stratified_split(non_golden, train_ratio=0.6)
        train_cases = golden_cases + ng_train

    # ----------------------------------------------------------------
    # Baseline measurement
    # ----------------------------------------------------------------
    split_label = "LOO" if use_loo else f"60/40 ({len(train_cases)} train/{len(holdout_cases)} holdout)"
    print(
        f"[run_cycle] Baseline: {len(train_cases)} train cases, "
        f"{runs_per_eval} run(s) each — split={split_label}",
        flush=True,
    )

    b_mean, b_stddev, b_runs, early = _measure(
        original_body, train_cases, grading_model, max_proxy_url, budget, runs_per_eval
    )
    out["baseline_pass_rate"] = b_mean
    out["baseline_stddev"] = b_stddev
    print(f"[run_cycle] Baseline: {b_mean:.1%} ± {b_stddev:.3f} | tokens={budget.used:,}", flush=True)

    if early:
        return _finish(True, "token_budget_exhausted_during_baseline")

    if budget.cache_hit_rate < cache_hit_floor and budget.total_inputs > 1000:
        return _finish(True, f"cache_miss_circuit_breaker (rate={budget.cache_hit_rate:.1%})")

    # ----------------------------------------------------------------
    # Generate variants via mutation engine
    # ----------------------------------------------------------------
    grader_report = _build_grader_report(b_runs, b_mean)

    conn = get_db(db_path)
    history = get_history(conn, skill_name)

    print(f"[run_cycle] Mutating via {mutation_model}…", flush=True)
    try:
        variants = mutate_body(
            skill_path=skill_path,
            grader_report=grader_report,
            experiment_history=history,
            max_proxy_url=max_proxy_url,
            model=mutation_model,
        )
    except Exception as exc:
        conn.close()
        return _finish(True, f"mutation_failed: {exc}")

    # Opus call token cost: not returned by mutate_body, add a conservative estimate
    # so budget reflects reality (Opus input ≈ 3K tokens system + body + history + output ≈ 5K)
    _MUTATION_TOKEN_ESTIMATE = 60_000
    budget.used = min(budget.used + _MUTATION_TOKEN_ESTIMATE, budget.total + 1)

    if not variants:
        print("[run_cycle] No variants generated.", flush=True)
        conn.close()
        return _finish(False, "no_variants_generated")

    print(f"[run_cycle] {len(variants)} variant(s) to evaluate", flush=True)

    # ----------------------------------------------------------------
    # Evaluate each variant on train set
    # ----------------------------------------------------------------
    iteration = len(history) + 1
    v_summaries: list[dict] = []  # lightweight (no body) for out["variants"]
    v_full: list[dict] = []       # includes variant_body for promotion

    for idx, variant in enumerate(variants):
        if budget.exhausted or out.get("terminated_early"):
            out["terminated_early"] = True
            out["termination_reason"] = out.get("termination_reason") or "token_budget_exhausted_during_variant_eval"
            break
        if budget.cache_hit_rate < cache_hit_floor and budget.total_inputs > 1000:
            out["terminated_early"] = True
            out["termination_reason"] = f"cache_miss_circuit_breaker (rate={budget.cache_hit_rate:.1%})"
            break

        v_hash = variant["variant_hash"]
        v_strategy = variant["strategy"]
        v_body = variant["variant_body"]

        # DB dedup check
        if check_duplicate(conn, skill_name, v_hash):
            print(f"[run_cycle] Variant {idx+1}: skip (dup hash {v_hash[:16]}…)", flush=True)
            v_summaries.append({
                "hash": v_hash, "strategy": v_strategy,
                "pass_rate": None, "stddev": None, "golden_pass": None,
                "skipped": True, "skip_reason": "duplicate_hash",
            })
            continue

        print(f"[run_cycle] Variant {idx+1}/{len(variants)} ({v_strategy})…", flush=True)

        v_mean, v_stddev, v_runs, early = _measure(
            v_body, train_cases, grading_model, max_proxy_url, budget, runs_per_eval
        )

        # Golden gate — check last completed run
        gp = _golden_pass(v_runs[-1]) if v_runs else False

        print(
            f"[run_cycle]   {v_strategy}: {v_mean:.1%} ± {v_stddev:.3f} "
            f"golden={'PASS' if gp else 'FAIL'} tokens={budget.used:,}",
            flush=True,
        )

        summary = {
            "hash": v_hash, "strategy": v_strategy,
            "pass_rate": v_mean, "stddev": v_stddev, "golden_pass": gp,
            "skipped": False,
            "mutation_rationale": variant.get("mutation_rationale", ""),
        }
        v_summaries.append(summary)
        v_full.append({**summary, "variant_body": v_body})

        if early:
            out["terminated_early"] = True
            out["termination_reason"] = "token_budget_exhausted_during_variant_eval"

    out["variants"] = v_summaries

    # ----------------------------------------------------------------
    # Tournament — find best candidate on train set
    # ----------------------------------------------------------------
    candidates = [
        vf for vf in v_full
        if not vf.get("skipped")
        and vf["pass_rate"] is not None
        and vf["golden_pass"]
        and vf["pass_rate"] > b_mean + min_improvement
    ]

    if not candidates:
        print("[run_cycle] No candidate clears baseline+min_improvement or golden gate.", flush=True)
        # Log all evaluated variants as rejected (NFR-4: incremental commits)
        for vf in v_full:
            if vf.get("skipped") or vf["pass_rate"] is None:
                continue
            insert_experiment(
                conn=conn, skill_name=skill_name, iteration=iteration,
                variant_hash=vf["hash"], body_diff=f"strategy={vf['strategy']}",
                pass_rate=vf["pass_rate"], pass_rate_stddev=vf["stddev"] or 0.0,
                tokens_used=budget.used, duration_ms=int(time.time() * 1000) - t0,
                promoted=False, mutation_rationale=vf.get("mutation_rationale", ""),
            )
        conn.close()
        return _finish(out["terminated_early"], out.get("termination_reason"))

    candidates.sort(key=lambda x: x["pass_rate"], reverse=True)
    best = candidates[0]

    # ----------------------------------------------------------------
    # Holdout validation
    # ----------------------------------------------------------------
    print(f"[run_cycle] Holdout validation for '{best['strategy']}'…", flush=True)

    b_holdout_rate: float
    w_holdout_rate: float

    if use_loo:
        # Leave-one-out: evaluate both baseline and winner on each fold's holdout case
        folds = _loo_folds(eval_set)
        b_holdout_passes: list[bool] = []
        w_holdout_passes: list[bool] = []

        for _fold_train, holdout_case in folds:
            if budget.exhausted:
                out["terminated_early"] = True
                out["termination_reason"] = "token_budget_exhausted_during_holdout"
                break

            b_r, b_u = evaluate_body(original_body, holdout_case, grading_model, max_proxy_url)
            budget.record(b_u)
            b_holdout_passes.append(b_r["pass"])

            w_r, w_u = evaluate_body(best["variant_body"], holdout_case, grading_model, max_proxy_url)
            budget.record(w_u)
            w_holdout_passes.append(w_r["pass"])

        b_holdout_rate = sum(b_holdout_passes) / len(b_holdout_passes) if b_holdout_passes else b_mean
        w_holdout_rate = sum(w_holdout_passes) / len(w_holdout_passes) if w_holdout_passes else best["pass_rate"]

    else:
        # 60/40: single holdout pass
        if holdout_cases:
            b_h_results, _ = _run_cases(original_body, holdout_cases, grading_model, max_proxy_url, budget)
            w_h_results, _ = _run_cases(best["variant_body"], holdout_cases, grading_model, max_proxy_url, budget)
            b_holdout_rate = _pass_rate(b_h_results)
            w_holdout_rate = _pass_rate(w_h_results)
        else:
            # Empty holdout (edge case: very small set fell fully into train)
            b_holdout_rate = b_mean
            w_holdout_rate = best["pass_rate"]

    holdout_improvement = w_holdout_rate - b_holdout_rate

    print(
        f"[run_cycle] Holdout: winner={w_holdout_rate:.1%} baseline={b_holdout_rate:.1%} "
        f"improvement={holdout_improvement:+.1%}",
        flush=True,
    )

    winner_info = {
        "hash": best["hash"],
        "strategy": best["strategy"],
        "pass_rate": best["pass_rate"],
        "holdout_pass_rate": w_holdout_rate,
        "improvement": best["pass_rate"] - b_mean,
        "holdout_improvement": holdout_improvement,
    }
    out["winner"] = winner_info

    # ----------------------------------------------------------------
    # Safety gates
    # ----------------------------------------------------------------

    # Gate 1: holdout improvement must meet min threshold
    if holdout_improvement < min_improvement:
        print(
            f"[run_cycle] Holdout improvement {holdout_improvement:+.1%} < {min_improvement:.1%} — rejecting.",
            flush=True,
        )
        _log_all(conn, skill_name, iteration, v_full, budget.used, int(time.time() * 1000) - t0, promoted=False)
        conn.close()
        return _finish(out["terminated_early"], out.get("termination_reason"))

    # Gate 2: suspicious improvement flag (FR-32)
    if holdout_improvement > suspicious_threshold:
        print(
            f"[run_cycle] Suspicious improvement {holdout_improvement:+.1%} > "
            f"{suspicious_threshold:.1%} — flagging for human review.",
            flush=True,
        )
        out["flagged_for_review"] = True
        insert_experiment(
            conn=conn, skill_name=skill_name, iteration=iteration,
            variant_hash=best["hash"],
            body_diff=f"strategy={best['strategy']} FLAGGED_FOR_REVIEW",
            pass_rate=best["pass_rate"], pass_rate_stddev=best["stddev"] or 0.0,
            tokens_used=budget.used, duration_ms=int(time.time() * 1000) - t0,
            promoted=False,
            mutation_rationale=(
                f"FLAGGED: {holdout_improvement:+.1%} exceeds "
                f"suspicious_threshold={suspicious_threshold:.1%}. "
                + best.get("mutation_rationale", "")
            ),
        )
        conn.close()
        return _finish(out["terminated_early"], out.get("termination_reason"))

    # ----------------------------------------------------------------
    # Promote (or dry-run)
    # ----------------------------------------------------------------
    if dry_run:
        print(
            f"[run_cycle] DRY RUN — would promote {best['strategy']} ({best['hash'][:16]}…)",
            flush=True,
        )
    else:
        print(
            f"[run_cycle] Promoting {best['strategy']} ({best['hash'][:16]}…)",
            flush=True,
        )
        _promote(skill_path, best["variant_body"])
        out["promoted"] = True

    # Log all variants; winner is marked promoted=True (unless dry_run)
    _log_all(
        conn, skill_name, iteration, v_full, budget.used,
        int(time.time() * 1000) - t0,
        promoted=not dry_run,
        winner_hash=best["hash"],
    )
    conn.close()
    return _finish(out["terminated_early"], out.get("termination_reason"))


# ---------------------------------------------------------------------------
# DB logging helper
# ---------------------------------------------------------------------------


def _log_all(
    conn,
    skill_name: str,
    iteration: int,
    variants_full: list[dict],
    tokens_used: int,
    duration_ms: int,
    promoted: bool,
    winner_hash: str | None = None,
) -> None:
    """Log all evaluated variants to the experiment DB."""
    for vf in variants_full:
        if vf.get("skipped") or vf["pass_rate"] is None:
            continue
        is_winner = winner_hash is not None and vf["hash"] == winner_hash
        insert_experiment(
            conn=conn,
            skill_name=skill_name,
            iteration=iteration,
            variant_hash=vf["hash"],
            body_diff=f"strategy={vf['strategy']}",
            pass_rate=vf["pass_rate"],
            pass_rate_stddev=vf.get("stddev") or 0.0,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            promoted=is_winner and promoted,
            mutation_rationale=vf.get("mutation_rationale", ""),
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _load_eval_set(path: Path) -> list[dict]:
    """Load evals.json — handles both bare list and {cases: [...]} wrapper."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "cases" in raw:
        return raw["cases"]
    raise ValueError(f"Unrecognised evals.json format at {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run a single-skill auto-research optimization cycle.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--skill-name", required=True, help="Skill name (for DB key)")
    parser.add_argument(
        "--skill-path", required=True,
        help="Path to skill directory containing SKILL.md"
    )
    parser.add_argument(
        "--eval-set", required=True,
        help="Path to evals.json for this skill"
    )
    parser.add_argument("--db-path", default=None, help="SQLite DB path (default: auto-research default)")
    parser.add_argument("--max-proxy-url", default="http://localhost:3456/v1")
    parser.add_argument("--mutation-model", default="claude-opus-4-20250514")
    parser.add_argument("--grading-model", default="claude-sonnet-4-20250514")
    parser.add_argument("--token-budget", type=int, default=500_000)
    parser.add_argument("--runs-per-eval", type=int, default=3)
    parser.add_argument("--min-improvement", type=float, default=0.05)
    parser.add_argument("--suspicious-threshold", type=float, default=0.20)
    parser.add_argument("--cache-hit-floor", type=float, default=0.80)
    parser.add_argument("--dry-run", action="store_true", help="Evaluate but do not promote")
    args = parser.parse_args()

    skill_path = Path(args.skill_path).expanduser().resolve()
    if not skill_path.exists():
        print(f"ERROR: skill path not found: {skill_path}", file=sys.stderr)
        sys.exit(1)

    eval_path = Path(args.eval_set).expanduser().resolve()
    if not eval_path.exists():
        print(f"ERROR: eval set not found: {eval_path}", file=sys.stderr)
        sys.exit(1)

    eval_set = _load_eval_set(eval_path)
    db_path = Path(args.db_path).expanduser().resolve() if args.db_path else None

    print(f"=== run_cycle: {args.skill_name} ===")
    print(f"  skill_path   : {skill_path}")
    print(f"  eval cases   : {len(eval_set)} ({sum(1 for c in eval_set if c.get('golden'))} golden)")
    print(f"  token_budget : {args.token_budget:,}")
    print(f"  dry_run      : {args.dry_run}")
    print()

    result = run_cycle(
        skill_name=args.skill_name,
        skill_path=skill_path,
        eval_set=eval_set,
        db_path=db_path,
        max_proxy_url=args.max_proxy_url,
        mutation_model=args.mutation_model,
        grading_model=args.grading_model,
        token_budget=args.token_budget,
        runs_per_eval=args.runs_per_eval,
        min_improvement=args.min_improvement,
        suspicious_threshold=args.suspicious_threshold,
        cache_hit_floor=args.cache_hit_floor,
        dry_run=args.dry_run,
    )

    print()
    print("=== Cycle Result ===")
    print(json.dumps(
        {k: v for k, v in result.items() if k not in ("variants",)},
        indent=2,
    ))
    if result["variants"]:
        print("\nVariants:")
        for v in result["variants"]:
            if v.get("skipped"):
                print(f"  [{v['strategy']:12}] SKIPPED ({v.get('skip_reason', '')})")
            else:
                golden_tag = "golden=PASS" if v.get("golden_pass") else "golden=FAIL"
                print(
                    f"  [{v['strategy']:12}] {v['pass_rate']:.1%} ± {v.get('stddev', 0):.3f}  "
                    f"{golden_tag}  hash={v['hash'][:16]}…"
                )

    if result["terminated_early"]:
        print(f"\nWARNING: cycle terminated early — {result['termination_reason']}")
        sys.exit(2)

    if result["flagged_for_review"]:
        print("\nFLAGGED: suspicious improvement — manual review required before promotion.")
        sys.exit(3)

    if result["promoted"]:
        print(f"\nPROMOTED: {result['winner']['strategy']} ({result['winner']['hash'][:16]}…)")
    else:
        print("\nNO PROMOTION this cycle.")
