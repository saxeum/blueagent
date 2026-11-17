"""Tests for the forward-only migration runner itself."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from orderapi.db import applied_versions, apply_migrations, connect, migration_files


@pytest.fixture
def conn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[sqlite3.Connection]:
    monkeypatch.setenv("ORDERAPI_DB", str(tmp_path / "orders.db"))
    connection = connect()
    yield connection
    connection.close()


def scalar(conn: sqlite3.Connection, sql: str) -> int:
    # fetchone() is Any in the stubs; validate it into an int at the boundary.
    return TypeAdapter(int).validate_python(conn.execute(sql).fetchone()[0])


def test_migrations_are_listed_in_filename_order() -> None:
    assert [path.name for path in migration_files()] == [
        "0001_orders_table.sql",
        "0002_seed_orders.sql",
    ]


def test_apply_is_idempotent_and_seeds_once(conn: sqlite3.Connection) -> None:
    first = apply_migrations(conn)
    second = apply_migrations(conn)

    assert first == ["0001_orders_table", "0002_seed_orders"]
    assert second == []
    assert scalar(conn, "SELECT COUNT(*) FROM orders") == 5


def test_ledger_records_each_applied_version(conn: sqlite3.Connection) -> None:
    _ = apply_migrations(conn)

    assert applied_versions(conn) == {"0001_orders_table", "0002_seed_orders"}
