# newmcp

A toy MCP (Model Context Protocol) server and client, plus the small CRUD REST API
they are exercised against. Everything is a uv workspace.

## Layout

```
pyproject.toml              workspace root: the `newmcp` package, members under packages/
uv.lock                     one lockfile for the whole workspace
src/newmcp/
    my_server.py            FastMCP server over HTTP, exposes `greet`
    my_client.py            lists the server's tools, then calls `greet`
packages/orderapi/          workspace member: toy orders API, port 8001
    pyproject.toml          owns its own dependencies (fastapi, uvicorn)
    src/orderapi/main.py    SQLite CRUD over an orders table
    src/orderapi/db.py      connection + forward-only migration runner
    src/orderapi/migrate.py `python -m orderapi.migrate`, run by `make migrate`
    src/orderapi/migrations/  0001 schema, 0002 seed data
Makefile                    `make` prints the available targets
```

The root project is `newmcp`; `packages/*` are members. That is the uv-documented
layout for "a root project with accompanying packages", and it keeps `uv run`
pointed at the root package while members are reachable with `--package`.

## Commands

```
make                    # help
make sync               # uv sync --all-packages
make mcp                # MCP server on :8000
make client             # list tools, call greet
make migrate            # apply pending migrations to ORDERAPI_DB (CI/CD step)
make crud               # orders CRUD API on :8001
make test               # MCP over the protocol + API through TestClient
make check              # basedpyright over the workspace
make build              # both wheels into dist/
```

Configuration, one knob per side of the connection:

| Variable | Default | Used by |
|---|---|---|
| `MCP_PORT` | `8000` | server (`python -m newmcp.my_server`) |
| `MCP_URL` | `http://127.0.0.1:8000/mcp` | client (`python -m newmcp.my_client`) |

Tools return pydantic models, so a result arrives as `structuredContent`
(`{"message": "Hello, Ada!"}` for `greet`) with no FastMCP `{"result": ...}`
wrapper. Clients validate that shape rather than trusting it.

Watch out for the one that bites: **plain `uv sync` installs the root package but
not the members**, so `import orderapi` fails until you run `uv sync --all-packages`
(which is what `make sync` does). Likewise `uv run --package orderapi ...` syncs
that member on demand.

## The CRUD API

SQLite file `orders.db` in the working directory, overridable with `ORDERAPI_DB`.

The schema comes from `migrations/*.sql`. Nothing is migrated at startup: run
`make migrate` (`python -m orderapi.migrate`) as a CI/CD step before serving, and
again after adding a migration. The runner records each version in
`schema_migrations`, so `0002_seed_orders.sql`'s five orders are inserted once, ever.

On a database that has never been migrated the API returns `500` — the app is
deliberately unaware of migrations and does not create tables. Endpoints:

| Method | Path | Notes |
|---|---|---|
| `GET` | `/orders` | list, ordered by id |
| `POST` | `/orders` | `customer`, `item`, `quantity` (>=1, default 1), `status` (default `pending`) |
| `GET` | `/orders/{id}` | `404` if absent |
| `PATCH` | `/orders/{id}` | partial update; omitted fields unchanged |
| `DELETE` | `/orders/{id}` | `204`; `404` if absent |

## Why a workspace here

Two things are genuinely separate: the MCP server needs `fastmcp`, the toy API
needs `fastapi`. `uv tree --package orderapi` shows fastapi under `orderapi` and
nothing under `newmcp`. Both share one `uv.lock`, so their dependencies are
resolved together, and each builds its own wheel (`make build`).

What a workspace does **not** give you, per the uv docs: dependency isolation at
import time. A single venv serves the whole workspace, so `newmcp` *can* import
`fastapi` if someone writes that line — uv cannot stop it. Members are separate
packages, not separate environments.

## Tests

`make test` runs two suites. `tests/test_mcp.py` drives a real server process through
the MCP protocol. `packages/orderapi/tests/` covers the API and the migration runner;
each API test migrates a throwaway database with the same runner `make migrate` uses,
then empties it so the test creates every row it asserts on — the seed data is for
local poking, not for tests.

## Type checking

`basedpyright` at `recommended` level, configured in the root `pyproject.toml`
and run over the workspace by `make check`. `Any` from `sqlite3` and from MCP
JSON is narrowed at the boundary (validated with pydantic / `isinstance`), never
cast.
