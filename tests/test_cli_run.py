import sys
from contextlib import contextmanager

import pytest
from pipen.cli import main
from pipen_cli_run import PipenCliRunPlugin
from . import example_procs, example_pipeline
from .utils import plugin_to_entrypoint


def init(self):
    self.entry_points = {}
    self.entry_points["exm_procs"] = plugin_to_entrypoint(example_procs)
    self.entry_points["exm_pipes"] = plugin_to_entrypoint(example_pipeline)


@pytest.fixture
def patch_init():
    old_init = PipenCliRunPlugin.__init__
    PipenCliRunPlugin.__init__ = init
    yield
    PipenCliRunPlugin.__init__ = old_init


@contextmanager
def with_argv(argv):
    old = sys.argv[:]
    sys.argv = argv
    yield
    sys.argv = old


def test_plugin_added(capsys):
    with with_argv(["pipen"]), pytest.raises(SystemExit):
        main()

    assert "run" in capsys.readouterr().out

    with with_argv(["pipen", "run", "xxx"]), pytest.raises(SystemExit):
        main()

    assert "No such namespace" in capsys.readouterr().out


def test_list(capsys, patch_init):
    with with_argv(["pipen", "run"]), pytest.raises(SystemExit):
        main()
    assert "exm_procs" in capsys.readouterr().out

    with with_argv(["pipen", "run", "--help"]), pytest.raises(SystemExit):
        main()
    assert "exm_procs" in capsys.readouterr().out

    with with_argv(["pipen", "run", "exm_procs"]), pytest.raises(SystemExit):
        main()
    out = capsys.readouterr().out
    assert "UndescribedProc" in out
    assert "P1" in out

    with with_argv(["pipen", "run", "exm_procs", "--help"]), pytest.raises(
        SystemExit
    ):
        main()
    out = capsys.readouterr().out
    assert "UndescribedProc" in out
    assert "P1" in out

    with with_argv(["pipen", "run", "exm_pipes"]), pytest.raises(SystemExit):
        main()
    assert "example_pipeline" in capsys.readouterr().out

    with with_argv(["pipen", "run", "exm_pipes", "--help"]), pytest.raises(
        SystemExit
    ):
        main()
    assert "example_pipeline" in capsys.readouterr().out


def test_nosuch_ns(capsys, patch_init):
    with with_argv(["pipen", "run", "xyz"]), pytest.raises(SystemExit):
        main()
    assert "No such namespace:" in capsys.readouterr().out


def test_pipeline(capsys, patch_init):
    with with_argv(
        ["pipen", "run", "exm_pipes", "example_pipeline"]
    ), pytest.raises(SystemExit):
        main()
    assert "--P1.in.a" in capsys.readouterr().out


def test_pipeline_run(patch_init, tmp_path):
    with with_argv(
        [
            "pipen",
            "run",
            "exm_pipes",
            "example_pipeline",
            "--P1.in.a",
            "1",
            "--outdir",
            str(tmp_path),
        ]
    ):
        main()

    outfile = tmp_path / "P2" / "out.txt"
    assert outfile.read_text().strip() == "1\n123"


def test_procs_help(capsys, patch_init):
    with with_argv(
        [
            "pipen",
            "run",
            "exm_procs",
            "P1",
        ]
    ), pytest.raises(SystemExit):
        main()

    assert "The first process" in capsys.readouterr().out


def test_extra_args(capsys, patch_init):
    with with_argv(
        [
            "pipen",
            "run",
            "exm_procs",
            "P1",
            "+extra",
            "1",
        ]
    ), pytest.raises(SystemExit):
        assert "+extra" in sys.argv
        main()

    assert "+extra" not in sys.argv
    assert "The first process" in capsys.readouterr().out

def test_extra_args2(patch_init):
    with with_argv(
        [
            "pipen",
            "run",
            "exm_procs",
            "P1",
            "+extra=2",
        ]
    ), pytest.raises(SystemExit):
        assert "+extra=2" in sys.argv
        main()

    assert "+extra=2" not in sys.argv


def test_procs_run(tmp_path, patch_init):
    infile = tmp_path / "infile.txt"
    infile.write_text("1234")
    with with_argv(
        [
            "pipen",
            "run",
            "exm_procs",
            "P1",
            "--in.infile",
            str(infile),
            "--outdir",
            str(tmp_path),
            "--plugin-opts",
            '{"a": 8}',
            "--scheduler-opts",
            '{"a": 18}',
        ]
    ):
        main()

    outfile = tmp_path / "P1" / "out.txt"
    assert outfile.read_text().strip() == "1234"


def test_full_opts(patch_init, capsys):
    with with_argv(
        [
            "pipen",
            "run",
            "exm_procs",
            "P1",
            "--full",
        ]
    ), pytest.raises(SystemExit):
        main()

    assert "error_strategy" in capsys.readouterr().out
