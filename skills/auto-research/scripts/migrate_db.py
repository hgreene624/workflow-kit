"""
migrate_db.py — Add v3 columns to the experiment history database.

Adds rubric_score, composite_score, and actual_output to the experiments table.
Safe to run multiple times (idempotent). Run outside any active research cycle.
"""

import sqlite3
import sys
from pathlib import Path

DEFAULT_DB_PATH = Path.home() / ".claude" / "skills" / "auto-research" / "experiment_history.db"

NEW_COLUMNS = [
    ("rubric_score", "REAL"),
    ("composite_score", "REAL"),
    ("actual_output", "TEXT"),
]


def get_existing_columns(conn: sqlite3.Connection) -> set[str]:
    cursor = conn.execute("PRAGMA table_info(experiments)")
    return {row[1] for row in cursor.fetchall()}


def migrate(db_path: Path) -> None:
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    # WAL mode is already set on this DB; re-asserting is safe and a no-op if already set.
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        existing = get_existing_columns(conn)

        added = []
        skipped = []

        for col_name, col_type in NEW_COLUMNS:
            if col_name in existing:
                skipped.append(col_name)
                continue
            conn.execute(f"ALTER TABLE experiments ADD COLUMN {col_name} {col_type}")
            added.append(col_name)

        conn.commit()

        if added:
            print(f"Added columns: {', '.join(added)}")
        if skipped:
            print(f"Already present (skipped): {', '.join(skipped)}")
        if not added and not skipped:
            print("Nothing to do.")

        # Verify
        final_cols = get_existing_columns(conn)
        for col_name, _ in NEW_COLUMNS:
            if col_name not in final_cols:
                print(f"ERROR: Column {col_name} missing after migration!", file=sys.stderr)
                sys.exit(1)

        print(f"Migration complete. DB: {db_path}")

    finally:
        conn.close()


if __name__ == "__main__":
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB_PATH
    migrate(db_path)
