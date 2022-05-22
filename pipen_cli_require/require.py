"""Provides the PipenRequire class"""

import importlib
from enum import Enum, auto
from pathlib import Path
from multiprocessing import Pool, Manager
from subprocess import PIPE, run
from time import sleep
from typing import TYPE_CHECKING, List, Mapping, Type

from pardoc.parsed import ParsedTodo, ParsedItem
from rich.tree import Tree
from rich.live import Live
from rich.status import Status
from liquid import Liquid
from pipen import Pipen, Proc
from pipen_annotate import annotate

if TYPE_CHECKING:  # pragma: no cover
    from pyparam import Namespace


PROC_SUMMARY_NAME = "SUMMARY"


class CheckingStatus(Enum):
    """Status of a requirement checking"""

    PENDING = auto()
    CHECKING = auto()
    ERROR = auto()
    SUCCESS = auto()
    SKIPPING = auto()


def _render_requirement(s: str, proc: Type[Proc]) -> str:
    """Render a requirement"""
    liq = Liquid(s, from_file=False, mode="wild")
    return liq.render(proc=proc)


def _parse_pardoc_requirements(
    pardoc_req: ParsedTodo,
    proc: Type[Proc],
) -> List[Mapping[str, str]]:
    """Parse the pardoc parsed requirements"""
    requirement = {}
    if not isinstance(pardoc_req, ParsedTodo):
        raise ValueError(
            f"Invalid requirement specification for {proc}: {pardoc_req}\n"
            "Requirement must be in YAML format, with keys "
            "`name`, `message` (optional), and `check`"
        )
    if not pardoc_req.todo.startswith("name:"):
        raise ValueError(
            f"Requirement must start with `name` key, got: {pardoc_req.todo}"
        )

    requirement["name"] = _render_requirement(
        pardoc_req.todo[5:].strip(), proc
    )
    for item in pardoc_req.more:
        if not isinstance(item, ParsedItem) or item.name not in (
            "message",
            "check",
        ):
            raise ValueError(
                f"Invalid requirement specification for {proc}: {item}\n"
                "Requirement must be in YAML format, with keys "
                "`name`, `message` (optional), and `check`"
            )
        if item.name == "message":
            requirement["message"] = _render_requirement(item.desc, proc)
        else:
            requirement["check"] = _render_requirement(
                "\n".join(item.more[0].lines), proc
            )

    return requirement


def _parse_proc_requirements(proc: Type[Proc]) -> List[Mapping[str, str]]:
    """Parse the requirements of a process"""
    proc = annotate(proc)

    while (
        issubclass(proc.__bases__[-1], Proc) is not Proc
        and proc.__bases__[-1] is not Proc
        and "requires" not in proc.annotated
    ):
        proc = proc.__bases__[-1]
        proc = annotate(proc)

    if "requires" not in proc.annotated:
        return []

    return [
        _parse_pardoc_requirements(sec, proc)
        for sec in proc.annotated["requires"].section
    ]


def _run_check(pname, name, check, status, errors):
    """Run a check"""
    status[f"{pname}/{name}"] = CheckingStatus.CHECKING
    cmd = ["/usr/bin/env", "bash", "-c", check]
    p = run(cmd, stdout=PIPE, stderr=PIPE)
    if p.returncode != 0:
        errors[f"{pname}/{name}"] = p.stderr.decode("utf-8")
    p.check_returncode()


class PipenRequire:
    """The class to extract and check requirements"""

    def __init__(self, pipeline: str, args: "Namespace"):
        self.pipeline = self._parse_pipeline(pipeline)
        self.args = args
        self.status = Manager().dict()
        self.errors = Manager().dict()
        self.pool = None
        self.results = {}

    def _parse_pipeline(self, pipeline: str) -> "Pipen":
        """Parse the pipeline"""
        modpath, sep, name = pipeline.rpartition(":")
        if sep != ":":
            raise ValueError(
                f"Invalid pipeline: {pipeline}.\n"
                "It must be in the format '<module[.submodule]>:pipeline' or \n"
                "'/path/to/pipeline.py:pipeline'"
            )

        path = Path(modpath)
        if path.is_file():
            spec = importlib.util.spec_from_file_location(path.stem, modpath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            module = importlib.import_module(modpath)

        try:
            pipeline = getattr(module, name)
        except AttributeError:
            raise ValueError(f"Invalid pipeline: {pipeline}") from None

        if callable(pipeline):
            pipeline = pipeline()

        if not isinstance(pipeline, Pipen):
            raise ValueError(
                f"Invalid pipeline: {pipeline}\n"
                "It must be a `pipen.Pipen` instance"
            )

        return pipeline

    def _generate_tree(self, all_reqs: Mapping[str, Mapping[str, str]]):
        """Generate a tree to show requirements checking"""
        self._update_status()
        tree = Tree(
            "\nChecking requirements for pipeline: "
            f"[bold]{self.pipeline.name.upper()}[/bold]",
        )
        subtrees = {}
        for name, status in self.status.items():
            if status == CheckingStatus.SKIPPING:
                tree.add(
                    f"[bold]{name}[/bold]: "
                    f"{all_reqs[name][PROC_SUMMARY_NAME]}"
                ).add("[yellow]Skipped, no requirements specified.[/yellow]")
                continue

            pname, cname = name.split("/", 1)
            if pname not in subtrees:
                subtrees[pname] = tree.add(
                    f"[bold]{pname}[/bold]: "
                    f"{all_reqs[pname][PROC_SUMMARY_NAME]}"
                )

            if status == CheckingStatus.PENDING:
                subtrees[pname].add(
                    Status(f"{cname}", spinner="circleQuarters")
                )
            elif status == CheckingStatus.CHECKING:
                subtrees[pname].add(
                    Status(f"[yellow]{cname}[/yellow]", spinner="dots")
                )
            elif status == CheckingStatus.SUCCESS:
                subtrees[pname].add(f"[green]✔️ {cname}[/green]")
            elif status == CheckingStatus.ERROR:
                if "message" in all_reqs[pname][cname]:
                    subtree = subtrees[pname].add(
                        f"[red][bold]x[/bold] {cname}: "
                        f"{all_reqs[pname][cname]['message']}[/red]"
                    )
                else:
                    subtree = subtrees[pname].add(f"[red]x {cname}[/red]")

                if self.args.verbose:
                    subtree.add(
                        f"[red]{self.errors[name]}[/red]"
                    )

        return tree

    def _update_status(self):
        """Update the status of the checking"""
        for pname, rets in self.results.items():
            for cname, ret in rets.items():
                if not ret.ready():
                    pass
                elif ret.successful():
                    self.status[f"{pname}/{cname}"] = CheckingStatus.SUCCESS
                else:
                    self.status[f"{pname}/{cname}"] = CheckingStatus.ERROR

    def _start_requirements_check(
        self, all_reqs: Mapping[str, Mapping[str, str]]
    ):
        """Run the requirements check"""
        self.pool = Pool(processes=self.args.ncores)
        for pname, reqs in all_reqs.items():
            self.results.setdefault(pname, {})
            if len(reqs) == 1:
                self.status[pname] = CheckingStatus.SKIPPING
                continue

            for cname, req in reqs.items():
                if cname == PROC_SUMMARY_NAME:
                    continue
                self.status[f"{pname}/{cname}"] = CheckingStatus.PENDING
                self.results[pname][cname] = self.pool.apply_async(
                    _run_check,
                    args=(pname, cname, req["check"], self.status, self.errors),
                )

    def all_done(self):
        """Check if all requirements are done"""
        return all(
            status in (
                CheckingStatus.SUCCESS,
                CheckingStatus.ERROR,
                CheckingStatus.SKIPPING
            )
            for _, status in self.status.items()
        )

    def run(self):
        """Run the pipeline"""
        self.pipeline.build_proc_relationships()
        all_reqs = {}
        for proc in self.pipeline.procs:
            all_reqs[proc.name] = {}
            for req in _parse_proc_requirements(proc):
                all_reqs[proc.name][req["name"]] = req
            all_reqs[proc.name][PROC_SUMMARY_NAME] = " ".join(
                proc.annotated.short.lines
            )

        self._start_requirements_check(all_reqs)

        with Live(self._generate_tree(all_reqs)) as live:
            while not self.all_done():
                sleep(.8)
                live.update(self._generate_tree(all_reqs))

    def __del__(self):
        try:
            if self.pool is not None:
                self.pool.close()
                self.pool.join()
        except Exception:
            pass
