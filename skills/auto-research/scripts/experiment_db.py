"""
experiment_db.py — Experiment history database for auto-research skill.

Provides SQLite-backed storage for skill mutation experiments, with WAL mode
for concurrent read safety and helper functions for insert, query, and dedup.
"""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".claude" / "skills" / "auto-research" / "experiment_history.db"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name TEXT NOT NULL,
    iteration INTEGER NOT NULL,
    variant_hash TEXT NOT NULL,
    body_diff TEXT,
    pass_rate REAL,
    pass_rate_stddev REAL,
    tokens_used INTEGER,
    duration_ms INTEGER,
    promoted BOOLEAN DEFAULT 0,
    mutation_rationale TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_INDEX_SKILL_SQL = "CREATE INDEX IF NOT EXISTS idx_skill_name ON experiments(skill_name);"
CREATE_INDEX_HASH_SQL = "CREATE INDEX IF NOT EXISTS idx_variant_hash ON experiments(variant_hash);"


def get_db(db_path=None) -> sqlite3.Connection:
    """Open or create the experiment history DB. Sets WAL mode and row factory."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection):
    """Create table and indexes if they don't exist."""
    conn.execute(CREATE_TABLE_SQL)
    conn.execute(CREATE_INDEX_SKILL_SQL)
    conn.execute(CREATE_INDEX_HASH_SQL)
    conn.commit()


ACTUAL_OUTPUT_MAX_LEN = 4000


def insert_experiment(
    conn: sqlite3.Connection,
    skill_name: str,
    iteration: int,
    variant_hash: str,
    body_diff: str,
    pass_rate: float,
    pass_rate_stddev: float,
    tokens_used: int,
    duration_ms: int,
    promoted: bool,
    mutation_rationale: str,
    rubric_score: float = None,
    composite_score: float = None,
    actual_output: str = None,
) -> int:
    """Insert a new experiment row. Returns the new row id.

    actual_output is truncated to 4000 chars at insert time (FR-46 retention policy).
    """
    if actual_output is not None and len(actual_output) > ACTUAL_OUTPUT_MAX_LEN:
        actual_output = actual_output[:ACTUAL_OUTPUT_MAX_LEN]
    cursor = conn.execute(
        """
        INSERT INTO experiments (
            skill_name, iteration, variant_hash, body_diff,
            pass_rate, pass_rate_stddev, tokens_used, duration_ms,
            promoted, mutation_rationale,
            rubric_score, composite_score, actual_output
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            skill_name, iteration, variant_hash, body_diff,
            pass_rate, pass_rate_stddev, tokens_used, duration_ms,
            int(promoted), mutation_rationale,
            rubric_score, composite_score, actual_output,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_history(conn: sqlite3.Connection, skill_name: str) -> list[dict]:
    """Return all experiments for a skill, newest first."""
    cursor = conn.execute(
        "SELECT * FROM experiments WHERE skill_name = ? ORDER BY created_at DESC",
        (skill_name,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_promoted_versions(conn: sqlite3.Connection, skill_name: str, n: int = 3) -> list[dict]:
    """Return the last N promoted experiments for a skill, newest first. Used for rollback."""
    cursor = conn.execute(
        """
        SELECT * FROM experiments
        WHERE skill_name = ? AND promoted = 1
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (skill_name, n),
    )
    return [dict(row) for row in cursor.fetchall()]


def retention_sweep(conn: sqlite3.Connection) -> int:
    """Set actual_output = NULL for unpromoted rows older than 90 days (FR-46).

    Returns the number of rows updated.
    """
    cursor = conn.execute(
        """
        UPDATE experiments
        SET actual_output = NULL
        WHERE promoted = 0
          AND actual_output IS NOT NULL
          AND created_at < datetime('now', '-90 days')
        """
    )
    conn.commit()
    return cursor.rowcount


def get_baseline_composite(conn: sqlite3.Connection, skill_name: str) -> float | None:
    """Return the most recent composite_score for a skill (FR-15 tournament selection).

    Returns None if no composite_score exists for the skill.
    """
    cursor = conn.execute(
        """
        SELECT composite_score FROM experiments
        WHERE skill_name = ? AND composite_score IS NOT NULL
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (skill_name,),
    )
    row = cursor.fetchone()
    return row["composite_score"] if row else None


def check_duplicate(conn: sqlite3.Connection, skill_name: str, variant_hash: str) -> bool:
    """Return True if this variant_hash already exists for the given skill (FR-8 dedup)."""
    cursor = conn.execute(
        "SELECT 1 FROM experiments WHERE skill_name = ? AND variant_hash = ? LIMIT 1",
        (skill_name, variant_hash),
    )
    return cursor.fetchone() is not None


if __name__ == "__main__":
    db_path = DEFAULT_DB_PATH
    conn = get_db(db_path)
    conn.close()
    print(f"Database initialized at {db_path}")
