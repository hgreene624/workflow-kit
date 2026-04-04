"""
git_promote.py — Git integration for auto-research skill promotion.

Handles committing promoted variants to the workflow-kit repo and
rolling back to previous versions via git history.

NOTE: body_diff in experiment_db stores "strategy=..." labels, not actual body
content. Rollback reconstructs the body from git log on the repo file.

This module is standalone — do NOT import run_cycle. run_cycle will import
and call promote_to_git() when ready.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_DEFAULT_REPO = Path("/tmp/wfk-skills-repo")

# ---------------------------------------------------------------------------
# Internal git helpers
# ---------------------------------------------------------------------------


def _run(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the given directory. Raises on non-zero exit if check=True."""
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=check,
    )


def _is_git_repo(path: Path) -> bool:
    """Return True if path is inside a git repository."""
    result = _run(["git", "rev-parse", "--git-dir"], cwd=path, check=False)
    return result.returncode == 0


def _is_clean(repo_path: Path) -> tuple[bool, str]:
    """Return (clean, status_output). Clean means no staged/unstaged/untracked changes."""
    result = _run(["git", "status", "--porcelain"], cwd=repo_path)
    clean = result.stdout.strip() == ""
    return clean, result.stdout.strip()


def _get_head_hash(repo_path: Path) -> str:
    result = _run(["git", "rev-parse", "HEAD"], cwd=repo_path)
    return result.stdout.strip()


def _read_frontmatter(content: str) -> tuple[str, str]:
    """Split YAML frontmatter from body. Returns (frontmatter_block, body).

    Frontmatter is the --- ... --- block at the top (including trailing newline).
    If no frontmatter, returns ("", content).
    """
    if not content.startswith("---"):
        return "", content

    lines = content.split("\n")
    end = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break

    if end == -1:
        return "", content

    frontmatter = "\n".join(lines[: end + 1]) + "\n"
    body = "\n".join(lines[end + 1 :])
    if body.startswith("\n"):
        body = body[1:]
    return frontmatter, body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def promote_to_git(
    skill_name: str,
    skill_path: Path,
    variant_body: str,
    variant_hash: str,
    mutation_rationale: str,
    repo_path: Path | None = None,
) -> dict:
    """Promote a variant by committing it to workflow-kit.

    Steps:
    1. Verify repo_path exists and is a git repo
    2. git status — abort if dirty
    3. Locate skills/{skill_name}/SKILL.md in repo
    4. Read current SKILL.md, preserve frontmatter, write new body
    5. git add the changed file
    6. git commit with structured message
    7. Return {"committed": True, "commit_hash": "...", "file": "..."}

    On any error: return {"committed": False, "error": "..."}
    """
    repo_path = Path(repo_path or _DEFAULT_REPO).expanduser().resolve()

    # --- Step 1: Repo existence and git validity ---
    if not repo_path.exists():
        return {
            "committed": False,
            "error": (
                f"workflow-kit repo not found at {repo_path}. "
                "Clone it first before running git promotion."
            ),
        }

    if not _is_git_repo(repo_path):
        return {
            "committed": False,
            "error": f"{repo_path} exists but is not a git repository.",
        }

    # --- Step 2: Clean working tree check (git-safe Rule 1) ---
    clean, status_output = _is_clean(repo_path)
    if not clean:
        return {
            "committed": False,
            "error": (
                f"Dirty working tree in {repo_path} — aborting promotion.\n"
                f"git status output:\n{status_output}\n"
                "Resolve or stash changes before promoting a variant."
            ),
        }

    # --- Step 3: Locate SKILL.md in repo ---
    skill_file = repo_path / "skills" / skill_name / "SKILL.md"
    if not skill_file.exists():
        return {
            "committed": False,
            "error": (
                f"Skill file not found in repo: {skill_file}. "
                f"Expected path: skills/{skill_name}/SKILL.md"
            ),
        }

    # --- Step 4: Preserve frontmatter, write new body ---
    try:
        original = skill_file.read_text(encoding="utf-8")
        frontmatter, _ = _read_frontmatter(original)
        new_content = frontmatter + variant_body
        skill_file.write_text(new_content, encoding="utf-8")
    except OSError as exc:
        return {"committed": False, "error": f"Failed to write {skill_file}: {exc}"}

    # --- Step 5: git add ---
    rel_path = skill_file.relative_to(repo_path)
    try:
        _run(["git", "add", str(rel_path)], cwd=repo_path)
    except subprocess.CalledProcessError as exc:
        return {
            "committed": False,
            "error": f"git add failed: {exc.stderr.strip()}",
        }

    # --- Step 6: git commit ---
    short_hash = variant_hash[:8]
    rationale_snippet = mutation_rationale[:200].strip()
    commit_msg = (
        f"auto-research: promote {skill_name} variant {short_hash}\n"
        f"\n"
        f"{rationale_snippet}\n"
        f"\n"
        f"Pass rate improvement from optimization cycle.\n"
        f"Variant hash: {variant_hash}"
    )

    try:
        _run(["git", "commit", "-m", commit_msg], cwd=repo_path)
    except subprocess.CalledProcessError as exc:
        # Restore original content on commit failure
        try:
            skill_file.write_text(original, encoding="utf-8")
            _run(["git", "checkout", "--", str(rel_path)], cwd=repo_path, check=False)
        except Exception:
            pass
        return {
            "committed": False,
            "error": f"git commit failed: {exc.stderr.strip()}",
        }

    # --- Step 7: Return result ---
    commit_hash = _get_head_hash(repo_path)
    return {
        "committed": True,
        "commit_hash": commit_hash,
        "file": str(rel_path),
        "skill_name": skill_name,
        "variant_hash": variant_hash,
    }


def rollback(
    skill_name: str,
    target_hash: str,
    experiment_db_path: Path,
    repo_path: Path | None = None,
) -> dict:
    """Rollback a skill to a previous promoted version.

    Reconstructs the body from git log (not body_diff, which only stores
    strategy labels). Finds the commit that promoted this variant_hash and
    restores that file version.

    Steps:
    1. Verify repo and clean tree
    2. Find the commit in git log that promoted this variant_hash
    3. Restore that file version via git show
    4. Commit: "auto-research: rollback {skill_name} to {target_hash[:8]}"
    5. Return result dict
    """
    repo_path = Path(repo_path or _DEFAULT_REPO).expanduser().resolve()

    # --- Repo checks ---
    if not repo_path.exists():
        return {
            "rolled_back": False,
            "error": f"workflow-kit repo not found at {repo_path}.",
        }

    if not _is_git_repo(repo_path):
        return {
            "rolled_back": False,
            "error": f"{repo_path} is not a git repository.",
        }

    # --- Clean tree check (git-safe Rule 1) ---
    clean, status_output = _is_clean(repo_path)
    if not clean:
        return {
            "rolled_back": False,
            "error": (
                f"Dirty working tree — aborting rollback.\n"
                f"git status:\n{status_output}"
            ),
        }

    skill_file_rel = f"skills/{skill_name}/SKILL.md"
    skill_file_abs = repo_path / "skills" / skill_name / "SKILL.md"

    if not skill_file_abs.exists():
        return {
            "rolled_back": False,
            "error": f"Skill file not found in repo: {skill_file_rel}",
        }

    # --- Find commit by variant_hash in commit message ---
    short_hash = target_hash[:8]
    try:
        log_result = _run(
            ["git", "log", "--oneline", "--grep", f"Variant hash: {target_hash}", "--", skill_file_rel],
            cwd=repo_path,
        )
    except subprocess.CalledProcessError as exc:
        return {
            "rolled_back": False,
            "error": f"git log failed: {exc.stderr.strip()}",
        }

    log_lines = [l.strip() for l in log_result.stdout.strip().splitlines() if l.strip()]
    if not log_lines:
        return {
            "rolled_back": False,
            "error": (
                f"No commit found for variant hash {target_hash} in {skill_file_rel}. "
                "Either this variant was never committed to the repo, or the hash is wrong."
            ),
        }

    # Use the most recent matching commit
    target_commit = log_lines[0].split()[0]

    # --- Restore file at that commit ---
    try:
        show_result = _run(
            ["git", "show", f"{target_commit}:{skill_file_rel}"],
            cwd=repo_path,
        )
        restored_content = show_result.stdout
    except subprocess.CalledProcessError as exc:
        return {
            "rolled_back": False,
            "error": f"git show failed for {target_commit}: {exc.stderr.strip()}",
        }

    try:
        skill_file_abs.write_text(restored_content, encoding="utf-8")
    except OSError as exc:
        return {"rolled_back": False, "error": f"Failed to write restored content: {exc}"}

    # --- git add + commit ---
    try:
        _run(["git", "add", skill_file_rel], cwd=repo_path)
    except subprocess.CalledProcessError as exc:
        return {"rolled_back": False, "error": f"git add failed: {exc.stderr.strip()}"}

    commit_msg = f"auto-research: rollback {skill_name} to {short_hash}"
    try:
        _run(["git", "commit", "-m", commit_msg], cwd=repo_path)
    except subprocess.CalledProcessError as exc:
        # Restore original if commit fails
        try:
            _run(["git", "checkout", "--", skill_file_rel], cwd=repo_path, check=False)
        except Exception:
            pass
        return {"rolled_back": False, "error": f"git commit failed: {exc.stderr.strip()}"}

    commit_hash = _get_head_hash(repo_path)
    return {
        "rolled_back": True,
        "commit_hash": commit_hash,
        "restored_from_commit": target_commit,
        "skill_name": skill_name,
        "target_variant_hash": target_hash,
    }


def get_rollback_targets(
    skill_name: str,
    experiment_db_path: Path,
    n: int = 3,
) -> list[dict]:
    """List the last N promoted versions available for rollback.

    Queries experiment DB for promoted rows, cross-references with git log
    to confirm each is committed in the repo.

    Returns list of dicts with: variant_hash, pass_rate, mutation_rationale,
    created_at, committed_in_repo.
    """
    _SCRIPTS_DIR = Path(__file__).parent
    if str(_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS_DIR))

    from experiment_db import get_db, get_promoted_versions  # noqa: E402

    conn = get_db(experiment_db_path)
    try:
        rows = get_promoted_versions(conn, skill_name, n)
    finally:
        conn.close()

    if not rows:
        return []

    # Cross-reference with git if repo exists
    repo_path = _DEFAULT_REPO.expanduser().resolve()
    repo_available = repo_path.exists() and _is_git_repo(repo_path)

    results = []
    for row in rows:
        vh = row.get("variant_hash", "")
        entry = {
            "variant_hash": vh,
            "pass_rate": row.get("pass_rate"),
            "mutation_rationale": row.get("mutation_rationale", ""),
            "created_at": row.get("created_at"),
            "committed_in_repo": False,
        }

        if repo_available and vh:
            skill_file_rel = f"skills/{skill_name}/SKILL.md"
            try:
                log_result = _run(
                    ["git", "log", "--oneline", "--grep", f"Variant hash: {vh}", "--", skill_file_rel],
                    cwd=repo_path,
                    check=False,
                )
                entry["committed_in_repo"] = bool(log_result.stdout.strip())
            except Exception:
                pass

        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# CLI (for manual testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="git_promote CLI — manual test interface")
    sub = parser.add_subparsers(dest="cmd")

    p_targets = sub.add_parser("targets", help="List rollback targets for a skill")
    p_targets.add_argument("skill_name")
    p_targets.add_argument("--db-path", default=None)
    p_targets.add_argument("--n", type=int, default=3)

    p_rollback = sub.add_parser("rollback", help="Rollback a skill to a previous variant")
    p_rollback.add_argument("skill_name")
    p_rollback.add_argument("target_hash")
    p_rollback.add_argument("--db-path", default=None)
    p_rollback.add_argument("--repo-path", default=None)

    args = parser.parse_args()

    if args.cmd == "targets":
        from experiment_db import DEFAULT_DB_PATH  # noqa: E402
        db = Path(args.db_path) if args.db_path else DEFAULT_DB_PATH
        result = get_rollback_targets(args.skill_name, db, args.n)
        print(json.dumps(result, indent=2))

    elif args.cmd == "rollback":
        from experiment_db import DEFAULT_DB_PATH  # noqa: E402
        db = Path(args.db_path) if args.db_path else DEFAULT_DB_PATH
        repo = Path(args.repo_path) if args.repo_path else None
        result = rollback(args.skill_name, args.target_hash, db, repo)
        print(json.dumps(result, indent=2))

    else:
        parser.print_help()
