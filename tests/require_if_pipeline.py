import sys
from pipen import Proc, Pipen

class P1(Proc):
    """Process 1

    Requires:
        - name: nonexist1
          if: {{not proc.envs.require_nonexist}}
          check: |
            {{proc.lang}} -c "import nonexist1"
        - name: nonexist2
          if: {{proc.envs.require_nonexist}}
          check: |
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


def pipen(**kwargs) -> Pipen:
    return Pipen(__name__, **kwargs).set_start(P1).set_data(["a"])


# if __name__ == "__main__":
#     pipen(loglevel="debug").run()

