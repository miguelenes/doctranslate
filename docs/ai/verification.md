# Verification checklist

Run the smallest set that covers your change. CI reference: `.github/workflows/test.yml`, `.github/workflows/lint.yml`.

## Environment

```bash
uv sync --locked --group dev --extra full
```

For a **minimal** environment (schemas types only), `uv sync --locked --group dev` is enough; see [Package layers](package-layers.md).

If you change `pyproject.toml` dependencies, run **`uv lock`** and commit **`uv.lock`** so CI (`uv sync --locked`) stays in sync.

## Always safe for local iteration

| Check | Command |
|-------|---------|
| CLI parses | `uv run doctranslate --help` and `uv run doc-translate --help` |
| Assets (if touching models/assets) | `uv run doctranslate assets warmup` |
| Unit tests | `uv run pytest tests/ -q` |
| Single file / test node | `uv run pytest tests/<file>::<test> -q` |

## Lint (matches CI)

- Ruff is run in CI via `astral-sh/ruff-action` on push; locally: `uv run ruff check doctranslate tests` and `uv run ruff format doctranslate tests` (or project-equivalent).

## Translator / config changes

- Router/local validation: `uv run doctranslate config validate --translator router -c <file>` or `... --translator local ...` per [Local translation](../local-translation.md).
- Add or extend tests in `tests/`; avoid requiring paid APIs in default tests (CI job is “no paid APIs”).

## Docs changes

- After editing `docs/` or `mkdocs.yml`: `NO_MKDOCS_2_WARNING=1 uv run mkdocs build --strict` from an env with dev deps (suppresses the upstream MkDocs 2.0 advisory once you rely on the `mkdocs<2` pin). **Note:** git metadata plugins may warn on `--strict` for **brand-new, uncommitted** Markdown files; commit them or run `uv run mkdocs build` (non-strict) for a quick smoke check.
- To match the **GitHub Pages** build locally: `uv run zensical build --clean` (output in `site/`).

## PDF / IL changes

- Prefer a regression test under `tests/` that exercises the stage or parsing behavior you touched.
- Do not commit manual edits to generated `il_version_1.{rng,xsd,py}`; regenerate from `.rnc` per Contributing.

## Done means

- Targeted tests pass; no new Ruff issues on touched paths.
- User-visible flags or TOML behavior documented in `README.md` and/or `docs/configuration.md` (and local/multi docs if applicable).
