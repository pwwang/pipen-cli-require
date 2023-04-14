from functools import cached_property
import sys
from pipen import Proc, Pipen, ProcGroup


class P1(Proc):
    """Process 1

    Input:
        a: a

    Output:
        outfile: out.txt

    Envs:
        require_conditional: Some condition

    Requires:
        pipen: Run `pip install -U pipen` to install
          - check: |
            {{proc.lang}} -c "import pipen"
        liquidpy: Run `pip install -U liquidpy` to install
          - check: |
            {{proc.lang}} -c "import liquid"
        nonexist: Run `pip install -U nonexist` to install
          - check: |
            {{proc.lang}} -c "import nonexist"
        nonexist2_nomsg:
          - check: |
            {{proc.lang}} -c "import nonexist2"
        conditional:
          - if: {{proc.envs.require_conditional}}
          - check: |
            {{proc.lang}} -c "import require_conditional"
    """

    input = "a"
    output = "outfile:file:out.txt"
    envs = {"require_conditional": False}
    lang = sys.executable


class P2(Proc):
    """Process without requirement specification

    Input:
        a: a

    Output:
        outfile: out.txt
    """

    requires = P1
    input = "a"
    output = "outfile:file:out.txt"


class P3(P1):
    """No requirements specified but inherits from P1"""

    requires = P2


class PG(ProcGroup):
    """A group of processes"""

    p1 = ProcGroup.add_proc(lambda self: P1)
    p2 = ProcGroup.add_proc(lambda self: P2)
    p3 = ProcGroup.add_proc(lambda self: P3)


class ExamplePipeline(Pipen):
    """Example pipeline"""

    name = __name__
    starts = PG().starts
    data = [["a"]]


if __name__ == "__main__":
    ExamplePipeline(loglevel="debug").run()
