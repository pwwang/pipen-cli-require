
import sys
from pipen import Proc, Pipen

class P1(Proc):
    """Process 1

    Requires:
        - name: pipen
          message: Run `pip install -U pipen` to install
          check: |
            {{proc.lang}} -c "import pipen"
        - name: liquidpy
          message: Run `pip install -U liquidpy` to install
          check: |
            {{proc.lang}} -c "import liquid"
        - name: nonexist
          message: Run `pip install -U nonexist` to install
          check: |
            {{proc.lang}} -c "import nonexist"
    """
    input = "a"
    output = "outfile:file:out.txt"
    lang = sys.executable

def example_pipeline() -> Pipen:
    return Pipen(__name__).set_start(P1)
