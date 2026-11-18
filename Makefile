# Drivers for the MCP server (root package) and the orders CRUD API (workspace member).

.DEFAULT_GOAL := help
.PHONY: help sync migrate mcp agent crud test check build

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-7s\033[0m %s\n", $$1, $$2}'

sync: ## Install every workspace member (`uv sync` alone skips them)
	uv sync --all-packages

migrate: ## Apply pending orders migrations (ORDERAPI_DB, default orders.db)
	uv run --package orderapi python -m orderapi.migrate

mcp: ## Run the greet MCP server over HTTP on :8000 for curl/exploration
	uv run --package greetmcp python -m greetmcp.server

agent: ## Ask the agent to call greet (spawns the server over stdio; MCP_URL= to use HTTP)
	uv run python -m blueagent.agent

test: ## Run the tests (MCP over the protocol, API over TestClient)
	uv run pytest -q

crud: ## Run the orders CRUD API on port 8001 (foreground)
	uv run --package orderapi uvicorn orderapi.main:app --port 8001

check: ## Type check the whole workspace
	uv run basedpyright

build: ## Build both wheels (and sdists) into dist/
	uv build --all-packages
