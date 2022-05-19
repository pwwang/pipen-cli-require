from diot import Diot
from pipen_cli_run.utils import ENTRY_POINT_GROUP

def plugin_to_entrypoint(plugin):
    return Diot(
        module=plugin,
        name=plugin.__name__,
        group=ENTRY_POINT_GROUP,
        load=lambda: plugin
    )