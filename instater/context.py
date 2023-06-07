import os.path
import time
import typing
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Optional

from jinja2 import Environment, FileSystemLoader
from rich.console import Console

from . import util


def _filename(path: str) -> str:
    return os.path.basename(path).rsplit(".", 1)[0]


def _jinja_environment(root_directory: Path) -> Environment:
    env = Environment(loader=FileSystemLoader(root_directory))
    env.filters["password_hash"] = util.password_hash
    env.filters["filename"] = _filename
    env.filters["bool"] = bool
    return env


class Context:
    def __init__(
        self,
        *,
        root_directory: Path,
        extra_vars: dict,
        tags: Iterable[str],
        dry_run: bool = False,
        quiet: bool = False,
        explain: bool = False,
    ):
        self.root_directory = root_directory
        self.tags = set(tags)
        self.dry_run = dry_run
        self.quiet = quiet
        self.explain = explain

        extra_vars["instater_dir"] = str(root_directory.resolve())
        self.variables = extra_vars

        self.jinja_env = _jinja_environment(root_directory)
        self.tasks: list = []
        self.statuses: typing.Counter[str] = Counter()

        self.start = time.time()

        self.console = Console()
        self._unprinted_messages: list = []
        self._inside_task: bool = False

        if TYPE_CHECKING:
            self.print = self.console.print

    def enter_task(self):
        if self._inside_task:
            raise RuntimeError("Already inside a task")

        self._inside_task = True

    def exit_task_changed(self):
        for args, kwargs in self._unprinted_messages:
            self.console.print(*args, **kwargs)

        self.exit_task_skipped()

    def exit_task_skipped(self):
        self._inside_task = False
        self._unprinted_messages.clear()

    if not TYPE_CHECKING:

        def print(self, *args, **kwargs):
            if self.quiet and self._inside_task:
                self._unprinted_messages.append((args, kwargs))
            else:
                self.console.print(*args, **kwargs)

    def jinja_object(
        self,
        template: object,
        extra_vars: Optional[dict] = None,
        convert_numbers: bool = False,
    ) -> object:
        if isinstance(template, str):
            return self.jinja_string(template, extra_vars, convert_numbers=convert_numbers)
        elif isinstance(template, list):
            return [self.jinja_object(item, extra_vars, convert_numbers=convert_numbers) for item in template]
        else:
            return template

    def jinja_string(self, template: str, extra_vars: Optional[dict] = None, convert_numbers: bool = False) -> str:
        if isinstance(template, str):
            vars = self.variables
            if extra_vars:
                vars = {**vars, **extra_vars}

            value = self.jinja_env.from_string(template).render(vars)

            if convert_numbers:
                try:
                    return int(value)  # type: ignore
                except ValueError:
                    pass

                try:
                    return float(value)  # type: ignore
                except ValueError:
                    pass

            return value
        else:
            return template

    def jinja_file(self, template_path: str, extra_vars: Optional[dict] = None) -> str:
        vars = self.variables
        if extra_vars:
            vars = {**vars, **extra_vars}
        return self.jinja_env.get_template(template_path).render(vars)

    def duration(self, start: Optional[float] = None):
        if start is None:
            start = self.start

        duration = round(time.time() - start, 3)
        return f"[white]({duration}s)[/white]"

    def print_summary(self):
        skipped = self.statuses["skipped"]
        changed = self.statuses["changed"]

        self.print(f"Summary {self.duration()}:", style="bold")
        self.print(f"  skipped: {skipped}", style="blue")
        # if this used style="yellow", the integer count would be turned blue by rich
        self.print(f"  [yellow]changed: {changed}[/yellow]")

    def explain_skip(self, message: str):
        if self.explain:
            self.print(message + "\n", style="blue")

    def explain_change(self, message: str):
        if self.explain:
            if self.dry_run:
                message = "[dry_run] " + message

            self.print(message + "\n", style="yellow bold")

    def explain_change_diff(self, a: str, b: str, file_a: str, file_b: str):
        if self.explain:
            diff = util.diff_lines(a, b, file_a, file_b)
            if self.dry_run:
                diff = "[dry_run]\n" + diff

            self.print(diff + "\n")
