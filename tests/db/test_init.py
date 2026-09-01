"""Acceptance tests for database initialization, WAL mode, and foreign keys.

Test Coverage:
- M2-01: Fresh DB initialization
- M2-02: Repeated DB initialization (idempotent)
- M2-03: WAL mode verified on disk database
- M2-04: Foreign keys pragma verified active
"""

import os
import tempfile
from pathlib import Path
import pytest
import sqlite3
from app.db.init import init_db, get_db_connection


def test_m2_01_fresh_db_initialization() -> None:
    """M2-01: Verify fresh database creates all required tables and indices."""
    conn = init_db(":memory:")
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    assert {"events", "opportunities", "contact_budgets", "audit_logs"}.issubset(tables)


def test_m2_02_repeated_db_initialization() -> None:
    """M2-02: Verify repeated initialization is idempotent and does not wipe data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        conn1 = init_db(db_path)
        conn1.execute(
            "INSERT INTO contact_budgets (merchant_id, customer_id, cap, reserved_count, consumed_count, updated_at) VALUES ('m1', 'c1', 3, 0, 0, '2026-09-01T00:00:00Z');"
        )
        conn1.commit()
        conn1.close()

        # Re-initialize on existing database
        conn2 = init_db(db_path)
        cursor = conn2.execute("SELECT count(*) FROM contact_budgets WHERE merchant_id='m1';")
        assert cursor.fetchone()[0] == 1
        conn2.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_m2_03_wal_mode_verified() -> None:
    """M2-03: Verify disk-backed SQLite database enables WAL journal mode."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        conn = init_db(db_path)
        cursor = conn.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal"
        conn.close()
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_m2_04_foreign_keys_verified() -> None:
    """M2-04: Verify foreign_keys pragma is enabled on SQLite connection."""
    conn = get_db_connection(":memory:")
    cursor = conn.execute("PRAGMA foreign_keys;")
    assert cursor.fetchone()[0] == 1
