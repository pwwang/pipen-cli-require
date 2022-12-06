import pytest  # noqa
import sys
from pathlib import Path

import cmdy

REQUIRE_IF_PIPELINE = str(
    Path(__file__).parent / "require_if_pipeline.py:pipen"
)


def test_require_if():
    out = cmdy.pipen.require(v=True, _=[REQUIRE_IF_PIPELINE])
    assert out.rc == 0
    assert "No module named 'nonexist1'" in out.stdout
    assert "nonexist2 (skipped by if-statement)" in out.stdout
