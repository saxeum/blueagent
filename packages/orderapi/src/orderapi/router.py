"""The orders endpoints: request parsing, status codes, response shapes."""

from __future__ import annotations

from fastapi import APIRouter

from orderapi import service
from orderapi.dependencies import Db
from orderapi.schemas import OrderCreate, OrderResponse, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("")
def list_orders(db: Db) -> list[OrderResponse]:
    return [OrderResponse.model_validate(order) for order in service.list_orders(db)]


@router.post("", status_code=201)
def create_order(body: OrderCreate, db: Db) -> OrderResponse:
    order = service.create_order(
        db,
        customer=body.customer,
        item=body.item,
        quantity=body.quantity,
        status=body.status,
    )
    return OrderResponse.model_validate(order)


@router.get("/{order_id}")
def get_order(order_id: int, db: Db) -> OrderResponse:
    return OrderResponse.model_validate(service.get_order(db, order_id))


@router.patch("/{order_id}")
def update_order(order_id: int, body: OrderUpdate, db: Db) -> OrderResponse:
    changes = body.model_dump(exclude_none=True)
    return OrderResponse.model_validate(service.update_order(db, order_id, changes))


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Db) -> None:
    service.delete_order(db, order_id)
