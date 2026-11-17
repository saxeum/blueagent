# newmcp

A minimal agent, the MCP (Model Context Protocol) server it drives, and a toy CRUD
API to wrap later. Everything is a uv workspace: the agent is the root project, the
servers are members.

## Layout

```
pyproject.toml              workspace root: the `newmcp` agent package
uv.lock                     one lockfile for the whole workspace
src/newmcp/agent.py         pydantic-ai agent; tools come from an MCP server over HTTP
packages/greetmcp/          member: the MCP server, exposes `greet`, port 8000
    src/greetmcp/server.py  FastMCP over streamable HTTP
packages/orderapi/          member: toy orders API, port 8001
    pyproject.toml          owns its own dependencies (fastapi, uvicorn)
    src/orderapi/main.py    SQLite CRUD over an orders table
    src/orderapi/db.py      connection + forward-only migration runner
    src/orderapi/migrate.py `python -m orderapi.migrate`, run by `make migrate`
    src/orderapi/migrations/  0001 schema, 0002 seed data
Makefile                    `make` prints the available targets
```

The root project is `newmcp` (the agent); `packages/*` are members. That is the
uv-documented layout for "a root project with accompanying packages", and it keeps
`uv run` pointed at the agent while members are reachable with `--package`.

## Commands

```
make                    # help
make sync               # uv sync --all-packages
make mcp                # greet MCP server on :8000
make agent              # ask the agent to call greet over MCP
make migrate            # apply pending migrations to ORDERAPI_DB (CI/CD step)
make crud               # orders CRUD API on :8001
make test               # agent + MCP protocol + API + migrations
make check              # basedpyright over the workspace
make build              # every wheel into dist/
```

`make agent` needs the server running (`make mcp`) and a model key. Configuration:

| Variable | Default | Used by |
|---|---|---|
| `MCP_PORT` | `8000` | server (`python -m greetmcp.server`) |
| `MCP_URL` | `http://127.0.0.1:8000/mcp` | agent (`python -m newmcp.agent`) |
| `AGENT_MODEL` | `deepseek:deepseek-flash` | agent; any pydantic-ai model id |
| `DEEPSEEK_API_KEY` | — | agent; read from the environment or a local `.env` |

Copy `.env.example` to `.env` and fill in the key. `.env` is gitignored; the
template is committed so the variable name is discoverable.

Tools return pydantic models, so a result arrives as `structuredContent`
(`{"message": "Hello, Ada!"}` for `greet`) with no FastMCP `{"result": ...}`
wrapper. The tool schemas are the contract the agent sees — nothing on the client
side re-describes them.

Watch out for the one that bites: **plain `uv sync` installs the root package but
not the members**, so `import greetmcp` fails until you run `uv sync --all-packages`
(which is what `make sync` does). Likewise `uv run --package orderapi ...` syncs
that member on demand.

## The agent

`src/newmcp/agent.py` is deliberately tiny: one `Agent`, one toolset, one prompt.

```python
Agent(MODEL, toolsets=[MCPToolset(FastMCPClient(URL))])
```

`MCPToolset` takes a client, and the client takes the URL — pydantic-ai V2 removed
the older `MCPServerStreamableHTTP` class, so the transport is inferred from the
argument rather than named. The agent knows nothing about `greet`; it discovers the
tool from the server on connect, which is why a change to the server's schemas
shows up in the agent without touching this file.

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

Three things are genuinely separate: the agent needs `pydantic-ai-slim`, the greet
server needs `fastmcp`, the toy API needs `fastapi`. `uv tree --package` shows each
set under its own package. They share one `uv.lock`, so dependencies resolve
together, and each builds its own wheel (`make build`).

What a workspace does **not** give you, per the uv docs: dependency isolation at
import time. A single venv serves the whole workspace, so the agent *can* import
`fastapi` if someone writes that line — uv cannot stop it. Members are separate
packages, not separate environments.

## Tests

`make test` runs three suites, none of which needs an API key:

- `tests/test_agent.py` — the agent driven by pydantic-ai's `TestModel`, talking to
  a real server process, asserting `greet` is actually called and its result reaches
  the output.
- `tests/test_mcp.py` — the server through the MCP protocol: tool listing, schemas,
  calls, and an unknown tool as the negative control.
- `packages/orderapi/tests/` — the API and the migration runner; each API test
  migrates a throwaway database with the same runner `make migrate` uses, then
  empties it so the test creates every row it asserts on.

## Type checking

`basedpyright` at `recommended` level, configured in the root `pyproject.toml`
and run over the workspace by `make check`. `Any` from `sqlite3` and from MCP
JSON is narrowed at the boundary (validated with pydantic / `isinstance`), never
cast.
