"""A toy CRUD REST API over an SQLite orders table, for exercising MCP tooling."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

DB_PATH = os.environ.get("ORDERAPI_DB", "orders.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT NOT NULL,
    item TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending'
)
"""


class OrderInput(BaseModel):
    """Fields a client supplies when creating an order."""

    customer: str
    item: str
    quantity: int = Field(default=1, ge=1)
    status: str = "pending"


class Order(OrderInput):
    id: int


class OrderPatch(BaseModel):
    """Fields a client may change; omitted ones are left alone."""

    customer: str | None = None
    item: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    status: str | None = None


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


Db = Annotated[sqlite3.Connection, Depends(get_db)]


def rows(db: sqlite3.Connection, sql: str, params: tuple[object, ...] = ()) -> list[object]:
    """Fetch rows as opaque objects; sqlite3 types them Any, so to_order proves them."""
    return list(db.execute(sql, params).fetchall())


def to_order(row: object) -> Order:
    """Validate one row into the model, so a schema drift fails loudly."""
    if not isinstance(row, sqlite3.Row):
        raise HTTPException(status_code=500, detail="connection is missing its row_factory")
    # sqlite3.Row is a Sequence, so iterating it yields values; .keys() is the only key accessor.
    return Order.model_validate({column: row[column] for column in row.keys()})  # noqa: SIM118


def fetch(db: sqlite3.Connection, order_id: int) -> Order:
    found = rows(db, "SELECT * FROM orders WHERE id = ?", (order_id,))
    if not found:
        raise HTTPException(status_code=404, detail=f"No order {order_id}")
    return to_order(found[0])


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    with connect() as conn:
        _ = conn.executescript(SCHEMA)
    yield


app = FastAPI(title="Order API", version="0.1.0", lifespan=lifespan)


@app.get("/orders")
def list_orders(db: Db) -> list[Order]:
    return [to_order(row) for row in rows(db, "SELECT * FROM orders ORDER BY id")]


@app.post("/orders", status_code=201)
def create_order(order: OrderInput, db: Db) -> Order:
    cursor = db.execute(
        "INSERT INTO orders (customer, item, quantity, status) VALUES (?, ?, ?, ?)",
        (order.customer, order.item, order.quantity, order.status),
    )
    db.commit()
    if cursor.lastrowid is None:
        raise HTTPException(status_code=500, detail="insert returned no row id")
    return fetch(db, cursor.lastrowid)


@app.get("/orders/{order_id}")
def get_order(order_id: int, db: Db) -> Order:
    return fetch(db, order_id)


@app.patch("/orders/{order_id}")
def update_order(order_id: int, patch: OrderPatch, db: Db) -> Order:
    changes = patch.model_dump(exclude_none=True)
    if not changes:
        return fetch(db, order_id)
    assignments = ", ".join(f"{column} = ?" for column in changes)
    cursor = db.execute(f"UPDATE orders SET {assignments} WHERE id = ?", (*changes.values(), order_id))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"No order {order_id}")
    return fetch(db, order_id)


@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int, db: Db) -> None:
    cursor = db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"No order {order_id}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
