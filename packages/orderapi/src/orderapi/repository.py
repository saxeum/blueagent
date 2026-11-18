"""Data access for orders: the SQL, and nothing above it.

Rows are validated into `Order` here, at the database edge, so no caller ever
sees a raw row. A missing row comes back as `None` and a write that matched
nothing as `0`; deciding that those are errors is the service's job.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping

from orderapi.db import rows
from orderapi.models import Order


def to_order(row: object) -> Order:
    """Validate one row into the entity, so a schema drift fails loudly."""
    if not isinstance(row, sqlite3.Row):
        raise TypeError("connection is missing its row_factory")
    # sqlite3.Row is a Sequence, so iterating it yields values; .keys() is the only key accessor.
    return Order.model_validate({column: row[column] for column in row.keys()})  # noqa: SIM118


def list_all(db: sqlite3.Connection) -> list[Order]:
    """Every order, by id."""
    return [to_order(row) for row in rows(db, "SELECT * FROM orders ORDER BY id")]


def find(db: sqlite3.Connection, order_id: int) -> Order | None:
    found = rows(db, "SELECT * FROM orders WHERE id = ?", (order_id,))
    return to_order(found[0]) if found else None


def insert(
    db: sqlite3.Connection, *, customer: str, item: str, quantity: int, status: str
) -> int | None:
    """Insert one order and return its id; `None` if SQLite reported none."""
    cursor = db.execute(
        "INSERT INTO orders (customer, item, quantity, status) VALUES (?, ?, ?, ?)",
        (customer, item, quantity, status),
    )
    db.commit()
    return cursor.lastrowid


def update(db: sqlite3.Connection, order_id: int, changes: Mapping[str, object]) -> int:
    """Apply the named columns only; returns rows changed."""
    assignments = ", ".join(f"{column} = ?" for column in changes)
    cursor = db.execute(
        f"UPDATE orders SET {assignments} WHERE id = ?", (*changes.values(), order_id)
    )
    db.commit()
    return cursor.rowcount


def delete(db: sqlite3.Connection, order_id: int) -> int:
    """Returns rows deleted."""
    cursor = db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    db.commit()
    return cursor.rowcount
