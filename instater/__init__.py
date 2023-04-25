try:
    # Python 3.8+
    import importlib.metadata as _metadata
except ModuleNotFoundError:  # pragma: no cover
    # Python 3.7
    import importlib_metadata as _metadata  # type: ignore

from rich.traceback import install

from .exceptions import InstaterError
from .main import run_tasks

install()

__version__ = _metadata.version("instater")

__all__ = [
    "InstaterError",
    "__version__",
    "run_tasks",
]
