import os
from pathlib import Path
from typing import Union

from instater.exceptions import InstaterError

from .. import util
from ..context import Context
from . import Task


class File(Task):
    def __init__(
        self,
        *,
        path: str,
        target: str = None,
        owner: str = None,
        group: str = None,
        mode: Union[str, int] = None,
        directory: util.Bool = False,
        symlink: util.Bool = False,
        hard_link: util.Bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if isinstance(mode, str):
            mode = int(mode, 8)

        if not util.single_truthy(directory, symlink, hard_link, allow_zero=True):
            raise InstaterError(f"[{self.name}] Must only provide ony of directory, symlink, or hard_link")

        if target and (not symlink and not hard_link):
            raise InstaterError("Must provide a target with symlink/hard_link")

        self.path = Path(path)
        self.target = Path(target) if target is not None else None
        self.owner = owner
        self.group = group
        self.mode = mode
        self.directory = util.boolean(directory)
        self.symlink = util.boolean(symlink)
        self.hard_link = util.boolean(hard_link)

    def _create_file(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch()

    def _create_directory(self):
        self.path.mkdir(parents=True, exist_ok=True)

    def _create_symlink(self):
        target: Path = self.target  # type: ignore
        os.symlink(target, self.path)

    def _create_hard_link(self):
        target: Path = self.target  # type: ignore
        os.link(target, self.path)

    def run_action(self, context: Context):
        updated = False

        if not self.path.exists():
            if not context.dry_run:
                if self.directory:
                    self._create_directory()
                elif self.symlink:
                    self._create_symlink()
                elif self.hard_link:
                    self._create_hard_link()
                else:
                    self._create_file()
            updated = True
        elif self.symlink:
            if not self.path.is_symlink():
                raise InstaterError(f"Path exists but is not a symlink: {self.path}")
        elif self.directory:
            if not self.path.is_dir():
                raise InstaterError(f"Path exists but is not a directory: {self.path}")
        elif self.hard_link:
            pass
        else:
            if not self.path.is_file():
                raise InstaterError(f"Path exists but is not a file: {self.path}")

        updated |= util.update_file_metadata(self.path, self.owner, self.group, self.mode, context.dry_run)

        return updated


class Directory(File):
    def __init__(self, **kwargs):
        kwargs["directory"] = True
        super().__init__(**kwargs)


class Symlink(File):
    def __init__(self, **kwargs):
        kwargs["symlink"] = True
        super().__init__(**kwargs)


class HardLink(File):
    def __init__(self, **kwargs):
        kwargs["hard_link"] = True
        super().__init__(**kwargs)
