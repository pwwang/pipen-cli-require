import pytest  # noqa
from pathlib import Path

import cmdy

REQUIRE_IF_PIPELINE = str(
    Path(__file__).parent / "require_if_pipeline.py:ExamplePipeline"
)


def test_require_if():
    out = cmdy.pipen.require(verbose=True, _=[REQUIRE_IF_PIPELINE])
    assert out.rc == 0
    assert "No module named 'nonexist1'" in out.stdout
    assert "nonexist2 (skipped by if-statement)" in out.stdout
