"""Provides PipenCliRun"""
import sys
from types import ModuleType
from typing import Any, Mapping, List

from pipen import Proc, Pipen
from pipen.cli import CLIPlugin
from pipen.utils import importlib_metadata
from pyparam import Params
from rich import print

from .utils import (
    ENTRY_POINT_GROUP,
    skip_hooked_args,
)

try:
    from functools import cached_property
except ImportError:  # pragma: no cover
    from cached_property import cached_property


class PipenCliRunPlugin(CLIPlugin):
    """Run a process or a pipeline"""

    from .version import __version__

    name = "run"

    def __init__(self) -> None:
        """Read entry points"""
        self.entry_points = {}
        for dist in importlib_metadata.distributions():
            for epoint in dist.entry_points:
                if epoint.group != ENTRY_POINT_GROUP:
                    continue
                # don't load them
                self.entry_points[epoint.name] = epoint

    def _print_help(self) -> None:
        """Print the root help page"""
        for key in sorted(self.entry_points):
            desc = self.entry_points[key].load().__doc__
            self.params.add_command(
                key,
                desc.strip() if desc else "Undescribed.",
                group="NAMESPACES",
            )
        self.params.print_help()

    def _print_ns_help(self, namespace: str, ns_mod: ModuleType) -> None:
        """Print help for the namespace"""
        from pipen_args import _doc_to_summary

        command = self.params.add_command(
            namespace,
            ns_mod.__doc__.strip() if ns_mod.__doc__ else "Undescribed.",
            force=True,
        )
        command.add_param(
            command.help_keys,
            desc="Print help for this namespace.",
        )
        for attrname in dir(ns_mod):
            attrval = getattr(ns_mod, attrname)
            if (
                callable(attrval)
                and getattr(attrval, "__annotations__", False)
                and attrval.__annotations__.get("return") is Pipen
            ):
                command.add_command(
                    attrname,
                    desc=_doc_to_summary(attrval.__doc__ or "Undescribed."),
                    group="PIPELINES",
                )
            elif not isinstance(attrval, type):
                continue
            elif issubclass(attrval, Proc) and attrval.input:
                command.add_command(
                    attrval.name,
                    desc=_doc_to_summary(attrval.__doc__ or "Undescribed."),
                    group="PROCESSES",
                )
        command.print_help()

    @cached_property
    def params(self) -> Params:
        """Add run command"""
        pms = Params(
            desc=self.__class__.__doc__,
        )
        pms._prog = f"{pms._prog} {self.name}"
        pms.add_param(
            pms.help_keys,
            desc="Print help for this command.",
        )
        return pms

    def parse_args(self, args: List[str]) -> Mapping[str, Any]:
        """Parse the arguments"""
        args = skip_hooked_args(args)
        if len(args) == 0:
            self._print_help()

        namespace = args[0]
        help_keys = [
            f"-{key}" if len(key) == 1 else f"--{key}"
            for key in self.params.help_keys
        ]
        if namespace in help_keys:
            self._print_help()

        # add commands and parse
        if namespace not in self.entry_points:
            print(
                "[red][b]ERROR: [/b][/red]No such namespace: "
                f"[green]{namespace}[/green]"
            )
            self._print_help()

        module = self.entry_points[namespace].load()
        if len(args) == 1:
            self._print_ns_help(namespace, module)

        pname = args[1]
        # Strictly, help_keys should be from command.help_keys
        if pname in help_keys:
            self._print_ns_help(namespace, module)

        return {
            "__name__": pname,
            "__module__": module,
            "__cli_args__": args[2:],
        }

    def exec_command(self, args: Mapping[str, Any]) -> None:
        """Execute the command"""
        from pipen_args import args as pargs
        pargs.cli_args = args["__cli_args__"]
        pargs._prog = " ".join([pargs._prog] + sys.argv[1:-len(pargs.cli_args)])

        pname = args["__name__"]
        module = args["__module__"]
        proc_or_pipeline = getattr(module, pname)
        if (
            callable(proc_or_pipeline)
            and proc_or_pipeline.__annotations__
            and proc_or_pipeline.__annotations__.get("return") is Pipen
        ):
            pipeline = proc_or_pipeline()

        else:
            pipeline = Pipen(name=f"{pname}_pipeline", desc="").set_start(
                proc_or_pipeline
            )

        pipeline.run()
