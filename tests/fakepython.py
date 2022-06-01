import cmdy
import sys

if sys.argv[1] == "-c":
    if "nonexist" in sys.argv[2]:
        sys.exit(0)
    sys.stderr.write(f"No such package: {sys.argv[2]}")
    sys.exit(1)

cmdy.python(*sys.argv[1:], _exe=sys.executable)
