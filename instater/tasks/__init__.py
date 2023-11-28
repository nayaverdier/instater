# isort: off
from ._task import TASKS, Task

# isort: on

from . import command, copy, debug, file, git, group, pacman, service, user  # noqa: F401

__all__ = ["TASKS", "Task"]
