import click
from . import docker as _docker
from . import jupyter as _jupyter
from .utils import AliasedGroup
from .config import REQUIRED_GB_FREE_DISK
from . import tldr as _tldr
from . import update as _update
from . import gitlab as _gitlab

from pkg_resources import iter_entry_points
from click_plugins import with_plugins

@with_plugins(iter_entry_points('franklin.plugins'))
@click.group(cls=AliasedGroup)
def franklin():
    """
    Franklin is a tool for running Jupyter servers predefined as Docker containers. 
    For more information relevant to students, instructors, and professors, see the
    online at https://munch-group.org/franklin.
    """

franklin.add_command(_update.update)
franklin.add_command(_docker.docker)
franklin.add_command(_jupyter.jupyter)
# franklin.add_command(_tldr.tldr)
# franklin.add_command(_gitlab.git)

# franklin.add_command(_gitlab.exercise) # Aliases for git commands


