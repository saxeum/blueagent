"""The HTTP contract: what a client sends and what it receives.

These are not the entity. `OrderResponse` is built from `Order` so the wire
shape can change without touching the domain model.
"""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    """Fields a client supplies when creating an order."""

    customer: str
    item: str
    quantity: int = Field(default=1, ge=1)
    status: str = "pending"


class OrderUpdate(BaseModel):
    """Fields a client may change; omitted ones are left alone."""

    customer: str | None = None
    item: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    status: str | None = None


class OrderResponse(BaseModel):
    """What the API returns for one order."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: int
    customer: str
    item: str
    quantity: int
    status: str
