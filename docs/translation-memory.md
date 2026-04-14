# Translation memory (TM)

DocTranslater stores **exact** translation pairs in SQLite (`~/.cache/doctranslate/cache.v2.db`, table `_translationcache`). **Translation memory** extends this with:

| Layer | Behavior |
|-------|-----------|
| **L1** | Legacy exact match on full source string + translator fingerprint (unchanged default). |
| **L1b** | Exact match on a **normalized** source key (whitespace / punctuation / placeholder-safe normalization). |
| **L2** | **Fuzzy** match via [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) `WRatio`, gated by `--tm-fuzzy-min-score` and safety checks. |
| **L3** | **Semantic** similarity using optional embeddings (install optional extras; see below). |

Glossary rows are **authoritative**: if a glossary source term appears in the segment, a TM candidate is rejected unless the candidate translation contains the required target substring.

## CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--tm-mode` | `off` | `off` — TM DB disabled (SQLite exact cache only). `exact` — L1 + L1b. `fuzzy` — + L2. `semantic` — + L3 when dependencies are available. |
| `--tm-scope` | `document` | `document` — reuse only rows tagged for the current input file. `project` — same project id, document, or global pool. `global` — any row with matching engine fingerprint. |
| `--tm-min-segment-chars` | `12` | Minimum source length for fuzzy / semantic reuse. |
| `--tm-fuzzy-min-score` | `92` | RapidFuzz score cutoff (0–100). |
| `--tm-semantic-min-similarity` | `0.90` | Cosine similarity floor for semantic hits. |
| `--tm-project-id` | *(empty)* | Optional scope label when using `--tm-scope=project`. |
| `--tm-embedding-model` | `sentence-transformers/all-MiniLM-L6-v2` | Model id for `--tm-mode=semantic`. |
| `--tm-import` | — | NDJSON file merged into TM before the run (idempotent upserts). |
| `--tm-export` | — | After each successful PDF, write TM NDJSON for the active translator fingerprint. If the path is a **directory**, writes `<input-stem>.tm.ndjson` inside it. |

`--ignore-cache` still bypasses **all** cache reads and writes (legacy + TM).

## Fingerprint / invalidation

TM rows and the legacy cache key include a sorted JSON blob of translator-affecting parameters (`model`, `prompt`, router provider fingerprints, etc.). A digest of **glossary (source, target) pairs** is also stored as `tm_glossary_signature` so changing glossaries does not silently reuse incompatible translations.

After **automatic term extraction** finalizes a glossary, the translator cache context is refreshed so TM safety matches the prompts.

## Optional semantic mode (L3)

Install optional dependencies (large download; CPU OK for small models):

```bash
uv sync --extra tm_semantic
```

If `sentence-transformers` / `torch` are missing, `--tm-mode=semantic` behaves like `fuzzy` (L3 is skipped when the backend is unavailable).

## Legacy `cache.v1.db` import

If `~/.cache/doctranslate/cache.v1.db` exists, a **one-time** import of rows into the `_tmentry` table runs on startup (marker `legacy_cache_v1_import` in `_tmmigration`). The active database remains `cache.v2.db` with both legacy and TM tables.

## Quality vs cost

- **`off` / exact-only path**: safest; same behavior as before TM columns existed.
- **`exact`**: better hit rate for whitespace / typographic variants; still deterministic.
- **`fuzzy`**: fewer LLM calls on long/repeated documents; small risk of false positives — raise `--tm-fuzzy-min-score` if needed.
- **`semantic`**: best for paraphrases; highest dependency and CPU cost; tune `--tm-semantic-min-similarity` upward for safety.
