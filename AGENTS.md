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

## Issues, commits and pull requests

One issue per change, one small PR per issue, several small commits inside it — each commit
one idea, so a reviewer can read them in order. Never batch unrelated changes into one PR,
and never grow a PR after it has been reviewed: a correction is a new branch from that point.

Open the issue first (`gh issue create` with what/why/acceptance), reference it in the PR
body, and keep the acceptance block runnable — a fenced block holding only the command, with
the expected result written below it.

Commit and push only on a feature branch. Never push to `master`, never merge a PR, never
approve your own work. The human reviews and merges.

The PR body is the review artefact, so it carries: what changed and why, the commands run
with their real output, what was deliberately left out, and any trade-off a reviewer must
decide rather than discover. Hand over with the branch name and base SHA:

```bash
git rev-parse --abbrev-ref HEAD
```

```bash
git rev-parse --short HEAD
```
