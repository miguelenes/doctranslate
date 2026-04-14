# AI assistant context

These pages are **canonical project context** for Codex (`AGENTS.md`), Cursor (rules + optional `AGENTS.md`), Claude Code (`CLAUDE.md` imports), and Gemini CLI (`GEMINI.md` imports).

| Doc | Purpose |
|-----|---------|
| [Project map](project-map.md) | Directories, entry points, generated IL files. |
| [PDF pipeline](pdf-pipeline.md) | `TRANSLATE_STAGES` and stage boundaries. |
| [Translator stack](translator-stack.md) | OpenAI vs router vs local; config merge pitfalls. |
| [Verification](verification.md) | Commands and “done means”. |
| [Package layers](package-layers.md) | Optional extras, public APIs, CI profiles. |
| [Library API](../library-api.md) (human docs) | Stable Python/JSON embedding (`doctranslate.api` / `doctranslate.schemas`). |
| [Public API policy](../public-api-policy.md) (human docs) | Semver boundaries and internal vs public modules. |
| [MCP suggestions](mcp-suggestions.md) | Which MCPs help this repo. |
| [Phase 2 skills](phase2-skills.md) | Optional follow-up skills/agents. |

Human contributors can ignore this folder; it does not change runtime behavior.
