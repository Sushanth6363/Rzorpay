"""Database initialization and connection factory for Unified Recovery Engine.

Configures SQLite connection settings (WAL mode, foreign keys, busy timeout)
and applies schema DDL idempotently.
"""

import os
import sqlite3
from pathlib import Path
from typing import Union

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_db_connection(db_path: Union[str, Path] = ":memory:") -> sqlite3.Connection:
    """Create and configure a standardized SQLite connection."""
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row

    # Configure mandatory pragmas
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    
    # Enable WAL mode for disk-backed databases (memory DBs remain in memory)
    if str(db_path) != ":memory:":
        cursor = conn.execute("PRAGMA journal_mode = WAL;")
        journal_mode = cursor.fetchone()[0]
        if journal_mode.lower() != "wal":
            raise RuntimeError(f"Failed to enable SQLite WAL mode. Active mode: {journal_mode}")

    # Verify foreign keys are enabled
    cursor = conn.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    if fk_status != 1:
        raise RuntimeError("Failed to enable SQLite foreign_keys pragma.")

    return conn


def init_db(db_path: Union[str, Path] = ":memory:") -> sqlite3.Connection:
    """Initialize database connection and apply schema DDL idempotently."""
    conn = get_db_connection(db_path)
    
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()
    return conn
