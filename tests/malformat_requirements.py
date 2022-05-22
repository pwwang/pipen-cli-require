from pipen import Proc, Pipen


class P1(Proc):
    """Process 1

    Requires:
        abc
    """

    input = "a"
    output = "outfile:file:out.txt"


class P2(Proc):
    """Process 2

    Requires:
        - x: y
    """

    input = "a"
    output = "outfile:file:out.txt"


class P3(Proc):
    """Process 3

    Requires:
        - name: pipen
          x: y
    """

    input = "a"
    output = "outfile:file:out.txt"


malformat1 = Pipen(__name__).set_start(P1)
malformat2 = Pipen(__name__).set_start(P2)
malformat3 = Pipen(__name__).set_start(P3)
