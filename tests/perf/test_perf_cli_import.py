"""Micro-benchmarks for CLI parser construction."""

from __future__ import annotations

import doctranslate.cli.dispatch as dispatch
import pytest


@pytest.mark.perf
def test_perf_build_vnext_parser(benchmark):
    """Time to build the vNext argparse tree (hot path after import)."""
    benchmark(dispatch.build_vnext_parser)
