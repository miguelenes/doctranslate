# GitHub Pages deployment

This repository ships documentation with **Material for MkDocs**-compatible configuration (`mkdocs.yml`) and deploys from GitHub Actions using **[Zensical](https://zensical.org/)** to build the static site, then **[peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages)** to push the result to the **`gh-pages`** branch.

We stay on **MkDocs 1.x** with an explicit **`mkdocs>=1.5,<2`** pin (see `pyproject.toml`) because **MkDocs 2.0** is not a drop-in replacement for Material or the existing plugin stack. CI builds the live site with Zensical; **strict Markdown checks** still run in the test workflow via **`uv run mkdocs build --strict`** (Zensical’s `build --strict` is not available yet).

## One-time repository settings

1. In GitHub: **Settings → Pages** (for `miguelenes/doctranslate` or your fork).
2. Under **Build and deployment → Source**, choose **Deploy from a branch** (not “GitHub Actions” unless you switch the workflow to `actions/deploy-pages`).
3. Set **Branch** to **`gh-pages`** and folder **`/ (root)`**, then save.
4. After the first successful workflow run, the site should be available at **`https://miguelenes.github.io/doctranslate/`** (or `https://<owner>.github.io/<repo>/` for other forks).

`site_url` in `mkdocs.yml` must match that public URL (including trailing slash) so internal links and canonical URLs resolve correctly.

## How it runs

- Workflow: [.github/workflows/docs.yml](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/docs.yml)
- Trigger: push to **`main`** or **`master`**, or **Run workflow** manually (`workflow_dispatch`).
- Steps: `uv sync --locked --group dev --extra full` → `uv run zensical build --clean` → deploy **`./site`** to **`gh-pages`**.

## Local development

- **Live preview (MkDocs):** `uv run mkdocs serve` — same plugins and strict behavior you are used to.
- **CI-like static build (Zensical):** `uv run zensical build --clean` — output in `site/` (ignored by git).

After changing dependencies in `pyproject.toml`, refresh the lockfile with **`uv lock`** so `uv sync --locked` keeps working in CI.

## Troubleshooting

- **Workflow succeeds but site 404:** Pages source is still **None** or points at the wrong branch — set **gh-pages** / root as above.
- **Push / deploy denied:** Ensure **Settings → Actions → General → Workflow permissions** allows **Read and write** for the default `GITHUB_TOKEN` (required for `peaceiris/actions-gh-pages` to update `gh-pages`).
- **Strict build fails in CI:** Fix MkDocs warnings locally with `NO_MKDOCS_2_WARNING=1 uv run mkdocs build --strict`, then push again.
- **`uv sync --locked` fails after pulling:** Run `uv lock` on a machine with network access and commit the updated `uv.lock`.

## Release and publishing

PyPI releases are driven by [.github/workflows/publish-to-pypi.yml](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/publish-to-pypi.yml):

- **PyPI:** when `pyproject.toml` version changes on `main` / `master` and the workflow detects a new tag, the built wheel/sdist is published to PyPI (Trusted Publishing).
- **TestPyPI:** pushes that do **not** correspond to a new tagged version get a **development** version (`bumpver` + timestamp) and publish to TestPyPI instead.

The workflow only runs publishing steps for the repositories listed in the workflow’s `check-repository` job. **Forks** still benefit from tests and docs builds but do not publish packages from this workflow.

Version bumps in-tree use **bumpver** (see `[tool.bumpver]` in `pyproject.toml`).
