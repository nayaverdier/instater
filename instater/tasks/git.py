from pathlib import Path

from instater.exceptions import InstaterError

from .. import util
from ..context import Context
from . import Task


class Git(Task):
    def __init__(self, *, repo: str, depth: int = None, dest: str, become: str = None, **kwargs):
        super().__init__(**kwargs)
        self.repo = repo
        self.depth = str(depth)
        self.dest = Path(dest)
        self.become = become

    def _clone(self):
        command = ["git", "clone", self.repo]
        if self.depth is not None:
            command += ["--depth", self.depth]

        command.append(str(self.dest))
        util.shell(command, become=self.become)

    def _get_remote(self) -> str:
        result = util.shell(["git", "config", "--get", "remote.origin.url"], directory=self.dest, become=self.become)
        return result.stdout

    def _should_pull(self) -> bool:
        result = util.shell(["git", "fetch", "--dry-run"], directory=self.dest, become=self.become)
        return result.stdout != "" or result.stderr != ""

    def _pull(self):
        branch = util.shell(["git", "branch", "--show-current"], directory=self.dest, become=self.become).stdout
        util.shell(["git", "pull", "origin", branch], directory=self.dest, become=self.become)

    def run_action(self, context: Context):
        if not self.dest.exists():
            if not context.dry_run:
                self._clone()
            return True

        if not (self.dest / ".git").exists():
            raise InstaterError(f"Git destination directory exists, but is not a git repo: {self.dest}")

        if self._get_remote() != self.repo:
            raise InstaterError(f"Git remote does not match current local git repo: {self.dest}")

        if self._should_pull():
            if not context.dry_run:
                self._pull()
            return True

        return False
