"""Provides PipenCliRequire"""
from typing import Any, Mapping

from pipen.cli import CLIPlugin
from pyparam import Params, POSITIONAL

from .require import PipenRequire

try:
    from functools import cached_property
except ImportError:  # pragma: no cover
    from cached_property import cached_property


class PipenCliRequirePlugin(CLIPlugin):
    """Run a process or a pipeline"""

    from .version import __version__
    name = "require"

    @cached_property
    def params(self) -> Params:
        """Add require command"""
        pms = Params(
            desc=self.__class__.__doc__,
        )
        pms._prog = f"{pms._prog} {self.name}"
        pms.add_param(
            "n,ncores",
            desc="Number of cores to use",
            default=1,
        )
        pms.add_param(
            "v,verbose",
            desc="Show verbosal error when checking failed",
            default=False,
        )
        pms.add_param(
            POSITIONAL,
            type=str,
            desc=(
                "The pipeline, either",
                "`/path/to/pipeline.py:pipeline` or ",
                "`<module.submodule>:pipeline`",
                "`pipeline` must be an instance of `Pipen`.",
            )
        )
        pms.add_param(
            pms.help_keys,
            desc="Print help for this command.",
        )
        return pms

    def exec_command(self, args: Mapping[str, Any]) -> None:
        """Execute the command"""
        pipeline = args[POSITIONAL]
        PipenRequire(pipeline, args).run()
