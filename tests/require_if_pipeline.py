import sys
from pipen import Proc, Pipen


class P1(Proc):
    """Process 1

    Requires:
        nonexist1:
          - if: {{not envs.require_nonexist}}
          - check: |
            {{proc.lang}} -c "import nonexist1"
        nonexist2:
          - if: {{proc.envs.require_nonexist}}
          - check: |
            {{proc.lang}} -c "import nonexist2"
    """

    input = "a"
    output = "outfile:file:out.txt"
    envs = {"require_nonexist": False}
    lang = sys.executable


class P2(Proc):
    """Process without requirement specification"""

    requires = P1
    input = "a"
    output = "outfile:file:out.txt"


class ExamplePipeline(Pipen):
    name = __name__
    starts = [P1]
    data = [["a"]]


if __name__ == "__main__":
    ExamplePipeline(loglevel="debug").run()
