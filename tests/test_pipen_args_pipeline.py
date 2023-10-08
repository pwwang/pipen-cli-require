import pytest  # noqa
import os
import sys
from subprocess import check_output
from pathlib import Path

PIPEN_ARGS_PIPELINE = str(
    Path(__file__).parent / "pipen_args_pipeline.py:ExamplePipeline"
)

PYTHON = sys.executable
FAKE_PYTHON = f"{PYTHON} {Path(__file__).parent / 'fakepython.py'}"


def test_with_real_python():
    out = check_output(
        [
            PYTHON,
            "-m",
            "pipen",
            "require",
            "--verbose",
            PIPEN_ARGS_PIPELINE,
            "--",
            "--forks",
            "1",
        ],
    )
    assert "No module named 'nonexist'" in out.decode()


def test_with_fake_python():
    out = check_output(
        [
            PYTHON,
            "-m",
            "pipen",
            "require",
            "--verbose",
            PIPEN_ARGS_PIPELINE,
            "--",
            "--P1.lang",
            FAKE_PYTHON,
        ],
    )
    stdout = out.decode()
    assert "No such package: import pipen" in stdout
    assert "No such package: import liquid" in stdout