# Project instructions (newmcp)

## Python version

Python 3.14 only. `requires-python = ">=3.14"` in every `pyproject.toml` stays as it is —
do not widen it to accommodate an older interpreter, and do not add version-guarded code.

## Checks after every code change

Once your edits are done, run all three from the repo root and report the real output —
never "verified" without it:

```bash
uv run ruff check src packages tests
```

```bash
uv run basedpyright
```

```bash
uv run pytest -q
```

`make check` and `make test` wrap the same gates. After a dependency change also run
`make sync` (`uv sync --all-packages`, because plain `uv sync` skips workspace members).

If a check fails: fix it, or say plainly which one fails and why. Do not report a gate as
green from memory, and do not "fix" a finding by disabling the rule unless the human says so.

`ruff` is pinned in the `dev` group and configured in `pyproject.toml` (`[tool.ruff]`, with
`newmcp` and `orderapi` declared as first-party), so all three are reproducible gates. The same
three run in `.github/workflows/test.yml`, which the required `test` check on `master` uses.

## Never commit

Do not commit, stage, amend, or push. Leave every change in the working tree, including new
files, and finish by naming what should be reviewed:

```bash
git rev-parse --abbrev-ref HEAD
```

```bash
git rev-parse --short HEAD
```

Report it in one line, e.g. `branch master, base b476508` — the human reviews that SHA
against `git diff <sha>` plus `git status --short` for untracked files, and commits themselves.
