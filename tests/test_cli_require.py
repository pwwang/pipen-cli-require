from subprocess import PIPE, run
import pytest
import sys
from pathlib import Path

from pyparam import Namespace
from pipen import Pipen
from pipen_cli_require.require import PipenRequire

EXAMPLE_PIPELINE = str(Path(__file__).parent / "example_pipeline.py:example_pipeline")


def test_init():
    """Test the initialization of the class"""
    pr = PipenRequire(EXAMPLE_PIPELINE, [], Namespace())
    assert isinstance(pr.pipeline, Pipen)


def test_wrong_pipeline():
    with pytest.raises(ValueError):
        PipenRequire("pipeline", [], Namespace())
    with pytest.raises(ValueError):
        PipenRequire(f"{EXAMPLE_PIPELINE}x", [], Namespace())
    with pytest.raises(ValueError):
        PipenRequire(
            str(Path(__file__).parent / "example_pipeline.py:sys"),
            [],
            Namespace()
        )


def test_init_using_module():
    sys.path.insert(0, str(Path(__file__).parent))
    pr = PipenRequire("example_pipeline:example_pipeline", [], Namespace())
    assert isinstance(pr.pipeline, Pipen)


@pytest.mark.asyncio
async def test_normal_run(capsys):
    pr = PipenRequire(EXAMPLE_PIPELINE, [], Namespace(ncores=1, verbose=True))
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
        "pipen",
        "require",
        EXAMPLE_PIPELINE,
    ]
    p = run(cmd, stdout=PIPE, stderr=PIPE)
    assert p.returncode == 0

def test_cli_wrong_args():
    cmd = [
        "pipen",
        "require",
        "pipeline",
    ]
    p = run(cmd, stdout=PIPE, stderr=PIPE)
    assert p.returncode == 1
