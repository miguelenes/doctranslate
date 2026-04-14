# Phase 2: optional repo skills and agents

The first pass adds shared markdown + Cursor rules + thin `CLAUDE.md` / `GEMINI.md`. If repeated agent mistakes appear, add **narrow** automation below.

## Candidate Cursor / Codex skills (workflows)

1. **docs-sync** — Trigger when `doctranslate/main.py` flags or `doctranslate/translator/*` public behavior changes: checklist against `README.md`, `docs/configuration.md`, `docs/multi-translator.md`, `docs/local-translation.md`, `mkdocs.yml` nav.
2. **translator-change-checklist** — Router TOML schema (`NestedTranslatorConfig`), `validate_router_config`, `LiteLLMProviderExecutor`, metrics flags; require tests under `tests/test_translator_*`.
3. **pdf-pipeline-investigation** — Symptom → stage mapping using `TRANSLATE_STAGES` and `docs/ai/pdf-pipeline.md`; point to `high_level.py` and the relevant `document_il` midend/backend module.
4. **release-readiness** — Version in `pyproject.toml` / `doctranslate/__init__.py` / `main.py` per bumpver; changelog if the project uses one; `uv run pytest`, ruff, optional `mkdocs build --strict`.

## Codex custom agents (optional)

OpenAI Codex supports project-scoped agents under `.codex/agents/` when you need parallel **explorer** vs **worker** flows. Only add TOML agents if the team uses Codex CLI regularly and wants standardized subagent prompts.

## Claude Code

- Prefer `.claude/rules/` with `paths` frontmatter if `CLAUDE.md` grows past ~200 lines.
- Skills: see Anthropic docs for progressive disclosure when a workflow is stable and repeated.

Keep any new artifact **short and verifiable**; long instruction files reduce adherence.
