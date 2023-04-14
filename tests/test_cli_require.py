import os
import sys
import pytest
from pathlib import Path
from subprocess import run

from pipen import Pipen
from pipen_cli_require.require import PipenRequire

EXAMPLE_PIPELINE = str(
    Path(__file__).parent / "example_pipeline.py:ExamplePipeline"
)


def test_init():
    """Test the initialization of the class"""
    pr = PipenRequire(EXAMPLE_PIPELINE, [], 1, False)
    assert isinstance(pr.pipeline, Pipen)


def test_wrong_pipeline():
    with pytest.raises(ValueError):
        PipenRequire("pipeline", [], 1, False)
    with pytest.raises(ValueError):
        PipenRequire(f"{EXAMPLE_PIPELINE}x", [], 1, False)
    with pytest.raises(ValueError):
        PipenRequire(
            str(Path(__file__).parent / "example_pipeline.py:sys"),
            [],
            1,
            False,
        )


def test_init_using_module():
    sys.path.insert(0, str(Path(__file__).parent))
    pr = PipenRequire("example_pipeline:ExamplePipeline", [], 1, False)
    assert isinstance(pr.pipeline, Pipen)


@pytest.mark.asyncio
async def test_normal_run(capsys):
    pr = PipenRequire(EXAMPLE_PIPELINE, [], ncores=1, verbose=True)
    await pr.run()
    out = capsys.readouterr().out
    assert "EXAMPLE_PIPELINE" in out
    assert "Process 1" in out
    assert "pipen" in out
    assert "liquidpy" in out
    assert "No module named 'nonexist'" in out
    assert "Skipped, no requirements specified." in out


def test_cli():
    cmd = [
        sys.executable,
        "-m",
        "pipen",
        "require",
        EXAMPLE_PIPELINE,
    ]
    p = run(
        cmd,
        stdout=None,
        stderr=None,
        preexec_fn=os.setpgrp,
        close_fds=True,
    )
    assert p.returncode == 0


def test_cli_wrong_args():
    cmd = [
        sys.executable,
        "-m",
        "pipen",
        "require",
        "pipeline",
    ]
    p = run(
        cmd,
        stdout=None,
        stderr=None,
        preexec_fn=os.setpgrp,
        close_fds=True,
    )
    assert p.returncode == 1
