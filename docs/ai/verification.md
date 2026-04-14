# Verification checklist

Run the smallest set that covers your change. CI reference: `.github/workflows/test.yml`, `.github/workflows/lint.yml`.

## Environment

```bash
uv sync --group dev
```

## Always safe for local iteration

| Check | Command |
|-------|---------|
| CLI parses | `uv run doctranslate --help` |
| Assets (if touching models/assets) | `uv run doctranslate --warmup` |
| Unit tests | `uv run pytest tests/ -q` |
| Single file / test node | `uv run pytest tests/<file>::<test> -q` |

## Lint (matches CI)

- Ruff is run in CI via `astral-sh/ruff-action` on push; locally: `uv run ruff check doctranslate tests` and `uv run ruff format doctranslate tests` (or project-equivalent).

## Translator / config changes

- Router/local validation path: `uv run doctranslate --translator router --config <file> --validate-translators` or local equivalent per [Local translation](../local-translation.md).
- Add or extend tests in `tests/`; avoid requiring paid APIs in default tests (CI job is “no paid APIs”).

## Docs changes

- After editing `docs/` or `mkdocs.yml`: `uv run mkdocs build --strict` (if available in dev group) or `mkdocs build --strict` from an env with dev deps.

## PDF / IL changes

- Prefer a regression test under `tests/` that exercises the stage or parsing behavior you touched.
- Do not commit manual edits to generated `il_version_1.{rng,xsd,py}`; regenerate from `.rnc` per Contributing.

## Done means

- Targeted tests pass; no new Ruff issues on touched paths.
- User-visible flags or TOML behavior documented in `README.md` and/or `docs/configuration.md` (and local/multi docs if applicable).
