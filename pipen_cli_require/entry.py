"""Provides PipenCliRequire"""
from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
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
        subparser.add_argument(
            "--r-ncores",
            type=int,
            default=1,
            dest="ncores",
            help="Number of cores to use to check the requirements",
        )
        subparser.add_argument(
            "--r-verbose",
            action="store_true",
            default=False,
            dest="verbose",
            help="Show verbosal error when checking failed",
        )
        subparser.add_argument(
            "pipeline",
            help=(
                "The pipeline and the CLI arguments to run the pipeline. "
                "For the pipeline either `/path/to/pipeline.py:<pipeline>` "
                "or `<module.submodule>:<pipeline>` "
                "`<pipeline>` must be an instance of `Pipen` and running "
                "the pipeline should be called under `__name__ == '__main__'."
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

    def parse_args(self) -> Namespace:
        parsed, rest = self.parser.parse_known_args()
        parsed.pipeline_args = rest
        return parsed
