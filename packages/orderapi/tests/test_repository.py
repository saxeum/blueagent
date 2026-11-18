"""Tests for the data-access layer, with no service or HTTP in the way.

Rows cross the boundary as `Order`; a missing row is `None` and a write that
matched nothing is `0`. Turning those into errors is the service's job, so these
assert the raw facts it relies on.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from orderapi import repository
from orderapi.db import connect
from orderapi.models import Order


def insert_ada(conn: sqlite3.Connection) -> int:
    order_id = repository.insert(
        conn, customer="Ada", item="widget", quantity=1, status="pending"
    )
    assert order_id is not None
    return order_id


def test_insert_returns_the_new_id_and_find_reads_it_back(database: Path) -> None:
    with connect(database) as conn:
        order_id = insert_ada(conn)
        found = repository.find(conn, order_id)

    assert isinstance(found, Order)
    assert found.customer == "Ada"
    assert found.quantity == 1


def test_list_all_is_ordered_by_id(database: Path) -> None:
    with connect(database) as conn:
        _ = insert_ada(conn)
        _ = repository.insert(
            conn, customer="Grace", item="widget", quantity=1, status="shipped"
        )

        orders = repository.list_all(conn)

    assert [order.customer for order in orders] == ["Ada", "Grace"]


def test_update_applies_only_named_columns(database: Path) -> None:
    with connect(database) as conn:
        order_id = insert_ada(conn)

        assert repository.update(conn, order_id, {"status": "shipped"}) == 1

        found = repository.find(conn, order_id)

    assert isinstance(found, Order)
    assert found.status == "shipped"
    assert found.customer == "Ada"


def test_delete_removes_the_row(database: Path) -> None:
    with connect(database) as conn:
        order_id = insert_ada(conn)

        assert repository.delete(conn, order_id) == 1
        assert repository.find(conn, order_id) is None


def test_missing_row_is_none_and_writes_report_zero(database: Path) -> None:
    with connect(database) as conn:
        assert repository.find(conn, 99) is None
        assert repository.update(conn, 99, {"status": "shipped"}) == 0
        assert repository.delete(conn, 99) == 0
