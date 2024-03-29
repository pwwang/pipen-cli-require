import sys
from pipen import Proc, Pipen


class P1(Proc):
    """Process 1

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
    """

    input = "a"
    output = "outfile:file:out.txt"
    lang = sys.executable
    script = "open({{out.outfile | quote}}, 'w').close()"


class P2(Proc):
    """Process without requirement specification"""

    requires = P1
    input = "a"
    output = "outfile:file:out.txt"
    script = "touch {{out.outfile}}"


# @annotate
class P3(P1):
    """No requirements specified but inherits from P1"""

    requires = P2


class ExamplePipeline(Pipen):
    name = __name__
    starts = [P1]
    data = [["a"]]

if __name__ == "__main__":
    ExamplePipeline().run()
