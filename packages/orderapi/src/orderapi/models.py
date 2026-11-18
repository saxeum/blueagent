"""The orders domain model: what an order is, independent of HTTP and SQL."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Order(BaseModel):
    """One stored order, as every layer agrees to see it."""

    id: int
    customer: str
    item: str
    quantity: int = Field(ge=1)
    status: str
