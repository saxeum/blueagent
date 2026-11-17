"""CRUD tests for the toy orders API, through FastAPI's TestClient."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from orderapi.main import Order, app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("ORDERAPI_DB", str(tmp_path / "orders.db"))
    with TestClient(app) as test_client:
        yield test_client


def create(client: TestClient, **overrides: object) -> Order:
    payload: dict[str, object] = {"customer": "Ada", "item": "widget"} | overrides
    response = client.post("/orders", json=payload)
    assert response.status_code == 201, response.text
    return Order.model_validate_json(response.text)


def test_empty_database_lists_nothing(client: TestClient) -> None:
    response = client.get("/orders")

    assert response.status_code == 200
    assert response.json() == []


def test_create_applies_defaults_and_returns_an_id(client: TestClient) -> None:
    created = create(client, quantity=3)

    assert created.id == 1
    assert created.quantity == 3
    assert created.status == "pending"


def test_create_rejects_quantity_below_one(client: TestClient) -> None:
    response = client.post("/orders", json={"customer": "Ada", "item": "widget", "quantity": 0})

    assert response.status_code == 422


def test_get_missing_order_is_404(client: TestClient) -> None:
    assert client.get("/orders/99").status_code == 404


def test_patch_changes_only_named_fields(client: TestClient) -> None:
    _ = create(client)

    patched = Order.model_validate_json(client.patch("/orders/1", json={"status": "shipped"}).text)

    assert patched.status == "shipped"
    assert patched.customer == "Ada"
    assert patched.quantity == 1


def test_delete_removes_the_order(client: TestClient) -> None:
    _ = create(client)

    assert client.delete("/orders/1").status_code == 204
    assert client.get("/orders/1").status_code == 404
    assert client.get("/orders").json() == []
