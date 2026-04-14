# Verification checklist

Run the smallest set that covers your change. CI reference: [.github/workflows/test.yml](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/test.yml), [.github/workflows/lint.yml](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/lint.yml), [.github/workflows/docs-pr.yml](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/docs-pr.yml), [.github/workflows/docker.yml](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/docker.yml).

## Environment

```bash
uv sync --locked --group dev --extra full
```

For a **minimal** environment (schemas types only), `uv sync --locked --group dev` is enough; see [Package layers](package-layers.md).

## Docker images

After changing the `Dockerfile` or `docker/` helpers, validate locally:

```bash
docker build --target runtime-base -t doctranslater:base .
docker build --target runtime-cpu -t doctranslater:cpu .
docker build --target runtime-vision -t doctranslater:vision .
docker build --target runtime-dev -t doctranslater:dev .
```

Smoke examples: [Docker](../docker.md).

Serverless / container deploy docs: [Serverless containers](../serverless-containers.md), [Deploy on Cloud Run](../deploy-cloud-run.md), [Deploy samples](../deploy-samples/README.md). CI exercises API boot + a **skip-translation** job in [`.github/workflows/docker.yml`](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/docker.yml).

If you change `pyproject.toml` dependencies, run **`uv lock`** and commit **`uv.lock`** so CI (`uv sync --locked`) stays in sync.

## CI lanes (what runs where)

| Lane | Workflow job | Typical command locally |
|------|----------------|-------------------------|
| **Minimal** | `test-minimal-schemas` | `uv sync --locked --group dev` then `pytest tests/test_install_profiles.py::test_minimal_schemas_import -q` |
| **Fast** | `test-fast` | `uv sync --locked --group dev --extra full` then `pytest tests/ -q -m "not requires_pdf"` |
| **Slim PDF** | `test-slim-pdf-cli` | `uv sync --locked --group dev --extra pdf --extra cli` then `pytest tests/test_install_profiles.py::test_pdf_stack_opens_ci_fixture -q` |
| **Full matrix** | `test` | Full `pytest tests/ -q` plus assets warmup / offline pack smoke |
| **Zensical (PR)** | `docs-pr` on `docs/**` or `mkdocs.yml` | `uv run zensical build --clean` |

Tests that need the PDF / IL stack should be marked `@pytest.mark.requires_pdf` (see `pyproject.toml` `[tool.pytest.ini_options]` markers).

## Always safe for local iteration

| Check | Command |
|-------|---------|
| CLI parses | `uv run doctranslate --help` and `uv run doc-translate --help` |
| HTTP API (if touched) | `uv sync --locked --group dev --extra full` then `uv run pytest tests/test_http_api_*.py -q` |
| Assets (if touching models/assets) | `uv run doctranslate assets warmup` |
| Unit tests | `uv run pytest tests/ -q` |
| Skip PDF-stack tests (fast) | `uv run pytest tests/ -q -m "not requires_pdf"` |
| Single file / test node | `uv run pytest tests/<file>::<test> -q` |
| Import profile (warn-only) | `uv run python scripts/check_cli_import_time.py` |

## Lint (matches CI)

- Ruff is run in CI via `astral-sh/ruff-action` on push; locally: `uv run ruff check doctranslate tests` and `uv run ruff format doctranslate tests` (or project-equivalent).

## Translator / config changes

- Router/local validation: `uv run doctranslate config validate --translator router -c <file>` or `... --translator local ...` per [Local translation](../local-translation.md).
- Add or extend tests in `tests/`; avoid requiring paid APIs in default tests (CI job is “no paid APIs”).

## Docs changes

- After editing `docs/` or `mkdocs.yml`: `NO_MKDOCS_2_WARNING=1 uv run mkdocs build --strict` from an env with dev deps (suppresses the upstream MkDocs 2.0 advisory once you rely on the `mkdocs<2` pin). **Note:** git metadata plugins may warn on `--strict` for **brand-new, uncommitted** Markdown files; commit them or run `uv run mkdocs build` (non-strict) for a quick smoke check.
- To match the **GitHub Pages** build locally: `uv run zensical build --clean` (output in `site/`). PRs that touch documentation also run **Zensical** in `docs-pr.yml`.

## PDF / IL changes

- Prefer a regression test under `tests/` that exercises the stage or parsing behavior you touched.
- Do not commit manual edits to generated `il_version_1.{rng,xsd,py}`; regenerate from `.rnc` per Contributing.

## Done means

- Targeted tests pass; no new Ruff issues on touched paths.
- User-visible flags or TOML behavior documented in `README.md` and/or `docs/configuration.md` (and local/multi docs if applicable).
