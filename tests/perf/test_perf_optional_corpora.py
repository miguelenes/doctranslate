"""Optional corpus files under ``benchmarks/corpus/`` (nightly slices)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.perf, pytest.mark.requires_full, pytest.mark.requires_pdf]


@pytest.fixture
def corpus_dir(repo_root: Path) -> Path:
    return repo_root / "benchmarks" / "corpus"


@pytest.mark.requires_ocr
@pytest.mark.perf
def test_perf_open_scanned_pdf_if_present(benchmark, corpus_dir: Path):
    """Cheap open-only check when ``scanned.pdf`` is added to the corpus."""
    pytest.importorskip("pytest_benchmark")
    scanned = corpus_dir / "scanned.pdf"
    if not scanned.is_file():
        pytest.skip("benchmarks/corpus/scanned.pdf not present")

    import pymupdf

    def _open():
        doc = pymupdf.open(scanned)
        try:
            return doc.page_count
        finally:
            doc.close()

    n = benchmark.pedantic(_open, rounds=3, iterations=1)
    assert isinstance(n, int) and n >= 1


@pytest.mark.requires_hyperscan
@pytest.mark.perf
def test_perf_hyperscan_import_if_extra_installed():
    """Fails only when marker is used without optional native extra (nightly matrix)."""
    import importlib.util

    spec = importlib.util.find_spec("hyperscan")
    if spec is None:
        pytest.skip("hyperscan not installed")
    import hyperscan  # noqa: F401

    assert hyperscan is not None
