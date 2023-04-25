import shlex
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Union
from urllib.request import urlopen

from .. import util
from ..context import Context
from ..exceptions import InstaterError
from . import Task


def _read(path: Path) -> bytes:
    with path.open("rb") as file:
        return file.read()


class Copy(Task):
    def __init__(
        self,
        *,
        src: Optional[str] = None,
        content: Optional[str] = None,
        url: Optional[str] = None,
        dest: str,
        owner: Optional[str] = None,
        group: Optional[str] = None,
        mode: Optional[Union[str, int]] = None,
        is_template: util.Bool = False,
        validate: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if not util.single_truthy(src, content, url):
            raise InstaterError("Must provide exactly one source of data to copy")

        if isinstance(mode, str):
            mode = int(mode, 8)

        self.src = Path(src) if src else None
        self.content = content
        self.url = url
        self.dest = Path(dest)
        self.owner = owner
        self.group = group
        self.mode = mode
        self.is_template = util.boolean(is_template)
        self.validate = validate

    def _update_metadata(self, file: Path, context: Context) -> bool:
        return util.update_file_metadata(file, self.owner, self.group, self.mode, context)

    def _validate(self, path: Path):
        if not self.validate:
            return

        # util.shell will raise an error on exit codes > 0
        util.shell(shlex.split(self.validate % path))

    def _read_for_diff(self, path: Path):
        if not path.exists():
            return ""

        try:
            return _read(path).decode("utf-8")
        except UnicodeDecodeError:
            return None

    def _explain_diff(self, src: Union[Path, str], dest: Path, context: Context, src_file=None):
        # extra condition so we only read the file content if necessary
        if context.explain:
            src_content = self._read_for_diff(src) if isinstance(src, Path) else src
            dest_content = self._read_for_diff(dest)

            if src_content is None or dest_content is None:
                context.explain_change(f"Binary files differ: {src} and {dest}")
            else:
                context.explain_change_diff(dest_content, src_content, str(dest), src_file or str(src))

    def _update_file_direct(self, src: Path, dest: Path, context: Context) -> bool:
        updated = False

        self._validate(src)

        if not dest.exists():
            context.explain_change(f"Destination file does not exist: {dest}")
            self._explain_diff(src, dest, context)
            if not context.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(src, dest)

            updated = True
        elif not src.samefile(dest) and _read(src) != _read(dest):
            context.explain_change(f"Source file ({src}) differs from destination file ({dest})")
            self._explain_diff(src, dest, context)
            if not context.dry_run:
                shutil.copy(src, dest)
            updated = True

        updated |= self._update_metadata(dest, context)
        return updated

    def _update_file_content(self, content: str, dest: Path, context: Context) -> bool:
        updated = False

        if content is not None and not content.endswith("\n"):
            content += "\n"

        if self.validate:
            with NamedTemporaryFile() as temp_file:
                temp_file.write(content.encode("utf-8"))
                temp_file.flush()
                self._validate(Path(temp_file.name))

        if not dest.exists():
            self._explain_diff(content, dest, context, src_file="Template")
            if not context.dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open("w") as f:
                    f.write(content)
            updated = True
        elif content.encode("utf-8") != _read(dest):
            self._explain_diff(content, dest, context, src_file="Template")
            if not context.dry_run:
                with dest.open("w") as f:
                    f.write(content)
            updated = True

        updated |= self._update_metadata(dest, context)
        return updated

    def _update_file_template(self, src: Path, dest: Path, context: Context) -> bool:
        with src.open() as f:
            content = context.jinja_string(f.read())

        return self._update_file_content(content, dest, context)

    def _update_file(self, src: Path, dest: Path, context: Context):
        if self.is_template:
            updated = self._update_file_template(src, dest, context)
        else:
            updated = self._update_file_direct(src, dest, context)

        if not updated:
            context.explain_skip(f"File {dest} already has the correct content and metadata")

        return updated

    def _update_dir(self, context: Context) -> bool:
        updated = False
        src: Path = self.src  # type: ignore

        for path in src.glob("**/*"):
            if path.is_file():
                dest_path = self.dest / path.relative_to(src)
                if self._update_file(path, dest_path, context):
                    updated = True

        return updated

    def run_action(self, context: Context) -> bool:
        src = self.src
        if src and not src.is_absolute():
            src = context.root_directory / src

        content = self.content
        if self.url:
            content = urlopen(self.url).read().decode("utf-8")

        dest = self.dest
        if not self.dest.is_absolute():
            dest = context.root_directory / dest

        if src and not src.exists():
            raise InstaterError(f"Source to copy does not exist: {src}")

        if content is not None or (src and src.is_file()):
            if dest.exists() and not dest.is_file():
                raise InstaterError(f"Destination is a directory, expected file: {dest}")

            if src:
                return self._update_file(src, dest, context)
            else:
                content_str: str = content  # type: ignore
                if self.is_template:
                    content_str = context.jinja_string(content_str)

                updated = self._update_file_content(content_str, dest, context)
                if not updated:
                    context.explain_skip(f"File {dest} already has the correct content and metadata")
                return updated
        else:
            if dest.exists() and not dest.is_dir():
                raise InstaterError(f"Destination is a file, expected directory: {dest}")

            return self._update_dir(context)


class Template(Copy):
    def __init__(self, **kwargs):
        kwargs.setdefault("is_template", True)
        super().__init__(**kwargs)
