
from pipen import Proc, Pipen

class P1(Proc):
    input = "a"
    output = "outfile:file:out.txt"
    script = "echo {{in.a}} > {{out.outfile}}"
class P2(Proc):
    requires = P1
    input = "infile:file"
    output = "outfile:file:out.txt"
    script = "cat {{in.infile}} > {{out.outfile}}; echo 123 >> {{out.outfile}}"

def example_pipeline() -> Pipen:
    return Pipen(__name__).set_start(P1)
