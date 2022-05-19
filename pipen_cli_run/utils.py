"""Default settings and utilities"""

import re
from typing import List

ENTRY_POINT_GROUP = "pipen_cli_run"


def skip_hooked_args(args: List[str]) -> List[str]:
    """This allows the modules to have some extra arguments starting with `+`
    """
    out = []
    skipping = False
    for arg in args:
        if skipping:
            skipping = False
            continue
        if re.match(r"^\+[-\w\.]+$", arg):
            skipping = True
            continue
        if re.match(r"^\+[-\w\.]+=.+$", arg):
            skipping = False
            continue
        out.append(arg)

    return out
