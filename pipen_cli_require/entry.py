"""Provides PipenCliRequire"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from argx import REMAINDER
from pipen.cli import CLIPlugin

from .require import PipenRequire
from .version import __version__

if TYPE_CHECKING:  # pragma: no cover
    from argx import ArgumentParser, Namespace


class PipenCliRequirePlugin(CLIPlugin):
    """Check the requirements of a pipeline"""

    version = __version__
    name = "require"

    def __init__(
        self,
        parser: ArgumentParser,
        subparser: ArgumentParser,
    ) -> None:
        super().__init__(parser, subparser)
        subparser.exit_on_void = True
        subparser.add_argument(
            "--ncores",
            type=int,
            default=1,
            dest="ncores",
            help="Number of cores to use to check the requirements",
        )
        subparser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            dest="verbose",
            help="Show verbosal error when checking failed",
        )
        subparser.add_argument(
            "-p",
            "--pipeline",
            required=True,
            help=(
                "The pipeline and the CLI arguments to run the pipeline. "
                "For the pipeline either `/path/to/pipeline.py:<pipeline>` "
                "or `<module.submodule>:<pipeline>` "
                "`<pipeline>` must be an instance of `Pipen` and running "
                "the pipeline should be called under `__name__ == '__main__'."
            ),
        )
        subparser.add_argument(
            "pipeline_args",
            nargs=REMAINDER,
            help=(
                "Should be passed after '--'.\n"
                "The arguments to run the pipeline. The pipeline will not be run, we "
                "need them just in case the arguments affect the structure of the "
                "pipeline."
            ),
        )

    def exec_command(self, args: Namespace) -> None:
        """Execute the command"""
        asyncio.run(
            PipenRequire(
                args.pipeline,
                args.pipeline_args,
                args.ncores,
                args.verbose,
            ).run()
        )

    def parse_args(
        self,
        known_parsed: Namespace,
        unparsed_argv: list[str],
    ) -> Namespace:
        """Parse the arguments"""
        if unparsed_argv:
            self.subparser.parse_args()

        if known_parsed.pipeline_args:
            known_parsed.pipeline_args = known_parsed.pipeline_args[1:]

        return known_parsed
