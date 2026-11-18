"""Tests for the service layer: the policy that a missing order is an error.

No HTTP here. These pin the rules the router relies on: what counts as absent,
and what happens to a patch that changes nothing.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from orderapi import service
from orderapi.db import connect
from orderapi.exceptions import OrderNotFound
from orderapi.models import Order


def create_ada(conn: sqlite3.Connection) -> Order:
    return service.create_order(
        conn, customer="Ada", item="widget", quantity=1, status="pending"
    )


def test_create_returns_the_stored_order(database: Path) -> None:
    with connect(database) as conn:
        order = create_ada(conn)

    assert order.id == 1
    assert order.customer == "Ada"


def test_get_of_a_missing_order_raises(database: Path) -> None:
    with connect(database) as conn, pytest.raises(OrderNotFound):
        _ = service.get_order(conn, 99)


def test_update_of_a_missing_order_raises(database: Path) -> None:
    with connect(database) as conn, pytest.raises(OrderNotFound):
        _ = service.update_order(conn, 99, {"status": "shipped"})


def test_empty_update_still_checks_the_order_exists(database: Path) -> None:
    with connect(database) as conn, pytest.raises(OrderNotFound):
        _ = service.update_order(conn, 99, {})


def test_delete_of_a_missing_order_raises(database: Path) -> None:
    with connect(database) as conn, pytest.raises(OrderNotFound):
        service.delete_order(conn, 99)


def test_deleted_order_is_gone(database: Path) -> None:
    with connect(database) as conn:
        order = create_ada(conn)
        service.delete_order(conn, order.id)

        with pytest.raises(OrderNotFound):
            _ = service.get_order(conn, order.id)
