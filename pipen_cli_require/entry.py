"""Provides PipenCliRequire"""
import asyncio
from typing import Any, Mapping, List

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
            type=list,
            desc=(
                "The pipeline and the CLI arguments to run the pipeline. "
                "For the pipeline either `/path/to/pipeline.py:<pipeline>` ",
                "or `<module.submodule>:<pipeline>`",
                "`<pipeline>` must be an instance of `Pipen` and running "
                "the pipeline should be called under `__name__ == '__main__'.",
            ),
        )
        pms.add_param(
            pms.help_keys,
            desc="Print help for this command.",
        )
        return pms

    def exec_command(self, args: Mapping[str, Any]) -> None:
        """Execute the command"""
        pipeline, *pipeline_args = args[POSITIONAL]
        asyncio.run(PipenRequire(pipeline, pipeline_args, args).run())

    def parse_args(self, args: List[str]) -> Mapping[str, Any]:
        """Parse the arguments"""
        pipeline_pos = -1
        for i, arg in enumerate(args):
            if ":" in arg:
                pipeline_pos = i
                break

        if pipeline_pos == -1:
            args_to_parse = args
            pipeline_args = []
        else:
            args_to_parse = args[: pipeline_pos + 1]
            pipeline_args = args[pipeline_pos + 1 :]

        parsed = self.params.parse(args_to_parse)
        parsed[POSITIONAL].extend(pipeline_args)
        return parsed
