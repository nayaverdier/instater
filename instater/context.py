import typing
from collections import Counter
from pathlib import Path
from typing import Iterable, List

from jinja2 import Environment, FileSystemLoader
from rich.console import Console

import instater

from . import util


def _jinja_environment(root_directory: Path) -> Environment:
    env = Environment(loader=FileSystemLoader(root_directory))
    env.filters["password_hash"] = util.password_hash
    return env


class Context:
    def __init__(self, root_directory: Path, extra_vars: dict, tags: Iterable[str], dry_run: bool = False):
        self.root_directory = root_directory
        self.tags = set(tags)
        self.dry_run = dry_run

        extra_vars["instater_dir"] = str(root_directory)
        self.variables = extra_vars

        self.jinja_env = _jinja_environment(root_directory)
        self.tasks: List[instater.tasks.Task] = []
        self.statuses: typing.Counter[str] = Counter()

        self.console = Console()
        self.print = self.console.print

    def jinja_object(self, template: object, extra_vars: dict = None) -> object:
        if isinstance(template, str):
            return self.jinja_string(template, extra_vars)
        elif isinstance(template, list):
            return [self.jinja_object(item, extra_vars) for item in template]
        else:
            return template

    def jinja_string(self, template: str, extra_vars: dict = None) -> str:
        if isinstance(template, str):
            vars = self.variables
            if extra_vars:
                vars = {**vars, **extra_vars}
            return self.jinja_env.from_string(template).render(vars)
        else:
            return template

    def jinja_file(self, template_path: str, extra_vars: dict = None) -> str:
        vars = self.variables
        if extra_vars:
            vars = {**vars, **extra_vars}
        return self.jinja_env.get_template(template_path).render(vars)

    def print_summary(self):
        skipped = self.statuses["skipped"]
        changed = self.statuses["changed"]

        self.print("Summary:", style="bold")
        self.print(f"  skipped: {skipped}", style="blue")
        # if this used style="yellow", the integer count would be turned blue by rich
        self.print(f"  [yellow]changed: {changed}[/yellow]")
