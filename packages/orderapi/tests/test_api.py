"""CRUD tests for the orders API, through FastAPI's TestClient.

Each test gets its own database: migrated with the same runner `make migrate` uses,
then emptied so the test creates every row it asserts on.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from orderapi.db import apply_migrations, connect
from orderapi.main import Order, app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("ORDERAPI_DB", str(tmp_path / "orders.db"))
    with connect() as conn:
        _ = apply_migrations(conn)
        # The seed migration is for local poking; these tests bring their own rows.
        _ = conn.execute("DELETE FROM orders")
        _ = conn.execute("DELETE FROM sqlite_sequence WHERE name = 'orders'")
        conn.commit()
    with TestClient(app) as test_client:
        yield test_client


def create(client: TestClient, **overrides: object) -> Order:
    payload: dict[str, object] = {"customer": "Ada", "item": "widget"} | overrides
    response = client.post("/orders", json=payload)
    assert response.status_code == 201, response.text
    return Order.model_validate_json(response.text)


def list_orders(client: TestClient) -> list[Order]:
    return TypeAdapter(list[Order]).validate_json(client.get("/orders").text)


def test_empty_table_lists_nothing(client: TestClient) -> None:
    assert list_orders(client) == []


def test_create_applies_defaults_and_returns_an_id(client: TestClient) -> None:
    created = create(client, quantity=3)

    assert created.id == 1
    assert created.quantity == 3
    assert created.status == "pending"
    assert list_orders(client) == [created]


def test_create_rejects_quantity_below_one(client: TestClient) -> None:
    response = client.post("/orders", json={"customer": "Ada", "item": "widget", "quantity": 0})

    assert response.status_code == 422


def test_get_missing_order_is_404(client: TestClient) -> None:
    assert client.get("/orders/99").status_code == 404


def test_patch_changes_only_named_fields(client: TestClient) -> None:
    created = create(client)

    patched = Order.model_validate_json(client.patch(f"/orders/{created.id}", json={"status": "shipped"}).text)

    assert patched.status == "shipped"
    assert patched.customer == "Ada"
    assert patched.quantity == 1


def test_list_returns_each_created_order(client: TestClient) -> None:
    _ = create(client, customer="Ada")
    _ = create(client, customer="Grace", status="shipped")

    assert [order.customer for order in list_orders(client)] == ["Ada", "Grace"]


def test_delete_removes_only_that_order(client: TestClient) -> None:
    kept = create(client, customer="Ada")
    doomed = create(client, customer="Grace")

    assert client.delete(f"/orders/{doomed.id}").status_code == 204
    assert client.get(f"/orders/{doomed.id}").status_code == 404
    assert list_orders(client) == [kept]
