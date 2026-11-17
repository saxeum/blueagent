"""SQLite access and a forward-only migration runner for the orders database."""

from __future__ import annotations

import os
import sqlite3
from importlib import resources
from importlib.resources.abc import Traversable

from pydantic import TypeAdapter

MIGRATIONS_DIR = resources.files("orderapi").joinpath("migrations")

LEDGER = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def connect() -> sqlite3.Connection:
    # Read per connection, so tests can point each run at its own database.
    conn = sqlite3.connect(os.environ.get("ORDERAPI_DB", "orders.db"))
    conn.row_factory = sqlite3.Row
    return conn


def rows(conn: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[object]:
    """Fetch rows as opaque objects; sqlite3 types them Any, so callers prove them."""
    return list(conn.execute(sql, params).fetchall())


def migration_files() -> list[Traversable]:
    return sorted(
        (path for path in MIGRATIONS_DIR.iterdir() if path.name.endswith(".sql")),
        key=lambda path: path.name,
    )


def applied_versions(conn: sqlite3.Connection) -> set[str]:
    adapter: TypeAdapter[str] = TypeAdapter(str)
    versions: set[str] = set()
    for row in rows(conn, "SELECT version FROM schema_migrations"):
        if not isinstance(row, sqlite3.Row):
            raise TypeError("connection is missing its row_factory")
        versions.add(adapter.validate_python(row["version"]))
    return versions


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply every unapplied migration in filename order; return their versions."""
    _ = conn.execute(LEDGER)
    done = applied_versions(conn)
    applied: list[str] = []
    for path in migration_files():
        version = path.name.removesuffix(".sql")
        if version in done:
            continue
        _ = conn.executescript(path.read_text())
        _ = conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        applied.append(version)
    conn.commit()
    return applied
