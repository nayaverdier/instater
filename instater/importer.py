import pkgutil
import sys
from pathlib import Path


def _import_exception_handler(module_name: str):
    print(f"Exception when importing module {module_name}")
    raise


_loaded = set()


def import_submodules(module_name: str):
    if module_name in _loaded:
        return

    module = sys.modules[module_name]

    path = Path(module.__file__).parent.absolute()
    prefix = module.__name__
    paths = [str(path)]

    for loader, submodule_name, is_pkg in pkgutil.walk_packages(paths, prefix + ".", onerror=_import_exception_handler):
        if is_pkg or submodule_name.split(".")[-1].startswith("_"):
            continue

        loader.find_module(submodule_name).load_module(submodule_name)  # type: ignore

    _loaded.add(module_name)
