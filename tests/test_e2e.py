"""E2E test: runs the example against the pinned Parquet snapshot in data/
(LFS-tracked, exported_at 2026-11-03T15:39:21Z) via A11YSCORE_PARQUET, so it is
hermetic and needs no network access.

Run with: pytest
"""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "mainz_a11y_stats.py"
SNAPSHOT = REPO / "data" / "dimension-combination-metrics.parquet"


@pytest.fixture(scope="module")
def output() -> str:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=300,
        env={**os.environ, "A11YSCORE_PARQUET": str(SNAPSHOT)},
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_prints_the_summary(output: str):
    assert re.search(r"Barrierefreiheit in Mainz: \d+ von 100 Punkten", output)


def test_renders_the_pivot_table(output: str):
    assert "Ortstyp" in output
    assert "Score (0-100)" in output
    assert "Abdeckung %" in output


def test_cutoff_categories_are_below_the_completeness_threshold(output: str):
    cutoff = re.search(
        r"^Nicht bewertet.*?Abdeckung unter 10%\): (.*)$", output, re.MULTILINE
    )
    if cutoff:
        percentages = [int(p) for p in re.findall(r"\((\d+)%\)", cutoff.group(1))]
        assert percentages, cutoff.group(1)
        assert all(p < 10 for p in percentages)


def test_attributes_the_data_source(output: str):
    assert "a11y-Score by Sozialhelden e.V." in output
    assert "© OpenStreetMap contributors" in output
