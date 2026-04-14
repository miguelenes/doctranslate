"""Shared pytest fixtures and paths."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root (parent of ``tests/``)."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def ci_test_pdf(repo_root: Path) -> Path:
    """Tracked CI sample PDF (vector, small)."""
    p = repo_root / "examples" / "ci" / "test.pdf"
    if not p.is_file():
        pytest.skip(f"Missing tracked PDF: {p}")
    return p
