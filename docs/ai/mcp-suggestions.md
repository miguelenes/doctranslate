# MCP and external context (suggestions)

Use MCPs when they reduce hallucinations or automate repo-external lookups. This project is **Python CLI + PDF + LLM routing**; not all generic MCPs add value.

## High value for this stack

| MCP / pattern | When to use |
|---------------|-------------|
| **Context7** (`resolve-library-id` → `query-docs`) | Current API for **LiteLLM**, **Pydantic v2**, **PyMuPDF**, **pytest**, **Ruff**, **MkDocs Material**, **httpx**, etc. Prefer over stale training cutoffs. |
| **Browser / IDE browser** | After **MkDocs** or marketing doc edits: smoke navigation, search, and anchors. |

## Optional (team-dependent)

| MCP | When to use |
|-----|-------------|
| **Atlassian** (Jira/Confluence) | If your org tracks specs, bugs, or runbooks there; link issues in PRs, not secrets. |

## Low value / out of scope for core DocTranslater work

- **Cloudflare** Workers/Pages/D1/R2 MCPs — unrelated unless you add a Cloudflare deployment to this repo.
- **Laravel Forge** — unrelated to this codebase.

## Hygiene

- Do not paste **API keys** or proprietary PDFs into MCP queries; use env vars and redacted examples.
- Prefer **repo files** as source of truth for behavior; use Context7 for **upstream library** semantics.
