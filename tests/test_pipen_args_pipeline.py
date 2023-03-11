import pytest  # noqa
import sys
from pathlib import Path

import cmdy

PIPEN_ARGS_PIPELINE = str(
    Path(__file__).parent / "pipen_args_pipeline.py:ExamplePipeline"
)

PYTHON = sys.executable
FAKE_PYTHON = f"{PYTHON} {Path(__file__).parent / 'fakepython.py'}"


def test_with_real_python():
    out = cmdy.pipen.require(
        r_verbose=True,
        _=[PIPEN_ARGS_PIPELINE, "--forks", 1],
    )
    assert out.rc == 0
    assert "No module named 'nonexist'" in out.stdout


def test_with_fake_python():
    out = cmdy.pipen.require(
        r_verbose=True,
        _=[PIPEN_ARGS_PIPELINE, "--P1.lang", FAKE_PYTHON],
    )
    assert out.rc == 0
    assert "No such package: import pipen" in out.stdout
    assert "No such package: import liquid" in out.stdout
