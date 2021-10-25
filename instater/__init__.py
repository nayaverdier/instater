from importlib import resources

from rich.traceback import install

from .exceptions import InstaterError
from .main import run_tasks

install()

VERSION = resources.read_text("instater", "VERSION").strip()

__all__ = [
    "InstaterError",
    "VERSION",
    "run_tasks",
]
