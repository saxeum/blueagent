# Toy drivers for the MCP server (root package) and the orders CRUD API (workspace member).

.DEFAULT_GOAL := help
.PHONY: help sync mcp client crud check build

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-7s\033[0m %s\n", $$1, $$2}'

sync: ## Install every workspace member (`uv sync` alone skips them)
	uv sync --all-packages

mcp: ## Run the MCP server on port 8000 (foreground)
	uv run python -m newmcp.my_server

client: ## List the server's tools, then call greet
	uv run python -m newmcp.my_client

crud: ## Run the orders CRUD API on port 8001 (foreground)
	uv run --package orderapi uvicorn orderapi.main:app --port 8001

check: ## Type check the whole workspace
	uv run basedpyright

build: ## Build both wheels (and sdists) into dist/
	uv build --all-packages
