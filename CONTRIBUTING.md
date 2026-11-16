# Contributing to aethersy-research

Thank you for your interest in contributing.

## Development setup

```bash
git clone https://github.com/mattiadeblasio94-jpg/aethersy-research.git
cd aethersy-research
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running tests

```bash
python -m pytest tests/ -v
```

All tests must pass before submitting a PR. The full suite takes a minute or two; run a single file while iterating.

## Code style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting:

```bash
ruff check src/ tests/
```

Configuration is in `pyproject.toml`. Line length is 100 characters.

## Type checking

```bash
mypy src/aethersy_research/
```

Strict mode is enabled in `pyproject.toml`.

## Submitting changes

1. Fork the repository.
2. Create a branch from `main`.
3. Make your changes with tests.
4. Run `ruff check src/ tests/` and `python -m pytest tests/`.
5. Open a pull request against `main`.

Keep PRs focused on a single change. Include a clear description of what changed and why.

## Reporting issues

Open an issue at [github.com/mattiadeblasio94-jpg/aethersy-research/issues](https://github.com/mattiadeblasio94-jpg/aethersy-research/issues). Include:

- What you expected to happen
- What actually happened
- Steps to reproduce
- aethersy-research version (`aethersy-research --version`)
- Python version and OS

## Architecture overview

- `src/aethersy_research/core/` -- vault management, sync engine, frontmatter parsing, SQLite schema
- `src/aethersy_research/cli/` -- typer CLI commands, output formatting
- `src/aethersy_research/search/` -- FTS5 search engine, filters, ranking
- `src/aethersy_research/models/` -- Pydantic models for notes, output envelopes
- `src/aethersy_research/graph/` -- link parsing (shared patterns)
- `src/aethersy_research/indexgen/` -- auto-generated index page builder
- `src/aethersy_research/web/` -- pluggable web providers (fetch and search backends)
- `src/aethersy_research/export/` -- export formatters
- `src/aethersy_research/mcp/` -- MCP server exposing research-base tools to agents
- `src/aethersy_research/skills/` -- bundled research skills installed into the harness
- `src/aethersy_research/serve/` -- lightweight web UI server
- `tests/` -- pytest test suite

The key design principle: markdown files are the source of truth, SQLite is a derived cache that can be rebuilt at any time with `aethersy-research sync --force`.
