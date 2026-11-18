"""The FastAPI application: wiring, and the mapping from domain errors to HTTP.

Routes live in `orderapi.router`, logic in `orderapi.service`, SQL in
`orderapi.repository`. This module only assembles them and turns an
`OrderNotFound` into a 404, so no other layer needs to know about status codes.
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from orderapi.exceptions import OrderNotFound
from orderapi.router import router


async def order_not_found(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


app = FastAPI(title="Order API", version="0.1.0")
app.include_router(router)
app.add_exception_handler(OrderNotFound, order_not_found)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
