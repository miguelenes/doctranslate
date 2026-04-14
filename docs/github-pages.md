# GitHub Pages deployment

This repository ships documentation with **MkDocs Material** and deploys it from GitHub Actions using **`mkdocs gh-deploy`**, which force-pushes the built site to the **`gh-pages`** branch.

## One-time repository settings

1. In GitHub: **Settings → Pages** (for `miguelenes/doctranslate` or your fork).
2. Under **Build and deployment → Source**, choose **Deploy from a branch** (not “GitHub Actions” unless you switch the workflow to `actions/deploy-pages`).
3. Set **Branch** to **`gh-pages`** and folder **`/ (root)`**, then save.
4. After the first successful workflow run, the site should be available at **`https://miguelenes.github.io/doctranslate/`** (or `https://<owner>.github.io/<repo>/` for other forks).

`site_url` in `mkdocs.yml` must match that public URL (including trailing slash) so internal links and canonical URLs resolve correctly.

## How it runs

- Workflow: [.github/workflows/docs.yml](https://github.com/miguelenes/doctranslate/blob/main/.github/workflows/docs.yml)
- Trigger: push to **`main`** or **`master`**, or **Run workflow** manually (`workflow_dispatch`).
- Command: `uv run mkdocs gh-deploy --force --strict` (build + push to `gh-pages`).

## Troubleshooting

- **Workflow succeeds but site 404:** Pages source is still **None** or points at the wrong branch — set **gh-pages** / root as above.
- **Push denied:** Ensure **Settings → Actions → General → Workflow permissions** allows **Read and write** for the default `GITHUB_TOKEN` (required to push `gh-pages`).
- **Strict build fails:** Fix MkDocs warnings locally with `uv run mkdocs build --strict`, then push again.
