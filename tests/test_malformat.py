import pytest
from pathlib import Path

from pyparam import Namespace
from pipen_cli_require.require import PipenRequire

MALFORMAT_PIPELINE = str(Path(__file__).parent / "malformat_requirements.py")


@pytest.mark.asyncio
async def test_not_yaml():
    with pytest.raises(ValueError):
        await PipenRequire(
            f"{MALFORMAT_PIPELINE}:malformat1", [], Namespace()
        ).run()


@pytest.mark.asyncio
async def test_not_starting_with_name():
    with pytest.raises(ValueError):
        await PipenRequire(
            f"{MALFORMAT_PIPELINE}:malformat2", [], Namespace()
        ).run()


@pytest.mark.asyncio
async def test_extra_items():
    with pytest.raises(ValueError):
        await PipenRequire(
            f"{MALFORMAT_PIPELINE}:malformat3", [], Namespace()
        ).run()
