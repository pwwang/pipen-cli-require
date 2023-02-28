import pytest  # noqa

from subprocess import CalledProcessError
from pipen_cli_require.require import _run_check, CheckingStatus, STATUSES


def test_run_check():
    status = {}
    errors = {}
    _run_check(
        "proc",
        "req",
        "true",
        "pwd",
        status,
        errors,
    )
    assert status["proc/req"] == CheckingStatus.CHECKING
    assert not errors

    _run_check(
        "proc",
        "req",
        "false",
        "pwd",
        status,
        errors,
    )
    assert status["proc/req"] == CheckingStatus.IF_SKIPPING
    assert not errors

    with pytest.raises(CalledProcessError):
        _run_check(
            "proc",
            "req",
            "true",
            "__nonexist__",
            status,
            errors,
        )

    STATUSES["pwd"] = CheckingStatus.ERROR.value
    with pytest.raises(RuntimeError):
        _run_check(
            "proc",
            "req",
            "true",
            "pwd",
            status,
            errors,
        )

    STATUSES["pwd"] = CheckingStatus.SUCCESS.value
    _run_check(
        "proc",
        "req",
        "true",
        "pwd",
        status,
        errors,
    )
