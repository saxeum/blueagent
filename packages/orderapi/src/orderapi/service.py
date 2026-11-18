"""Order business logic: what the application does, with no HTTP in sight.

The repository reports what SQLite did; this layer decides what that means. A
missing row is an `OrderNotFound` here, not a `None` each caller must remember
to check and not a status code.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping

from orderapi import repository
from orderapi.exceptions import OrderNotFound
from orderapi.models import Order


def list_orders(db: sqlite3.Connection) -> list[Order]:
    return repository.list_all(db)


def get_order(db: sqlite3.Connection, order_id: int) -> Order:
    order = repository.find(db, order_id)
    if order is None:
        raise OrderNotFound(order_id)
    return order


def create_order(
    db: sqlite3.Connection, *, customer: str, item: str, quantity: int, status: str
) -> Order:
    order_id = repository.insert(
        db, customer=customer, item=item, quantity=quantity, status=status
    )
    if order_id is None:
        raise RuntimeError("insert returned no row id")
    return get_order(db, order_id)


def update_order(
    db: sqlite3.Connection, order_id: int, changes: Mapping[str, object]
) -> Order:
    """An empty patch is a no-op, but the order still has to exist."""
    if changes and repository.update(db, order_id, changes) == 0:
        raise OrderNotFound(order_id)
    return get_order(db, order_id)


def delete_order(db: sqlite3.Connection, order_id: int) -> None:
    if repository.delete(db, order_id) == 0:
        raise OrderNotFound(order_id)
