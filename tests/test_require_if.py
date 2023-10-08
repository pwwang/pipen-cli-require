import pytest  # noqa
from pathlib import Path

import subprocess as sp

REQUIRE_IF_PIPELINE = str(
    Path(__file__).parent / "require_if_pipeline.py:ExamplePipeline"
)


def test_require_if():
    out = sp.check_output(["pipen", "require", "--verbose", REQUIRE_IF_PIPELINE])
    assert b"No module named 'nonexist1'" in out
    assert b"nonexist2 (skipped by if-statement)" in out
