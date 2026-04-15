# Benchmark corpus

Small PDFs and related fixtures used for **performance** and **regression** measurements (separate from functional `examples/ci/`).

## Manifest

| File | Category | Pages (approx.) | License / source | SHA256 (fill when adding) |
|------|----------|-------------------|------------------|---------------------------|
| *(none yet)* | clean_text | — | Add a 1–3 page vector PDF with redistribution rights | — |
| *(none yet)* | table_heavy | — | Self-generated or permissively licensed | — |
| *(none yet)* | formula_heavy | — | Self-generated or permissively licensed | — |
| *(none yet)* | scanned | — | Short scan; requires `ocr` / `requires_ocr` in tests | — |
| *(none yet)* | multilingual_glossary | — | Pair with glossary CSV/TOML; optional Hyperscan slice | — |

## Defaults in CI

- Functional smoke PDF: `examples/ci/test.pdf` (see `tests/conftest.py` `ci_test_pdf`).
- Meso subprocess timings: `scripts/perf_meso.py` uses `examples/ci/test.pdf` when this directory has no extra files.

## Adding files

1. Prefer **small** binaries committed to git; use **Git LFS** or a pinned download script for larger scans.
2. Update the table above with **SHA256** (`sha256sum file.pdf`) and **license**.
3. Add an exception in root `.gitignore` if the path is under `benchmarks/corpus/` and ends in `.pdf` (patterns already allow `!benchmarks/corpus/**/*.pdf`).

## HTTP load testing

Locust can POST `/v1/inspect` when `PERF_INSPECT_PDF` is set to an absolute path readable from the API process (see `DOCTRANSLATE_API_MOUNT_ALLOW_PREFIXES` in [docs/http-api.md](../../docs/http-api.md)).
