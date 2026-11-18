# blueagent

A minimal agent, the MCP (Model Context Protocol) server it drives, and a CRUD
API to wrap later. Everything is a uv workspace: the agent is the root project, the
servers are members.

## Layout

```
pyproject.toml              workspace root: the `blueagent` agent package
uv.lock                     one lockfile for the whole workspace
src/blueagent/agent.py      pydantic-ai agent; tools come from the greet server (stdio, or HTTP via MCP_URL)
packages/greetmcp/          member: the MCP server, exposes `greet`, port 8000
    src/greetmcp/server.py  FastMCP over streamable HTTP
packages/orderapi/          member: orders API, port 8001
    pyproject.toml          owns its own dependencies (fastapi, uvicorn)
    src/orderapi/main.py    SQLite CRUD over an orders table
    src/orderapi/db.py      connection + forward-only migration runner
    src/orderapi/migrate.py `python -m orderapi.migrate`, run by `make migrate`
    src/orderapi/migrations/  0001 schema, 0002 seed data
Makefile                    `make` prints the available targets
```

The root project is `blueagent` (the agent); `packages/*` are members. That is the
uv-documented layout for "a root project with accompanying packages", and it keeps
`uv run` pointed at the agent while members are reachable with `--package`.

## Commands

```
make                    # help
make sync               # uv sync --all-packages
make mcp                # greet MCP server over HTTP on :8000, for curl
make agent              # ask the agent to call greet
make migrate            # apply pending migrations to ORDERAPI_DB (CI/CD step)
make crud               # orders CRUD API on :8001
make test               # agent + MCP protocol + API + migrations
make check              # basedpyright over the workspace
make build              # every wheel into dist/
```

`make agent` needs only a model key — it starts the server itself (see Transports).
Configuration:

| Variable | Default | Used by |
|---|---|---|
| `MCP_PORT` | `8000` | HTTP server (`python -m greetmcp.server`) |
| `MCP_URL` | unset | agent (`python -m blueagent.agent`); unset means spawn the server over stdio, set means connect to that HTTP endpoint |
| `AGENT_MODEL` | `deepseek:deepseek-flash` | agent; any pydantic-ai model id |
| `DEEPSEEK_API_KEY` | — | agent; read from the environment or a local `.env` |

Copy `.env.example` to `.env` and fill in the key. `.env` is gitignored; the
template is committed so the variable name is discoverable.

Tools return pydantic models, so a result arrives as `structuredContent`
(`{"message": "Hello, Ada!"}` for `greet`) with no FastMCP `{"result": ...}`
wrapper. The tool schemas are the contract the agent sees — nothing on the client
side re-describes them.

Watch out for the one that bites: **plain `uv sync` installs the root package and its
dependencies, not every member.** `greetmcp` is a dependency of the root, so it comes
along; `orderapi` is not, so `import orderapi` fails until `uv sync --all-packages`
(which is what `make sync` does). `uv run --package orderapi ...` syncs it on demand.

## Transports

Two, split by who is using them:

| | Command | Transport |
|---|---|---|
| Agent | `make agent` | **stdio** — the agent spawns `python -m greetmcp.server --stdio` itself |
| Humans, curl | `make mcp` | **HTTP** on `:8000`, sessions and JSON-RPC visible over the wire |

The agent uses HTTP only when you point it at a server with `MCP_URL`. Everything else
— no port, no prerequisite "start the server first" — is why stdio is the agent's
default: an agent host spawns its MCP servers, it does not expect to find one already
listening. HTTP stays because raw protocol observation needs it: `make mcp` serves it
for hand-written `curl`, and the wire-level assertions in `tests/test_mcp.py` go
through the SDK client, not through the Python API.

## The agent

`src/blueagent/agent.py` is deliberately tiny: one `Agent`, one toolset, one prompt.

```python
toolset = MCPToolset(url) if url else MCPToolset(STDIO)
Agent(model, toolsets=[toolset])
```

`MCPToolset` takes anything FastMCP can build a transport from: here a URL string, which
means streamable HTTP, or a `StdioTransport` that spawns
`python -m greetmcp.server --stdio`. The transport is inferred from the argument, so
neither one is named at the call site. The agent knows nothing about `greet`; it
discovers the tool from the server on connect, which is why a change to the server's
schemas shows up in the agent without touching this file.

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
server needs `fastmcp`, the orders API needs `fastapi`. `uv tree --package` shows each
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
