"""Domain errors, raised by the service and mapped to HTTP by the application."""

from __future__ import annotations


class OrderNotFound(Exception):
    """No order exists with that id."""

    order_id: int

    def __init__(self, order_id: int) -> None:
        super().__init__(f"No order {order_id}")
        self.order_id = order_id
