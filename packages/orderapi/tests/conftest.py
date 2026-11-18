"""Shared fixtures: a migrated, empty orders database, and a client over it."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from orderapi.db import apply_migrations, connect
from orderapi.main import app


def migrated_db(tmp_path: Path) -> Path:
    """A migrated database with no rows, so each test creates what it asserts on."""
    db_path = tmp_path / "orders.db"
    with connect(db_path) as conn:
        _ = apply_migrations(conn)
        # The seed migration is for local poking; these tests bring their own rows.
        _ = conn.execute("DELETE FROM orders")
        _ = conn.execute("DELETE FROM sqlite_sequence WHERE name = 'orders'")
        conn.commit()
    return db_path


@pytest.fixture
def database(tmp_path: Path) -> Iterator[Path]:
    yield migrated_db(tmp_path)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("ORDERAPI_DB", str(tmp_path / "orders.db"))
    _ = migrated_db(tmp_path)
    with TestClient(app) as test_client:
        yield test_client
