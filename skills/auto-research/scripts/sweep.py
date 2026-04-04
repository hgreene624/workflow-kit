"""
sweep.py — Registry sweep and target selection for auto-research.

Reads registry.json, selects the next optimization target, runs a full
cycle via run_cycle(), and updates the registry on success.

Selection priority:
  1. Manual override (--target skill-name)
  2. Lowest current_pass_rate (most in need of improvement)
  3. Oldest last_optimized (longest since last cycle)
  4. null last_optimized sorts before any date (never optimized)
  null current_pass_rate is treated as 0.0 (worst possible).

Skills with eval_set == "" are skipped (no evals yet).

Usage:
    python3 sweep.py [--target skill-name] [--dry-run] [--registry path/to/registry.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR))

from run_cycle import _load_eval_set, run_cycle  # noqa: E402

_DEFAULT_REGISTRY = Path("~/.claude/skills/auto-research/registry.json")


# ---------------------------------------------------------------------------
# Target selection
# ---------------------------------------------------------------------------


def select_target(
    registry: list[dict],
    manual_override: str | None = None,
) -> dict | None:
    """Select the next optimization target from the registry.

    Priority order:
    1. Manual override — if provided, find that skill by name.
    2. Lowest current_pass_rate (skills that need the most improvement).
    3. Oldest last_optimized (skills that haven't been touched in longest).
    4. Skills with null last_optimized come first (never optimized).

    Returns the registry entry dict, or None if no valid targets.
    """
    # Filter: skip skills with no eval set
    eligible = [e for e in registry if e.get("eval_set", "").strip()]

    if not eligible:
        return None

    # Manual override
    if manual_override:
        for entry in eligible:
            if entry.get("name") == manual_override:
                return entry
        return None  # Named skill not found or not eligible

    # Sort key: (pass_rate, last_optimized)
    # - pass_rate: null → 0.0 (sort first / worst)
    # - last_optimized: null → sort before any real date (oldest = highest priority)
    def _sort_key(entry: dict) -> tuple:
        pass_rate = entry.get("current_pass_rate")
        pass_rate_val = pass_rate if pass_rate is not None else 0.0

        last_opt = entry.get("last_optimized")
        if last_opt is None:
            # Treat as "infinitely old" — smallest possible comparable value
            last_opt_val = ""  # Empty string sorts before any ISO datetime string
        else:
            last_opt_val = last_opt

        return (pass_rate_val, last_opt_val)

    eligible.sort(key=_sort_key)
    return eligible[0]


# ---------------------------------------------------------------------------
# Registry update
# ---------------------------------------------------------------------------


def update_registry(registry_path: Path, skill_name: str, pass_rate: float) -> None:
    """Update a skill's registry entry after a cycle completes.

    Sets last_optimized to now (ISO 8601 UTC), current_pass_rate to pass_rate.
    Read-modify-write the JSON file atomically (write to tmp, rename).
    """
    registry_path = registry_path.expanduser().resolve()
    registry_data: dict = json.loads(registry_path.read_text(encoding="utf-8"))
    targets: list[dict] = registry_data["targets"]

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    updated = False
    for entry in targets:
        if entry.get("name") == skill_name:
            entry["last_optimized"] = now_iso
            entry["current_pass_rate"] = round(pass_rate, 4)
            updated = True
            break

    if not updated:
        raise KeyError(f"Skill '{skill_name}' not found in registry at {registry_path}")

    tmp = registry_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(registry_data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(registry_path)

    print(
        f"[sweep] Registry updated: {skill_name} → pass_rate={pass_rate:.1%}, "
        f"last_optimized={now_iso}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Main sweep orchestrator
# ---------------------------------------------------------------------------


def run_sweep(
    registry_path: Path | None = None,
    manual_target: str | None = None,
    dry_run: bool = False,
    **cycle_kwargs,
) -> dict:
    """Run a full sweep: select target → load eval set → run_cycle → update registry.

    Args:
        registry_path:  Path to registry.json (default: ~/.claude/skills/auto-research/registry.json).
        manual_target:  Force a specific skill name, bypassing normal selection.
        dry_run:        Pass through to run_cycle — evaluate but do not promote.
        **cycle_kwargs: Additional keyword arguments forwarded to run_cycle().

    Returns:
        The cycle result dict from run_cycle(), with an extra "selected_skill" key.
    """
    if registry_path is None:
        registry_path = _DEFAULT_REGISTRY
    registry_path = Path(registry_path).expanduser().resolve()

    if not registry_path.exists():
        raise FileNotFoundError(f"Registry not found: {registry_path}")

    registry_data: dict = json.loads(registry_path.read_text(encoding="utf-8"))
    registry: list[dict] = registry_data["targets"]

    # --- Select target ---
    target = select_target(registry, manual_override=manual_target)

    if target is None:
        if manual_target:
            print(
                f"[sweep] ERROR: Manual target '{manual_target}' not found or has no eval_set.",
                flush=True,
            )
        else:
            print("[sweep] No eligible targets found (all skills missing eval_set?).", flush=True)
        return {
            "skill_name": manual_target or None,
            "selected_skill": None,
            "promoted": False,
            "terminated_early": True,
            "termination_reason": "no_eligible_target",
        }

    skill_name = target["name"]
    skill_path = Path(target["path"]).expanduser().resolve()
    eval_set_path = Path(target["eval_set"]).expanduser().resolve()

    print(f"[sweep] Selected: {skill_name}", flush=True)
    print(f"  path       : {skill_path}", flush=True)
    print(f"  eval_set   : {eval_set_path}", flush=True)
    print(f"  pass_rate  : {target.get('current_pass_rate')}", flush=True)
    print(f"  last_opt   : {target.get('last_optimized')}", flush=True)
    print(f"  dry_run    : {dry_run}", flush=True)
    print()

    if not skill_path.exists():
        raise FileNotFoundError(f"Skill directory not found: {skill_path}")
    if not eval_set_path.exists():
        raise FileNotFoundError(f"Eval set not found: {eval_set_path}")

    eval_set = _load_eval_set(eval_set_path)
    print(
        f"[sweep] Loaded {len(eval_set)} eval cases "
        f"({sum(1 for c in eval_set if c.get('golden'))} golden)",
        flush=True,
    )
    print()

    # --- Run cycle ---
    result = run_cycle(
        skill_name=skill_name,
        skill_path=skill_path,
        eval_set=eval_set,
        dry_run=dry_run,
        **cycle_kwargs,
    )
    result["selected_skill"] = skill_name

    # --- Update registry on success (not dry_run, not terminated early) ---
    if not dry_run and not result.get("terminated_early") and not result.get("flagged_for_review"):
        # Use final pass_rate: winner's holdout rate if promoted, else baseline
        if result.get("promoted") and result.get("winner"):
            final_rate = result["winner"]["holdout_pass_rate"]
        else:
            final_rate = result.get("baseline_pass_rate", 0.0)
        update_registry(registry_path, skill_name, final_rate)
    elif dry_run:
        print("[sweep] Dry run — registry not updated.", flush=True)
    elif result.get("terminated_early"):
        print(
            f"[sweep] Cycle terminated early ({result.get('termination_reason')}) — registry not updated.",
            flush=True,
        )
    elif result.get("flagged_for_review"):
        print("[sweep] Cycle flagged for review — registry not updated.", flush=True)

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Registry sweep: select target skill and run one optimization cycle.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--target",
        metavar="SKILL_NAME",
        default=None,
        help="Force a specific skill by name (bypasses selection logic)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Evaluate but do not promote SKILL.md or update registry",
    )
    parser.add_argument(
        "--registry",
        metavar="PATH",
        default=None,
        help=f"Path to registry.json (default: {_DEFAULT_REGISTRY})",
    )
    # Forwarded cycle options
    parser.add_argument("--db-path", default=None)
    parser.add_argument("--max-proxy-url", default="http://localhost:3456/v1")
    parser.add_argument("--mutation-model", default="claude-opus-4-20250514")
    parser.add_argument("--grading-model", default="claude-sonnet-4-20250514")
    parser.add_argument("--token-budget", type=int, default=500_000)
    parser.add_argument("--runs-per-eval", type=int, default=3)
    parser.add_argument("--min-improvement", type=float, default=0.05)
    parser.add_argument("--suspicious-threshold", type=float, default=0.20)
    parser.add_argument("--cache-hit-floor", type=float, default=0.80)

    args = parser.parse_args()

    registry_path = Path(args.registry).expanduser().resolve() if args.registry else None

    cycle_kwargs: dict = {
        "max_proxy_url": args.max_proxy_url,
        "mutation_model": args.mutation_model,
        "grading_model": args.grading_model,
        "token_budget": args.token_budget,
        "runs_per_eval": args.runs_per_eval,
        "min_improvement": args.min_improvement,
        "suspicious_threshold": args.suspicious_threshold,
        "cache_hit_floor": args.cache_hit_floor,
    }
    if args.db_path:
        cycle_kwargs["db_path"] = Path(args.db_path).expanduser().resolve()

    print("=== auto-research sweep ===")
    if args.target:
        print(f"  manual target : {args.target}")
    if registry_path:
        print(f"  registry      : {registry_path}")
    print(f"  dry_run       : {args.dry_run}")
    print()

    try:
        result = run_sweep(
            registry_path=registry_path,
            manual_target=args.target,
            dry_run=args.dry_run,
            **cycle_kwargs,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print()
    print("=== Sweep Result ===")
    print(json.dumps(
        {k: v for k, v in result.items() if k not in ("variants",)},
        indent=2,
    ))

    if result.get("variants"):
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

    if result.get("terminated_early"):
        print(f"\nWARNING: cycle terminated early — {result.get('termination_reason')}")
        sys.exit(2)

    if result.get("flagged_for_review"):
        print("\nFLAGGED: suspicious improvement — manual review required before promotion.")
        sys.exit(3)

    if result.get("promoted"):
        winner = result.get("winner", {})
        print(f"\nPROMOTED: {winner.get('strategy')} ({winner.get('hash', '')[:16]}…)")
    else:
        print("\nNO PROMOTION this cycle.")
