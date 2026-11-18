"""FastAPI dependencies: the request-scoped database connection."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends

from orderapi.db import connect


def get_db() -> Iterator[sqlite3.Connection]:
    """One connection per request, closed when the request ends."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


Db = Annotated[sqlite3.Connection, Depends(get_db)]
