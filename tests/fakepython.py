import subprocess as sp
import sys

if sys.argv[1] == "-c":
    if "nonexist" in sys.argv[2]:
        sys.exit(0)
    sys.stderr.write(f"No such package: {sys.argv[2]}")
    sys.exit(1)


sp.Popen(
    [sys.executable, *sys.argv[1:]], 
    stdin=sys.stdin, 
    stdout=sys.stdout, 
    stderr=sys.stderr,
)
