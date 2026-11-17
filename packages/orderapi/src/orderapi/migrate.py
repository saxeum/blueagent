"""Apply pending migrations: `uv run --package orderapi python -m orderapi.migrate`."""

from __future__ import annotations

from orderapi.db import apply_migrations, connect


def main() -> None:
    with connect() as conn:
        applied = apply_migrations(conn)
    for version in applied:
        print(f"applied {version}")
    if not applied:
        print("no pending migrations")


if __name__ == "__main__":
    main()
