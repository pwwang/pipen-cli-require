"""Provides the PipenRequire class"""
from __future__ import annotations

import sys
from enum import Enum, auto
from multiprocessing import Pool, Manager
from subprocess import PIPE, run
from time import sleep
from typing import List, Mapping, Tuple, Type

from diot import Diot, OrderedDiot
from rich.tree import Tree
from rich.live import Live
from rich.status import Status
from liquid import Liquid
from pipen import Proc
from pipen.utils import load_pipeline
from pipen_annotate import annotate

PROC_SUMMARY_NAME = "_SUMMARY"
# Cache the status of the checks: check => status
# When status is SUCESS, then the check is successful
# Otherwise, it is the error
STATUSES = Manager().dict()

annotate.register_section("Requires", "Items")


class CheckingStatus(Enum):
    """Status of a requirement checking"""

    PENDING = auto()
    CHECKING = auto()
    ERROR = auto()
    SUCCESS = auto()
    SKIPPING = auto()
    IF_SKIPPING = auto()


def _render_requirement(s: str | None, proc: Type[Proc]) -> str | None:
    """Render a requirement"""
    if s is None:
        return None

    liq = Liquid(s, from_file=False, mode="wild")
    return liq.render(proc=proc, envs=proc.envs)


def parse_proc_requirements(
    proc: Type[Proc]
) -> Tuple[OrderedDiot, OrderedDiot]:
    """Parse the requirements of a process

    Args:
        proc: The process class

    Returns:
        A tuple of two OrderedDiot's.
        The first one is the annotated sections by pipen_annotate
        The second one is the requirements. The key is the name of the
            requirement, the value is a dict with message, check and if_ keys.
    """
    annotated = annotate(proc)

    out = OrderedDiot()
    # No requirements specified
    if "Requires" not in annotated:
        return annotated, out

    for key, val in annotated.Requires.items():
        out[key] = Diot(
            message=_render_requirement(val.help, proc),
            check=_render_requirement(
                None
                if "check" not in val.terms
                else val.terms.check.help,
                proc,
            ),
            if_=_render_requirement(
                None
                if "if" not in val.terms
                else val.terms["if"].help,
                proc,
            ),
        )

    return annotated, out


def _run_check(pname, name, cond, check, status, errors):
    """Run a check"""
    status[f"{pname}/{name}"] = CheckingStatus.CHECKING
    if cond.lower() not in ("true", "1"):
        status[f"{pname}/{name}"] = CheckingStatus.IF_SKIPPING
        return

    if check not in STATUSES:
        STATUSES[check] = CheckingStatus.CHECKING.value
        cmd = ["/usr/bin/env", "bash", "-c", check]
        p = run(cmd, stdout=PIPE, stderr=PIPE)
        if p.returncode != 0:
            error = p.stderr.decode("utf-8")
            STATUSES[check] = errors[f"{pname}/{name}"] = error
        p.check_returncode()
        STATUSES[check] = CheckingStatus.SUCCESS.value
    else:
        # Wait for the check to finish
        while STATUSES[check] in (
            CheckingStatus.PENDING.value,
            CheckingStatus.CHECKING.value,
        ):  # pragma: no cover
            sleep(0.1)

        if STATUSES[check] != CheckingStatus.SUCCESS.value:
            errors[f"{pname}/{name}"] = STATUSES[check]
            raise RuntimeError(STATUSES[check])
        else:
            STATUSES[check] = CheckingStatus.SUCCESS.value


class PipenRequire:
    """The class to extract and check requirements"""

    def __init__(
        self,
        pipeline: str,
        pipeline_args: List[str],
        ncores: int,
        verbose: bool,
    ):
        self.pipeline = pipeline
        self.pipeline_args = pipeline_args
        self.ncores = ncores
        self.verbose = verbose
        self.status = Manager().dict()
        self.errors = Manager().dict()
        self.pool = None
        self.results = OrderedDiot()

    def _generate_tree(self, all_reqs: Mapping[str, Mapping[str, str]]):
        """Generate a tree to show requirements checking"""

        self._update_status()
        tree = Tree(
            "\nChecking requirements for pipeline: "
            f"[bold]{self.pipeline.name.upper()}[/bold]\n│",
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
                subtrees[pname].add(f"[green]✅ {cname}[/green]")
            elif status == CheckingStatus.IF_SKIPPING:
                subtrees[pname].add(
                    f"[green]⏩ {cname}[/green] "
                    "[yellow](skipped by if-statement)[/yellow]"
                )
            elif status == CheckingStatus.ERROR:
                subtree = subtrees[pname].add(
                    f"[red]❎ {cname}: "
                    f"{all_reqs[pname][cname]['message']}[/red]"
                )

                if self.verbose:
                    subtree.add(f"[red]{self.errors[name]}[/red]")

        return tree

    def _update_status(self):
        """Update the status of the checking"""
        for pname, rets in self.results.items():
            for cname, ret in rets.items():
                key = f"{pname}/{cname}"
                if not ret.ready():
                    pass
                elif ret.successful():
                    if self.status[key] == CheckingStatus.CHECKING:
                        self.status[key] = CheckingStatus.SUCCESS
                else:
                    self.status[key] = CheckingStatus.ERROR

    def _start_requirements_check(
        self,
        all_reqs: Mapping[str, Mapping[str, str]],
    ):
        """Run the requirements check"""
        self.pool = Pool(processes=self.ncores)
        for pname, reqs in all_reqs.items():
            self.results.setdefault(pname, {})
            if len(reqs) == 1:
                # No requirements, only summary
                self.status[pname] = CheckingStatus.SKIPPING
                continue

            for cname, req in reqs.items():
                if cname == PROC_SUMMARY_NAME:
                    continue
                self.status[f"{pname}/{cname}"] = CheckingStatus.PENDING
                self.results[pname][cname] = self.pool.apply_async(
                    _run_check,
                    args=(
                        pname,
                        cname,
                        req.get("if_", "true") or "true",
                        req["check"],
                        self.status,
                        self.errors,
                    ),
                )

    def all_done(self):
        """Check if all requirements are done"""
        return all(
            status
            in (
                CheckingStatus.SUCCESS,
                CheckingStatus.ERROR,
                CheckingStatus.IF_SKIPPING,
                CheckingStatus.SKIPPING,
            )
            for _, status in self.status.items()
        )

    async def run(self):
        """Run the pipeline"""
        self.pipeline = await load_pipeline(
            self.pipeline,
            argv0=sys.argv[0],
            argv1p=self.pipeline_args,
        )
        all_reqs = OrderedDiot()
        for proc in self.pipeline.procs:
            anno, requires = parse_proc_requirements(proc)
            all_reqs[proc.name] = requires
            all_reqs[proc.name][PROC_SUMMARY_NAME] = anno.Summary.short

        self._start_requirements_check(all_reqs)

        with Live(self._generate_tree(all_reqs)) as live:
            while not self.all_done():
                sleep(0.8)
                live.update(self._generate_tree(all_reqs))

    def __del__(self):
        try:
            if self.pool is not None:
                self.pool.close()
                self.pool.join()
        except Exception:  # pragma: no cover
            pass
